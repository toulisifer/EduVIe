"""Bậc 6 — Agent tự đánh giá & tự sửa.

1. validate_plan():   kiểm tra cứng (không dùng LLM) một kế hoạch theo 5 luật -> danh sách vi phạm.
2. plan_outcome():    đo hậu quả một kế hoạch: % việc hoàn thành, mastery các chủ đề nhắm tới thay đổi ra sao.
3. reflect():         agent phản tư đọc hậu quả các kế hoạch cũ + vi phạm + hành vi -> rút BÀI HỌC -> lưu DB.
4. lessons_prompt():  lấy bài học đang hiệu lực để chèn vào system prompt của agent lập kế hoạch lần sau.
5. log_run():         ghi nhật ký mỗi lần agent chạy (để vẽ chất lượng theo thời gian).

Vòng kín: lập kế hoạch -> người học làm -> đo hậu quả -> rút bài học -> kế hoạch sau tốt hơn.
"""
from __future__ import annotations

import json
import re
from datetime import datetime

from app import analytics
from app.db import AgentLesson, AgentRun, PlanItem, SessionLocal, StudyPlan, Topic
from app.learning import due_topics, prereq_mastery, prerequisites, weak_prereqs
from app.llm import generate_json

RULES = {
    "R1_prereq": "Không luyện chủ đề khi tiên quyết của nó còn Yếu trước khi có việc củng cố tiên quyết đó",
    "R2_cover": "Mọi chủ đề Yếu phải xuất hiện trong kế hoạch",
    "R3_due": "Chủ đề đến hạn ôn phải nằm trong 2 ngày đầu",
    "R4_load": "Mỗi ngày 1–3 việc, không ngày trống ở giữa",
    "R5_mix": "Có quiz ít nhất mỗi 2 ngày",
}


# ----------------------------- 1. VALIDATOR CỨNG -----------------------------
def validate_plan(items: list[dict], user_id: int, subject_id: int | None, days: int) -> list[str]:
    """items: [{day, topic_id, kind, ...}]. Trả về danh sách vi phạm dạng 'R1_prereq: ...'."""
    m = analytics.topic_mastery(user_id, subject_id)
    m_all = prereq_mastery(user_id)   # tiên quyết có thể nằm ở môn/lớp khác
    names = dict(zip(m_all["topic_id"].astype(int), m_all["topic"]))
    pre = prerequisites()
    v: list[str] = []
    by_day: dict[int, list[dict]] = {}
    for it in items:
        by_day.setdefault(int(it.get("day", 0)), []).append(it)

    # R1: tiên quyết yếu phải được củng cố trước (ngày nhỏ hơn hoặc bằng)
    first_day_of = {}
    for it in items:
        t = int(it.get("topic_id") or 0)
        if t:
            first_day_of[t] = min(first_day_of.get(t, 99), int(it.get("day", 99)))
    for it in items:
        t = int(it.get("topic_id") or 0)
        if not t or it.get("kind") not in ("quiz", "study"):
            continue
        for w in weak_prereqs(t, m_all, pre):
            wid = next((k for k, n in names.items() if n == w), None)
            if wid and first_day_of.get(wid, 99) > int(it.get("day", 0)):
                v.append(f"R1_prereq: '{names.get(t, t)}' ngày {it.get('day')} nhưng tiên quyết '{w}' còn yếu chưa được củng cố trước")

    # R2: phủ chủ đề yếu
    weak_ids = set(m[m["level"] == "Yếu"]["topic_id"].astype(int))
    covered = {int(it.get("topic_id") or 0) for it in items}
    for t in weak_ids - covered:
        v.append(f"R2_cover: chủ đề yếu '{names[t]}' không có trong kế hoạch")

    # R3: đến hạn ôn -> trong 2 ngày đầu. Nếu chủ đề đó bị chặn bởi tiên quyết yếu thì thay bằng:
    #     tiên quyết yếu phải được củng cố trong 2 ngày đầu, còn chủ đề đến hạn xếp SAU tiên quyết (tránh xung đột với R1).
    # Chỉ ép 3 chủ đề quá hạn lâu nhất (2 ngày × ≤3 việc không thể chứa nhiều hơn); phần còn lại không tính vi phạm.
    due_df = due_topics(user_id, subject_id)
    due = list(due_df.sort_values("overdue_days", ascending=False)["topic_id"].astype(int))[:3] if not due_df.empty else []
    for t in due:
        blocked = weak_prereqs(t, m_all, pre)
        if blocked:
            for w in blocked:
                wid = next((k for k, n in names.items() if n == w), None)
                dw = first_day_of.get(wid)
                if dw is None or dw > 2:
                    v.append(f"R3_due: '{names.get(t, t)}' đến hạn ôn nhưng bị chặn bởi tiên quyết yếu '{w}' — "
                             f"phải củng cố '{w}' trong 2 ngày đầu (hiện " + ("không có" if dw is None else f"ngày {dw}") + ")")
            continue
        d = first_day_of.get(t)
        if d is None or d > 2:
            v.append(f"R3_due: '{names.get(t, t)}' đến hạn ôn nhưng " + ("không có trong kế hoạch" if d is None else f"xếp ngày {d}"))

    # R4: khối lượng
    for d in range(1, days + 1):
        n = len(by_day.get(d, []))
        if n == 0 and d < max(by_day, default=0):
            v.append(f"R4_load: ngày {d} trống")
        elif n > 3:
            v.append(f"R4_load: ngày {d} có {n} việc (>3)")

    # R5: quiz mỗi 2 ngày
    quiz_days = sorted({int(it["day"]) for it in items if it.get("kind") == "quiz"})
    last = 0
    for d in range(1, days + 1):
        if d in quiz_days:
            last = d
        elif d - last >= 2 and d < days:
            v.append(f"R5_mix: không có quiz trong 2 ngày liên tiếp (tới ngày {d})")
            last = d  # báo một lần
    return v


# ----------------------------- 1b. TỰ SỬA BẰNG CODE -----------------------------
def auto_repair(items: list[dict], user_id: int, subject_id: int | None, days: int, max_passes: int = 4) -> tuple[list[dict], list[str]]:
    """Sửa xác định các vi phạm có cách sửa rõ ràng ("LLM đề xuất, code bảo đảm"):
    - R1: chèn việc 'củng cố nhanh' tiên quyết Y vào ngày của X (nếu ngày đó đầy thì dời X sang ngày sau).
    - R2: thêm study+quiz cho chủ đề yếu bị bỏ sót vào ngày còn chỗ.
    - R3 (không bị chặn): dời việc sớm nhất của chủ đề đến hạn lên ngày 1–2 nếu còn chỗ.
    Trả về (items mới, danh sách thay đổi đã thực hiện)."""
    m = analytics.topic_mastery(user_id, subject_id)
    names = dict(zip(m["topic_id"].astype(int), m["topic"]))
    ids_by_name = {v: k for k, v in names.items()}
    pre = prerequisites()
    items = [dict(it) for it in items]
    changes: list[str] = []

    def day_load(d):
        return sum(1 for it in items if int(it.get("day", 0)) == d)

    def first_day(t):
        ds = [int(it["day"]) for it in items if int(it.get("topic_id") or 0) == t]
        return min(ds) if ds else None

    def free_day(prefer: int):
        for d in list(range(prefer, days + 1)) + list(range(prefer - 1, 0, -1)):
            if day_load(d) < 3:
                return d
        return None

    for _ in range(max_passes):
        viol = validate_plan(items, user_id, subject_id, days)
        if not viol:
            break
        fixed_any = False
        for v in viol:
            if v.startswith("R1_prereq"):
                x, w = re.search(r"'(.+?)' ngày (\d+) nhưng tiên quyết '(.+?)'", v).group(1), re.search(r"tiên quyết '(.+?)'", v).group(1)
                dx = first_day(ids_by_name[x])
                dw = first_day(ids_by_name.get(w, -1))
                if dw is not None and dw <= dx:
                    continue
                if day_load(dx) >= 3:            # ngày đầy -> dời X sang ngày sau
                    for it in items:
                        if int(it.get("topic_id") or 0) == ids_by_name[x] and int(it["day"]) == dx and dx < days:
                            it["day"] = dx + 1
                items.append({"day": dx, "topic_id": ids_by_name[w], "kind": "study",
                              "title": f"Củng cố nhanh: {w} (tiên quyết của {x})",
                              "detail": "20 phút: đọc lại khung kiến thức + làm 3 câu dễ trước khi học " + x})
                changes.append(f"R1: chèn củng cố '{w}' ngày {dx} trước '{x}'"); fixed_any = True
            elif v.startswith("R2_cover"):
                t = re.search(r"'(.+?)'", v).group(1)
                d = free_day(days)
                if d:
                    items.append({"day": d, "topic_id": ids_by_name[t], "kind": "quiz", "title": f"Quiz ngắn: {t}",
                                  "detail": "5 câu để đo lại mức nắm vững"})
                    changes.append(f"R2: thêm quiz '{t}' ngày {d}"); fixed_any = True
            elif v.startswith("R3_due") and "bị chặn" in v:
                # đến hạn nhưng nền yếu -> đưa TIÊN QUYẾT vào ngày 1–2
                w = re.search(r"tiên quyết yếu '(.+?)'", v).group(1)
                wid = ids_by_name.get(w)
                d = next((dd for dd in (1, 2) if day_load(dd) < 3), None)
                cur = first_day(wid) if wid else None
                if wid and d and (cur is None or cur > 2):
                    if cur is not None:
                        for it in items:
                            if int(it.get("topic_id") or 0) == wid and int(it["day"]) == cur:
                                it["day"] = d; break
                    else:
                        items.append({"day": d, "topic_id": wid, "kind": "study", "title": f"Củng cố nền: {w}",
                                      "detail": "25 phút: khung kiến thức + 5 câu dễ (tiên quyết của chủ đề đến hạn)"})
                    changes.append(f"R3: đưa tiên quyết '{w}' lên ngày {d}"); fixed_any = True
            elif v.startswith("R3_due"):
                t = re.search(r"'(.+?)'", v).group(1)
                tid = ids_by_name[t]
                d = next((dd for dd in (1, 2) if day_load(dd) < 3), None)
                cur = first_day(tid)
                if d and cur and cur > 2:
                    for it in items:
                        if int(it.get("topic_id") or 0) == tid and int(it["day"]) == cur:
                            it["day"] = d; break
                    changes.append(f"R3: dời '{t}' từ ngày {cur} lên ngày {d}"); fixed_any = True
                elif d and cur is None:
                    items.append({"day": d, "topic_id": tid, "kind": "review", "title": f"Ôn lại: {t} (đến hạn)",
                                  "detail": "15 phút xem lại + 3 câu"})
                    changes.append(f"R3: thêm ôn '{t}' ngày {d}"); fixed_any = True
        if not fixed_any:
            break
    return items, changes


# ----------------------------- 2. ĐO HẬU QUẢ -----------------------------
def _snapshot_from_evidence(evidence: str) -> dict[int, float]:
    """Kế hoạch cũ chưa có snapshot JSON: rút '<tên topic>: NN%' từ text rồi map sang id."""
    with SessionLocal() as s:
        by_name = {t.name: t.id for t in s.query(Topic)}
    out = {}
    for name, pct in re.findall(r"-\s*(.+?):\s*(\d+)%", evidence or ""):
        if name.strip() in by_name:
            out[by_name[name.strip()]] = float(pct)
    return out


def plan_outcome(plan_id: int) -> dict:
    with SessionLocal() as s:
        p = s.get(StudyPlan, plan_id)
        items = [{"day": i.day, "topic_id": i.topic_id, "kind": i.kind, "title": i.title, "done": i.done} for i in p.items]
        uid, sid = p.user_id, p.subject_id
        snap = {int(k): float(v) for k, v in (p.snapshot or {}).items()} or _snapshot_from_evidence(p.evidence)
        created = p.created_at
    m = analytics.topic_mastery(uid, sid).set_index("topic_id")
    targets = sorted({int(i["topic_id"]) for i in items if i["topic_id"]})
    deltas = []
    for t in targets:
        if t in snap and t in m.index and m.loc[t, "n"] > 0:
            now = float(m.loc[t, "mastery"])
            deltas.append({"topic_id": t, "topic": m.loc[t, "topic"], "before": snap[t], "after": now, "delta": round(now - snap[t])})
    done = sum(i["done"] for i in items)
    return {
        "plan_id": plan_id, "created_at": created, "age_days": round((datetime.utcnow() - created).total_seconds() / 86400, 1),
        "n_items": len(items), "done": done, "completion": round(100 * done / len(items)) if items else 0,
        "skipped_kinds": {k: sum(1 for i in items if i["kind"] == k and not i["done"]) for k in ("study", "quiz", "review")},
        "topic_deltas": deltas,
        "avg_delta": round(sum(d["delta"] for d in deltas) / len(deltas), 1) if deltas else None,
    }


# ----------------------------- 3. PHẢN TƯ -----------------------------
REFLECT_SCHEMA = {
    "type": "object",
    "properties": {"lessons": {"type": "array", "items": {"type": "object", "properties": {
        "lesson": {"type": "string"}, "evidence": {"type": "string"}, "scope": {"type": "string", "enum": ["user", "global"]}},
        "required": ["lesson", "evidence", "scope"]}}},
    "required": ["lessons"],
}

REFLECT_SYS = """Bạn là AGENT PHẢN TƯ: nhìn lại các kế hoạch học tập mà agent lập kế hoạch đã tạo và HẬU QUẢ thực tế,
rồi rút ra bài học ngắn, cụ thể, hành động được, để agent lập kế hoạch lần sau làm tốt hơn.
Chỉ rút bài học có bằng chứng trong dữ liệu. Tối đa 4 bài học. Mỗi bài học 1 câu, bắt đầu bằng động từ.
scope = 'user' nếu chỉ đúng với học sinh này (thói quen), 'global' nếu là lỗi cách lập kế hoạch nói chung.
Ví dụ tốt: "Rút việc 'đọc lại lý thuyết' xuống 20 phút vì học sinh này bỏ qua 4/5 việc study dài."
Ví dụ xấu: "Cần cải thiện kế hoạch." """


def reflect(user_id: int, max_plans: int = 4) -> list[dict]:
    with SessionLocal() as s:
        plans = s.query(StudyPlan).filter_by(user_id=user_id).order_by(StudyPlan.id.desc()).limit(max_plans).all()
        plan_ids = [p.id for p in plans]
        runs = {r.plan_id: r for r in s.query(AgentRun).filter(AgentRun.plan_id.in_(plan_ids))} if plan_ids else {}
    if not plans:
        return []
    report = []
    for pid in plan_ids:
        o = plan_outcome(pid)
        r = runs.get(pid)
        report.append({**{k: v for k, v in o.items() if k != "created_at"},
                       "critic_score": r.critic_score if r else None, "violations": r.violations if r else None})
    existing = [l.lesson for l in active_lessons(user_id)]
    prompt = f"""HẬU QUẢ CÁC KẾ HOẠCH GẦN ĐÂY (mới nhất trước):
{json.dumps(report, ensure_ascii=False, default=str, indent=1)}

BÀI HỌC ĐÃ CÓ (đừng lặp lại): {existing or '(chưa có)'}

Rút bài học mới."""
    data = generate_json(prompt, REFLECT_SCHEMA, system=REFLECT_SYS, temperature=0.2)
    saved = []
    with SessionLocal() as s:
        for l in data.get("lessons", [])[:4]:
            if any(l["lesson"].strip().lower() == e.strip().lower() for e in existing):
                continue
            row = AgentLesson(user_id=user_id if l["scope"] == "user" else None, lesson=l["lesson"],
                              evidence=l["evidence"], source_plan_id=plan_ids[0])
            s.add(row); saved.append(l)
        s.commit()
    return saved


def active_lessons(user_id: int) -> list[AgentLesson]:
    with SessionLocal() as s:
        q = s.query(AgentLesson).filter(AgentLesson.active == True,  # noqa: E712
                                        (AgentLesson.user_id == user_id) | (AgentLesson.user_id == None))  # noqa: E711
        return q.order_by(AgentLesson.id.desc()).limit(8).all()


def lessons_prompt(user_id: int) -> str:
    ls = active_lessons(user_id)
    if not ls:
        return ""
    return "\nBÀI HỌC TỪ CÁC KẾ HOẠCH TRƯỚC (agent tự rút ra, PHẢI áp dụng):\n" + "\n".join(f"- {l.lesson}" for l in ls)


# ----------------------------- 5. NHẬT KÝ -----------------------------
def log_run(user_id: int, mode: str, plan_id: int | None, n_tool_calls: int, duration_s: float,
            critic_score: int | None = None, critic_approved: bool | None = None, violations: list | None = None) -> int:
    with SessionLocal() as s:
        r = AgentRun(user_id=user_id, mode=mode, plan_id=plan_id, n_tool_calls=n_tool_calls, duration_s=duration_s,
                     critic_score=critic_score, critic_approved=critic_approved, violations=violations or [])
        s.add(r); s.commit()
        return r.id


def save_snapshot(plan_id: int):
    """Lưu mastery hiện tại vào kế hoạch vừa tạo (gọi ngay sau khi lưu plan)."""
    with SessionLocal() as s:
        p = s.get(StudyPlan, plan_id)
        m = analytics.topic_mastery(p.user_id, p.subject_id)
        p.snapshot = {str(int(r.topic_id)): float(r.mastery) for r in m.itertuples() if r.n > 0}
        s.commit()
