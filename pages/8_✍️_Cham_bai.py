import streamlit as st

from app.db import Chapter, SessionLocal
from app.grader import grade, save_as_answer
from app.ui import require_login, subject_selector

st.set_page_config(page_title="Chấm bài", page_icon="✍️", layout="wide")
user = require_login()
st.title("✍️ Chấm bài tự luận / bài giải viết tay")
st.caption("Chụp ảnh bài làm (hoặc dán text). AI đọc, chấm từng bước, chỉ ra **bước sai đầu tiên** và lỗi kiến thức. "
           "Kết quả được ghi vào hồ sơ học tập như một câu tự luận.")

subject = subject_selector()
with SessionLocal() as s:
    chapters = [(c.id, c.name, [(t.id, t.name) for t in c.topics])
                for c in s.query(Chapter).filter_by(subject_id=subject.id).order_by(Chapter.order)]
chapter = st.selectbox("Chương (để AI chọn đúng chủ đề)", [None] + chapters,
                       format_func=lambda c: "— Cả môn —" if c is None else c[1])
topic_ids = [t[0] for t in chapter[2]] if chapter else []

col1, col2 = st.columns(2)
with col1:
    img = st.file_uploader("Ảnh bài làm (jpg/png)", type=["jpg", "jpeg", "png", "webp"])
    if img:
        st.image(img, use_container_width=True)
with col2:
    problem = st.text_area("Đề bài (tuỳ chọn, nếu ảnh không có đề)", height=100)
    text = st.text_area("Hoặc dán bài làm dạng text", height=180)

if st.button("Chấm bài", type="primary", disabled=not (img or text.strip())):
    with st.spinner("AI đang đọc và chấm (1 request)..."):
        try:
            r = grade(user.id, subject.id, img.getvalue() if img else None, img.type if img else "",
                      text, problem, topic_ids)
        except Exception as e:  # noqa: BLE001
            st.error(f"Lỗi: {e}")
            st.stop()
    st.session_state.grade_result = r

r = st.session_state.get("grade_result")
if r:
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Điểm", f"{r['score']:.1f}/10")
    c2.metric("Loại lỗi", r["error_type"])
    c3.metric("Bước sai đầu tiên", "—" if r["first_error_step"] <= 0 else f"Bước {r['first_error_step']}")
    st.markdown(f"**Đề bài:** {r['problem']}")
    st.subheader("Từng bước")
    for i, stp in enumerate(r["steps"], 1):
        mark = "✅" if stp["correct"] else "❌"
        box = st.container(border=True)
        box.markdown(f"{mark} **Bước {i}.** {stp['step']}")
        box.caption(stp["comment"])
    st.info(f"**Nhận xét:** {r['feedback']}")
    st.success(f"**Cách làm đúng:** {r['correct_solution_hint']}")
    with SessionLocal() as s:
        from app.db import Topic
        t = s.get(Topic, r["topic_id"])
        st.caption(f"Chủ đề: {t.path if t else r['topic_id']}")
    if st.button("💾 Lưu vào hồ sơ học tập"):
        save_as_answer(user.id, subject.id, r)
        st.session_state.grade_result = None
        st.toast("Đã lưu — sẽ tính vào mastery và lịch ôn.")
        st.rerun()
