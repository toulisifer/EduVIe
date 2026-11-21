"""Ngân hàng câu hỏi: nạp, đếm, lấy ra, ghép thành đề mà không gọi AI.

Trả lời đúng tình huống giáo viên nêu: kho có ít câu hơn số đề xin thì xử lý ra sao.
Không tốn lượt gọi AI.

  python -m scripts.test_ngan_hang
"""
from app import bank, db
from app.quiz import generate_quiz

TEN = "_nh_hoc_sinh"
dat, sai = [], []


def thu(mo_ta, ok, chi_tiet=""):
    (dat if ok else sai).append(mo_ta)
    print(f"  {'✓' if ok else '✗'} {mo_ta}")
    if chi_tiet:
        print(f"      {chi_tiet}")


def don(topic_ids):
    with db.SessionLocal() as s:
        u = s.query(db.User).filter_by(username=TEN).first()
        if u:
            for q in s.query(db.Quiz).filter_by(user_id=u.id):
                s.query(db.Question).filter_by(quiz_id=q.id).delete()
                s.delete(q)
            s.query(db.Answer).filter_by(user_id=u.id).delete()
            s.delete(u)
        s.query(db.BankQuestion).filter(db.BankQuestion.source == "test").delete()
        s.commit()


def main():
    db.init_db()
    with db.SessionLocal() as s:
        sub = s.query(db.Subject).filter_by(name="Khoa học tự nhiên 8").first()
        topics = [t for c in sorted(sub.chapters, key=lambda c: c.order) for t in c.topics][:2]
        tids = [t.id for t in topics]
        ten_cd = [t.name for t in topics]
        sid = sub.id
    don(tids)

    print(f"Dùng 2 chủ đề của {sub.name}: {ten_cd}\n")

    print("1. Nạp câu vào kho")
    them = 0
    for i, tid in enumerate(tids):
        for j in range(4 if i == 0 else 10):      # chủ đề 1 có 4 câu, chủ đề 2 có 10
            cid = bank.them_cau(tid, "easy", f"[kiểm thử {tid}.{j}] 2 + {j} bằng bao nhiêu?",
                                ["a", "b", "c", "d"], j % 4, "giải thích thử", source="test")
            them += cid is not None
    thu("nạp 14 câu mới", them == 14, f"đã nạp {them}")

    trung = bank.them_cau(tids[0], "easy", "[kiểm thử %d.0] 2 + 0 bằng bao nhiêu?" % tids[0],
                          ["a", "b", "c", "d"], 0, "", source="test")
    thu("nạp lại câu y hệt thì bị bỏ qua", trung is None)

    print("\n2. Đếm số câu dùng được")
    co = bank.dem_kha_dung(tids, "easy")
    thu("đếm đúng theo từng chủ đề", co[tids[0]] >= 4 and co[tids[1]] >= 10, f"{co}")

    print("\n3. Kho ít hơn số câu đề xin — tình huống giáo viên nêu")
    from app.learning import phan_bo_cau_hoi
    bo = phan_bo_cau_hoi({t: 1.0 for t in tids}, 20, kha_dung=co)
    thu("xin 20 câu, kho chỉ có 14 -> lấy hết 14, không bịa thêm",
        sum(bo.values()) == sum(co.values()),
        f"{bo} = {sum(bo.values())}/20, kho có {sum(co.values())}")

    bo2 = phan_bo_cau_hoi({t: 1.0 for t in tids}, 12, kha_dung=co)
    thu("xin 12 câu: chủ đề thiếu chỉ góp 4, phần còn lại dồn sang chủ đề kia",
        sum(bo2.values()) == 12 and bo2[tids[0]] <= co[tids[0]], f"{bo2}")

    print("\n4. Ghép đề từ kho, KHÔNG gọi AI")
    with db.SessionLocal() as s:
        u = db.User(username=TEN, password_hash="x", role="user")
        s.add(u); s.commit()
        uid = u.id
        tops = [s.get(db.Topic, t) for t in tids]
        for t in tops:
            _ = t.path
        qid = generate_quiz(uid, sid, tops, "easy", 8)

    with db.SessionLocal() as s:
        qs = s.query(db.Question).filter_by(quiz_id=qid).all()
        tu_kho = [q for q in qs if q.bank_id]
        quiz = s.get(db.Quiz, qid)
    thu("đề có đủ 8 câu", len(qs) == 8, f"{len(qs)} câu, mã đề {quiz.code}")
    thu("mọi câu đều lấy từ kho (bank_id có giá trị)", len(tu_kho) == len(qs),
        f"{len(tu_kho)}/{len(qs)} câu có nguồn trong kho")

    print("\n5. Lấy câu phải ĐỔI giữa hai lần gọi (để tạo lại thì ra đề khác)")
    # Giao kèo cũ ở đây là "gọi hai lần cho cùng kết quả", để hai học sinh nhận cùng
    # một đề. Giao kèo đó đã sai từ khi có mã đề: hai người nhận cùng đề là nhờ MÃ
    # (de_theo_ma chép lại đúng đề đã lưu), không nhờ việc rút câu lặp lại được.
    # Giữ nguyên nó thì tạo đề lần hai ra y hệt lần một — đúng lỗi người dùng báo.
    nhieu_lan = {tuple(c.id for c in bank.lay_cau(tids[1], "easy", 5)) for _ in range(8)}
    l1 = [c.id for c in bank.lay_cau(tids[1], "easy", 5)]
    thu("gọi nhiều lần không ra mãi một bộ", len(nhieu_lan) > 1,
        f"8 lần đều ra {next(iter(nhieu_lan))}")
    thu("lần nào cũng đủ số câu", all(len(x) == 5 for x in nhieu_lan))
    thu("trong một lần gọi không có câu trùng",
        all(len(set(x)) == len(x) for x in nhieu_lan))

    print("\n6. Câu bị báo sai thì không được dùng nữa")
    truoc = bank.dem_kha_dung([tids[1]], "easy")[tids[1]]
    bank.danh_dau_sai(l1[0])
    sau = bank.dem_kha_dung([tids[1]], "easy")[tids[1]]
    thu("đánh dấu sai thì số câu dùng được giảm", sau == truoc - 1, f"{truoc} -> {sau}")
    thu("câu đó không còn được lấy ra", l1[0] not in [c.id for c in bank.lay_cau(tids[1], "easy", 9)])

    don(tids)
    print(f"\n{len(dat)}/{len(dat) + len(sai)} phép thử đạt")
    for m in sai:
        print("  SAI:", m)
    print("(đã xoá dữ liệu thử)")
    return 1 if sai else 0


if __name__ == "__main__":
    raise SystemExit(main())
