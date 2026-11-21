import streamlit as st

from app.advisor import build_plan, latest_plan, toggle_item
from app.agent import run_agent
from app.analytics import answers_df
from app.ui import require_login, subject_selector

st.set_page_config(page_title="Lộ trình", page_icon="🧭", layout="wide")
user = require_login()
st.title("🧭 AI nhận xét & lộ trình học")

KIND_ICON = {"study": "📖", "quiz": "📝", "review": "🔁"}
TOOL_VI = {"get_student_overview": "Xem tổng quan học tập", "get_topic_mastery": "Lấy mastery từng chủ đề",
           "get_recent_mistakes": "Xem các câu làm sai gần đây", "search_documents": "Tra cứu sách giáo khoa",
           "save_study_plan": "Lưu kế hoạch"}

with st.expander("Tạo lộ trình mới", expanded=latest_plan(user.id) is None):
    subject = subject_selector("Môn (để 'Tất cả' nếu muốn tổng hợp)", allow_all=True)
    goal = st.text_input("Mục tiêu", placeholder="ví dụ: đạt 8 điểm kiểm tra giữa kỳ chương 1")
    c1, c2 = st.columns(2)
    days = c1.slider("Số ngày", 3, 14, 7)
    hours = c2.slider("Giờ học / ngày", 0.5, 4.0, 1.0, 0.5)
    mode = st.radio("Cách phân tích", ["🤖 AI Agent (tự tra cứu dữ liệu, ~5–10 request, kỹ hơn)",
                                        "🤖🤖🤖 Multi-agent: Chẩn đoán → Lập kế hoạch → Phản biện (~10–15 request, chặt chẽ nhất)",
                                        "⚡ Nhanh (1 request)"], horizontal=False)
    n_answers = len(answers_df(user.id))
    if n_answers < 5:
        st.warning(f"Mới có {n_answers} câu quiz. AI vẫn lập được kế hoạch nhưng sẽ chung chung — nên làm thêm quiz trước.")

    if st.button("Phân tích và lập kế hoạch", type="primary"):
        sid = subject.id if subject else None
        try:
            if mode.startswith("⚡"):
                with st.spinner("AI đang đọc số liệu của bạn..."):
                    build_plan(user.id, sid, goal, days, hours)
            elif mode.startswith("🤖🤖🤖"):
                from app.multi_agent import run_pipeline
                log = st.status("Multi-agent đang làm việc...", expanded=True)
                NAMES = {"diagnoser": "🩺 Agent chẩn đoán", "planner": "🗺️ Agent lập kế hoạch", "critic": "🧐 Agent phản biện", "done": "✅"}

                def on_event(stage, text):
                    if stage == "tool":
                        log.write(f"  🔧 {text}")
                    elif text == "bắt đầu":
                        log.write(f"**{NAMES.get(stage, stage)}** bắt đầu")
                    elif stage == "critic":
                        log.write(f"**{NAMES['critic']}**:\n{text}")
                    elif stage == "done":
                        log.write(text)
                    elif stage == "planner" and text.startswith("sửa"):
                        log.write("🗺️ Agent lập kế hoạch sửa theo phản biện")

                out = run_pipeline(user.id, sid, goal, days, hours, on_event=on_event)
                log.update(label=f"Multi-agent xong — {len(out['trace'])} lần gọi công cụ, phản biện chấm {out['critique']['score']}/10",
                           state="complete", expanded=False)
                st.session_state.agent_answer = out["diagnosis"]
            else:
                log = st.status("Agent đang làm việc...", expanded=True)

                def on_step(step):
                    args = ", ".join(f"{k}={v}" for k, v in step["args"].items() if k != "items" and k != "summary")
                    log.write(f"🔧 **{TOOL_VI.get(step['tool'], step['tool'])}** `{step['tool']}({args})`"
                              + ("" if step["ok"] else " ❌"))

                msg = (f"Phân tích tình hình học tập của em và lập kế hoạch {days} ngày, khoảng {hours} giờ/ngày. "
                       f"Mục tiêu: {goal or 'nắm vững chương đang học'}. Nhớ gọi save_study_plan để lưu kế hoạch.")
                import time as _t
                _t0 = _t.time()
                answer, trace = run_agent(user.id, sid, msg, on_step=on_step)
                from app.reflection import log_run, save_snapshot, validate_plan
                _p = latest_plan(user.id)
                _viol = []
                if _p:
                    save_snapshot(_p.id)
                    _viol = validate_plan([{"day": i.day, "topic_id": i.topic_id, "kind": i.kind} for i in _p.items], user.id, sid, _p.days)
                    log_run(user.id, "agent", _p.id, n_tool_calls=len(trace), duration_s=_t.time() - _t0, violations=_viol)
                log.update(label=f"Agent xong — {len(trace)} lần gọi công cụ" + (f" · validator: {len(_viol)} vi phạm" if _viol else " · validator ✅"),
                           state="complete", expanded=False)
                st.session_state.agent_answer = answer
        except Exception as e:  # noqa: BLE001
            st.error(f"Lỗi: {e}")
            st.stop()
        st.rerun()

if st.session_state.get("agent_answer"):
    with st.expander("Phân tích chi tiết của Agent", expanded=True):
        st.markdown(st.session_state.agent_answer)

plan = latest_plan(user.id)
if not plan:
    st.stop()

st.caption(f"Tạo lúc {plan.created_at:%H:%M %d/%m/%Y} · {plan.days} ngày · Mục tiêu: {plan.goal or '—'}")
from app.reflection import plan_outcome
_o = plan_outcome(plan.id)
if _o["age_days"] >= 1 or _o["done"]:
    c1, c2, c3 = st.columns(3)
    c1.metric("Đã hoàn thành", f"{_o['done']}/{_o['n_items']} việc")
    c2.metric("Mastery các chủ đề nhắm tới", f"{_o['avg_delta']:+.0f} điểm" if _o["avg_delta"] is not None else "—",
              help="So với lúc tạo kế hoạch (agent tự đo hậu quả của chính nó)")
    c3.metric("Tuổi kế hoạch", f"{_o['age_days']:.0f} ngày")
    if _o["topic_deltas"]:
        with st.expander("Chi tiết thay đổi theo chủ đề"):
            for d in _o["topic_deltas"]:
                st.write(f"- {d['topic']}: {d['before']:.0f}% → {d['after']:.0f}% ({d['delta']:+d})")
st.subheader("Nhận xét")
st.markdown(plan.summary)
with st.expander("Số liệu lúc tạo kế hoạch"):
    st.text(plan.evidence)

st.subheader("Kế hoạch")
total = len(plan.items)
done = sum(i.done for i in plan.items)
st.progress(done / total if total else 0, text=f"Hoàn thành {done}/{total} việc")

for day in range(1, plan.days + 1):
    items = [i for i in plan.items if i.day == day]
    if not items:
        continue
    st.markdown(f"**Ngày {day}**")
    for it in items:
        c1, c2, c3 = st.columns([1, 12, 2])
        checked = c1.checkbox("done", value=it.done, key=f"it{it.id}", label_visibility="collapsed")
        if it.kind == "quiz" and it.topic and not it.done:
            if c3.button("Làm ngay", key=f"go{it.id}"):
                st.session_state.quiz_preset = {"topic_id": it.topic_id, "plan_item_id": it.id}
                st.session_state.quiz_id = None
                st.session_state.quiz_result = None
                st.switch_page("pages/3_📝_Quiz.py")
        if checked != it.done:
            toggle_item(it.id, checked)
            st.rerun()
        label = f"{KIND_ICON.get(it.kind, '•')} **{it.title}**"
        if it.topic:
            label += f" · _{it.topic.name}_"
        c2.markdown(("~~" + label + "~~") if it.done else label)
        if it.detail:
            c2.caption(it.detail)

st.info("💡 Sau khi làm thêm quiz, hãy tạo lộ trình mới — AI sẽ điều chỉnh theo kết quả mới nhất.")
