"""REST API (FastAPI + JWT) bọc quanh app/ — chạy song song với Streamlit, dùng chung DB & vector store.

Chạy:   uvicorn api.main:app --reload --port 8000
Docs:   http://localhost:8000/docs   (Swagger UI, thử trực tiếp)

Luồng: POST /auth/register hoặc /auth/login -> nhận access_token (JWT)
       -> gửi header  Authorization: Bearer <token>  cho các endpoint còn lại.
"""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi import (BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Request,
                     UploadFile, status)
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Annotated

from app import analytics, db
from app.advisor import build_plan, latest_plan
from app.agent import run_agent
from app.config import UPLOAD_DIR
from app import sua_sai as sua_sai_mod
from app.quiz import (DaLamRoi, chuan_hoa_ma, de_theo_ma, flag_question, generate_quiz,
                      lich_su, load_quiz, submit_attempt, xem_lai)
from app.rag.chat import answer
from app.rag.ingest import delete_document, ingest

from api import chan_dap, jobs
from api.deps import admin_user, clean, current_user, make_token, own_attempt, own_quiz
from api.extra import router as extra_router

app = FastAPI(title="EduVie API", version="2.0",
              description="API cho trợ lý học tập EduVie: tài liệu, RAG, quiz, phân tích, lộ trình, agent, lớp học.")
db.init_db()

# --- giao diện web (cùng origin nên không cần CORS) ---
WEB = Path(__file__).resolve().parent.parent / "web"
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(WEB / "templates" / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(WEB / "static" / "images" / "favicon-tab.png")


def _make_token(user: db.User):
    """Giữ tên cũ để phần code bên dưới không phải đổi."""
    return make_token(user)


class Credentials(BaseModel):
    username: str
    password: str


@app.post("/auth/register", tags=["auth"], summary="Đăng ký tài khoản, trả về token và mã khôi phục")
def api_register(c: Credentials, req: Request):
    # Chặn tạo tài khoản hàng loạt: đó là cửa vào để bơm dữ liệu huấn luyện DKT.
    chan_dap.chan(f"dangky:{chan_dap.dia_chi(req)}", 5, 3600,
                  "Tạo quá nhiều tài khoản từ một máy.")
    u, err, code = db.register(c.username, c.password, c.password)
    if err:
        raise HTTPException(400, err)
    t = _make_token(u)
    return {**t, "recovery_code": code}   # mã khôi phục chỉ trả về 1 lần này


class ChangePw(BaseModel):
    old: str
    new: str


@app.post("/auth/change-password", tags=["auth"], summary="Đổi mật khẩu (mọi token cũ hết hiệu lực)")
def api_change_password(body: ChangePw, u: db.User = Depends(current_user)):
    err = db.change_password(u.id, body.old, body.new, body.new)
    if err:
        raise HTTPException(400, err)
    return {"ok": True}


class ResetPw(BaseModel):
    username: str
    recovery_code: str
    new: str


@app.post("/auth/reset-password", tags=["auth"], summary="Quên mật khẩu: tên + mã khôi phục -> mật khẩu mới")
def api_reset_password(body: ResetPw):
    ok, err, new_code = db.reset_password_with_code(body.username, body.recovery_code, body.new, body.new)
    if not ok:
        raise HTTPException(400, err)
    return {"ok": True, "new_recovery_code": new_code}


@app.post("/auth/login", tags=["auth"], summary="Đăng nhập, trả về token dùng cho mọi endpoint khác")
def api_login(c: Credentials, req: Request):
    # Đếm theo CẢ tên đăng nhập lẫn IP: theo tên thì chặn dò mật khẩu của một người,
    # theo IP thì chặn quét nhiều tài khoản một lúc.
    ten = (c.username or "").strip().lower()
    chan_dap.chan(f"dangnhap:ten:{ten}", 10, 300, "Sai mật khẩu quá nhiều lần.")
    chan_dap.chan(f"dangnhap:ip:{chan_dap.dia_chi(req)}", 30, 300, "Quá nhiều lượt đăng nhập.")
    u, err = db.login(c.username, c.password)
    if err:
        raise HTTPException(401, err)
    chan_dap.xoa_dau_vet(f"dangnhap:ten:{ten}")      # vào được rồi thì xoá bộ đếm
    return _make_token(u)


@app.get("/me", tags=["auth"], summary="Thông tin tài khoản đang đăng nhập")
def api_me(u: db.User = Depends(current_user)):
    return {"id": u.id, "username": u.username, "role": u.role, "goal": u.goal}


# ----------------------------- TAXONOMY -----------------------------
@app.get("/subjects", tags=["taxonomy"], summary="Cây môn - chương - chủ đề (công khai, không cần đăng nhập)")
def api_subjects():
    with db.SessionLocal() as s:
        return [{"id": sub.id, "name": sub.name, "chapters": [
            {"id": c.id, "name": c.name, "topics": [{"id": t.id, "name": t.name} for t in c.topics]}
            for c in sub.chapters]} for sub in s.query(db.Subject).all()]


# ----------------------------- DOCUMENTS -----------------------------
@app.get("/documents", tags=["documents"], summary="Danh sách sách đã nạp xong")
def api_documents(u: db.User = Depends(current_user)):
    with db.SessionLocal() as s:
        return [{"id": d.id, "filename": d.filename, "subject_id": d.subject_id, "chapter_id": d.chapter_id,
                 "n_chunks": d.n_chunks, "status": d.status, "error": d.error}
                for d in s.query(db.Document).filter_by(status="ready").order_by(db.Document.subject_id, db.Document.chapter_id)]


def _run_ingest(doc_id: int, dest: Path, user_id: int, subject_id: int, chapter_id: int | None,
                pages: list[int] | None):
    """Chạy nền: OCR + chia đoạn + nhúng vector, cập nhật tiến độ vào CSDL.

    Tách khỏi request để tải sách dày không bị proxy/tunnel ngắt (Cloudflare bỏ sau 100 giây).
    """
    def _set(**kw):
        with db.SessionLocal() as s:
            d = s.get(db.Document, doc_id)
            for k, v in kw.items():
                setattr(d, k, v)
            s.commit()

    def _progress(i, total, page_no):
        _set(progress=f"OCR trang {i + 1}/{total} (trang sách {page_no})")

    _set(status="processing", progress="Đang đọc tệp…")
    try:
        n = ingest(doc_id, dest, user_id, subject_id, chapter_id, pages=pages, progress=_progress)
        _set(status="ready", n_chunks=n, error="", progress=f"Xong: {n} đoạn")
    except Exception as e:  # noqa: BLE001
        _set(status="failed", n_chunks=0, error=str(e), progress="")


@app.post("/documents", status_code=202, tags=["documents"],
          summary="[admin] Tải tài liệu lên; việc OCR/nhúng chạy nền, theo dõi bằng GET /documents/{id}")
def api_upload(background: BackgroundTasks, file: UploadFile = File(...), subject_id: int = Form(...),
               chapter_id: int | None = Form(None), page_from: int = Form(1), page_to: int = Form(0),
               u: db.User = Depends(admin_user)):
    dest = UPLOAD_DIR / f"{u.id}_{file.filename}"
    dest.write_bytes(file.file.read())
    with db.SessionLocal() as s:
        d = db.Document(user_id=u.id, subject_id=subject_id, chapter_id=chapter_id,
                        filename=file.filename, path=str(dest), status="processing",
                        progress="Đang xếp hàng…")
        s.add(d); s.commit(); doc_id = d.id
    pages = list(range(page_from, page_to + 1)) if page_to else None
    background.add_task(_run_ingest, doc_id, dest, u.id, subject_id, chapter_id, pages)
    return {"id": doc_id, "status": "processing", "n_chunks": 0}


@app.get("/documents/{doc_id}", tags=["documents"], summary="Trạng thái xử lý của một tài liệu")
def api_document_status(doc_id: int, u: db.User = Depends(current_user)):
    with db.SessionLocal() as s:
        d = s.get(db.Document, doc_id)
        if not d:
            raise HTTPException(404, "Không tìm thấy tài liệu")
        return {"id": d.id, "filename": d.filename, "status": d.status,
                "progress": d.progress or "", "n_chunks": d.n_chunks, "error": d.error or ""}


@app.delete("/documents/{doc_id}", tags=["documents"], summary="[admin] Xoá tài liệu khỏi thư viện và kho vector")
def api_delete_document(doc_id: int, u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        d = s.get(db.Document, doc_id)
        if not d:
            raise HTTPException(404, "Không tìm thấy tài liệu")
        delete_document(doc_id); s.delete(d); s.commit()
    return {"deleted": doc_id}


# ----------------------------- CHAT (RAG) -----------------------------
class ChatIn(BaseModel):
    message: str
    subject_id: int | None = None


@app.post("/chat", tags=["chat"], summary="Hỏi đáp theo tài liệu, trả lời kèm trích dẫn trang")
def api_chat(body: ChatIn, u: db.User = Depends(current_user)):
    with db.SessionLocal() as s:
        hist = [{"role": m.role, "content": m.content} for m in
                s.query(db.ChatMessage).filter_by(user_id=u.id).order_by(db.ChatMessage.id.desc()).limit(6)][::-1]
    text, hits = answer(body.message, u.id, body.subject_id, hist)
    with db.SessionLocal() as s:
        s.add(db.ChatMessage(user_id=u.id, role="user", content=body.message))
        s.add(db.ChatMessage(user_id=u.id, role="assistant", content=text, citations=hits)); s.commit()
    return {"answer": text, "citations": hits}


# ----------------------------- QUIZ -----------------------------
class QuizIn(BaseModel):
    subject_id: int
    topic_ids: list[int] = Field(min_length=1)
    difficulty: str = "medium"
    n: int = Field(5, ge=3, le=60)


def _lay_topics(topic_ids: list[int]) -> list[db.Topic]:
    with db.SessionLocal() as s:
        topics = [t for t in (s.get(db.Topic, i) for i in topic_ids) if t]
        for t in topics:
            _ = t.path                 # nạp sẵn trước khi đóng session
    if not topics:
        raise HTTPException(400, "topic_ids không hợp lệ")
    return topics


def _de_json(qid: int, n_requested: int) -> dict:
    qs = load_quiz(qid)
    with db.SessionLocal() as s:
        quiz = s.get(db.Quiz, qid)
        code = quiz.code or ""
        # bao nhiêu người đã nhận đúng đề này — cho thấy đề được dùng lại chứ không sinh mới mỗi lần
        da_dung = s.query(db.Quiz).filter(db.Quiz.code == code).count() if code else 1
    return {"quiz_id": qid, "code": code, "n_requested": n_requested, "n_actual": len(qs),
            "shared_with": da_dung,
            "questions": [
                {"id": q.id, "topic_id": q.topic_id, "difficulty": q.difficulty,
                 "content": q.content, "options": q.options}
                for q in qs]}


@app.post("/quiz", tags=["quiz"], summary="Sinh đề trắc nghiệm theo chủ đề (không trả đáp án)")
def api_create_quiz(body: QuizIn, u: db.User = Depends(current_user)):
    """Chạy đồng bộ. Đề dài (đo được: 60 câu mất ~50–120 giây) nên dùng /quiz2 để khỏi
    bị tunnel cắt ở giây thứ 100."""
    topics = _lay_topics(body.topic_ids)
    qid = generate_quiz(u.id, body.subject_id, topics, body.difficulty, body.n)
    return _de_json(qid, body.n)


@app.post("/quiz2", tags=["quiz"],
          summary="Sinh đề chạy nền — trả job_id, theo dõi bằng GET /jobs/{job_id}")
def api_create_quiz2(body: QuizIn, u: db.User = Depends(current_user)):
    """Vì sao cần: sinh 60 câu đo được ~50 giây cho lượt đầu, và nếu bước kiểm tra chéo
    loại bớt thì còn thêm lượt xin bù — tổng có thể vượt 100 giây, ngưỡng Cloudflare
    tunnel cắt kết nối (lỗi 524). Trả job_id ngay, client hỏi tiến độ."""
    topics = _lay_topics(body.topic_ids)

    def work(on_step):
        on_step({"stage": "sinh", "text": f"Đang soạn {body.n} câu"})
        qid = generate_quiz(u.id, body.subject_id, topics, body.difficulty, body.n)
        on_step({"stage": "xong", "text": "Đã soạn xong"})
        return _de_json(qid, body.n)

    return {"job_id": jobs.start(u.id, f"quiz-{body.n}", work), "status": "running"}


class MaDeIn(BaseModel):
    code: str = Field(description="Mã đề, ví dụ M1-A036FD-02")


@app.post("/quiz/by-code", tags=["quiz"],
          summary="Mở lại đúng đề mang mã này (không trả đáp án)")
def api_quiz_by_code(body: MaDeIn, u: db.User = Depends(current_user)):
    """Ai có mã thì nhận đúng đề đó, từng câu từng lựa chọn y nguyên — để giáo viên
    đọc mã cho cả lớp, hoặc hai bạn cùng làm một đề rồi so đáp án.

    Bài làm vẫn riêng: mỗi người nhận một bản sao của mình, điểm không lẫn nhau.
    """
    ma = chuan_hoa_ma(body.code)
    if not ma:
        raise HTTPException(400, "Mã đề trống")
    qid = de_theo_ma(ma, u.id)
    if qid is None:
        raise HTTPException(404, f"Không có đề nào mang mã {ma}")
    qs = load_quiz(qid)
    return _de_json(qid, len(qs))


@app.get("/quiz/mistakes", tags=["quiz"],
         summary="Những câu đang làm sai — gom theo chủ đề, để luyện lại")
def api_mistakes(subject_id: int | None = None, u: db.User = Depends(current_user)):
    """Chỉ tính câu mà LẦN TRẢ LỜI GẦN NHẤT vẫn sai: sửa được rồi thì rút khỏi danh sách."""
    return sua_sai_mod.tom_tat(u.id, subject_id)


class LuyenLaiIn(BaseModel):
    subject_id: int | None = None
    n: int = Field(10, ge=1, le=sua_sai_mod.TOI_DA_MOI_DE)


@app.post("/quiz/mistakes/practice", tags=["quiz"],
          summary="Dựng đề gồm đúng những câu mình đang làm sai")
def api_practice_mistakes(body: LuyenLaiIn, u: db.User = Depends(current_user)):
    qid = sua_sai_mod.de_sua_sai(u.id, body.subject_id, body.n)
    if qid is None:
        raise HTTPException(404, "Không có câu nào cần luyện lại — bạn đang làm đúng hết")
    qs = load_quiz(qid)
    return _de_json(qid, len(qs))


@app.get("/quiz/history", tags=["quiz"], summary="Lịch sử làm đề: mã đề, điểm, ngày làm")
def api_quiz_history(limit: int = 50, u: db.User = Depends(current_user)):
    """Gồm cả đề tự luyện lẫn bài tập lớp giao. Mã đề trong danh sách mở lại được
    bằng /quiz/by-code, nên học sinh làm lại đúng đề cũ để đối chiếu tiến bộ."""
    return [{**x, "submitted_at": clean(x["submitted_at"])}
            for x in lich_su(u.id, max(1, min(limit, 200)))]


@app.get("/quiz/history/{attempt_id}", tags=["quiz"],
         summary="Xem lại một lần làm bài: từng câu, mình chọn gì, đúng hay sai")
def api_quiz_review(attempt_id: int, u: db.User = Depends(current_user)):
    own_attempt(attempt_id, u)                 # không xem được bài làm của người khác
    r = xem_lai(attempt_id)
    if not r:
        raise HTTPException(404, "Không có bài làm này")
    r["submitted_at"] = clean(r["submitted_at"])
    return r


class SubmitIn(BaseModel):
    answers: dict[int, Annotated[int, Field(ge=0, le=3)] | None] = Field(
        description="{question_id: index lựa chọn 0-3 hoặc null}")


@app.post("/quiz/{quiz_id}/submit", tags=["quiz"], summary="Nộp bài: chấm, lưu từng câu, trả đáp án + giải thích")
def api_submit(quiz_id: int, body: SubmitIn, u: db.User = Depends(current_user)):
    q = own_quiz(quiz_id, u)                   # không cho nộp vào đề của người khác
    # Đề kiểm tra phải đi qua /assignments/{id}/submit. Nộp thẳng vào đây thì endpoint
    # trả đáp án đầy đủ mà giáo viên không ghi nhận gì — học sinh xem đáp án xong mới
    # nộp bài thật.
    if q.assignment_id:
        raise HTTPException(409, "Đây là đề kiểm tra — hãy nộp ở mục Lớp học")
    qs = load_quiz(quiz_id)
    if not qs:
        raise HTTPException(404, "Không có quiz")
    try:
        r = submit_attempt(quiz_id, u.id, body.answers)
    except DaLamRoi as e:
        raise HTTPException(409, str(e)) from e
    r["review"] = [{"id": q.id, "correct": q.correct, "selected": body.answers.get(q.id),
                    "explanation": q.explanation, "topic": q.topic.path} for q in qs]
    return r


@app.post("/questions/{question_id}/flag", tags=["quiz"], summary="Báo câu hỏi/đáp án sai")
def api_flag(question_id: int, u: db.User = Depends(current_user)):
    flag_question(question_id)
    return {"flagged": question_id}


# ----------------------------- SCORES -----------------------------
class ScoreIn(BaseModel):
    subject_id: int
    kind: str = "15p"
    value: float = Field(ge=0, le=10)
    weight: float = 1.0
    date: datetime | None = None


@app.post("/scores", tags=["scores"], summary="Nhập một cột điểm trên lớp")
def api_add_score(body: ScoreIn, u: db.User = Depends(current_user)):
    with db.SessionLocal() as s:
        sc = db.Score(user_id=u.id, subject_id=body.subject_id, kind=body.kind, value=body.value,
                      weight=body.weight, date=body.date or datetime.utcnow())
        s.add(sc); s.commit()
        return {"id": sc.id}


@app.get("/scores/summary", tags=["scores"], summary="Trung bình có hệ số theo từng môn")
def api_score_summary(u: db.User = Depends(current_user)):
    df = analytics.score_summary(u.id)
    return df.to_dict("records") if not df.empty else []


# ----------------------------- ANALYTICS -----------------------------
def _records(df):
    """DataFrame -> list[dict], NaN -> null (JSON không chấp nhận NaN)."""
    import math
    return [{k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in r.items()}
            for r in df.to_dict("records")]


@app.get("/analytics/mastery", tags=["analytics"], summary="Mastery từng chủ đề (có trọng số độ khó, thời gian)")
def api_mastery(subject_id: int | None = None, u: db.User = Depends(current_user)):
    m = analytics.topic_mastery(u.id, subject_id)
    return _records(m)


@app.get("/analytics/weak", tags=["analytics"], summary="Chủ đề đang yếu, xếp theo mức nắm vững tăng dần")
def api_weak(subject_id: int | None = None, u: db.User = Depends(current_user)):
    return _records(analytics.weak_topics(u.id, subject_id))


# ----------------------------- PLAN & AGENT -----------------------------
class PlanIn(BaseModel):
    subject_id: int | None = None
    goal: str = ""
    days: int = Field(7, ge=3, le=14)
    hours_per_day: float = 1.0
    use_agent: bool = False


def _plan_out(plan):
    return {"id": plan.id, "goal": plan.goal, "days": plan.days, "summary": plan.summary,
            "created_at": plan.created_at, "items": [
                {"id": i.id, "day": i.day, "kind": i.kind, "title": i.title, "detail": i.detail,
                 "topic_id": i.topic_id, "done": i.done} for i in plan.items]}


@app.post("/plan", tags=["plan"], summary="AI nhận xét + lập lộ trình (use_agent=true: agent function calling)")
def api_plan(body: PlanIn, u: db.User = Depends(current_user)):
    trace = []
    if body.use_agent:
        msg = (f"Phân tích tình hình học tập và lập kế hoạch {body.days} ngày, {body.hours_per_day} giờ/ngày. "
               f"Mục tiêu: {body.goal or 'nắm vững chương đang học'}. Nhớ gọi save_study_plan.")
        _, trace = run_agent(u.id, body.subject_id, msg)
    else:
        build_plan(u.id, body.subject_id, body.goal, body.days, body.hours_per_day)
    return {"plan": _plan_out(latest_plan(u.id)), "agent_trace": trace}


@app.get("/plan/latest", tags=["plan"], summary="Lộ trình gần nhất (bản cũ, giữ cho tương thích)")
def api_plan_latest(u: db.User = Depends(current_user)):
    p = latest_plan(u.id)
    return _plan_out(p) if p else None


@app.patch("/plan/items/{item_id}", tags=["plan"], summary="Đánh dấu một việc trong lộ trình đã làm xong")
def api_plan_item(item_id: int, done: bool, u: db.User = Depends(current_user)):
    with db.SessionLocal() as s:
        it = s.get(db.PlanItem, item_id)
        if not it or it.plan.user_id != u.id:
            raise HTTPException(404, "Không tìm thấy")
        it.done = done; s.commit()
    return {"id": item_id, "done": done}


class AgentIn(BaseModel):
    message: str
    subject_id: int | None = None


@app.post("/agent", status_code=202, tags=["agent"],
          summary="Hỏi gia sư AI — chạy nền, theo dõi bằng GET /jobs/{job_id}")
def api_agent(body: AgentIn, u: db.User = Depends(current_user)):
    """Một lượt gia sư gọi nhiều công cụ, có thể mất vài phút; giữ request mở suốt thời gian đó
    sẽ bị proxy/tunnel cắt ở giây thứ 100. Trả job_id ngay để client hỏi tiến độ."""
    jid = jobs.start(u.id, "agent", lambda on_step: dict(
        zip(("answer", "trace"), run_agent(u.id, body.subject_id, body.message, on_step=on_step))))
    return {"job_id": jid, "status": "running"}


@app.get("/jobs/{job_id}", tags=["agent"], summary="Tiến độ và kết quả của một việc chạy nền")
def api_job(job_id: str, u: db.User = Depends(current_user)):
    job = jobs.get(job_id, u.id)
    if not job:
        raise HTTPException(404, "Không tìm thấy việc này (có thể server đã khởi động lại) — hãy gửi lại yêu cầu")
    return job


# --- các endpoint bổ sung cho giao diện web ---
app.include_router(extra_router)
