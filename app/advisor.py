"""AI nhận xét và xây dựng lộ trình học dựa trên số liệu thật của người học.

Chưa dùng function calling: toàn bộ số liệu (mastery theo topic, điểm số) được
tính sẵn bằng analytics rồi đưa vào prompt, AI chỉ việc lập luận trên đó -> 1 request.
"""
from datetime import datetime

from app.analytics import student_summary_text, topic_mastery
from app.db import PlanItem, SessionLocal, StudyPlan, Topic
from app.llm import generate_json

SYSTEM = """Bạn là gia sư cá nhân. Bạn nhận được số liệu học tập THẬT của một học sinh
(mức độ nắm vững từng chủ đề tính từ kết quả quiz, điểm số các môn) và phải:
1. Nhận xét ngắn gọn, cụ thể, dựa trên số liệu (nêu con số), giọng khích lệ nhưng thẳng thắn.
2. Lập kế hoạch học theo ngày. Nguyên tắc:
   - Ưu tiên chủ đề Yếu, rồi đến chủ đề chưa có dữ liệu, sau đó ôn nhẹ chủ đề Trung bình.
   - Mỗi ngày 1–3 việc, mỗi việc 20–45 phút, có việc cụ thể (đọc lại phần nào, làm quiz chủ đề nào, làm dạng bài gì).
   - Xen kẽ: học (study) → làm quiz (quiz) → ôn lại (review). Có ít nhất 1 quiz mỗi 2 ngày để hệ thống đo lại tiến bộ.
   - Chỉ dùng topic_id trong danh sách được cung cấp; việc không gắn chủ đề cụ thể thì để topic_id = 0.
3. Không bịa số liệu không có trong dữ liệu."""

SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "advice": {"type": "array", "items": {"type": "string"}},
        "plan": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer"},
                    "topic_id": {"type": "integer"},
                    "kind": {"type": "string", "enum": ["study", "quiz", "review"]},
                    "title": {"type": "string"},
                    "detail": {"type": "string"},
                },
                "required": ["day", "topic_id", "kind", "title", "detail"],
            },
        },
    },
    "required": ["summary", "strengths", "weaknesses", "advice", "plan"],
}


PHIEN_BAN_LO_TRINH = 1


def ma_lo_trinh(user_id: int, subject_id: int | None, goal: str, days: int, hours_per_day: float) -> str:
    """Mã lộ trình từ tình trạng học + yêu cầu. Cùng mã -> cùng kế hoạch.

    Mastery được làm tròn về bội số 5 trước khi băm: hai học sinh 61% và 63% coi như
    cùng một tình trạng, không vì lệch 2% mà nhận hai lộ trình khác nhau.
    """
    import hashlib

    m = topic_mastery(user_id, subject_id)
    van_trang_thai = ";".join(
        f"{int(r['topic_id'])}:{'-' if not r['n'] else int(round(r['mastery'] / 5) * 5)}"
        for _, r in m.sort_values("topic_id").iterrows())
    van = (f"v{PHIEN_BAN_LO_TRINH}|m{subject_id}|d{days}|h{hours_per_day}"
           f"|g{(goal or '').strip().lower()}|{van_trang_thai}")
    return f"LT-{hashlib.sha256(van.encode()).hexdigest()[:6].upper()}"


def _sao_chep_lo_trinh(code: str, user_id: int, subject_id: int | None, goal: str, days: int) -> int | None:
    """Có lộ trình cũ cùng mã thì dựng lại y hệt cho người này, khỏi gọi AI."""
    with SessionLocal() as s:
        cu = s.query(StudyPlan).filter(StudyPlan.code == code).order_by(StudyPlan.id).first()
        if not cu:
            return None
        items = s.query(PlanItem).filter_by(plan_id=cu.id).order_by(PlanItem.day, PlanItem.id).all()
        if not items:
            return None
        moi = StudyPlan(user_id=user_id, subject_id=subject_id, goal=goal, days=days,
                        summary=cu.summary, evidence=cu.evidence, code=code)
        s.add(moi); s.flush()
        for it in items:
            s.add(PlanItem(plan_id=moi.id, day=it.day, topic_id=it.topic_id,
                           kind=it.kind, title=it.title, detail=it.detail))
        s.commit()
        plan_id = moi.id
    from app.reflection import save_snapshot
    save_snapshot(plan_id)
    return plan_id


def build_plan(user_id: int, subject_id: int | None, goal: str, days: int, hours_per_day: float) -> int:
    """Gọi AI 1 lần, lưu StudyPlan + PlanItem, trả về plan_id.

    Nếu đã có lộ trình cùng mã (cùng tình trạng học, cùng yêu cầu) thì dựng lại cái đó.
    """
    code = ma_lo_trinh(user_id, subject_id, goal, days, hours_per_day)
    lai = _sao_chep_lo_trinh(code, user_id, subject_id, goal, days)
    if lai is not None:
        return lai

    summary = student_summary_text(user_id, subject_id)
    m = topic_mastery(user_id, subject_id)
    topic_list = "\n".join(f"- topic_id={int(r['topic_id'])}: {r['chapter']} / {r['topic']}" for _, r in m.iterrows())

    prompt = f"""SỐ LIỆU HỌC TẬP (mastery % = mức nắm vững tính từ quiz, có trọng số độ khó và thời gian):
{summary}

DANH SÁCH CHỦ ĐỀ HỢP LỆ:
{topic_list}

MỤC TIÊU CỦA HỌC SINH: {goal or 'nắm vững chương đang học'}
THỜI GIAN: {days} ngày, khoảng {hours_per_day} giờ/ngày.
Hôm nay là {datetime.now():%d/%m/%Y}.

Hãy nhận xét và lập kế hoạch {days} ngày."""

    from app.reflection import lessons_prompt
    data = generate_json(prompt, SCHEMA, system=SYSTEM + lessons_prompt(user_id), temperature=0.6)
    valid = {int(t) for t in m["topic_id"]}

    with SessionLocal() as s:
        plan = StudyPlan(user_id=user_id, subject_id=subject_id, goal=goal, days=days, code=code,
                         summary="\n".join([data["summary"], "",
                                            "**Điểm mạnh:** " + "; ".join(data["strengths"]) if data["strengths"] else "",
                                            "**Cần cải thiện:** " + "; ".join(data["weaknesses"]) if data["weaknesses"] else "",
                                            "**Lời khuyên:**\n" + "\n".join(f"- {a}" for a in data["advice"])]),
                         evidence=summary)
        s.add(plan); s.flush()
        for it in data["plan"]:
            if not (1 <= it["day"] <= days):
                continue
            tid = it["topic_id"] if it["topic_id"] in valid else None
            s.add(PlanItem(plan_id=plan.id, day=it["day"], topic_id=tid, kind=it["kind"],
                           title=it["title"], detail=it["detail"]))
        s.commit()
        plan_id = plan.id
    # bậc 6: snapshot để đo hậu quả + validator cứng + nhật ký
    from app.reflection import log_run, save_snapshot, validate_plan
    save_snapshot(plan_id)
    viol = validate_plan(data["plan"], user_id, subject_id, days)
    log_run(user_id, "quick", plan_id, n_tool_calls=0, duration_s=0, violations=viol)
    return plan_id


def latest_plan(user_id: int) -> StudyPlan | None:
    with SessionLocal() as s:
        plan = s.query(StudyPlan).filter_by(user_id=user_id).order_by(StudyPlan.id.desc()).first()
        if plan:
            for it in plan.items:
                _ = it.topic.name if it.topic else None
        return plan


def toggle_item(item_id: int, done: bool):
    with SessionLocal() as s:
        s.get(PlanItem, item_id).done = done
        s.commit()
