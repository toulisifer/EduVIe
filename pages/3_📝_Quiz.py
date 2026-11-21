import streamlit as st

from app.db import Chapter, SessionLocal, Topic
from app.quiz import DIFFICULTY_VI, flag_question, generate_quiz, load_quiz, submit_attempt
from app.ui import require_login, subject_selector

st.set_page_config(page_title="Quiz", page_icon="📝", layout="wide")
user = require_login()
st.title("📝 Kiểm tra nhanh")

ss = st.session_state
ss.setdefault("quiz_id", None)
ss.setdefault("quiz_result", None)

# ---------- Bước 1: cấu hình & sinh quiz ----------
if ss.quiz_id is None:
    subject = subject_selector()
    from app.learning import recommend_quiz
    with st.container(border=True):
        st.markdown("**🎯 Đề vừa sức (adaptive)** — hệ thống tự chọn chủ đề đến hạn ôn / đang yếu / vừa sức, tôn trọng thứ tự tiên quyết.")
        if st.button("Gợi ý cho tôi"):
            ss.quiz_reco = recommend_quiz(user.id, subject.id)
        reco = ss.get("quiz_reco")
        if reco and reco["topics"]:
            for tid, name, why in reco["topics"]:
                st.write(f"- **{name}** — {why}")
            st.caption(f"Độ khó đề xuất: {DIFFICULTY_VI[reco['difficulty']]} · nguồn: {reco['source']}")
            if reco["blocked"]:
                st.caption("Tạm hoãn (nền còn yếu): " + "; ".join(f"{n} ← cần {', '.join(b)}" for _, n, b in reco["blocked"][:3]))
            if st.button("Tạo đề theo gợi ý", type="primary"):
                ss.quiz_preset = {"topic_ids": [t for t, _, _ in reco["topics"]], "difficulty": reco["difficulty"]}
                ss.quiz_reco = None
                st.rerun()
    with SessionLocal() as s:
        chapters = [(c.id, c.name, [(t.id, t.name) for t in c.topics])
                    for c in s.query(Chapter).filter_by(subject_id=subject.id).all()]
    preset = ss.get("quiz_preset") or {}
    want = set(preset.get("topic_ids") or ([preset["topic_id"]] if preset.get("topic_id") else []))
    ch_idx = next((i for i, c in enumerate(chapters) if any(t[0] in want for t in c[2])), 0)
    chapter = st.selectbox("Chương", chapters, index=ch_idx, format_func=lambda c: c[1])
    default_topics = [t for t in chapter[2] if t[0] in want]
    if default_topics:
        st.info("Chủ đề đã chọn sẵn: " + ", ".join(f"**{t[1]}**" for t in default_topics))
    topics = st.multiselect("Chủ đề (bỏ trống = cả chương)", chapter[2], default=default_topics, format_func=lambda t: t[1])
    if not topics:
        topics = chapter[2]
    c1, c2 = st.columns(2)
    difficulty = c1.selectbox("Độ khó", list(DIFFICULTY_VI), format_func=DIFFICULTY_VI.get,
                              index=list(DIFFICULTY_VI).index(preset.get("difficulty", "medium")))
    n = c2.slider("Số câu", 3, 15, 5)

    if st.button("Tạo đề", type="primary"):
        with st.spinner("AI đang soạn đề (1 request)..."):
            try:
                with SessionLocal() as s:
                    full_topics = [s.get(Topic, t[0]) for t in topics]
                    for t in full_topics:
                        _ = t.path
                    ss.quiz_id = generate_quiz(user.id, subject.id, full_topics, difficulty, n)
            except Exception as e:  # noqa: BLE001
                st.error(f"Lỗi sinh đề: {e}")
                st.stop()
        ss.quiz_result = None
        st.rerun()
    st.stop()

# ---------- Bước 2: làm bài ----------
questions = load_quiz(ss.quiz_id)
if not questions:
    st.error("Đề không có câu hợp lệ, hãy tạo lại.")
    ss.quiz_id = None
    st.stop()

if ss.quiz_result is None:
    st.caption(f"{len(questions)} câu · Độ khó: {DIFFICULTY_VI.get(questions[0].difficulty, '')}")
    with st.form("quiz_form"):
        selections = {}
        for i, q in enumerate(questions, 1):
            st.markdown(f"**Câu {i}.** {q.content}")
            choice = st.radio("Chọn đáp án", q.options, index=None, key=f"q{q.id}",
                              label_visibility="collapsed")
            selections[q.id] = q.options.index(choice) if choice is not None else None
            st.divider()
        if st.form_submit_button("Nộp bài", type="primary"):
            ss.quiz_result = submit_attempt(ss.quiz_id, user.id, selections)
            ss.quiz_selections = selections
            if (ss.get("quiz_preset") or {}).get("plan_item_id"):
                from app.advisor import toggle_item
                toggle_item(ss.quiz_preset["plan_item_id"], True)   # tự tick việc trong lộ trình
                ss.quiz_preset = None
            st.rerun()
    if st.button("Huỷ, tạo đề khác"):
        ss.quiz_id = None
        st.rerun()
    st.stop()

# ---------- Bước 3: kết quả ----------
r = ss.quiz_result
st.metric("Điểm", f"{r['score']}/10", f"{r['n_correct']}/{r['n']} câu đúng")

st.subheader("Kết quả theo chủ đề")
for topic, oks in r["per_topic"].items():
    pct = 100 * sum(oks) // len(oks)
    st.write(f"{'🟢' if pct >= 75 else '🟡' if pct >= 50 else '🔴'} {topic.split(' / ')[-1]}: {sum(oks)}/{len(oks)} ({pct}%)")

st.subheader("Chi tiết")
for i, q in enumerate(questions, 1):
    sel = ss.quiz_selections.get(q.id)
    ok = sel == q.correct
    with st.expander(f"{'✅' if ok else '❌'} Câu {i}: {q.content[:80]}..."):
        st.markdown(q.content)
        for j, opt in enumerate(q.options):
            mark = "✅" if j == q.correct else ("❌" if j == sel else "▫️")
            st.markdown(f"{mark} {opt}")
        st.info(f"**Giải thích:** {q.explanation}")
        st.caption(f"Chủ đề: {q.topic.path}")
        if st.button("🚩 Báo câu hỏi/đáp án sai", key=f"flag{q.id}"):
            flag_question(q.id)
            st.toast("Đã ghi nhận, cảm ơn bạn!")

if st.button("Làm đề mới", type="primary"):
    ss.quiz_id = None
    ss.quiz_result = None
    st.rerun()
