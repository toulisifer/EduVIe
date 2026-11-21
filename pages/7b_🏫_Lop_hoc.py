from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from app.classroom import (assignment_results, assignments_for_student, class_heatmap, class_overview,
                           class_topic_avg, classes_of_student, create_assignment, create_class, join_class,
                           my_classes, start_assignment, submit_assignment)
from app.db import Chapter, SessionLocal, Subject
from app.quiz import DIFFICULTY_VI, load_quiz
from app.ui import require_login

st.set_page_config(page_title="Lớp học", page_icon="🏫", layout="wide")
user = require_login()
is_teacher = user.role in ("teacher", "admin")
st.title("🏫 Lớp học")
ss = st.session_state

# =========================================================== HỌC SINH
def student_view():
    st.subheader("Lớp của tôi")
    with st.form("join"):
        code = st.text_input("Mã lớp (giáo viên cung cấp)", placeholder="ví dụ: 12A1-7F3K")
        if st.form_submit_button("Tham gia") and code.strip():
            c, err = join_class(user.id, code)
            st.error(err) if err and not c else st.success(f"Đã vào lớp {c.name}")
            if c and not err:
                st.rerun()
    cs = classes_of_student(user.id)
    if not cs:
        st.info("Bạn chưa ở trong lớp nào.")
    for c in cs:
        st.write(f"- **{c.name}** · mã `{c.code}` · {len(c.assignments)} đề đã giao")

    st.subheader("Đề được giao")
    asg = assignments_for_student(user.id)
    if not asg:
        st.caption("Chưa có đề nào.")
    for a in asg:
        c1, c2 = st.columns([6, 1])
        status = f"✅ {a['score']}/10" if a["done"] else ("⏰ hạn " + a["due"].strftime("%d/%m") if a["due"] else "⏳ chưa làm")
        c1.write(f"**{a['title']}** · {a['class']} · {a['n_questions']} câu · {status}")
        if not a["done"] and c2.button("Làm", key=f"do{a['id']}"):
            ss.asg_quiz = (a["id"], start_assignment(a["id"], user.id))
            st.rerun()

    if ss.get("asg_quiz"):
        aid, qid = ss.asg_quiz
        qs = load_quiz(qid)
        st.divider()
        st.subheader("Bài làm")
        with st.form("asg_form"):
            sel = {}
            for i, q in enumerate(qs, 1):
                st.markdown(f"**Câu {i}.** {q.content}")
                ch = st.radio("Chọn", q.options, index=None, key=f"aq{q.id}", label_visibility="collapsed")
                sel[q.id] = q.options.index(ch) if ch is not None else None
                st.divider()
            if st.form_submit_button("Nộp bài", type="primary"):
                r = submit_assignment(aid, qid, user.id, sel)
                ss.asg_quiz = None
                st.success(f"Điểm: {r['score']}/10 ({r['n_correct']}/{r['n']} đúng)")
                st.rerun()


# =========================================================== GIÁO VIÊN
def teacher_view():
    tab_cls, tab_asg = st.tabs(["📊 Lớp & phân tích", "📝 Giao đề"])
    with tab_cls:
        with st.expander("Tạo lớp mới"):
            with SessionLocal() as s:
                subjects = [(x.id, x.name) for x in s.query(Subject)]
            name = st.text_input("Tên lớp", placeholder="12A1")
            subj = st.selectbox("Môn", [None] + subjects, format_func=lambda x: "Tất cả môn" if x is None else x[1])
            if st.button("Tạo lớp") and name.strip():
                c = create_class(user.id, name.strip(), subj[0] if subj else None)
                st.success(f"Đã tạo lớp {c.name} — mã tham gia: **{c.code}**")
                st.rerun()
        cs = my_classes(user.id)
        if not cs:
            st.info("Chưa có lớp. Tạo lớp và gửi mã cho học sinh.")
            return
        cls = st.selectbox("Lớp", cs, format_func=lambda c: f"{c.name} (mã {c.code}) · {len(c.members)} học sinh")
        ss.cls_id = cls.id
        st.markdown(f"Mã tham gia: `{cls.code}` — gửi cho học sinh nhập ở trang Lớp học.")
        ov = class_overview(cls.id)
        if ov.empty:
            st.caption("Chưa có học sinh.")
            return
        st.subheader("Tổng quan học sinh")
        st.dataframe(ov.drop(columns="user_id"), use_container_width=True, hide_index=True)

        hm = class_heatmap(cls.id)
        if not hm.empty:
            st.subheader("Bản đồ mastery cả lớp")
            long = hm.reset_index().melt(id_vars="Học sinh", var_name="Chủ đề", value_name="Mastery").dropna()
            chart = alt.Chart(long).mark_rect(stroke="white").encode(
                x=alt.X("Chủ đề:N", axis=alt.Axis(labelAngle=-30, labelLimit=160)), y="Học sinh:N",
                color=alt.Color("Mastery:Q", scale=alt.Scale(domain=[0, 50, 100], range=["#d9534f", "#f0ad4e", "#5cb85c"])),
                tooltip=["Học sinh", "Chủ đề", alt.Tooltip("Mastery:Q", format=".0f")])
            text = alt.Chart(long).mark_text(fontSize=11).encode(x="Chủ đề:N", y="Học sinh:N", text=alt.Text("Mastery:Q", format=".0f"))
            st.altair_chart((chart + text).properties(height=max(160, 32 * len(hm))), use_container_width=True)
            st.subheader("Chủ đề cả lớp yếu nhất")
            avg = class_topic_avg(cls.id)
            st.dataframe(avg.head(5).round(0), use_container_width=True, hide_index=True)

    with tab_asg:
        cs = my_classes(user.id)
        if not cs:
            st.info("Tạo lớp trước.")
            return
        cls = st.selectbox("Giao cho lớp", cs, format_func=lambda c: c.name, key="asg_cls")
        with SessionLocal() as s:
            sid = cls.subject_id or s.query(Subject).first().id
            chapters = [(c.id, c.name, [(t.id, t.name) for t in c.topics])
                        for c in s.query(Chapter).filter_by(subject_id=sid).order_by(Chapter.order)]
        title = st.text_input("Tên đề", placeholder="Kiểm tra 15 phút — Chương 1")
        chap = st.selectbox("Chương", chapters, format_func=lambda c: c[1])
        topics = st.multiselect("Chủ đề (trống = cả chương)", chap[2], format_func=lambda t: t[1]) or chap[2]
        c1, c2, c3 = st.columns(3)
        diff = c1.selectbox("Độ khó", list(DIFFICULTY_VI), format_func=DIFFICULTY_VI.get, index=1)
        n = c2.slider("Số câu", 3, 20, 10)
        due = c3.date_input("Hạn nộp", None)
        if st.button("Tạo và giao đề", type="primary", disabled=not title.strip()):
            with st.spinner("AI đang soạn đề..."):
                a = create_assignment(cls.id, user.id, title.strip(), [t[0] for t in topics], diff, n,
                                      datetime.combine(due, datetime.min.time()) if due else None)
            st.success(f"Đã giao: {a.title}")
            st.rerun()

        st.subheader("Đề đã giao")
        for a in cls.assignments:
            with st.expander(f"{a.title} · {a.created_at:%d/%m}" + (f" · hạn {a.due:%d/%m}" if a.due else "")):
                res, per_q = assignment_results(a.id)
                st.dataframe(res, use_container_width=True, hide_index=True)
                if not per_q.empty:
                    st.caption("Tỷ lệ đúng từng câu của lớp — câu thấp là chỗ cần giảng lại:")
                    st.dataframe(per_q, use_container_width=True, hide_index=True)


if is_teacher:
    mode = st.radio("Vai trò", ["Giáo viên", "Học sinh"], horizontal=True, label_visibility="collapsed")
    teacher_view() if mode == "Giáo viên" else student_view()
else:
    student_view()
