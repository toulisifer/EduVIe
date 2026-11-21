import streamlit as st

from app.db import ChatMessage, SessionLocal
from app.rag.chat import answer_stream
from app.ui import require_login, subject_selector

st.set_page_config(page_title="Hỏi AI", page_icon="💬", layout="wide")
user = require_login()
st.title("💬 Hỏi AI theo tài liệu")

with st.sidebar:
    subject = subject_selector("Phạm vi tìm kiếm", allow_all=True)
    if st.button("🗑️ Xoá lịch sử chat"):
        with SessionLocal() as s:
            s.query(ChatMessage).filter_by(user_id=user.id).delete(); s.commit()
        st.rerun()

with SessionLocal() as s:
    history = s.query(ChatMessage).filter_by(user_id=user.id).order_by(ChatMessage.id).all()
    history = [{"role": m.role, "content": m.content, "citations": m.citations} for m in history]

for m in history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m["role"] == "assistant" and m.get("citations"):
            with st.expander("Nguồn trích dẫn"):
                for i, c in enumerate(m["citations"]):
                    st.markdown(f"**[{i+1}] {c['filename']} — trang {c['page']}** (độ liên quan {c['score']})")
                    st.caption(c["text"][:400] + ("..." if len(c["text"]) > 400 else ""))

if q := st.chat_input("Đặt câu hỏi về bài học..."):
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Đang tìm trong tài liệu..."):
                hits, stream = answer_stream(q, user.id, subject.id if subject else None, history)
            text = st.write_stream(stream)
        except Exception as e:  # noqa: BLE001
            st.error(f"Lỗi gọi AI: {e}")
            st.stop()
        if hits:
            with st.expander("Nguồn trích dẫn"):
                for i, c in enumerate(hits):
                    st.markdown(f"**[{i+1}] {c['filename']} — trang {c['page']}** (độ liên quan {c['score']})")
                    st.caption(c["text"][:400] + ("..." if len(c["text"]) > 400 else ""))
    with SessionLocal() as s:
        s.add(ChatMessage(user_id=user.id, role="user", content=q))
        s.add(ChatMessage(user_id=user.id, role="assistant", content=text, citations=hits))
        s.commit()
