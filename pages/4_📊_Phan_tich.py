import altair as alt
import pandas as pd
import streamlit as st

from app.analytics import (GOOD_ABOVE, MIN_ANSWERS, WEAK_BELOW, answers_df,
                           attempt_trend, topic_mastery)
from app.ui import require_login, subject_selector

st.set_page_config(page_title="Phân tích", page_icon="📊", layout="wide")
user = require_login()
st.title("📊 Phân tích năng lực")

c_sub, c_ch = st.columns(2)
with c_sub:
    subject = subject_selector(allow_all=True)
sid = subject.id if subject else None
m = topic_mastery(user.id, sid)
with c_ch:
    chapters = ["Tất cả"] + list(dict.fromkeys(m["chapter"]))          # giữ thứ tự chương
    chosen = st.selectbox("Chương", chapters)
if chosen != "Tất cả":
    m = m[m["chapter"] == chosen]
df = answers_df(user.id)
if not df.empty:
    if sid:
        df = df[df["subject_id"] == sid]
    if chosen != "Tất cả":
        df = df[df["chapter"] == chosen]

# ---------- Tổng quan ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Câu đã làm", int(df.shape[0]) if not df.empty else 0)
c2.metric("Tỷ lệ đúng", f"{100 * df['is_correct'].mean():.0f}%" if not df.empty else "—")
c3.metric("Chủ đề yếu", int((m["level"] == "Yếu").sum()))
c4.metric("Chủ đề tốt", int((m["level"] == "Tốt").sum()))

if df.empty:
    st.info("Chưa có dữ liệu. Hãy làm vài bài Quiz trước.")
    st.stop()

# ---------- Heatmap mastery ----------
st.subheader("Bản đồ mức độ nắm vững")
st.caption(f"Màu theo mastery %: 🔴 < {WEAK_BELOW} · 🟡 {WEAK_BELOW}–{GOOD_ABOVE} · 🟢 ≥ {GOOD_ABOVE}. "
           f"Chủ đề dưới {MIN_ANSWERS} câu chưa được kết luận. Kết quả gần đây và câu khó có trọng số cao hơn.")
plot = m.copy()
plot["mastery_plot"] = plot["mastery"].fillna(-1)
plot["label"] = plot.apply(lambda r: f"{int(r['mastery'])}%" if r["n"] else "", axis=1)
plot["chapter_short"] = plot["chapter"].str.split(":").str[0]
heat = alt.Chart(plot).mark_rect(stroke="white").encode(
    x=alt.X("chapter_short:N", title="Chương"),
    y=alt.Y("topic:N", title=None, sort=None),
    color=alt.condition(alt.datum.mastery_plot >= 0,
                        alt.Color("mastery_plot:Q", scale=alt.Scale(domain=[0, 50, 100], range=["#d9534f", "#f0ad4e", "#5cb85c"]),
                                  legend=alt.Legend(title="Mastery %")),
                        alt.value("#3a3a3a")),
    tooltip=["topic", "chapter", alt.Tooltip("mastery:Q", title="Mastery %"), alt.Tooltip("n:Q", title="Số câu"), "level"],
)
text = alt.Chart(plot).mark_text(fontSize=12).encode(x="chapter_short:N", y=alt.Y("topic:N", sort=None), text="label:N")
st.altair_chart((heat + text).properties(height=max(200, 34 * len(plot))), use_container_width=True)

# ---------- Danh sách yếu / tốt ----------
col_w, col_g = st.columns(2)
with col_w:
    st.subheader("🔴 Cần cải thiện")
    weak = m[m["level"] == "Yếu"].sort_values("mastery")
    if weak.empty:
        st.write("Chưa phát hiện chủ đề yếu (hoặc chưa đủ dữ liệu).")
    for _, r in weak.iterrows():
        st.write(f"- **{r['topic']}** — {int(r['mastery'])}% ({r['n_correct']}/{r['n']} câu)")
    thin = m[(m["n"] > 0) & (m["n"] < MIN_ANSWERS)]
    if not thin.empty:
        st.caption("Chưa đủ dữ liệu: " + ", ".join(f"{r['topic']} ({r['n']} câu)" for _, r in thin.iterrows()))
with col_g:
    st.subheader("🟢 Đã nắm tốt")
    good = m[m["level"] == "Tốt"].sort_values("mastery", ascending=False)
    if good.empty:
        st.write("Chưa có.")
    for _, r in good.iterrows():
        st.write(f"- **{r['topic']}** — {int(r['mastery'])}% ({r['n_correct']}/{r['n']} câu)")

# ---------- Tiên quyết & lịch ôn ----------
from app.learning import prerequisites, review_schedule, weak_prereqs
pre = prerequisites()
blocked = [(r["topic"], weak_prereqs(int(r["topic_id"]), m, pre)) for _, r in m.iterrows()]
blocked = [(t, b) for t, b in blocked if b]
if blocked:
    st.subheader("🔗 Nền tảng cần củng cố trước")
    st.caption("Theo đồ thị kiến thức: chủ đề bên trái nên học sau khi vững chủ đề bên phải.")
    for t, b in blocked:
        st.write(f"- **{t}** ← cần vững: {', '.join(b)}")
sch = review_schedule(user.id, sid)
if chosen != "Tất cả" and not sch.empty:
    sch = sch[sch["topic_id"].isin(set(m["topic_id"]))]
if not sch.empty:
    st.subheader("🔁 Lịch ôn tập (spaced repetition)")
    show = sch.assign(**{"Ôn tới": sch["due"].dt.strftime("%d/%m"), "Khoảng (ngày)": sch["interval"],
                         "Trạng thái": sch["overdue_days"].map(lambda d: f"quá hạn {d:.0f} ngày" if d >= 0 else f"còn {-d:.0f} ngày")})
    st.dataframe(show[["topic", "Ôn tới", "Khoảng (ngày)", "Trạng thái"]].rename(columns={"topic": "Chủ đề"}),
                 use_container_width=True, hide_index=True)

# ---------- Xu hướng ----------
st.subheader("Xu hướng điểm quiz")
tr = attempt_trend(user.id)
if len(tr) >= 2:
    tr["Lần"] = range(1, len(tr) + 1)
    st.altair_chart(alt.Chart(tr).mark_line(point=True).encode(
        x=alt.X("Lần:O", title="Lần làm bài"), y=alt.Y("Điểm:Q", scale=alt.Scale(domain=[0, 10])),
        tooltip=["Thời gian:T", "Điểm"]).properties(height=220), use_container_width=True)
else:
    st.caption("Cần ít nhất 2 bài quiz để vẽ xu hướng.")

# ---------- Tiến bộ theo chủ đề ----------
st.subheader("Tiến bộ theo chủ đề")
done_topics = m[m["n"] > 0]
if not done_topics.empty:
    pick = st.selectbox("Chủ đề", done_topics["topic_id"].tolist(),
                        format_func=lambda tid: done_topics.set_index("topic_id").loc[tid, "topic"])
    d = df[df["topic_id"] == pick].sort_values("answered_at").copy()
    d["Lần"] = range(1, len(d) + 1)
    d["Tỷ lệ đúng luỹ kế (%)"] = (100 * d["is_correct"].expanding().mean()).round(0)
    d["Đúng/Sai"] = d["is_correct"].map({1: "Đúng", 0: "Sai"})
    line = alt.Chart(d).mark_line(point=True).encode(
        x=alt.X("Lần:O", title="Câu thứ"), y=alt.Y("Tỷ lệ đúng luỹ kế (%):Q", scale=alt.Scale(domain=[0, 100])),
        tooltip=["Lần", "Tỷ lệ đúng luỹ kế (%)", "Đúng/Sai", "difficulty", alt.Tooltip("answered_at:T", title="Lúc")])
    dots = alt.Chart(d).mark_point(size=80, filled=True).encode(
        x="Lần:O", y="Tỷ lệ đúng luỹ kế (%):Q",
        color=alt.Color("Đúng/Sai:N", scale=alt.Scale(domain=["Đúng", "Sai"], range=["#5cb85c", "#d9534f"])))
    st.altair_chart((line + dots).properties(height=220), use_container_width=True)
    st.caption("Đường đi lên = đang tiến bộ; mỗi điểm là một câu trả lời (xanh đúng, đỏ sai).")

# ---------- Dự đoán bằng Deep Knowledge Tracing ----------
st.subheader("🧠 Dự đoán bằng Deep Knowledge Tracing (LSTM)")
from app.ml.kt_app import model_info, predict_user
info = model_info()
pred = predict_user(user.id) if info else None
if not info:
    st.caption("Chưa có mô hình DKT. Quản trị viên huấn luyện ở trang Quản trị khi đủ dữ liệu.")
elif not pred:
    st.caption("Bạn chưa có dữ liệu quiz để mô hình dự đoán.")
else:
    done_ids = set(m[m["n"] > 0]["topic_id"])
    rows_kt = [{"Chủ đề": r["topic"], "Mastery thống kê (%)": int(r["mastery"]) if r["n"] else None,
                "DKT: P(đúng câu tiếp theo) (%)": round(100 * pred[int(r["topic_id"])]), "Số câu": int(r["n"])}
               for _, r in m.iterrows() if int(r["topic_id"]) in done_ids and int(r["topic_id"]) in pred]
    st.dataframe(pd.DataFrame(rows_kt), use_container_width=True, hide_index=True)
    st.caption(f"Mô hình DKT huấn luyện trên dữ liệu hệ thống lúc {info['trained_at']} "
               f"({info['n_answers']} câu, {info['n_users']} người). Dữ liệu còn nhỏ nên dự đoán chỉ mang tính tham khảo; "
               f"cùng kiến trúc đạt AUC 0.82 trên ASSISTments 2009 (325k tương tác) — xem eval/kt_results.md.")

# ---------- Theo độ khó ----------
st.subheader("Tỷ lệ đúng theo độ khó")
by_diff = df.groupby("difficulty")["is_correct"].agg(["mean", "size"]).reindex(["easy", "medium", "hard"]).dropna()
by_diff.index = by_diff.index.map({"easy": "Dễ", "medium": "Trung bình", "hard": "Khó"})
st.dataframe(pd.DataFrame({"Tỷ lệ đúng": (100 * by_diff["mean"]).round(0).astype(int).astype(str) + "%",
                           "Số câu": by_diff["size"].astype(int)}), use_container_width=True)
