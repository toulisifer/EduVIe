"""AI Agent thật: Gemini + function calling.

Khác với advisor.py (đưa sẵn số liệu vào prompt), ở đây agent TỰ quyết định gọi tool nào,
theo thứ tự nào, dựa trên câu hỏi/mục tiêu của người học. Vòng lặp:
    model -> (function_call?) -> chạy tool Python -> trả kết quả cho model -> ... -> câu trả lời cuối.
Mọi lần gọi tool được ghi vào `trace` để hiển thị cho người dùng (minh bạch) và để đánh giá.
"""
import json
from datetime import datetime

from google.genai import types

from app import analytics
from app.db import Answer, PlanItem, Question, SessionLocal, StudyPlan, Topic
from app.llm import CHAT_MODELS, call_with_fallback
from app.rag.chat import retrieve

MAX_STEPS = 8

SYSTEM = """Bạn là gia sư AI cá nhân, có các công cụ để tra cứu dữ liệu học tập THẬT của học sinh.
Nguyên tắc:
- Luôn tra cứu dữ liệu bằng công cụ trước khi nhận xét hay lập kế hoạch; không phỏng đoán.
- Nhận xét phải dẫn số liệu cụ thể lấy từ công cụ (ví dụ: "Cực trị: 47%, 7/14 câu").
- Khi lập kế hoạch: gọi get_review_and_prerequisites để biết chủ đề đến hạn ôn và chủ đề bị chặn; củng cố tiên quyết TRƯỚC,
  ưu tiên chủ đề yếu, xen kẽ học → làm quiz → ôn; gọi save_study_plan để lưu.
- Khi cần dẫn nội dung sách, dùng search_documents và ghi rõ trang.
- Trả lời bằng tiếng Việt, ngắn gọn, có cấu trúc (tiêu đề, gạch đầu dòng)."""


# ----------------------------- TOOLS -----------------------------
# Mỗi tool là một hàm Python thuần; docstring + type hint được SDK chuyển thành schema cho Gemini.

def make_tools(user_id: int, subject_id: int | None):
    """Đóng gói user_id vào các tool (model không cần/không được biết user_id)."""

    def get_student_overview() -> dict:
        """Tổng quan học tập của học sinh: số câu đã làm, tỷ lệ đúng, điểm trung bình các môn, số chủ đề yếu/tốt."""
        df = analytics.answers_df(user_id)
        m = analytics.topic_mastery(user_id, subject_id)
        sc = analytics.score_summary(user_id)
        return {
            "total_answers": int(len(df)),
            "accuracy_pct": round(100 * df["is_correct"].mean()) if len(df) else None,
            "weak_topics": int((m["level"] == "Yếu").sum()),
            "good_topics": int((m["level"] == "Tốt").sum()),
            "scores": sc.to_dict("records") if not sc.empty else [],
        }

    def get_topic_mastery() -> list[dict]:
        """Mức nắm vững (mastery %) từng chủ đề, số câu đã làm, số câu đúng và mức đánh giá (Yếu/Trung bình/Tốt/Chưa đủ dữ liệu)."""
        m = analytics.topic_mastery(user_id, subject_id)
        return [{"topic_id": int(r.topic_id), "topic": r.topic, "chapter": r.chapter,
                 "mastery_pct": None if r.n == 0 else int(r.mastery), "n_answers": int(r.n),
                 "n_correct": int(r.n_correct), "level": r.level} for r in m.itertuples()]

    def get_recent_mistakes(topic_id: int, limit: int = 5) -> list[dict]:
        """Các câu học sinh làm SAI gần đây trong một chủ đề (đề bài, đáp án đã chọn, đáp án đúng, giải thích) để tìm lỗi lặp lại.

        Args:
            topic_id: id chủ đề (lấy từ get_topic_mastery).
            limit: số câu tối đa.
        """
        with SessionLocal() as s:
            rows = (s.query(Answer, Question).join(Question, Answer.question_id == Question.id)
                    .filter(Answer.user_id == user_id, Answer.topic_id == topic_id, Answer.is_correct == False)  # noqa: E712
                    .order_by(Answer.answered_at.desc()).limit(limit).all())
            return [{"question": q.content[:300], "chosen": q.options[a.selected] if a.selected is not None and a.selected < len(q.options) else None,
                     "correct": q.options[q.correct], "explanation": q.explanation[:300],
                     "difficulty": a.difficulty} for a, q in rows]

    def search_documents(query: str, k: int = 4) -> list[dict]:
        """Tìm đoạn liên quan trong tài liệu/sách giáo khoa đã nạp. Trả về nội dung kèm tên file và số trang.

        Args:
            query: nội dung cần tìm (khái niệm, dạng bài, tên chủ đề...).
            k: số đoạn tối đa.
        """
        return [{"page": h["page"], "file": h["filename"], "text": h["text"][:600]}
                for h in retrieve(query, user_id, subject_id, k=k)]

    def save_study_plan(goal: str, days: int, summary: str, items: list[dict]) -> dict:
        """Lưu kế hoạch học tập cho học sinh. Gọi sau khi đã phân tích xong.

        Args:
            goal: mục tiêu của học sinh.
            days: số ngày của kế hoạch.
            summary: nhận xét tổng quan (markdown), nêu số liệu cụ thể.
            items: danh sách việc, mỗi việc là dict {day: int, topic_id: int (0 nếu không gắn chủ đề), kind: 'study'|'quiz'|'review', title: str, detail: str}.
        """
        with SessionLocal() as s:
            valid = {t.id for t in s.query(Topic).all()}
            plan = StudyPlan(user_id=user_id, subject_id=subject_id, goal=goal, days=int(days),
                             summary=summary, evidence=analytics.student_summary_text(user_id, subject_id))
            s.add(plan); s.flush()
            n = 0
            for it in items:
                day = int(it.get("day", 1))
                if not (1 <= day <= days):
                    continue
                tid = int(it.get("topic_id") or 0)
                s.add(PlanItem(plan_id=plan.id, day=day, topic_id=tid if tid in valid else None,
                               kind=it.get("kind", "study"), title=str(it.get("title", ""))[:200],
                               detail=str(it.get("detail", ""))))
                n += 1
            s.commit()
            return {"plan_id": plan.id, "items_saved": n}

    def get_review_and_prerequisites() -> dict:
        """Chủ đề đến hạn ôn lại (spaced repetition) và các chủ đề đang bị chặn vì kiến thức tiên quyết còn yếu.
        Dùng để sắp thứ tự học: củng cố tiên quyết trước, ôn chủ đề đến hạn đúng ngày."""
        from app.learning import due_topics, recommend_quiz
        due = due_topics(user_id, subject_id)
        rec = recommend_quiz(user_id, subject_id) if subject_id else {"topics": [], "blocked": [], "difficulty": "medium"}
        return {"due_for_review": [{"topic_id": int(r.topic_id), "topic": r.topic, "overdue_days": float(r.overdue_days)} for r in due.itertuples()],
                "blocked_by_weak_prerequisites": [{"topic_id": t, "topic": n, "needs": b} for t, n, b in rec["blocked"]],
                "recommended_next_quiz": {"topics": [{"topic_id": t, "topic": n, "why": w} for t, n, w in rec["topics"]],
                                          "difficulty": rec["difficulty"]}}

    return [get_student_overview, get_topic_mastery, get_recent_mistakes, get_review_and_prerequisites,
            search_documents, save_study_plan]


def _lessons(user_id: int) -> str:
    """Bài học agent tự rút ra từ các kế hoạch trước (bậc 6) — chèn vào system prompt."""
    try:
        from app.reflection import lessons_prompt
        return lessons_prompt(user_id)
    except Exception:  # noqa: BLE001
        return ""


# ----------------------------- AGENT LOOP -----------------------------

def run_agent(user_id: int, subject_id: int | None, user_message: str, on_step=None,
              system: str | None = None, tool_names: list[str] | None = None) -> tuple[str, list[dict]]:
    """Chạy agent. Trả về (câu trả lời cuối, trace các bước). on_step(step_dict) được gọi sau mỗi tool để UI cập nhật.
    system / tool_names: tuỳ biến vai trò và tập công cụ (dùng cho multi-agent)."""
    tools = make_tools(user_id, subject_id)
    if tool_names:
        tools = [f for f in tools if f.__name__ in tool_names]
    fn_map = {f.__name__: f for f in tools}
    config = types.GenerateContentConfig(
        system_instruction=(system or SYSTEM) + _lessons(user_id) + f"\nHôm nay: {datetime.now():%d/%m/%Y}.",
        tools=tools,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),  # tự điều khiển vòng lặp để ghi log
        temperature=0.4,
    )
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=user_message)])]
    trace: list[dict] = []

    for _ in range(MAX_STEPS):
        res = call_with_fallback(CHAT_MODELS, contents, config)
        cand = res.candidates[0]
        calls = [p.function_call for p in cand.content.parts if p.function_call]
        if not calls:
            return res.text or "", trace
        contents.append(cand.content)
        result_parts = []
        for fc in calls:
            args = dict(fc.args or {})
            try:
                out = fn_map[fc.name](**args)
                ok = True
            except Exception as e:  # noqa: BLE001
                out, ok = {"error": str(e)}, False
            step = {"tool": fc.name, "args": args, "ok": ok,
                    "result_preview": json.dumps(out, ensure_ascii=False, default=str)[:400]}
            trace.append(step)
            if on_step:
                on_step(step)
            result_parts.append(types.Part.from_function_response(name=fc.name, response={"result": out}))
        contents.append(types.Content(role="user", parts=result_parts))

    return "Agent dừng vì quá số bước cho phép.", trace
