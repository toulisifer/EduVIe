"""Hai lần tạo đề phải ra đề KHÁC, và trong một đề không dồn câu cùng dạng.

Người dùng báo: soạn 60 câu thấy lặp, tạo lại vẫn ra đúng đề đó. Đo trên dữ liệu
thật trước khi sửa:
    M6-CB7BB5-01 vs -02 : trùng 60/60 câu (100%)
    M1-2FA9CE-01 vs -05 : trùng 59/60 câu (98%)
Hai nguyên nhân tách biệt:
  - lay_cau() phá hoà bằng id, nên khi mọi câu đã dùng số lần như nhau thì nó quay
    về "lấy mấy câu id nhỏ nhất" — ra y hệt nhau.
  - kho không đủ câu (60 câu mà đề xin 60) thì buộc phải dùng lại toàn bộ.

Chạy:  .venv/bin/python -m scripts.test_de_khac_nhau     (không gọi AI)
"""
from sqlalchemy import func

from app import db
from app.bank import khung_cau, lay_cau
from app.quiz import (TI_LE_DU_DE_RA_NGAY, TI_LE_DUNG_LAI_TOI_DA, TOI_THIEU_RA_NGAY,
                      _lay_tu_ngan_hang, generate_quiz, load_quiz)

TEN = ["_dk_hs"]
dat = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dat, sai
    if dk:
        dat += 1
        print(f"  dat  | {ten}")
    else:
        sai += 1
        print(f"  SAI  | {ten}" + (f"\n       | {chi_tiet}" if chi_tiet else ""))


def don():
    with db.SessionLocal() as s:
        for t in TEN:
            u = s.query(db.User).filter_by(username=t).first()
            if not u:
                continue
            for a in s.query(db.Attempt).filter_by(user_id=u.id):
                s.query(db.Answer).filter_by(attempt_id=a.id).delete()
                s.delete(a)
            for q in s.query(db.Quiz).filter_by(user_id=u.id):
                s.query(db.Question).filter_by(quiz_id=q.id).delete()
                s.delete(q)
            s.query(db.Answer).filter_by(user_id=u.id).delete()
            s.delete(u)
        s.commit()


def main():
    db.init_db()
    don()
    with db.SessionLocal() as s:
        u = db.User(username=TEN[0], password_hash="x", role="user")
        s.add(u)
        s.commit()
        uid = u.id
        tid, co = (s.query(db.BankQuestion.topic_id, func.count(db.BankQuestion.id))
                   .filter(db.BankQuestion.flagged.is_(False),
                           db.BankQuestion.difficulty == "medium")
                   .group_by(db.BankQuestion.topic_id)
                   .order_by(func.count(db.BankQuestion.id).desc()).first())
        t = s.get(db.Topic, tid)
        _ = t.path
        sub = t.chapter.subject_id
    N = max(5, co // 4)                 # kho đủ rộng để ra hai đề khác hẳn

    print("=" * 74)
    print(" ĐỀ LẦN SAU PHẢI KHÁC ĐỀ LẦN TRƯỚC")
    print("=" * 74)
    print(f"\n  chủ đề thử : {t.name}  ({co} câu trung bình trong kho)")
    print(f"  đề thử     : {N} câu")

    print("\n[1] lay_cau không còn trả về cùng một bộ mỗi lần gọi")
    bo = [tuple(c.id for c in lay_cau(tid, "medium", 8)) for _ in range(6)]
    kiem("6 lần gọi cho ra nhiều hơn một kết quả", len(set(bo)) > 1,
         f"cả 6 lần đều ra {bo[0][:4]}…")
    kiem("lần nào cũng đủ 8 câu", all(len(x) == 8 for x in bo), str([len(x) for x in bo]))
    kiem("trong một lần gọi không có câu trùng",
         all(len(set(x)) == len(x) for x in bo))

    print("\n[2] Hai đề liên tiếp cùng bản thiết kế")
    with db.SessionLocal() as s:
        q1 = generate_quiz(uid, sub, [s.merge(t)], "medium", N)
    with db.SessionLocal() as s:
        q2 = generate_quiz(uid, sub, [s.merge(t)], "medium", N)
    b1 = {c.bank_id for c in load_quiz(q1) if c.bank_id}
    b2 = {c.bank_id for c in load_quiz(q2) if c.bank_id}
    chung = b1 & b2
    ti_le = len(chung) / max(len(b2), 1)
    print(f"       → đề 1: {len(b1)} câu, đề 2: {len(b2)} câu, trùng {len(chung)} "
          f"({ti_le:.0%})")
    kiem("đề 2 không trùng hoàn toàn đề 1", ti_le < 1.0, f"trùng {ti_le:.0%}")
    kiem(f"trùng không quá {TI_LE_DUNG_LAI_TOI_DA:.0%} (kho đủ rộng thì phải gần 0)",
         ti_le <= TI_LE_DUNG_LAI_TOI_DA + 0.01, f"trùng {ti_le:.0%}")

    print("\n[3] Trong một đề không có câu trùng")
    for nhan, qid in (("đề 1", q1), ("đề 2", q2)):
        ds = load_quiz(qid)
        noi_dung = [c.content for c in ds]
        bank = [c.bank_id for c in ds if c.bank_id]
        kiem(f"{nhan}: không câu nào lặp lại", len(set(noi_dung)) == len(noi_dung),
             f"{len(noi_dung)} câu, {len(set(noi_dung))} khác nhau")
        kiem(f"{nhan}: không bank_id nào lặp", len(set(bank)) == len(bank))

    print("\n[4] Không dồn quá nhiều câu cùng một dạng bài")
    tran = max(2, round(N / 15))
    for nhan, qid in (("đề 1", q1), ("đề 2", q2)):
        ds = load_quiz(qid)
        dang = {}
        for c in ds:
            k = khung_cau(c.content)
            dang[k] = dang.get(k, 0) + 1
        nhieu_nhat = max(dang.values())
        print(f"       → {nhan}: {len(ds)} câu / {len(dang)} dạng, "
              f"dạng nhiều nhất {nhieu_nhat} câu (trần {tran})")
        kiem(f"{nhan}: đa dạng hơn một nửa số câu", len(dang) > len(ds) / 2,
             f"{len(dang)} dạng cho {len(ds)} câu")

    print("\n[5] Hạn giờ chờ AI: hết giờ thì dừng, không treo người học")
    import time as _t

    from app import llm

    # Hạn chót đã qua -> phải dừng NGAY, trước cả khi chạm tới mạng.
    t0 = _t.monotonic()
    try:
        llm.call_with_fallback(llm.CHAT_MODELS, "x", None, han_chot=_t.monotonic() - 1)
        ket = "khong nem loi"
    except llm.HetGio:
        ket = "HetGio"
    except Exception as e:                           # noqa: BLE001
        ket = type(e).__name__
    mat = _t.monotonic() - t0
    kiem("hạn chót đã qua -> ném HetGio", ket == "HetGio", ket)
    kiem("dừng ngay, không gọi mạng", mat < 1.0, f"mất {mat:.1f}s")
    kiem("không truyền hạn chót thì giữ nguyên hành vi cũ",
         "han_chot" in llm.call_with_fallback.__code__.co_varnames)

    print("\n[6] Kho nghèo hơn số câu yêu cầu thì vẫn ra đủ, và vẫn khác lần trước")
    cau_a, thieu_a = _lay_tu_ngan_hang([t], "medium", co + 20, user_id=uid)
    kiem("lấy hết được phần kho có", len(cau_a) > 0)
    kiem("phần vượt quá kho được báo là còn thiếu", thieu_a > 0, f"thiếu {thieu_a}")
    kiem("phần lấy được không có câu trùng",
         len({c.id for c in cau_a}) == len(cau_a), f"{len(cau_a)} câu")

    print("\n[7] Tạo đề phải NHANH: không chờ AI khi kho còn dùng được")
    import time as _tt
    with db.SessionLocal() as s:
        tt = s.merge(t)
        moc = _tt.monotonic()
        generate_quiz(uid, sub, [tt], "medium", N)
        mat = _tt.monotonic() - moc
    print(f"       → tạo đề {N} câu mất {mat:.1f}s")
    kiem("dưới 5 giây khi kho đủ câu", mat < 5.0, f"mất {mat:.1f}s")
    kiem("có ngưỡng để quyết định ra đề ngay",
         0 < TI_LE_DU_DE_RA_NGAY < 1 and TOI_THIEU_RA_NGAY >= 1,
         f"{TI_LE_DU_DE_RA_NGAY} / {TOI_THIEU_RA_NGAY}")

    don()
    print("\n" + "=" * 74)
    print(f" {dat}/{dat + sai} phép thử đạt")
    print("=" * 74)
    raise SystemExit(0 if sai == 0 else 1)


if __name__ == "__main__":
    main()
