"""Logic ra đề: chia số câu theo chỗ yếu, tránh câu đã gặp, xoay vòng ngân hàng.

Ba tính chất này trước đây đều không có:
  - số câu luôn chia ĐỀU cho mọi chủ đề, dù trọng số ưu tiên đã được tính ra
    (recommend_quiz trả trường "weights" mà không ai đọc);
  - đề mới có thể lặp lại đúng câu người học vừa làm sai hôm qua;
  - ngân hàng luôn bị rút từ đầu theo id, nên chủ đề 57 câu chỉ dùng tới 5 câu đầu.

Chạy:  .venv/bin/python -m scripts.test_ra_de      (không gọi AI nếu kho đủ câu)
"""
from datetime import datetime, timedelta

from sqlalchemy import func

from app import db
from app.bank import lay_cau
from app.learning import trong_so_uu_tien
from app.quiz import _lay_tu_ngan_hang, generate_quiz, load_quiz, submit_attempt

TEN = ["_rd_hs"]
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


def hai_chu_de(toi_thieu=8):
    """Hai chủ đề cùng môn, mỗi chủ đề còn nhiều câu trong kho."""
    with db.SessionLocal() as s:
        rows = (s.query(db.BankQuestion.topic_id, func.count(db.BankQuestion.id).label("n"))
                .filter(db.BankQuestion.flagged.is_(False),
                        db.BankQuestion.difficulty == "medium")
                .group_by(db.BankQuestion.topic_id)
                .having(func.count(db.BankQuestion.id) >= toi_thieu)
                .order_by(func.count(db.BankQuestion.id).desc()).all())
        theo_mon = {}
        for tid, n in rows:
            t = s.get(db.Topic, tid)
            theo_mon.setdefault(t.chapter.subject_id, []).append(t)
        for sid, ts in theo_mon.items():
            if len(ts) >= 2:
                for t in ts[:2]:
                    _ = t.path
                return ts[0], ts[1], sid
    return None, None, None


def main():
    db.init_db()
    don()
    yeu, gioi, sub = hai_chu_de()
    if not yeu:
        print("Khong du du lieu: can 2 chu de cung mon, moi chu de >= 10 cau trong kho.")
        raise SystemExit(1)
    with db.SessionLocal() as s:
        u = db.User(username=TEN[0], password_hash="x", role="user")
        s.add(u)
        s.commit()
        uid = u.id

    print("=" * 72)
    print(" LOGIC RA DE")
    print("=" * 72)
    print(f"\nchu de A (se cho yeu) : {yeu.name}")
    print(f"chu de B (se cho gioi): {gioi.name}")

    # dựng lịch sử: A làm sai nhiều, B làm đúng nhiều — ghi thẳng vào Answer nên
    # không dính câu nào của ngân hàng, tách bạch với phép thử "tránh câu đã gặp"
    moc = datetime.utcnow() - timedelta(hours=2)
    with db.SessionLocal() as s:
        for i in range(10):
            s.add(db.Answer(user_id=uid, topic_id=yeu.id, difficulty="medium",
                            is_correct=(i < 1), answered_at=moc + timedelta(minutes=i)))
            s.add(db.Answer(user_id=uid, topic_id=gioi.id, difficulty="medium",
                            is_correct=(i < 9), answered_at=moc + timedelta(minutes=i)))
        s.commit()

    print("\n[1] Trong so uu tien phan anh dung tinh trang hoc")
    w = trong_so_uu_tien(uid, [yeu.id, gioi.id], sub)
    print(f"       -> {yeu.name[:28]}: {w[yeu.id]:.0f}   {gioi.name[:28]}: {w[gioi.id]:.0f}")
    kiem("chu de yeu co trong so cao hon", w[yeu.id] > w[gioi.id], str(w))

    print("\n[2] De chia nhieu cau hon cho chu de yeu")
    cau, thieu = _lay_tu_ngan_hang([yeu, gioi], "medium", 10, user_id=uid, uu_tien=w)
    dem = {yeu.id: 0, gioi.id: 0}
    for c in cau:
        dem[c.topic_id] = dem.get(c.topic_id, 0) + 1
    print(f"       -> yeu {dem[yeu.id]} cau / gioi {dem[gioi.id]} cau (tong {len(cau)})")
    kiem("lay du 10 cau tu kho", len(cau) == 10 and thieu == 0, f"{len(cau)} cau, thieu {thieu}")
    kiem("chu de yeu duoc nhieu cau hon", dem[yeu.id] > dem[gioi.id], str(dem))
    kiem("chu de gioi van co cau (khong bo han)", dem[gioi.id] > 0, str(dem))

    deu, _ = _lay_tu_ngan_hang([yeu, gioi], "medium", 10, user_id=uid, uu_tien=None)
    dem_deu = {}
    for c in deu:
        dem_deu[c.topic_id] = dem_deu.get(c.topic_id, 0) + 1
    kiem("khong truyen trong so thi chia deu nhu cu",
         dem_deu.get(yeu.id) == dem_deu.get(gioi.id), str(dem_deu))

    print("\n[3] Khong ra lai cau nguoi hoc da tra loi")
    with db.SessionLocal() as s:
        q1 = generate_quiz(uid, sub, [s.merge(yeu)], "medium", 5)
    ds1 = load_quiz(q1)
    bank1 = {q.bank_id for q in ds1 if q.bank_id}
    kiem("de dau lay tu ngan hang", len(bank1) == 5, f"{len(bank1)} cau co bank_id")
    submit_attempt(q1, uid, {q.id: 0 for q in ds1})

    with db.SessionLocal() as s:
        q2 = generate_quiz(uid, sub, [s.merge(yeu)], "medium", 5)
    bank2 = {q.bank_id for q in load_quiz(q2) if q.bank_id}
    chung = bank1 & bank2
    print(f"       -> de 1: {sorted(bank1)}")
    print(f"       -> de 2: {sorted(bank2)}")
    kiem("de sau khong lap lai cau da lam", not chung, f"trung {sorted(chung)}")

    print("\n[4] Ngan hang xoay vong theo so lan da dung")
    with db.SessionLocal() as s:
        dung = {c.id: (c.times_used or 0)
                for c in s.query(db.BankQuestion).filter(db.BankQuestion.id.in_(bank1))}
    kiem("cau da vao de duoc dem times_used", all(v >= 1 for v in dung.values()), str(dung))

    # lay_cau xep theo times_used roi boc NGAU NHIEN khi hoa, nen khong the doi hoi
    # dung mot bo id. Doi hoi dung: moi cau lay ra phai nam trong nhom it dung nhat.
    with db.SessionLocal() as s:
        muc = {c.id: (c.times_used or 0) for c in s.query(db.BankQuestion)
               .filter_by(topic_id=yeu.id, flagged=False, difficulty="medium")}
    lay = [c.id for c in lay_cau(yeu.id, "medium", 3)]
    thap_nhat = sorted(muc.values())[:3]
    kiem("lay_cau chi lay trong nhom it dung nhat",
         sorted(muc[i] for i in lay) == thap_nhat,
         f"{[muc[i] for i in lay]} vs {thap_nhat}")
    nhieu_lan = {tuple(sorted(c.id for c in lay_cau(yeu.id, "medium", 3))) for _ in range(8)}
    kiem("goi nhieu lan khong ra mai mot bo (da bo pha hoa bang id)",
         len(nhieu_lan) > 1 or len(muc) <= 3, f"8 lan deu ra {nhieu_lan}")
    lay_tru = [c.id for c in lay_cau(yeu.id, "medium", 3, tru=set(lay))]
    kiem("tham so tru loai dung cau da chon", not (set(lay) & set(lay_tru)), str(lay_tru))

    print("\n[5] Het cau chua gap thi van ra duoc de, khong bo trong")
    with db.SessionLocal() as s:
        tong = (s.query(func.count(db.BankQuestion.id))
                .filter_by(topic_id=yeu.id, flagged=False).scalar())
    cau5, thieu5 = _lay_tu_ngan_hang([yeu], "medium", min(tong, 8), user_id=uid)
    kiem("van lay du so cau yeu cau", thieu5 == 0, f"thieu {thieu5}")
    kiem("khong co cau nao trung trong cung mot de",
         len({c.id for c in cau5}) == len(cau5), f"{len(cau5)} cau")

    don()
    print("\n" + "=" * 72)
    print(f" {dat}/{dat + sai} phep thu dat")
    print("=" * 72)
    raise SystemExit(0 if sai == 0 else 1)


if __name__ == "__main__":
    main()
