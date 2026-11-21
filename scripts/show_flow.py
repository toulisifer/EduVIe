"""Trình diễn LUỒNG CHẠY cho người chấm: in code theo thứ tự thực thi (file:dòng) rồi chạy thật từng bước.

    python -m scripts.show_flow --flow register # đăng ký -> băm mật khẩu -> INSERT users -> cookie (không tốn LLM)
    python -m scripts.show_flow --flow quiz    # nộp quiz -> ghi answers -> mastery -> lịch ôn -> gợi ý đề (không tốn LLM)
    python -m scripts.show_flow --flow rag     # câu hỏi -> embedding -> Chroma + BM25 -> đoạn sách + trang (1 request embedding)
    python -m scripts.show_flow --flow agent   # agent gọi tool nào, tool đọc DB ra sao (không tốn LLM: chạy tool trực tiếp)
"""
import argparse
import inspect
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
W = 74


def head(t):
    print("\n" + "=" * W); print(" " + t); print("=" * W)


def step(n, t):
    print(f"\n── Bước {n}: {t} " + "─" * max(0, W - 12 - len(t)))


def code(obj, first_lines: int = 0, grep: str | None = None, around: int = 3):
    """In mã nguồn của hàm/lớp kèm file:dòng. grep=regex -> chỉ in vùng quanh dòng khớp."""
    src, start = inspect.getsourcelines(obj)
    path = Path(inspect.getsourcefile(obj)).relative_to(ROOT)
    print(f"  📄 {path}:{start}  ({obj.__name__})")
    if grep:
        idx = [i for i, l in enumerate(src) if re.search(grep, l)]
        lo = max(0, idx[0] - around) if idx else 0
        hi = min(len(src), (idx[-1] + around + 1) if idx else len(src))
        rng = range(lo, hi)
    else:
        rng = range(0, first_lines or len(src))
    for i in rng:
        print(f"  {start + i:4d} │ {src[i].rstrip()}")
    print()


def out(label, value):
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, default=str)
    print(f"  ▶ {label}: {str(value)[:600]}")


# ================================================================== QUIZ
def flow_quiz():
    from app import analytics, quiz
    from app.db import Attempt, Answer, SessionLocal, User
    from app.learning import recommend_quiz, review_schedule

    with SessionLocal() as s:
        u = s.query(User).filter_by(username="demo").first()
        last = s.query(Attempt).filter_by(user_id=u.id).order_by(Attempt.id.desc()).first()
        n_ans = s.query(Answer).filter_by(user_id=u.id).count()
    head("LUỒNG: học sinh nộp bài quiz → dữ liệu → phân tích → gợi ý")
    print("  Người dùng minh hoạ: demo · đã có", n_ans, "câu trả lời trong DB")

    step(1, "Giao diện gọi submit_attempt() khi bấm 'Nộp bài'  (pages/3_📝_Quiz.py)")
    page = (ROOT / "pages/3_📝_Quiz.py").read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(page):
        if "submit_attempt(" in l:
            print(f"  📄 pages/3_📝_Quiz.py:{i+1}\n  {i+1:4d} │ {l.rstrip()}\n")
            break

    step(2, "submit_attempt(): chấm từng câu và GHI bảng attempts + answers")
    code(quiz.submit_attempt)
    o = analytics.answers_df(u.id)
    out("answers_df(demo) — số dòng đọc được từ bảng answers", len(o))
    out("3 dòng gần nhất", o.sort_values("answered_at").tail(3)[["topic", "difficulty", "is_correct", "answered_at"]].to_dict("records"))

    step(3, "topic_mastery(): ĐỌC answers → mastery theo chủ đề (trọng số độ khó × suy giảm thời gian)")
    code(analytics.answers_df, grep=r"df\[\"w\"\]", around=2)
    code(analytics.topic_mastery, grep=r"mastery", around=2)
    m = analytics.topic_mastery(u.id, 1)
    out("kết quả", m[m["n"] > 0][["topic", "mastery", "n", "level"]].to_dict("records"))

    step(4, "review_schedule(): cùng dữ liệu → lịch ôn (SM-2)")
    code(review_schedule, grep=r"if q >= 0.6", around=4)
    sch = review_schedule(u.id, 1)
    out("chủ đề đến hạn", sch[sch["overdue_days"] >= 0][["topic", "overdue_days"]].to_dict("records"))

    step(5, "recommend_quiz(): mastery + lịch ôn + tiên quyết → đề tiếp theo")
    code(recommend_quiz, grep=r"score, why =", around=1)
    rec = recommend_quiz(u.id, 1)
    out("gợi ý", {"topics": rec["topics"], "difficulty": rec["difficulty"], "nguồn": rec["source"]})
    out("bị chặn vì nền yếu", [(n, b) for _, n, b in rec["blocked"]])
    print("\n  ⇒ Từ 1 lần bấm 'Nộp bài': ghi 2 bảng, và 4 chức năng (mastery, heatmap, lịch ôn, đề vừa sức) tự cập nhật — không cần gọi AI.")


# ================================================================== REGISTER
def flow_register():
    import logging
    from app import db, ui
    head("LUỒNG: người dùng bấm 'Tạo tài khoản' → dữ liệu đi vào SQLite như thế nào")
    demo_user, demo_pw = "hocsinh_demo", "matkhau123"
    print(f"  Dữ liệu nhập ở form: tên = '{demo_user}', mật khẩu = '{demo_pw}', email = '' ")

    step(1, "Form Streamlit thu dữ liệu và gọi register()  (app/ui.py)")
    page = (ROOT / "app/ui.py").read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(page):
        if 'with st.form("register")' in l:
            for j in range(i, i + 15):
                print(f"  {j+1:4d} │ {page[j].rstrip()}")
            break
    print()

    step(2, "register(): kiểm tra hợp lệ → băm mật khẩu → tạo đối tượng User → commit  (app/db.py)")
    code(db.register)
    code(db._hash)

    step(3, "Chạy thật, bật echo để thấy SQL mà SQLAlchemy sinh ra")
    with db.SessionLocal() as s:                     # dọn nếu lần trước còn sót
        old = s.query(db.User).filter_by(username=demo_user).first()
        if old:
            s.delete(old); s.commit()
    import sys
    sys.stdout.flush()
    logging.basicConfig(format="      SQL │ %(message)s", stream=sys.stdout, force=True)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    user, err, code_ = db.register(demo_user, demo_pw, demo_pw, "")
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    print()
    out("kết quả trả về", {"user.id": user.id, "username": user.username, "err": err, "mã khôi phục (hiện 1 lần)": code_})

    step(4, "Dòng vừa ghi trong bảng users (đọc lại bằng SQL thuần)")
    import sqlite3
    con = sqlite3.connect(db.DB_PATH)
    cur = con.execute("select id, username, role, password_hash, recovery_hash, email, created_at from users where username=?", (demo_user,))
    for c, v in zip([d[0] for d in cur.description], cur.fetchone()):
        print(f"  {c:14s} = {v}")
    con.close()
    print("\n  ⇒ Mật khẩu '" + demo_pw + "' KHÔNG xuất hiện trong DB — chỉ có chuỗi bcrypt. Mã khôi phục cũng vậy.")

    step(5, "Sau khi tạo: giao diện đặt cookie ghi nhớ (JWT) và hiện mã khôi phục 1 lần")
    code(db.make_remember_token)
    tok = db.make_remember_token(user)
    out("token trong cookie (rút gọn)", tok[:60] + "…")
    out("giải mã token → user", db.user_from_remember_token(tok).username)

    step(6, "Đăng nhập lại: login() so mật khẩu với hash bằng bcrypt")
    code(db.login, grep=r"_check\(password", around=1)
    out("login(đúng mật khẩu)", db.login(demo_user, demo_pw)[0] is not None)
    out("login(sai mật khẩu)", db.login(demo_user, "sai")[1])

    with db.SessionLocal() as s:                     # dọn user demo
        s.delete(s.get(db.User, user.id)); s.commit()
    print("\n  (đã xoá tài khoản minh hoạ)")


# ================================================================== RAG
def flow_rag():
    from app.rag import chat, ingest
    from app.llm import embed
    head("LUỒNG: câu hỏi → tìm đoạn sách (RAG) → prompt cho Gemini")
    q = "Điều kiện để hàm số đồng biến trên khoảng K là gì?"
    print("  Câu hỏi minh hoạ:", q)

    step(1, "Lúc nạp sách: PDF → chunk → embedding → ChromaDB  (đã làm trước, không chạy lại)")
    code(ingest.split_text, first_lines=6)
    code(ingest.ingest, grep=r"col.upsert", around=3)

    step(2, "Lúc hỏi: embed câu hỏi (1 request Gemini embedding)")
    code(embed, first_lines=3)
    v = embed([q], task="RETRIEVAL_QUERY")[0]
    out("vector câu hỏi", f"{len(v)} chiều, 5 giá trị đầu {[round(x, 3) for x in v[:5]]}")

    step(3, "retrieve(): Chroma (cosine) lấy ứng viên → BM25 chấm lại → trộn RRF → top-k")
    code(chat.retrieve, grep=r"fused = ", around=6)
    hits = chat.retrieve(q, user_id=0, subject_id=1, k=3)
    for i, h in enumerate(hits, 1):
        print(f"  [{i}] {h['filename'][:32]}… trang {h['page']}  (cosine {h['score']})\n      {h['text'][:110].replace(chr(10), ' ')}…")

    step(4, "build_prompt(): ghép đoạn sách + câu hỏi thành prompt; SYSTEM bắt trích dẫn [n]")
    code(chat.build_prompt)
    p = chat.build_prompt(q, hits, None)
    out("prompt gửi Gemini (rút gọn)", p[:300].replace("\n", " ⏎ "))
    print("\n  ⇒ Gemini chỉ được trả lời dựa trên các đoạn này và phải ghi [1][2]… → câu trả lời có trích dẫn trang, không bịa.")
    print("     (Bước gọi Gemini sinh câu trả lời bỏ qua ở đây để không tốn quota; xem trang 💬 Hỏi AI.)")


# ================================================================== AGENT
def flow_agent():
    from app import agent
    from app.db import SessionLocal, User
    with SessionLocal() as s:
        uid = s.query(User).filter_by(username="demo").first().id
    head("LUỒNG: AI Agent — vòng lặp gọi công cụ (tool) đọc DB")

    step(1, "Vòng lặp agent: model → function_call? → chạy tool Python → trả kết quả → lặp")
    code(agent.run_agent, grep=r"for _ in range\(MAX_STEPS\)", around=9)

    step(2, "Tool là hàm Python thường; docstring = hướng dẫn để model biết khi nào dùng")
    tools = agent.make_tools(uid, 1)
    fn = {f.__name__: f for f in tools}
    code(fn["get_topic_mastery"])

    step(3, "Chạy tool trực tiếp (đúng thứ tự agent thường gọi) — không tốn LLM")
    for name in ["get_student_overview", "get_topic_mastery", "get_review_and_prerequisites"]:
        r = fn[name]()
        if isinstance(r, list):
            r = [x for x in r if x.get("n_answers", 1)][:4]
        out(f"{name}()", r)
    out("get_recent_mistakes(topic_id=2, limit=2)", fn["get_recent_mistakes"](2, 2))

    step(4, "Sau khi đủ dữ liệu, agent gọi save_study_plan() → ghi study_plans + plan_items")
    code(fn["save_study_plan"], grep=r"StudyPlan\(", around=4)
    print("\n  ⇒ Agent không 'đoán': mọi con số trong nhận xét/kế hoạch đều đến từ các tool đọc DB ở trên. Log tool hiển thị ở trang 🧭 Lộ trình.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--flow", choices=["register", "quiz", "rag", "agent"], default="quiz")
    a = ap.parse_args()
    {"register": flow_register, "quiz": flow_quiz, "rag": flow_rag, "agent": flow_agent}[a.flow]()
