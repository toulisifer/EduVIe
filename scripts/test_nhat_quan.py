"""Hai người có kết quả học giống hệt nhau thì hệ thống có gợi ý giống nhau không?

Dựng 2 tài khoản thử với CÙNG lịch sử làm bài, rồi so sánh đầu ra của recommend_quiz.
Không tốn lượt gọi AI. Dữ liệu thử được xoá sạch sau khi chạy.

  python -m scripts.test_nhat_quan
"""
from datetime import datetime, timedelta

from app import db
from app.learning import recommend_quiz

TEN = ["_nq_an", "_nq_binh"]
SUBJECT = 1                       # Toán 12
# kịch bản giống hệt nhau: (chỉ số chủ đề trong môn, số câu đúng, số câu sai)
KICH_BAN = [(0, 8, 2), (1, 3, 7), (2, 5, 5), (3, 1, 9)]


def don():
    with db.SessionLocal() as s:
        for t in TEN:
            u = s.query(db.User).filter_by(username=t).first()
            if u:
                s.query(db.Answer).filter_by(user_id=u.id).delete()
                s.delete(u)
        s.commit()


def dung_du_lieu() -> list[int]:
    """Tạo 2 user với lịch sử làm bài giống hệt nhau. Trả về danh sách user_id."""
    with db.SessionLocal() as s:
        sub = s.get(db.Subject, SUBJECT)
        topics = [t for c in sorted(sub.chapters, key=lambda c: c.order) for t in c.topics]
        ids = []
        for ten in TEN:
            u = db.User(username=ten, password_hash="x", role="user")
            s.add(u); s.flush()
            moc = datetime(2026, 9, 20, 8, 0)      # cùng mốc thời gian -> cùng trọng số thời gian
            for idx, dung, sai in KICH_BAN:
                t = topics[idx]
                for i in range(dung + sai):
                    s.add(db.Answer(user_id=u.id, topic_id=t.id, difficulty="medium",
                                    is_correct=i < dung, answered_at=moc + timedelta(minutes=i)))
            ids.append(u.id)
        s.commit()
        return ids


def main():
    db.init_db()
    don()
    an, binh = dung_du_lieu()

    print("Hai tài khoản có lịch sử làm bài GIỐNG HỆT NHAU:")
    with db.SessionLocal() as s:
        sub = s.get(db.Subject, SUBJECT)
        topics = [t for c in sorted(sub.chapters, key=lambda c: c.order) for t in c.topics]
    for idx, dung, sai in KICH_BAN:
        print(f"   {topics[idx].name:<34} {dung}/{dung + sai} câu đúng")

    ra = recommend_quiz(an, SUBJECT)
    rb = recommend_quiz(binh, SUBJECT)

    print("\n" + "=" * 70)
    for ten, r in (("An", ra), ("Bình", rb)):
        print(f"\nGợi ý cho {ten}:")
        print(f"   độ khó: {r['difficulty']}   (nguồn: {r['source']})")
        for tid, name, why in r["topics"]:
            print(f"   - [{tid}] {name} — {why}")

    giong = (r_t := [t[0] for t in ra["topics"]]) == [t[0] for t in rb["topics"]] \
        and ra["difficulty"] == rb["difficulty"]
    print("\n" + "=" * 70)
    print("KẾT LUẬN: chọn chủ đề và độ khó", "GIỐNG NHAU ✓" if giong else "KHÁC NHAU ✗")
    print(f"           (An: {r_t}  |  Bình: {[t[0] for t in rb['topics']]})")

    don()
    print("\n(đã xoá dữ liệu thử)")
    return 0 if giong else 1


if __name__ == "__main__":
    raise SystemExit(main())
