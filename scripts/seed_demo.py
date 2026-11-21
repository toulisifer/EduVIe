"""Tạo tài khoản `demo` với ~2 tuần dữ liệu quiz + điểm số để demo dashboard mà không tốn quota.

Chạy:  python -m scripts.seed_demo            (tạo mới / làm lại)
       python -m scripts.seed_demo --wipe     (chỉ xoá)

Dữ liệu được thiết kế có chủ đích:
- Chương 1: 'Tính đơn điệu' tốt, 'Cực trị' tiến bộ dần, 'Đường tiệm cận' yếu, 'GTLN/GTNN' trung bình.
- Chương 2: chỉ mới làm 'Vectơ trong không gian' (ít câu -> chưa đủ dữ liệu).
"""
import random
import sys
from datetime import datetime, timedelta

from app.db import (Answer, Attempt, Question, Quiz, Score, SessionLocal, StudyPlan,
                    PlanItem, Subject, Topic, User, init_db)

random.seed(42)
DEMO = "demo"

# (tên topic, xác suất đúng đầu kỳ, xác suất đúng cuối kỳ)
PROFILE = {
    "Tính đơn điệu của hàm số": (0.75, 0.9),
    "Cực trị của hàm số": (0.3, 0.8),      # tiến bộ rõ
    "Giá trị lớn nhất và nhỏ nhất": (0.55, 0.65),
    "Đường tiệm cận": (0.25, 0.35),          # yếu kéo dài
    "Khảo sát và vẽ đồ thị hàm số": (0.5, 0.5),
    "Lũy thừa": (0.6, 0.6),
}
DIFFS = ["easy", "medium", "medium", "hard"]


def wipe(s, uid):
    quiz_ids = [q.id for q in s.query(Quiz).filter_by(user_id=uid)]
    plan_ids = [p.id for p in s.query(StudyPlan).filter_by(user_id=uid)]
    s.query(Answer).filter_by(user_id=uid).delete()
    s.query(Attempt).filter_by(user_id=uid).delete()
    if quiz_ids:
        s.query(Question).filter(Question.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
    s.query(Quiz).filter_by(user_id=uid).delete()
    s.query(Score).filter_by(user_id=uid).delete()
    if plan_ids:
        s.query(PlanItem).filter(PlanItem.plan_id.in_(plan_ids)).delete(synchronize_session=False)
    s.query(StudyPlan).filter_by(user_id=uid).delete()


def main():
    init_db()
    with SessionLocal() as s:
        u = s.query(User).filter_by(username=DEMO).first()
        if not u:
            u = User(username=DEMO, goal="Đạt 8 điểm giữa kỳ Toán")
            s.add(u); s.commit()
        wipe(s, u.id); s.commit()
        if "--wipe" in sys.argv:
            print("đã xoá dữ liệu demo"); return

        subject = s.query(Subject).first()
        topics = {t.name: t for t in s.query(Topic).all()}
        start = datetime.utcnow() - timedelta(days=14)

        # 12 bài quiz rải trong 14 ngày, mỗi bài 5 câu, 1-2 topic
        n_answers = 0
        for k in range(12):
            when = start + timedelta(days=k * 14 / 12, hours=random.randint(17, 21))
            progress = k / 11
            picks = random.sample([t for t in PROFILE if t != "Lũy thừa"], 2) if k < 10 else ["Lũy thừa"]
            quiz = Quiz(user_id=u.id, subject_id=subject.id, difficulty="medium", created_at=when)
            s.add(quiz); s.flush()
            attempt = Attempt(quiz_id=quiz.id, user_id=u.id, submitted_at=when)
            s.add(attempt); s.flush()
            correct = 0
            for i in range(5):
                tname = picks[i % len(picks)]
                p0, p1 = PROFILE[tname]
                p_ok = p0 + (p1 - p0) * progress
                diff = random.choice(DIFFS)
                p_ok *= {"easy": 1.15, "medium": 1.0, "hard": 0.8}[diff]
                ok = random.random() < min(p_ok, 0.97)
                q = Question(quiz_id=quiz.id, topic_id=topics[tname].id, difficulty=diff,
                             content=f"[Demo] Câu hỏi về {tname} (#{k+1}.{i+1})",
                             options=["A", "B", "C", "D"], correct=0, explanation="Dữ liệu demo")
                s.add(q); s.flush()
                s.add(Answer(attempt_id=attempt.id, question_id=q.id, user_id=u.id, topic_id=q.topic_id,
                             difficulty=diff, selected=0 if ok else 1, is_correct=ok, answered_at=when))
                correct += ok; n_answers += 1
            attempt.score = round(10 * correct / 5, 2)

        # Điểm nhập tay
        for kind, w, val, d in [("mieng", 1, 8.0, 12), ("15p", 1, 6.5, 9), ("15p", 1, 7.5, 4), ("giua_ky", 2, 6.75, 1)]:
            s.add(Score(user_id=u.id, subject_id=subject.id, kind=kind, value=val, weight=w,
                        date=datetime.utcnow() - timedelta(days=d)))
        s.commit()
        print(f"OK: user '{DEMO}' (id={u.id}) — 12 quiz, {n_answers} câu, 4 đầu điểm. Đăng nhập bằng tên: demo")


if __name__ == "__main__":
    main()
