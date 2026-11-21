import pandas as pd
import streamlit as st
from sqlalchemy import func

from app.db import (Answer, Attempt, ChatMessage, Chapter, Document, PlanItem, Question, Quiz, Score,
                    SessionLocal, StudyPlan, Subject, User)
from app.rag.ingest import delete_document
from app.ui import require_login

st.set_page_config(page_title="Quản trị", page_icon="⚙️", layout="wide")
user = require_login()
if user.role != "admin":
    st.error("Trang này chỉ dành cho quản trị viên.")
    st.stop()
st.title("⚙️ Quản trị hệ thống")

tab_users, tab_docs, tab_stats, tab_ml, tab_agent = st.tabs(["👥 Người dùng", "📚 Tài liệu (tất cả)", "📈 Thống kê", "🧠 Mô hình ML", "🤖 Agent tự đánh giá"])

# ---------------- Người dùng ----------------
with tab_users:
    with SessionLocal() as s:
        rows = []
        for u in s.query(User).order_by(User.id):
            rows.append({
                "id": u.id, "Tên": u.username, "Vai trò": u.role, "Tạo lúc": u.created_at,
                "Quiz": s.query(Attempt).filter_by(user_id=u.id).count(),
                "Câu": s.query(Answer).filter_by(user_id=u.id).count(),
                "Chat": s.query(ChatMessage).filter_by(user_id=u.id, role="user").count(),
                "Tài liệu": s.query(Document).filter_by(user_id=u.id).count(),
            })
    df = pd.DataFrame(rows)
    st.dataframe(df.drop(columns="id"), use_container_width=True, hide_index=True)

    st.subheader("Thao tác")
    target = st.selectbox("Chọn tài khoản", [r for r in rows if r["id"] != user.id],
                          format_func=lambda r: f"{r['Tên']} ({r['Vai trò']})")
    c0, c1, c2, c3 = st.columns(4)
    if target and c0.button("Đặt làm giáo viên" if target["Vai trò"] != "teacher" else "Hạ xuống user"):
        with SessionLocal() as s:
            u = s.get(User, target["id"]); u.role = "user" if u.role == "teacher" else "teacher"; s.commit()
        st.rerun()
    if target and c1.button("Đặt làm admin" if target["Vai trò"] != "admin" else "Hạ xuống user"):
        with SessionLocal() as s:
            u = s.get(User, target["id"]); u.role = "user" if u.role == "admin" else "admin"; s.commit()
        st.rerun()
    if target and c2.button("Đặt lại mật khẩu (người đó tự đặt lần đăng nhập tới)"):
        with SessionLocal() as s:
            s.get(User, target["id"]).password_hash = ""; s.commit()
        st.success("Đã xoá mật khẩu; lần đăng nhập tới họ gõ mật khẩu mới là được.")
    if target and c3.button("🗑️ Xoá tài khoản và toàn bộ dữ liệu", type="primary"):
        uid = target["id"]
        with SessionLocal() as s:
            quiz_ids = [q.id for q in s.query(Quiz).filter_by(user_id=uid)]
            plan_ids = [p.id for p in s.query(StudyPlan).filter_by(user_id=uid)]
            s.query(Answer).filter_by(user_id=uid).delete()
            s.query(Attempt).filter_by(user_id=uid).delete()
            if quiz_ids:
                s.query(Question).filter(Question.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
            s.query(Quiz).filter_by(user_id=uid).delete()
            s.query(Score).filter_by(user_id=uid).delete()
            s.query(ChatMessage).filter_by(user_id=uid).delete()
            if plan_ids:
                s.query(PlanItem).filter(PlanItem.plan_id.in_(plan_ids)).delete(synchronize_session=False)
            s.query(StudyPlan).filter_by(user_id=uid).delete()
            for d in s.query(Document).filter_by(user_id=uid):
                delete_document(d.id); s.delete(d)
            s.delete(s.get(User, uid)); s.commit()
        st.rerun()

# ---------------- Tài liệu ----------------
with tab_docs:
    with SessionLocal() as s:
        docs = (s.query(Document, User.username, Subject.name, Chapter.name)
                .join(User, Document.user_id == User.id)
                .join(Subject, Document.subject_id == Subject.id)
                .outerjoin(Chapter, Document.chapter_id == Chapter.id)
                .order_by(Subject.name, Chapter.order, Document.id).all())
    total = sum(d.n_chunks for d, *_ in docs)
    st.caption(f"{len(docs)} tài liệu · {total} đoạn trong kho dùng chung")
    for d, uname, sname, cname in docs:
        icon = {"ready": "✅", "failed": "❌"}.get(d.status, "⏳")
        c1, c2 = st.columns([8, 1])
        c1.write(f"{icon} **{sname}** · {(cname or '—').split(':')[0]} · {d.filename} — {d.n_chunks} đoạn · _up bởi {uname}_")
        if c2.button("Xoá", key=f"adel{d.id}"):
            delete_document(d.id)
            with SessionLocal() as s:
                s.delete(s.get(Document, d.id)); s.commit()
            st.rerun()

# ---------------- Thống kê ----------------
with tab_stats:
    with SessionLocal() as s:
        n_users = s.query(User).count()
        n_attempts = s.query(Attempt).count()
        n_answers = s.query(Answer).count()
        n_flag = s.query(Question).filter_by(flagged=True).count()
        n_q = s.query(Question).count()
        n_chat = s.query(ChatMessage).filter_by(role="user").count()
        per_day = (s.query(func.date(Answer.answered_at), func.count(Answer.id))
                   .group_by(func.date(Answer.answered_at)).order_by(func.date(Answer.answered_at)).all())
    c = st.columns(5)
    c[0].metric("Người dùng", n_users)
    c[1].metric("Bài quiz", n_attempts)
    c[2].metric("Câu đã làm", n_answers)
    c[3].metric("Câu bị 🚩", f"{n_flag}/{n_q}", f"{100*n_flag/max(n_q,1):.1f}% lỗi" if n_q else None, delta_color="inverse")
    c[4].metric("Lượt chat", n_chat)
    if per_day:
        st.bar_chart(pd.DataFrame(per_day, columns=["Ngày", "Câu trả lời"]).set_index("Ngày"))


# ---------------- ML ----------------
with tab_ml:
    from pathlib import Path as _P
    from app.ml.kt_app import MIN_ANSWERS, model_info, train_app_model
    st.subheader("Deep Knowledge Tracing trên dữ liệu hệ thống")
    info = model_info()
    if info:
        st.write(f"Mô hình hiện tại: huấn luyện {info['trained_at']} · {info['n_answers']} câu · {info['n_users']} người · "
                 f"{info['n_topics']} chủ đề · AUC khớp {info['fit_auc']:.3f}")
    else:
        st.write("Chưa có mô hình.")
    with SessionLocal() as s:
        n_now = s.query(Answer).count()
    st.caption(f"Hiện có {n_now} câu trả lời trong hệ thống (cần ≥ {MIN_ANSWERS}). Nên huấn luyện lại mỗi tuần khi có thêm dữ liệu.")
    if st.button("🔁 Huấn luyện lại DKT", type="primary"):
        log = st.status("Đang huấn luyện...", expanded=True)
        meta = train_app_model(log=log.write)
        log.update(label="Xong" if meta else "Chưa đủ dữ liệu", state="complete" if meta else "error", expanded=False)
        st.rerun()

    st.subheader("Kết quả kiểm chứng trên ASSISTments 2009")
    res = _P("eval/kt_results.md")
    if res.exists():
        st.markdown(res.read_text(encoding="utf-8"))
    else:
        st.caption("Chạy: python -m scripts.train_kt")


# ---------------- Agent (bậc 6) ----------------
with tab_agent:
    from app.db import AgentLesson, AgentRun, StudyPlan
    from app.reflection import RULES, plan_outcome, reflect
    st.subheader("Nhật ký chạy agent")
    with SessionLocal() as s:
        runs = s.query(AgentRun).order_by(AgentRun.id.desc()).limit(50).all()
        uname = {u.id: u.username for u in s.query(User)}
        rows = [{"Lúc": r.created_at.strftime("%d/%m %H:%M"), "User": uname.get(r.user_id, r.user_id), "Chế độ": r.mode,
                 "Tool calls": r.n_tool_calls, "Giây": round(r.duration_s), "Phản biện": r.critic_score,
                 "Vi phạm validator": len(r.violations or []), "Plan": r.plan_id} for r in runs]
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        df_r = pd.DataFrame(rows)
        c1, c2, c3 = st.columns(3)
        c1.metric("Lần chạy", len(df_r))
        c2.metric("Tỷ lệ kế hoạch không vi phạm", f"{100 * (df_r['Vi phạm validator'] == 0).mean():.0f}%")
        c3.metric("Điểm phản biện TB", f"{df_r['Phản biện'].dropna().mean():.1f}" if df_r["Phản biện"].notna().any() else "—")
    else:
        st.caption("Chưa có lần chạy nào được ghi (chạy Lộ trình để bắt đầu ghi).")
    with st.expander("5 luật của bộ kiểm tra tự động"):
        for k, v in RULES.items():
            st.write(f"- `{k}`: {v}")

    st.subheader("Hiệu quả các kế hoạch gần đây")
    with SessionLocal() as s:
        plans = s.query(StudyPlan).order_by(StudyPlan.id.desc()).limit(10).all()
        pl = [(pp.id, uname.get(pp.user_id, pp.user_id)) for pp in plans]
    out_rows = []
    for pid, un in pl:
        o = plan_outcome(pid)
        out_rows.append({"Plan": pid, "User": un, "Tuổi (ngày)": o["age_days"], "Hoàn thành": f"{o['done']}/{o['n_items']}",
                         "Δ mastery TB": o["avg_delta"], "Bỏ qua study/quiz/review":
                         f"{o['skipped_kinds']['study']}/{o['skipped_kinds']['quiz']}/{o['skipped_kinds']['review']}"})
    if out_rows:
        st.dataframe(pd.DataFrame(out_rows), use_container_width=True, hide_index=True)

    st.subheader("Bài học agent tự rút ra (được chèn vào prompt lần sau)")
    with SessionLocal() as s:
        lessons = s.query(AgentLesson).order_by(AgentLesson.id.desc()).limit(30).all()
        ls = [(l.id, l.lesson, l.evidence, l.active, uname.get(l.user_id, "chung") if l.user_id else "chung", l.created_at) for l in lessons]
    for lid, lesson, ev, active, scope, at in ls:
        c1, c2 = st.columns([10, 1])
        c1.markdown(f"{'✅' if active else '⏸️'} **{lesson}** · _{scope}_ · {at:%d/%m}")
        c1.caption(f"Bằng chứng: {ev}")
        if c2.button("Tắt" if active else "Bật", key=f"ls{lid}"):
            with SessionLocal() as s:
                l = s.get(AgentLesson, lid); l.active = not l.active; s.commit()
            st.rerun()
    with SessionLocal() as s:
        users_with_plans = [(u.id, u.username) for u in s.query(User) if s.query(StudyPlan).filter_by(user_id=u.id).count()]
    tgt = st.selectbox("Phản tư cho người dùng", users_with_plans, format_func=lambda x: x[1]) if users_with_plans else None
    if tgt and st.button("🪞 Chạy agent phản tư ngay (1 request)"):
        with st.spinner("Đang nhìn lại các kế hoạch cũ..."):
            new = reflect(tgt[0])
        st.success(f"Rút được {len(new)} bài học mới.")
        st.rerun()
