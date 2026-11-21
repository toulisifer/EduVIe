import streamlit as st

from app.advisor import latest_plan
from app.analytics import answers_df, score_summary, topic_mastery
from app.db import Document, SessionLocal
from app.ui import require_login

st.set_page_config(page_title="AI Learning Assistant", page_icon="🎓", layout="wide")
user = require_login()

st.title(f"🎓 Xin chào, {user.username}!")

df = answers_df(user.id)
m = topic_mastery(user.id)
with SessionLocal() as s:
    n_docs = s.query(Document).filter_by(user_id=user.id, status="ready").count()
sc = score_summary(user.id)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📚 Tài liệu", n_docs)
c2.metric("📝 Câu đã làm", len(df))
c3.metric("✅ Tỷ lệ đúng", f"{100 * df['is_correct'].mean():.0f}%" if len(df) else "—")
c4.metric("🔴 Chủ đề yếu", int((m["level"] == "Yếu").sum()))
c5.metric("🎯 Điểm TB", sc["avg"].mean().round(2) if not sc.empty else "—")

left, right = st.columns([1, 1])

with left:
    st.subheader("Cần ưu tiên")
    weak = m[m["level"] == "Yếu"].sort_values("mastery")
    thin = m[(m["n"] > 0) & (m["n"] < 3)]
    if weak.empty and thin.empty:
        st.write("Chưa có chủ đề nào bị đánh dấu yếu. Làm thêm quiz để hệ thống đánh giá.")
    for _, r in weak.head(5).iterrows():
        st.write(f"🔴 **{r['topic']}** — {int(r['mastery'])}% ({r['n_correct']}/{r['n']} câu)")
    for _, r in thin.head(3).iterrows():
        st.write(f"⚪ {r['topic']} — mới {r['n']} câu, cần làm thêm")
    from app.learning import due_topics
    due = due_topics(user.id)
    if not due.empty:
        st.markdown("**🔁 Đến hạn ôn lại** (spaced repetition)")
        for _, r in due.head(4).iterrows():
            st.write(f"- {r['topic']} — quá hạn {r['overdue_days']:.0f} ngày")
    st.page_link("pages/3_📝_Quiz.py", label="→ Làm quiz ngay", icon="📝")

with right:
    st.subheader("Kế hoạch hôm nay")
    plan = latest_plan(user.id)
    if not plan:
        st.write("Chưa có lộ trình.")
        st.page_link("pages/6_🧭_Lo_trinh.py", label="→ Tạo lộ trình", icon="🧭")
    else:
        pending = [i for i in plan.items if not i.done]
        if not pending:
            st.success("Bạn đã hoàn thành toàn bộ kế hoạch! Tạo lộ trình mới để tiếp tục.")
        else:
            day = pending[0].day
            for it in [i for i in pending if i.day == day][:3]:
                icon = {"study": "📖", "quiz": "📝", "review": "🔁"}.get(it.kind, "•")
                st.write(f"{icon} **{it.title}**" + (f" · _{it.topic.name}_" if it.topic else ""))
            done = len(plan.items) - len(pending)
            st.progress(done / len(plan.items), text=f"Ngày {day}/{plan.days} · hoàn thành {done}/{len(plan.items)} việc")
        st.page_link("pages/6_🧭_Lo_trinh.py", label="→ Xem lộ trình", icon="🧭")

from app.classroom import assignments_for_student
todo = [a for a in assignments_for_student(user.id) if not a["done"]]
if todo:
    st.subheader("📌 Đề giáo viên giao")
    for a in todo[:3]:
        st.write(f"- **{a['title']}** · {a['class']} · {a['n_questions']} câu" + (f" · hạn {a['due']:%d/%m}" if a["due"] else ""))
    st.page_link("pages/7b_🏫_Lop_hoc.py", label="→ Làm bài", icon="🏫")

st.divider()
st.caption("Vòng lặp: 📚 Tài liệu → 💬 Hỏi AI → 📝 Quiz → 📊 Phân tích → 🧭 Lộ trình → học tiếp")
