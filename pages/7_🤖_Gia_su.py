import streamlit as st

from app.agent import run_agent
from app.ui import require_login, subject_selector

st.set_page_config(page_title="Gia sư AI", page_icon="🤖", layout="wide")
user = require_login()
st.title("🤖 Gia sư AI (Agent)")
st.caption("Khác với 'Hỏi AI' (trả lời theo sách), Gia sư AI tự tra cứu dữ liệu học tập của bạn "
           "bằng công cụ rồi mới trả lời. Mỗi câu tốn 2–8 request.")

TOOL_VI = {"get_student_overview": "Xem tổng quan học tập", "get_topic_mastery": "Lấy mastery từng chủ đề",
           "get_recent_mistakes": "Xem các câu làm sai gần đây", "search_documents": "Tra cứu sách giáo khoa",
           "save_study_plan": "Lưu kế hoạch"}

with st.sidebar:
    subject = subject_selector("Phạm vi", allow_all=True)
    st.markdown("**Gợi ý câu hỏi**")
    for q in ["Em đang yếu nhất chỗ nào? Vì sao?",
              "Em hay sai kiểu gì ở phần cực trị?",
              "Tối nay có 45 phút, em nên học gì?",
              "So với tuần trước em có tiến bộ không?"]:
        if st.button(q, use_container_width=True):
            st.session_state.tutor_q = q

ss = st.session_state
ss.setdefault("tutor_history", [])

for m in ss.tutor_history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("trace"):
            with st.expander(f"🔧 Agent đã gọi {len(m['trace'])} công cụ"):
                for step in m["trace"]:
                    args = ", ".join(f"{k}={v}" for k, v in step["args"].items() if k not in ("items", "summary"))
                    st.markdown(f"- **{TOOL_VI.get(step['tool'], step['tool'])}** `{step['tool']}({args})`")
                    st.caption(step["result_preview"][:200] + "…")

q = st.chat_input("Hỏi gia sư về việc học của bạn...") or ss.pop("tutor_q", None)
if q:
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        log = st.status("Đang tra cứu...", expanded=True)

        def on_step(step):
            args = ", ".join(f"{k}={v}" for k, v in step["args"].items() if k not in ("items", "summary"))
            log.write(f"🔧 {TOOL_VI.get(step['tool'], step['tool'])} `{step['tool']}({args})`")

        try:
            # đưa 2 lượt gần nhất làm ngữ cảnh
            ctx = "\n".join(f"{m['role']}: {m['content'][:500]}" for m in ss.tutor_history[-4:])
            msg = (f"Hội thoại trước:\n{ctx}\n\nCâu hỏi mới: {q}" if ctx else q)
            answer, trace = run_agent(user.id, subject.id if subject else None, msg, on_step=on_step)
        except Exception as e:  # noqa: BLE001
            log.update(label="Lỗi", state="error")
            st.error(str(e))
            st.stop()
        log.update(label=f"Đã gọi {len(trace)} công cụ", state="complete", expanded=False)
        st.markdown(answer)
    ss.tutor_history += [{"role": "user", "content": q}, {"role": "assistant", "content": answer, "trace": trace}]
    st.rerun()
