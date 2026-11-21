"""Multi-agent lập lộ trình: 3 agent chuyên biệt, mỗi agent có vai trò, công cụ và tiêu chí riêng.

  1. DIAGNOSER  (Chẩn đoán)  — chỉ đọc dữ liệu (overview, mastery, mistakes, review/prereq) -> bản chẩn đoán.
  2. PLANNER    (Lập kế hoạch) — nhận chẩn đoán, tra sách, tạo kế hoạch NHÁP (chưa lưu).
  3. CRITIC     (Phản biện)   — kiểm tra kế hoạch theo checklist (tiên quyết, phủ chủ đề yếu, khối lượng, xen kẽ quiz);
                                 nếu có lỗi -> PLANNER sửa 1 lần -> lưu.

So với single-agent: mỗi agent có prompt ngắn, nhiệm vụ rõ, dễ kiểm tra; critic bắt được lỗi mà một agent tự làm
thường bỏ qua (ví dụ luyện 'Khảo sát đồ thị' khi 'Cực trị' còn yếu).
"""
from __future__ import annotations

import json
from datetime import datetime

from app.agent import run_agent
from app.llm import generate_json

DIAGNOSER_SYS = """Bạn là AGENT CHẨN ĐOÁN. Chỉ được đọc dữ liệu bằng công cụ, KHÔNG lập kế hoạch.
Nhiệm vụ: gọi get_student_overview, get_topic_mastery, get_review_and_prerequisites, và get_recent_mistakes cho 2–3 chủ đề yếu nhất.
Đầu ra (markdown, ngắn, có số liệu):
## Chẩn đoán
- Tổng quan: ...
- Chủ đề yếu (mastery %, n câu): ...
- Lỗi lặp lại quan sát được: ...
- Chủ đề bị chặn bởi tiên quyết yếu: ...
- Chủ đề đến hạn ôn: ...
- Thứ tự học đề xuất (tiên quyết trước): ..."""

PLANNER_SYS = """Bạn là AGENT LẬP KẾ HOẠCH. Bạn nhận một bản CHẨN ĐOÁN đã có số liệu; KHÔNG cần tra lại dữ liệu học sinh.
Có thể dùng search_documents để dẫn trang sách cho việc 'đọc lại'.
Kế hoạch sẽ bị BỘ KIỂM TRA TỰ ĐỘNG chấm theo 5 luật cứng — hãy tự kiểm tra trước khi trả lời:
R1. Tiên quyết trước: chủ đề X có tiên quyết Y đang Yếu -> phải có việc củng cố Y ở ngày <= ngày của X.
R2. Phủ đủ: mọi chủ đề Yếu trong chẩn đoán đều có mặt.
R3. Đến hạn ôn: chủ đề đến hạn xếp ngày 1–2; NẾU nó bị chặn bởi tiên quyết yếu thì xếp TIÊN QUYẾT vào ngày 1–2 và chủ đề đó ngay sau.
R4. Khối lượng: mỗi ngày 1–3 việc, không ngày trống ở giữa, 20–45 phút/việc.
R5. Xen kẽ: có quiz ít nhất mỗi 2 ngày.
Mẹo gỡ xung đột R1/R3: ngày 1 = củng cố tiên quyết (study ngắn + quiz), ngày 2 = chủ đề đến hạn.
CHƯA gọi save_study_plan. Trả về kế hoạch NHÁP dưới dạng JSON thuần (không markdown) theo mẫu:
{"summary": "...", "items": [{"day": 1, "topic_id": 0, "kind": "study|quiz|review", "title": "...", "detail": "..."}]}"""

CRITIC_SCHEMA = {
    "type": "object",
    "properties": {
        "approved": {"type": "boolean"},
        "issues": {"type": "array", "items": {"type": "string"}},
        "suggested_fixes": {"type": "array", "items": {"type": "string"}},
        "score": {"type": "integer"},
    },
    "required": ["approved", "issues", "suggested_fixes", "score"],
}

CRITIC_SYS = """Bạn là AGENT PHẢN BIỆN, kiểm tra kế hoạch học của một agent khác. Chấm theo checklist:
1. Thứ tự tiên quyết: không luyện chủ đề mà chẩn đoán nói nền còn yếu trước khi củng cố nền.
2. Phủ đủ: mọi chủ đề Yếu trong chẩn đoán đều xuất hiện trong kế hoạch.
3. Đến hạn ôn: chủ đề đến hạn được xếp trong 2 ngày đầu.
4. Khối lượng: mỗi ngày 1–3 việc; không ngày nào trống ở giữa.
5. Xen kẽ: có quiz ít nhất mỗi 2 ngày; không toàn study.
6. Cụ thể: mỗi việc nói rõ làm gì (trang sách, dạng bài, số câu), không chung chung.
Trả về approved=true chỉ khi không vi phạm mục 1–3. score 0–10."""


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):]
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def run_pipeline(user_id: int, subject_id: int | None, goal: str, days: int, hours: float, on_event=None) -> dict:
    """Trả về {diagnosis, draft, critique, final_plan_id, trace}. on_event(stage, text) để UI hiển thị."""
    ev = on_event or (lambda *a: None)
    trace: list[dict] = []
    t_start = datetime.now()

    # 1) Chẩn đoán
    ev("diagnoser", "bắt đầu")
    diagnosis, t1 = run_agent(user_id, subject_id, f"Chẩn đoán tình hình học tập. Mục tiêu học sinh: {goal or 'nắm vững chương đang học'}.",
                              on_step=lambda st: ev("tool", f"[Chẩn đoán] {st['tool']}"), system=DIAGNOSER_SYS,
                              tool_names=["get_student_overview", "get_topic_mastery", "get_recent_mistakes", "get_review_and_prerequisites"])
    trace += [{"agent": "diagnoser", **s} for s in t1]
    ev("diagnoser", diagnosis)

    # 2) Lập kế hoạch nháp
    ev("planner", "bắt đầu")
    ask = f"""CHẨN ĐOÁN:
{diagnosis}

YÊU CẦU: kế hoạch {days} ngày, {hours} giờ/ngày. Mục tiêu: {goal or 'nắm vững chương đang học'}."""
    draft_text, t2 = run_agent(user_id, subject_id, ask, on_step=lambda st: ev("tool", f"[Kế hoạch] {st['tool']}"),
                               system=PLANNER_SYS, tool_names=["search_documents"])
    trace += [{"agent": "planner", **s} for s in t2]
    draft = _extract_json(draft_text)
    ev("planner", draft_text)

    # 3) Phản biện
    ev("critic", "bắt đầu")
    critique = generate_json(f"CHẨN ĐOÁN:\n{diagnosis}\n\nKẾ HOẠCH:\n{json.dumps(draft, ensure_ascii=False)}",
                             CRITIC_SCHEMA, system=CRITIC_SYS, temperature=0.1)
    ev("critic", f"approved={critique['approved']} score={critique['score']}\n" + "\n".join(f"- {i}" for i in critique["issues"]))

    # 4) Sửa 1 lần nếu bị bác
    if not critique["approved"] and critique["suggested_fixes"]:
        ev("planner", "sửa theo phản biện")
        fix_ask = ask + "\n\nKẾ HOẠCH NHÁP TRƯỚC:\n" + json.dumps(draft, ensure_ascii=False) + \
                  "\n\nPHẢN BIỆN YÊU CẦU SỬA:\n" + "\n".join(f"- {f}" for f in critique["suggested_fixes"]) + \
                  "\n\nHãy trả về kế hoạch đã sửa (JSON thuần)."
        draft_text, t3 = run_agent(user_id, subject_id, fix_ask, on_step=lambda st: ev("tool", f"[Kế hoạch v2] {st['tool']}"),
                                   system=PLANNER_SYS, tool_names=["search_documents"])
        trace += [{"agent": "planner_v2", **s} for s in t3]
        draft = _extract_json(draft_text)

    # 4b) Cổng chặn cứng (bậc 6): validator bằng code, không phụ thuộc LLM. Vi phạm còn lại -> sửa thêm 1 lần.
    from app.reflection import log_run, save_snapshot, validate_plan
    viol = validate_plan(draft.get("items", []), user_id, subject_id, days)
    for round_ in range(2):                       # tối đa 2 vòng sửa theo validator
        if not viol:
            break
        ev("validator", "\n".join(f"- {x}" for x in viol))
        fix_ask = ask + "\n\nKẾ HOẠCH NHÁP:\n" + json.dumps(draft, ensure_ascii=False) + \
                  "\n\nBỘ KIỂM TRA TỰ ĐỘNG PHÁT HIỆN VI PHẠM (bắt buộc sửa hết, giữ nguyên phần đã đúng):\n" + \
                  "\n".join(f"- {x}" for x in viol) + \
                  "\n\nTrả về kế hoạch đã sửa (JSON thuần)."
        draft_text, t4 = run_agent(user_id, subject_id, fix_ask, on_step=lambda st: ev("tool", f"[Kế hoạch v{3 + round_}] {st['tool']}"),
                                   system=PLANNER_SYS, tool_names=["search_documents"])
        trace += [{"agent": f"planner_v{3 + round_}", **s} for s in t4]
        draft = _extract_json(draft_text)
        viol = validate_plan(draft.get("items", []), user_id, subject_id, days)

    # 4c) Còn vi phạm -> code tự sửa xác định ("LLM đề xuất, code bảo đảm")
    repairs: list[str] = []
    if viol:
        from app.reflection import auto_repair
        new_items, repairs = auto_repair(draft.get("items", []), user_id, subject_id, days)
        if repairs:
            draft["items"] = new_items
            viol = validate_plan(new_items, user_id, subject_id, days)
            ev("repair", "\n".join(f"- {r}" for r in repairs))

    # 5) Lưu
    from app.agent import make_tools
    save = next(f for f in make_tools(user_id, subject_id) if f.__name__ == "save_study_plan")
    summary = f"{draft.get('summary', '')}\n\n---\n**Chẩn đoán (agent 1):**\n{diagnosis}\n\n" \
              f"**Phản biện (agent 3):** {'✅ đạt' if critique['approved'] else '⚠️ đã sửa theo góp ý'} · điểm {critique['score']}/10" + \
              ("\n" + "\n".join(f"- {i}" for i in critique["issues"]) if critique["issues"] else "") + \
              (f"\n\n**Bộ kiểm tra tự động:** {'✅ không vi phạm' if not viol else '⚠️ còn ' + str(len(viol)) + ' vi phạm: ' + '; '.join(viol[:3])}")
    res = save(goal=goal, days=days, summary=summary, items=draft.get("items", []))
    save_snapshot(res["plan_id"])
    log_run(user_id, "multi", res["plan_id"], n_tool_calls=len(trace), duration_s=(datetime.now() - t_start).total_seconds(),
            critic_score=int(critique["score"]), critic_approved=bool(critique["approved"]), violations=viol)
    ev("done", f"đã lưu kế hoạch #{res['plan_id']} ({res['items_saved']} việc)" + (f" · còn {len(viol)} vi phạm" if viol else " · validator ✅"))
    return {"diagnosis": diagnosis, "draft": draft, "critique": critique, "violations": viol,
            "final_plan_id": res["plan_id"], "trace": trace}
