"""Lớp học: giáo viên tạo lớp (mã tham gia), giao đề; học sinh tham gia bằng mã, làm đề được giao."""
from __future__ import annotations

import secrets
from datetime import datetime

import pandas as pd

from app import analytics
from app.db import (Answer, Assignment, AssignmentSubmission, Attempt, ClassMember, Classroom, Question, Quiz,
                    SessionLocal, Topic, User)
from app.quiz import generate_quiz, submit_attempt


# ----------------------------- LỚP -----------------------------
def create_class(teacher_id: int, name: str, subject_id: int | None) -> Classroom:
    with SessionLocal() as s:
        import re, unicodedata
        base = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
        base = re.sub(r"[^A-Za-z0-9]", "", base).upper()[:4] or "LOP"
        code = f"{base}-{secrets.token_hex(2).upper()}"
        c = Classroom(name=name, code=code, teacher_id=teacher_id, subject_id=subject_id)
        s.add(c); s.commit()
        return c


def my_classes(teacher_id: int) -> list[Classroom]:
    with SessionLocal() as s:
        cs = s.query(Classroom).filter_by(teacher_id=teacher_id).all()
        for c in cs:
            _ = [m.user.username for m in c.members]; _ = [a.title for a in c.assignments]
        return cs


def join_class(user_id: int, code: str) -> tuple[Classroom | None, str]:
    with SessionLocal() as s:
        c = s.query(Classroom).filter_by(code=code.strip().upper()).first()
        if not c:
            return None, "Mã lớp không đúng"
        if s.query(ClassMember).filter_by(class_id=c.id, user_id=user_id).first():
            return c, "Bạn đã ở trong lớp này"
        s.add(ClassMember(class_id=c.id, user_id=user_id)); s.commit()
        return c, ""


def classes_of_student(user_id: int) -> list[Classroom]:
    with SessionLocal() as s:
        cs = [m.classroom for m in s.query(ClassMember).filter_by(user_id=user_id)]
        for c in cs:
            _ = [a.title for a in c.assignments]
        return cs


# ----------------------------- PHÂN TÍCH LỚP -----------------------------
def class_overview(class_id: int) -> pd.DataFrame:
    """Mỗi học sinh một dòng: số câu, tỷ lệ đúng, số chủ đề yếu, chủ đề yếu nhất."""
    with SessionLocal() as s:
        c = s.get(Classroom, class_id)
        members = [(m.user.id, m.user.username) for m in c.members]
        sid = c.subject_id
    rows = []
    for uid, name in members:
        df = analytics.answers_df(uid)
        if sid and not df.empty:
            df = df[df["subject_id"] == sid]
        m = analytics.topic_mastery(uid, sid)
        weak = m[m["level"] == "Yếu"].sort_values("mastery")
        rows.append({"user_id": uid, "Học sinh": name, "Câu đã làm": int(len(df)),
                     "Tỷ lệ đúng (%)": round(100 * df["is_correct"].mean()) if len(df) else None,
                     "Chủ đề yếu": int(len(weak)),
                     "Yếu nhất": weak.iloc[0]["topic"] if len(weak) else "—"})
    return pd.DataFrame(rows)


def class_heatmap(class_id: int) -> pd.DataFrame:
    """Ma trận học sinh × chủ đề (mastery %), chỉ chủ đề có ít nhất 1 người làm."""
    with SessionLocal() as s:
        c = s.get(Classroom, class_id)
        members = [(m.user.id, m.user.username) for m in c.members]
        sid = c.subject_id
    frames = []
    for uid, name in members:
        m = analytics.topic_mastery(uid, sid)
        m = m[m["n"] > 0][["topic", "mastery"]].assign(**{"Học sinh": name})
        frames.append(m)
    if not frames:
        return pd.DataFrame()
    long = pd.concat(frames)
    return long.pivot_table(index="Học sinh", columns="topic", values="mastery", aggfunc="mean")


def class_topic_avg(class_id: int) -> pd.DataFrame:
    hm = class_heatmap(class_id)
    if hm.empty:
        return hm
    return hm.mean().sort_values().reset_index().rename(columns={0: "Mastery TB (%)", "topic": "Chủ đề"})


# ----------------------------- GIAO ĐỀ -----------------------------
def create_assignment(class_id: int, teacher_id: int, title: str, topic_ids: list[int], difficulty: str,
                      n: int, due: datetime | None) -> Assignment:
    with SessionLocal() as s:
        c = s.get(Classroom, class_id)
        topics = [s.get(Topic, t) for t in topic_ids]
        for t in topics:
            _ = t.path
        subject_id = c.subject_id or topics[0].chapter.subject_id
    quiz_id = generate_quiz(teacher_id, subject_id, topics, difficulty, n)   # đề mẫu thuộc giáo viên
    with SessionLocal() as s:
        a = Assignment(class_id=class_id, quiz_id=quiz_id, title=title, due=due)
        s.add(a); s.flush()
        # đánh dấu đề mẫu là đề kiểm tra: không mở được bằng mã, không nộp được qua
        # đường tự luyện, nên học sinh không lấy được đáp án trước khi làm
        s.get(Quiz, quiz_id).assignment_id = a.id
        s.commit()
        return a


def assignments_for_student(user_id: int) -> list[dict]:
    with SessionLocal() as s:
        out = []
        for m in s.query(ClassMember).filter_by(user_id=user_id):
            for a in m.classroom.assignments:
                sub = s.query(AssignmentSubmission).filter_by(assignment_id=a.id, user_id=user_id).first()
                out.append({"id": a.id, "title": a.title, "class": m.classroom.name, "due": a.due,
                            "n_questions": len(a.quiz.questions), "done": sub is not None,
                            "score": sub.score if sub else None})
        return out


class HetHan(Exception):
    """Đã quá hạn nộp."""


class DaNop(Exception):
    """Bài này đã nộp rồi."""


def _qua_han(a: Assignment) -> bool:
    return bool(a.due and datetime.utcnow() > a.due)


def start_assignment(assignment_id: int, user_id: int) -> int:
    """Sao chép đề mẫu thành quiz riêng của học sinh, trả về quiz_id.

    Đã nộp rồi thì trả lại đúng bản cũ thay vì dựng bản mới: dựng mới sẽ cho học sinh
    một đề sạch để thử lại, và sinh thêm đề rác trong lịch sử.
    """
    with SessionLocal() as s:
        a = s.get(Assignment, assignment_id)
        if _qua_han(a):
            raise HetHan(f"Bài này đã hết hạn nộp lúc {a.due:%H:%M %d/%m/%Y}")
        cu = s.query(AssignmentSubmission).filter_by(
            assignment_id=assignment_id, user_id=user_id).first()
        if cu:
            raise DaNop("Bạn đã nộp bài này rồi — xem lại trong lịch sử làm đề")
        dang_lam = (s.query(Quiz).filter_by(assignment_id=assignment_id, user_id=user_id)
                    .order_by(Quiz.id).first())
        if dang_lam:
            return dang_lam.id                  # mở lại bản đang làm dở
        # giữ nguyên mã của đề mẫu: học sinh thấy mã trong lịch sử và mở lại được đúng đề
        quiz = Quiz(user_id=user_id, subject_id=a.quiz.subject_id,
                    difficulty=a.quiz.difficulty, code=a.quiz.code or "",
                    assignment_id=assignment_id)
        s.add(quiz); s.flush()
        for q in a.quiz.questions:
            # chép cả bank_id: thiếu nó thì câu học sinh làm sai trong bài kiểm tra
            # không nối được về ngân hàng, nên không vào danh sách luyện lại câu sai
            # và cũng không cộng vào thống kê của câu đó
            s.add(Question(quiz_id=quiz.id, topic_id=q.topic_id, difficulty=q.difficulty,
                           content=q.content, options=q.options, correct=q.correct,
                           explanation=q.explanation, bank_id=q.bank_id))
        s.commit()
        return quiz.id


def submit_assignment(assignment_id: int, quiz_id: int, user_id: int, selections: dict) -> dict:
    """Nộp bài tập. Một học sinh một lần nộp, và không nộp được sau hạn.

    Trước đây hai điều kiện này đều thiếu: nộp sau hạn ba ngày vẫn vào, và nộp nhiều
    lần tạo nhiều bản ghi — mà assignment_results() gom bằng dict nên chỉ giữ bản
    CUỐI, tức là nộp bừa lấy 0 điểm, xem đáp án, rồi nộp lại 10 điểm.
    """
    with SessionLocal() as s:
        a = s.get(Assignment, assignment_id)
        if not a:
            raise DaNop("Không tìm thấy bài tập")
        if _qua_han(a):
            raise HetHan(f"Bài này đã hết hạn nộp lúc {a.due:%H:%M %d/%m/%Y}")
        if s.query(AssignmentSubmission).filter_by(
                assignment_id=assignment_id, user_id=user_id).first():
            raise DaNop("Bạn đã nộp bài này rồi")
        q = s.get(Quiz, quiz_id)
        if not q or q.assignment_id != assignment_id or q.user_id != user_id:
            raise DaNop("Đề này không thuộc bài tập đó")
    r = submit_attempt(quiz_id, user_id, selections)
    with SessionLocal() as s:
        s.add(AssignmentSubmission(assignment_id=assignment_id, user_id=user_id,
                                   attempt_id=r["attempt_id"], score=r["score"]))
        s.commit()
    return r


def assignment_results(assignment_id: int) -> pd.DataFrame:
    with SessionLocal() as s:
        a = s.get(Assignment, assignment_id)
        members = [(m.user.id, m.user.username) for m in a.classroom.members]
        subs = {x.user_id: x for x in s.query(AssignmentSubmission).filter_by(assignment_id=assignment_id)}
        rows = [{"Học sinh": name, "Điểm": subs[uid].score if uid in subs else None,
                 "Nộp lúc": subs[uid].submitted_at if uid in subs else None} for uid, name in members]
        # tỷ lệ đúng từng câu của lớp
        per_q = []
        for q in a.quiz.questions:
            ans = (s.query(Answer).join(Question, Answer.question_id == Question.id)
                   .filter(Question.content == q.content, Answer.user_id.in_([u for u, _ in members])).all())
            if ans:
                per_q.append({"Câu": q.content[:70], "Chủ đề": q.topic.name,
                              "Tỷ lệ đúng (%)": round(100 * sum(x.is_correct for x in ans) / len(ans))})
    return pd.DataFrame(rows), pd.DataFrame(per_q)
