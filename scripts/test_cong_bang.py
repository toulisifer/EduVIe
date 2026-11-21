"""Hai học sinh có kết quả như nhau thì được đối xử như nhau — kiểm chứng đủ ba việc.

1. Chọn chủ đề và độ khó  -> giống nhau
2. Mã đề                   -> giống nhau (và khác với người học khác hẳn)
3. Mã lộ trình             -> giống nhau

Không tốn lượt gọi AI. Thêm --that để sinh đề và lộ trình thật (tốn 3-5 lượt).

  python -m scripts.test_cong_bang
  python -m scripts.test_cong_bang --that
"""
import sys
from datetime import datetime, timedelta

from app import db
from app.advisor import build_plan, ma_lo_trinh
from app.learning import phan_bo_cau_hoi, recommend_quiz
from app.quiz import generate_quiz, ma_de

TEN = ["_cb_an", "_cb_binh", "_cb_chi"]
SUBJECT = 1
GIONG = [(0, 8, 2), (1, 3, 7), (2, 5, 5), (3, 1, 9)]
KHAC = [(0, 9, 1), (1, 9, 1), (2, 2, 8), (3, 8, 2)]
N_CAU, SO_NGAY = 6, 5

dat, sai = [], []


def thu(mo_ta: str, ok: bool, chi_tiet: str = ""):
    (dat if ok else sai).append(mo_ta)
    print(f"  {'✓' if ok else '✗'} {mo_ta}")
    if chi_tiet:
        print(f"      {chi_tiet}")


def don():
    with db.SessionLocal() as s:
        for t in TEN:
            u = s.query(db.User).filter_by(username=t).first()
            if not u:
                continue
            for q in s.query(db.Quiz).filter_by(user_id=u.id):
                s.query(db.Question).filter_by(quiz_id=q.id).delete()
                s.delete(q)
            for p in s.query(db.StudyPlan).filter_by(user_id=u.id):
                s.query(db.PlanItem).filter_by(plan_id=p.id).delete()
                s.delete(p)
            s.query(db.Answer).filter_by(user_id=u.id).delete()
            s.delete(u)
        s.commit()


def dung(ten: str, kich_ban) -> int:
    with db.SessionLocal() as s:
        sub = s.get(db.Subject, SUBJECT)
        topics = [t for c in sorted(sub.chapters, key=lambda c: c.order) for t in c.topics]
        u = db.User(username=ten, password_hash="x", role="user")
        s.add(u); s.flush()
        moc = datetime(2026, 9, 20, 8, 0)
        for idx, d, x in kich_ban:
            for i in range(d + x):
                s.add(db.Answer(user_id=u.id, topic_id=topics[idx].id, difficulty="medium",
                                is_correct=i < d, answered_at=moc + timedelta(minutes=i)))
        s.commit()
        return u.id


def main():
    db.init_db()
    don()
    an, binh, chi = dung(TEN[0], GIONG), dung(TEN[1], GIONG), dung(TEN[2], KHAC)

    print("An và Bình làm bài GIỐNG HỆT NHAU; Chi học khác hẳn.\n")

    print("1. Chọn chủ đề và độ khó")
    ra, rb, rc = (recommend_quiz(u, SUBJECT) for u in (an, binh, chi))
    ta, tb, tc = ([t[0] for t in r["topics"]] for r in (ra, rb, rc))
    thu("An và Bình được gợi ý cùng chủ đề", ta == tb, f"An {ta} · Bình {tb}")
    thu("cùng độ khó", ra["difficulty"] == rb["difficulty"], f"cả hai: {ra['difficulty']}")
    thu("Chi được gợi ý khác", tc != ta, f"Chi {tc}")

    print("\n2. Mã đề")
    ma_a = ma_de(SUBJECT, ta, ra["difficulty"], N_CAU)
    ma_b = ma_de(SUBJECT, tb, rb["difficulty"], N_CAU)
    ma_c = ma_de(SUBJECT, tc, rc["difficulty"], N_CAU)
    thu("An và Bình cùng mã đề", ma_a == ma_b, f"{ma_a}")
    thu("Chi mã khác", ma_c != ma_a, f"{ma_c}")
    thu("thứ tự chủ đề không làm đổi mã",
        ma_de(SUBJECT, [4, 2], "easy", 6) == ma_de(SUBJECT, [2, 4], "easy", 6))
    thu("đổi số câu thì đổi mã",
        ma_de(SUBJECT, [2, 4], "easy", 6) != ma_de(SUBJECT, [2, 4], "easy", 10))

    print("\n3. Mã lộ trình")
    la = ma_lo_trinh(an, SUBJECT, "", SO_NGAY, 1.0)
    lb = ma_lo_trinh(binh, SUBJECT, "", SO_NGAY, 1.0)
    lc = ma_lo_trinh(chi, SUBJECT, "", SO_NGAY, 1.0)
    thu("An và Bình cùng mã lộ trình", la == lb, f"{la}")
    thu("Chi mã khác", lc != la, f"{lc}")
    thu("đổi số ngày thì đổi mã", ma_lo_trinh(an, SUBJECT, "", 7, 1.0) != la)

    print("\n4. Chia câu theo trọng số")
    w = ra.get("weights", {})
    bo = phan_bo_cau_hoi(w, 20)
    thu("tổng số câu chia ra đúng bằng số xin", sum(bo.values()) == 20, f"{bo}")
    bo2 = phan_bo_cau_hoi(w, 60, kha_dung={t: 20 for t in w})
    thu("ngân hàng chỉ 20 câu mỗi chủ đề, xin 60 -> lấy được 40 và báo thiếu",
        sum(bo2.values()) == 40, f"{bo2} = {sum(bo2.values())}/60")

    if "--that" in sys.argv:
        print("\n5. Sinh đề và lộ trình THẬT bằng AI")
        with db.SessionLocal() as s:
            tops = [s.get(db.Topic, t) for t in ta]
            q1 = generate_quiz(an, SUBJECT, tops, ra["difficulty"], N_CAU)
            q2 = generate_quiz(binh, SUBJECT, tops, rb["difficulty"], N_CAU)
            c1 = [q.content for q in s.query(db.Question).filter_by(quiz_id=q1).order_by(db.Question.id)]
            c2 = [q.content for q in s.query(db.Question).filter_by(quiz_id=q2).order_by(db.Question.id)]
        thu("đề của An và Bình giống hệt nhau", c1 == c2 and len(c1) > 0,
            f"{len(c1)} câu, đề #{q1} và #{q2}")

        p1 = build_plan(an, SUBJECT, "", SO_NGAY, 1.0)
        p2 = build_plan(binh, SUBJECT, "", SO_NGAY, 1.0)
        with db.SessionLocal() as s:
            i1 = [(i.day, i.topic_id, i.title) for i in
                  s.query(db.PlanItem).filter_by(plan_id=p1).order_by(db.PlanItem.day, db.PlanItem.id)]
            i2 = [(i.day, i.topic_id, i.title) for i in
                  s.query(db.PlanItem).filter_by(plan_id=p2).order_by(db.PlanItem.day, db.PlanItem.id)]
        thu("lộ trình của An và Bình giống hệt nhau", i1 == i2 and len(i1) > 0,
            f"{len(i1)} việc, kế hoạch #{p1} và #{p2}")

    don()
    print(f"\n{len(dat)}/{len(dat) + len(sai)} phép thử đạt")
    for m in sai:
        print("  SAI:", m)
    print("(đã xoá dữ liệu thử)")
    return 1 if sai else 0


if __name__ == "__main__":
    raise SystemExit(main())
