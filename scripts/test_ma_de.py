"""Mã đề: mỗi lần tạo ra một đề KHÁC, nhưng gõ lại mã thì ra ĐÚNG đề cũ.

Trước đây mã đề quyết định luôn nội dung: cùng bản thiết kế thì mãi mãi một đề,
làm lại cũng y hệt. Nay mã đề đổi vai thành chìa khoá tra cứu:

    M1-A036FD-02
    └─ nền ──┘ └┘ lượt thứ mấy

  - nền  = băm từ môn + chủ đề + độ khó + số câu (không đổi, vẫn so sánh được)
  - lượt = tăng mỗi lần tạo đề -> đề mới, rút sang đoạn kho chưa dùng

Chạy:  .venv/bin/python -m scripts.test_ma_de
Không gọi AI nếu ngân hàng còn đủ câu. Dữ liệu thử được xoá sau khi chạy.
"""
from app import db
from app.quiz import (chuan_hoa_ma, de_theo_ma, generate_quiz, load_quiz,
                      ma_bien_the, ma_de)

TEN = ["_md_an", "_md_binh"]
dat = sai = 0


def kiem(ten: str, dieu_kien: bool, chi_tiet: str = ""):
    global dat, sai
    if dieu_kien:
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
            for q in s.query(db.Quiz).filter_by(user_id=u.id):
                s.query(db.Question).filter_by(quiz_id=q.id).delete()
                s.delete(q)
            s.query(db.Answer).filter_by(user_id=u.id).delete()
            s.delete(u)
        s.commit()


def nguoi(ten: str) -> int:
    with db.SessionLocal() as s:
        u = db.User(username=ten, password_hash="x", role="user")
        s.add(u); s.commit()
        return u.id


def main():
    db.init_db()
    don()
    an, binh = nguoi(TEN[0]), nguoi(TEN[1])

    # chọn một chủ đề còn nhiều câu trong kho để khỏi phải gọi AI
    with db.SessionLocal() as s:
        from sqlalchemy import func
        tid, co = (s.query(db.BankQuestion.topic_id, func.count(db.BankQuestion.id))
                   .filter(db.BankQuestion.flagged.is_(False),
                           db.BankQuestion.difficulty == "medium")
                   .group_by(db.BankQuestion.topic_id)
                   .order_by(func.count(db.BankQuestion.id).desc()).first())
        t = s.get(db.Topic, tid)
        _ = t.path
        sub = t.chapter.subject_id
    N = 5
    print("=" * 70)
    print(" MÃ ĐỀ: TẠO THÌ KHÁC, GÕ MÃ THÌ GIỐNG")
    print("=" * 70)
    print(f"\nchủ đề thử: {t.name} ({co} câu trong kho, đề {N} câu)")

    # ---------------------------------------------------------------- 1
    print("\n[1] Phần nền của mã vẫn là hàm thuần của bản thiết kế")
    nen = ma_de(sub, [tid], "medium", N)
    kiem("cùng yêu cầu -> cùng nền", ma_de(sub, [tid], "medium", N) == nen)
    kiem("thứ tự chủ đề không đổi nền",
         ma_de(sub, [4, 2], "easy", 6) == ma_de(sub, [2, 4], "easy", 6))
    kiem("đổi số câu thì đổi nền",
         ma_de(sub, [2, 4], "easy", 6) != ma_de(sub, [2, 4], "easy", 10))
    kiem("đổi độ khó thì đổi nền",
         ma_de(sub, [2, 4], "easy", 6) != ma_de(sub, [2, 4], "hard", 6))

    # ---------------------------------------------------------------- 2
    print("\n[2] Mỗi lần tạo đề là một đề khác")
    with db.SessionLocal() as s:
        tt = s.merge(t)
        q1 = generate_quiz(an, sub, [tt], "medium", N)
        q2 = generate_quiz(an, sub, [tt], "medium", N)
    d1, d2 = load_quiz(q1), load_quiz(q2)
    c1 = [q.content for q in d1]
    c2 = [q.content for q in d2]
    with db.SessionLocal() as s:
        m1 = s.get(db.Quiz, q1).code
        m2 = s.get(db.Quiz, q2).code
    print(f"       → lần 1: {m1}   lần 2: {m2}")
    kiem("hai lần cho hai mã khác nhau", m1 != m2, f"{m1} vs {m2}")
    kiem("cùng phần nền", m1.startswith(nen) and m2.startswith(nen), f"nền {nen}")
    kiem("nội dung thực sự khác", set(c1) != set(c2))
    kiem("không câu nào trùng nhau", not (set(c1) & set(c2)),
         f"trùng {len(set(c1) & set(c2))} câu")
    kiem("cả hai đề đều đủ câu", len(c1) == N and len(c2) == N, f"{len(c1)} và {len(c2)}")

    # ---------------------------------------------------------------- 3
    print("\n[3] Gõ mã thì nhận đúng đề đó")
    q3 = de_theo_ma(m1, binh)
    c3 = [q.content for q in load_quiz(q3)]
    kiem("Bình gõ mã của An -> ra đúng đề đó", c3 == c1,
         f"{len(c3)} câu, giống: {c3 == c1}")
    kiem("thứ tự câu giữ nguyên", c3 == c1)
    with db.SessionLocal() as s:
        q = s.get(db.Quiz, q3)
        kiem("bài làm là của Bình, không phải của An", q.user_id == binh)
        kiem("vẫn mang đúng mã đó", q.code == m1, str(q.code))

    # ---------------------------------------------------------------- 4
    print("\n[4] Gõ thiếu số lượt thì lấy đề mới nhất")
    # Dùng số câu khác để có một phần nền chưa đề nào mang đúng chuỗi đó. Nếu có đề
    # mang đúng mã nền (dữ liệu từ bản cũ, khi mã chưa có số lượt) thì khớp chính xác
    # phải thắng — đó mới là đề người ta muốn mở.
    N2 = N + 2
    nen2 = ma_de(sub, [tid], "medium", N2)
    with db.SessionLocal() as s:
        co_san = s.query(db.Quiz).filter(db.Quiz.code == nen2).first() is not None
    kiem("tình huống sạch: chưa đề nào mang đúng mã nền", not co_san, nen2)
    with db.SessionLocal() as s:
        tt = s.merge(t)
        generate_quiz(an, sub, [tt], "medium", N2)
        qb = generate_quiz(an, sub, [tt], "medium", N2)
    cb = [q.content for q in load_quiz(qb)]
    q4 = de_theo_ma(nen2, binh)
    c4 = [q.content for q in load_quiz(q4)] if q4 else []
    kiem("gõ phần nền -> ra đề lượt gần nhất", c4 == cb, f"khớp lượt cuối: {c4 == cb}")

    with db.SessionLocal() as s:
        cu = db.Quiz(user_id=an, subject_id=sub, difficulty="medium", code=nen2)
        s.add(cu); s.flush()
        s.add(db.Question(quiz_id=cu.id, topic_id=tid, difficulty="medium",
                          content="__cau_de_cu__", options=["a", "b", "c", "d"],
                          correct=0, explanation=""))
        s.commit()
    c4b = [q.content for q in load_quiz(de_theo_ma(nen2, binh))]
    kiem("có đề mang đúng mã nền -> khớp chính xác thắng",
         c4b == ["__cau_de_cu__"], str(c4b)[:60])

    # ---------------------------------------------------------------- 5
    print("\n[5] Gõ sai thì báo không có, không dựng đề rỗng")
    kiem("mã không tồn tại -> None", de_theo_ma("M9-ZZZZZZ-99", binh) is None)
    kiem("mã rỗng -> None", de_theo_ma("   ", binh) is None)

    # ---------------------------------------------------------------- 6
    print("\n[6] Gõ tay lôi thôi vẫn hiểu")
    kiem("chữ thường + khoảng trắng", chuan_hoa_ma("  m1-a036fd-02 ") == "M1-A036FD-02")
    kiem("gạch dài copy từ Word", chuan_hoa_ma("M1—A036FD") == "M1-A036FD")
    q5 = de_theo_ma(m1.lower(), binh)
    kiem("mở được đề bằng mã viết thường", q5 is not None)

    # ---------------------------------------------------------------- 7
    print("\n[7] Số lượt không nhảy lung tung")
    ma_moi, lan = ma_bien_the(nen)
    kiem("lượt kế tiếp lớn hơn số đề đã có", lan >= 3, f"lan={lan}")
    kiem("mã mới chưa ai dùng", ma_moi not in (m1, m2), ma_moi)

    # Xoá đề mới nhất rồi xin mã tiếp: không được cấp lại mã vừa xoá, vì ai đã ghi
    # mã đó lại sẽ mở ra một đề hoàn toàn khác.
    with db.SessionLocal() as s:
        q = s.get(db.Quiz, q2)
        s.query(db.Question).filter_by(quiz_id=q.id).delete()
        s.delete(q); s.commit()
    ma_sau, _ = ma_bien_the(nen)
    kiem("xoá đề mới nhất rồi tạo tiếp -> không cấp lại mã cũ", ma_sau != m2,
         f"vừa xoá {m2}, lại cấp {ma_sau}")

    # Hai người bấm Tạo đề cùng lúc thì phải ra hai mã khác nhau
    import threading
    ra = []
    khoa = threading.Lock()

    def xin():
        m, _ = ma_bien_the(nen)
        with khoa:
            ra.append(m)

    ts = [threading.Thread(target=xin) for _ in range(8)]
    for x in ts:
        x.start()
    for x in ts:
        x.join()
    kiem("8 người xin mã cùng lúc -> 8 mã khác nhau", len(set(ra)) == 8,
         f"chỉ có {len(set(ra))} mã khác nhau: {sorted(ra)}")

    don()
    print("\n" + "=" * 70)
    print(f" {dat}/{dat + sai} phép thử đạt")
    print("=" * 70)
    raise SystemExit(0 if sai == 0 else 1)


if __name__ == "__main__":
    main()
