from datetime import date, datetime

import altair as alt
import pandas as pd
import streamlit as st

from app.db import Score, SessionLocal, Subject
from app.ui import require_login

st.set_page_config(page_title="Điểm số", page_icon="🎯", layout="wide")
user = require_login()
st.title("🎯 Quản lý điểm số")

KINDS = {"mieng": ("Kiểm tra miệng", 1), "15p": ("Kiểm tra 15 phút", 1),
         "giua_ky": ("Giữa kỳ", 2), "cuoi_ky": ("Cuối kỳ", 3)}

col_form, col_view = st.columns([1, 2])

with col_form:
    st.subheader("Nhập điểm")
    with SessionLocal() as s:
        subjects = [(x.id, x.name) for x in s.query(Subject).all()]
    with st.form("score_form", clear_on_submit=True):
        subj = st.selectbox("Môn", subjects, format_func=lambda x: x[1])
        kind = st.selectbox("Loại điểm", list(KINDS), format_func=lambda k: f"{KINDS[k][0]} (hệ số {KINDS[k][1]})")
        value = st.number_input("Điểm", 0.0, 10.0, 7.0, 0.25)
        d = st.date_input("Ngày", date.today())
        if st.form_submit_button("Lưu", type="primary"):
            with SessionLocal() as s:
                s.add(Score(user_id=user.id, subject_id=subj[0], kind=kind, value=value,
                            weight=KINDS[kind][1], date=datetime.combine(d, datetime.min.time())))
                s.commit()
            st.success("Đã lưu")
            st.rerun()

with col_view:
    with SessionLocal() as s:
        rows = (s.query(Score.id, Subject.name, Score.kind, Score.value, Score.weight, Score.date)
                .select_from(Score).join(Subject, Score.subject_id == Subject.id)
                .filter(Score.user_id == user.id).order_by(Score.date).all())
    df = pd.DataFrame(rows, columns=["id", "Môn", "kind", "Điểm", "Hệ số", "Ngày"])
    if df.empty:
        st.info("Chưa có điểm nào.")
        st.stop()
    df["Loại"] = df["kind"].map(lambda k: KINDS.get(k, (k,))[0])

    st.subheader("Điểm trung bình")
    avg = (df.assign(wv=df["Điểm"] * df["Hệ số"]).groupby("Môn")
             .agg(TB=("wv", "sum"), w=("Hệ số", "sum"), n=("Điểm", "size")))
    avg["TB"] = (avg["TB"] / avg["w"]).round(2)
    cols = st.columns(max(len(avg), 1))
    for c, (name, r) in zip(cols, avg.iterrows()):
        c.metric(name, r["TB"], f"{int(r['n'])} đầu điểm")

    st.subheader("Xu hướng")
    st.altair_chart(alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("Ngày:T"), y=alt.Y("Điểm:Q", scale=alt.Scale(domain=[0, 10])), color="Môn:N",
        tooltip=["Môn", "Loại", "Điểm", alt.Tooltip("Ngày:T", format="%d/%m/%Y")]).properties(height=240),
        use_container_width=True)

    st.subheader("Danh sách")
    for _, r in df.sort_values("Ngày", ascending=False).iterrows():
        c1, c2 = st.columns([6, 1])
        c1.write(f"{r['Ngày']:%d/%m/%Y} · **{r['Môn']}** · {r['Loại']} · **{r['Điểm']}**")
        if c2.button("Xoá", key=f"del{r['id']}"):
            with SessionLocal() as s:
                s.delete(s.get(Score, int(r["id"]))); s.commit()
            st.rerun()
