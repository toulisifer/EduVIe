"""Phân tích năng lực từ bảng Answer: mastery theo topic, topic yếu, xu hướng.

Phương pháp thống kê minh bạch (chưa dùng ML):
- Mỗi câu trả lời có trọng số = w_khó × w_thời_gian
  - w_khó: easy 0.7, medium 1.0, hard 1.3 (trả lời đúng câu khó đáng giá hơn)
  - w_thời_gian: giảm dần theo tuổi câu trả lời (half-life 14 ngày) -> kết quả gần đây quan trọng hơn
- mastery = Σ(w × đúng) / Σ(w), tính theo %.
- Chỉ kết luận "yếu" khi topic có >= MIN_ANSWERS câu để tránh nhiễu.
"""
from datetime import datetime

import pandas as pd

from app.db import Answer, Attempt, Chapter, Score, SessionLocal, Subject, Topic

DIFF_W = {"easy": 0.7, "medium": 1.0, "hard": 1.3}
HALF_LIFE_DAYS = 14
MIN_ANSWERS = 3
WEAK_BELOW, GOOD_ABOVE = 50, 75


def level(m: float | None) -> str:
    if m is None:
        return "Chưa đủ dữ liệu"
    return "Yếu" if m < WEAK_BELOW else "Trung bình" if m < GOOD_ABOVE else "Tốt"


def answers_df(user_id: int) -> pd.DataFrame:
    with SessionLocal() as s:
        rows = (s.query(Answer.id, Answer.topic_id, Answer.difficulty, Answer.is_correct, Answer.answered_at,
                        Topic.name.label("topic"), Chapter.name.label("chapter"), Subject.name.label("subject"),
                        Subject.id.label("subject_id"))
                .select_from(Answer).join(Topic, Answer.topic_id == Topic.id)
                .join(Chapter, Topic.chapter_id == Chapter.id).join(Subject, Chapter.subject_id == Subject.id)
                .filter(Answer.user_id == user_id).all())
    df = pd.DataFrame(rows, columns=["id", "topic_id", "difficulty", "is_correct", "answered_at",
                                     "topic", "chapter", "subject", "subject_id"])
    if df.empty:
        return df
    now = datetime.utcnow()
    age_days = (now - pd.to_datetime(df["answered_at"])).dt.total_seconds() / 86400
    df["w"] = df["difficulty"].map(DIFF_W).fillna(1.0) * (0.5 ** (age_days / HALF_LIFE_DAYS))
    df["is_correct"] = df["is_correct"].astype(int)
    return df


def topic_mastery(user_id: int, subject_id: int | None = None) -> pd.DataFrame:
    """Một dòng / topic: mastery %, số câu, mức. Bao gồm cả topic chưa có dữ liệu."""
    with SessionLocal() as s:
        q = (s.query(Topic.id, Topic.name, Chapter.name, Subject.name, Subject.id)
             .select_from(Topic).join(Chapter, Topic.chapter_id == Chapter.id).join(Subject, Chapter.subject_id == Subject.id))
        if subject_id:
            q = q.filter(Subject.id == subject_id)
        all_topics = pd.DataFrame(q.all(), columns=["topic_id", "topic", "chapter", "subject", "subject_id"])

    df = answers_df(user_id)
    if not df.empty:
        g = df.groupby("topic_id").apply(
            lambda x: pd.Series({"mastery": 100 * (x["w"] * x["is_correct"]).sum() / x["w"].sum(),
                                 "n": len(x), "n_correct": x["is_correct"].sum()}),
            include_groups=False)
        all_topics = all_topics.merge(g, left_on="topic_id", right_index=True, how="left")
    else:
        all_topics["mastery"], all_topics["n"], all_topics["n_correct"] = float("nan"), 0, 0

    all_topics["n"] = all_topics["n"].fillna(0).astype(int)
    all_topics["n_correct"] = all_topics["n_correct"].fillna(0).astype(int)
    all_topics["mastery"] = all_topics["mastery"].round(0)
    all_topics["level"] = all_topics.apply(
        lambda r: level(r["mastery"] if r["n"] >= MIN_ANSWERS else None), axis=1)
    return all_topics


def weak_topics(user_id: int, subject_id: int | None = None) -> pd.DataFrame:
    m = topic_mastery(user_id, subject_id)
    return m[m["level"] == "Yếu"].sort_values("mastery")


def attempt_trend(user_id: int) -> pd.DataFrame:
    with SessionLocal() as s:
        rows = (s.query(Attempt.submitted_at, Attempt.score).filter(Attempt.user_id == user_id)
                .order_by(Attempt.submitted_at).all())
    return pd.DataFrame(rows, columns=["Thời gian", "Điểm"])


def score_summary(user_id: int) -> pd.DataFrame:
    """Điểm nhập tay: trung bình có trọng số theo môn."""
    with SessionLocal() as s:
        rows = (s.query(Subject.name, Score.kind, Score.value, Score.weight, Score.date)
                .select_from(Score).join(Subject, Score.subject_id == Subject.id).filter(Score.user_id == user_id).all())
    df = pd.DataFrame(rows, columns=["subject", "kind", "value", "weight", "date"])
    if df.empty:
        return df
    return (df.assign(wv=df["value"] * df["weight"])
              .groupby("subject").agg(avg=("wv", "sum"), w=("weight", "sum"), n=("value", "size"))
              .assign(avg=lambda x: (x["avg"] / x["w"]).round(2)).drop(columns="w").reset_index())


def student_summary_text(user_id: int, subject_id: int | None = None) -> str:
    """Tóm tắt dạng text để đưa vào prompt cho AI nhận xét / lộ trình."""
    m = topic_mastery(user_id, subject_id)
    lines = []
    for ch, grp in m.groupby("chapter", sort=False):
        lines.append(f"* {ch}")
        for _, r in grp.iterrows():
            stat = f"{int(r['mastery'])}% ({r['n_correct']}/{r['n']} câu)" if r["n"] else "chưa làm"
            lines.append(f"  - {r['topic']}: {stat} → {r['level']}")
    sc = score_summary(user_id)
    if not sc.empty:
        lines.append("* Điểm trung bình các môn (nhập tay):")
        lines += [f"  - {r['subject']}: {r['avg']} ({r['n']} đầu điểm)" for _, r in sc.iterrows()]
    return "\n".join(lines)
