"""Chấm bài tự luận / bài giải viết tay bằng Gemini vision.

Đầu vào: ảnh (hoặc text) bài làm + (tuỳ chọn) đề bài + chủ đề.
Đầu ra (JSON): điểm 0-10, từng bước (đúng/sai + nhận xét), bước sai đầu tiên, lỗi kiến thức, gợi ý sửa, topic.
Kết quả được lưu như một Answer (đúng nếu điểm >= 7) để đưa vào mastery / DKT / spaced repetition.
"""
from __future__ import annotations

from datetime import datetime

from google.genai import types

from app.db import Answer, Attempt, Question, Quiz, SessionLocal, Topic
from app.llm import CHAT_MODELS, call_with_fallback
from app.rag.chat import retrieve

SYSTEM = """Bạn là giáo viên chấm bài tự luận. Nhiệm vụ:
1. Đọc bài làm (ảnh viết tay hoặc text). Chép lại đề bài nếu có trong ảnh.
2. Chia lời giải thành các bước; với mỗi bước ghi rõ đúng/sai và vì sao.
3. Xác định BƯỚC SAI ĐẦU TIÊN (nếu có) — đây là điểm học sinh cần sửa; các bước sau phụ thuộc vào nó.
4. Phân loại lỗi: tính toán / công thức / lập luận / trình bày / không có lỗi.
5. Cho điểm 0–10 theo mức hoàn thành và đúng đắn. Nhận xét ngắn, khích lệ, và gợi ý cụ thể cách làm đúng.
6. Chọn topic_id phù hợp nhất trong DANH SÁCH CHỦ ĐỀ.
Nếu có TÀI LIỆU tham khảo, hãy dựa vào đó khi nói "công thức đúng là...". Công thức viết bằng LaTeX $...$."""

SCHEMA = {
    "type": "object",
    "properties": {
        "problem": {"type": "string"},
        "score": {"type": "number"},
        "steps": {"type": "array", "items": {"type": "object", "properties": {
            "step": {"type": "string"}, "correct": {"type": "boolean"}, "comment": {"type": "string"}},
            "required": ["step", "correct", "comment"]}},
        "first_error_step": {"type": "integer"},
        "error_type": {"type": "string", "enum": ["tính toán", "công thức", "lập luận", "trình bày", "không có lỗi"]},
        "feedback": {"type": "string"},
        "correct_solution_hint": {"type": "string"},
        "topic_id": {"type": "integer"},
    },
    "required": ["problem", "score", "steps", "first_error_step", "error_type", "feedback", "correct_solution_hint", "topic_id"],
}


def grade(user_id: int, subject_id: int, image_bytes: bytes | None, mime: str, text: str,
          problem_hint: str, topic_ids: list[int]) -> dict:
    with SessionLocal() as s:
        topics = s.query(Topic).filter(Topic.id.in_(topic_ids)).all() if topic_ids else \
                 [t for t in s.query(Topic) if t.chapter.subject_id == subject_id]
        topic_list = "\n".join(f"- topic_id={t.id}: {t.name}" for t in topics)
    query = problem_hint or text[:300] or "bài giải toán"
    ctx = "\n\n".join(f"[{h['filename']} tr.{h['page']}] {h['text'][:500]}" for h in retrieve(query, user_id, subject_id, k=3))
    prompt = f"""DANH SÁCH CHỦ ĐỀ:
{topic_list}

TÀI LIỆU THAM KHẢO:
{ctx or '(không có)'}

ĐỀ BÀI (nếu người dùng cung cấp): {problem_hint or '(xem trong bài làm)'}
BÀI LÀM DẠNG TEXT (nếu có): {text or '(xem ảnh)'}

Hãy chấm bài."""
    parts = [prompt]
    if image_bytes:
        parts.insert(0, types.Part.from_bytes(data=image_bytes, mime_type=mime))
    res = call_with_fallback(CHAT_MODELS, parts, types.GenerateContentConfig(
        system_instruction=SYSTEM, temperature=0.2, response_mime_type="application/json", response_schema=SCHEMA))
    import json
    return json.loads(res.text)


def save_as_answer(user_id: int, subject_id: int, result: dict) -> int:
    """Lưu kết quả chấm như 1 câu tự luận trong hệ thống để tính mastery. Trả về attempt_id."""
    ok = float(result["score"]) >= 7
    with SessionLocal() as s:
        quiz = Quiz(user_id=user_id, subject_id=subject_id, difficulty="medium")
        s.add(quiz); s.flush()
        q = Question(quiz_id=quiz.id, topic_id=result["topic_id"], difficulty="medium",
                     content="[Tự luận] " + result["problem"][:400], options=["Tự luận"], correct=0,
                     explanation=result["feedback"][:800])
        s.add(q); s.flush()
        att = Attempt(quiz_id=quiz.id, user_id=user_id, score=float(result["score"]), submitted_at=datetime.utcnow())
        s.add(att); s.flush()
        s.add(Answer(attempt_id=att.id, question_id=q.id, user_id=user_id, topic_id=result["topic_id"],
                     difficulty="medium", selected=0 if ok else None, is_correct=ok))
        s.commit()
        return att.id
