import streamlit as st

from app.config import UPLOAD_DIR
from app.db import Chapter, Document, SessionLocal, Subject, User
from app.rag.ingest import delete_document, ingest
from app.ui import require_login, subject_selector

st.set_page_config(page_title="Tài liệu", page_icon="📚", layout="wide")
user = require_login()
is_admin = user.role == "admin"
st.title("📚 Tài liệu học tập")


def library():
    """Thư viện dùng chung: mọi user đều xem được; chỉ admin có nút xoá."""
    with SessionLocal() as s:
        rows = (s.query(Document, Subject.name, Chapter.name, Chapter.order, User.username)
                .join(Subject, Document.subject_id == Subject.id)
                .outerjoin(Chapter, Document.chapter_id == Chapter.id)
                .join(User, Document.user_id == User.id)
                .filter(Document.status == "ready")
                .order_by(Subject.name, Chapter.order, Document.id).all())
    if not rows:
        st.info("Thư viện chưa có tài liệu.")
        return
    by_subject: dict[str, list] = {}
    for d, sname, cname, _, uname in rows:
        by_subject.setdefault(sname, []).append((d, cname, uname))
    for sname, items in by_subject.items():
        with st.expander(f"**{sname}** — {len(items)} tài liệu, {sum(d.n_chunks for d, _, _ in items)} đoạn", expanded=True):
            for d, cname, uname in items:
                c1, c2 = st.columns([8, 1])
                tag = f" · {cname.split(':')[0]}" if cname else ""
                c1.write(f"📄 **{d.filename}**{tag} — {d.n_chunks} đoạn" + (f" · _up bởi {uname}_" if is_admin else ""))
                if is_admin and c2.button("Xoá", key=f"del{d.id}"):
                    delete_document(d.id)
                    with SessionLocal() as s:
                        s.delete(s.get(Document, d.id)); s.commit()
                    st.rerun()


if not is_admin:
    st.caption("Tài liệu do quản trị viên cung cấp. Bạn có thể hỏi AI, làm quiz và học theo các tài liệu này.")
    library()
    st.stop()

# ---------------- Admin: upload ----------------
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("Tải lên (admin)")
    subject = subject_selector()
    with SessionLocal() as s:
        chapters = [(c.id, c.name) for c in s.query(Chapter).filter_by(subject_id=subject.id).order_by(Chapter.order)] if subject else []
    chapter = st.selectbox("Chương (tuỳ chọn)", [None] + chapters,
                           format_func=lambda c: "— Không chọn —" if c is None else c[1])
    files = st.file_uploader("Chọn PDF / DOCX / TXT / MD", type=["pdf", "docx", "txt", "md"], accept_multiple_files=True)
    c1, c2 = st.columns(2)
    p_from = c1.number_input("Trang từ", min_value=1, value=1, step=1)
    p_to = c2.number_input("đến trang (0 = hết)", min_value=0, value=0, step=1)
    st.caption("PDF scan sẽ được OCR bằng Gemini (~7 giây/trang). Nên nạp theo từng chương và chọn đúng chương.")

    if st.button("Tải lên và xử lý", type="primary", disabled=not files or not subject):
        pages = list(range(int(p_from), int(p_to) + 1)) if p_to else None
        for f in files:
            dest = UPLOAD_DIR / f"{user.id}_{f.name}"
            dest.write_bytes(f.getbuffer())
            with SessionLocal() as s:
                doc = Document(user_id=user.id, subject_id=subject.id, chapter_id=chapter[0] if chapter else None,
                               filename=f.name, path=str(dest))
                s.add(doc); s.commit(); doc_id = doc.id
            bar = st.progress(0, text=f"Đang xử lý {f.name}...")

            def progress(i, n, page_no):
                bar.progress(i / n, text=f"OCR trang {page_no} ({i + 1}/{n})")

            try:
                n = ingest(doc_id, dest, user.id, subject.id, chapter[0] if chapter else None, pages=pages, progress=progress)
                status, err = "ready", ""
                bar.progress(1.0, text="Xong")
                st.success(f"{f.name}: {n} đoạn đã được index")
            except Exception as e:  # noqa: BLE001
                n, status, err = 0, "failed", str(e)
                st.error(f"{f.name}: {e}")
            with SessionLocal() as s:
                d = s.get(Document, doc_id); d.n_chunks, d.status, d.error = n, status, err; s.commit()

with col2:
    st.subheader("Thư viện")
    library()
    with SessionLocal() as s:
        failed = s.query(Document).filter_by(status="failed").all()
    if failed:
        st.caption("Tài liệu lỗi:")
        for d in failed:
            c1, c2 = st.columns([8, 1])
            c1.write(f"❌ {d.filename} — _{d.error[:120]}_")
            if c2.button("Xoá", key=f"fdel{d.id}"):
                with SessionLocal() as s:
                    s.delete(s.get(Document, d.id)); s.commit()
                st.rerun()
