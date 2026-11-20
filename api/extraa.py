"""Endpoint bổ sung để giao diện web dùng được TOÀN BỘ chức năng của hệ thống.

Nhóm: dashboard · learning (lịch ôn, đề vừa sức, tiên quyết) · điểm số chi tiết ·
chấm bài viết tay · lớp học · lộ trình nâng cao · góp ý · quản trị (users, thống kê, ML, agent).
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func

import app.quiz as quiz_mod
from app import analytics, classroom, db
from app.advisor import latest_plan
from app.grader import grade as grade_work
from app.grader import save_as_answer
from app.learning import due_topics, prereq_mastery, prerequisites, recommend_quiz, review_schedule, weak_prereqs
from app.quiz import load_quiz
from api import jobs
from api.deps import (admin_user, clean, current_user, member_of_assignment, own_assignment,
                      own_class, own_plan, own_quiz, records, teacher_user)

router = APIRouter()


# ============================================================ DASHBOARD
@router.get("/dashboard", tags=["dashboard"], summary="Số liệu trang chủ: chỉ số, chủ đề yếu, đến hạn ôn, việc hôm nay")
def api_dashboard(u: db.User = Depends(current_user)):
    df = analytics.answers_df(u.id)
    m = analytics.topic_mastery(u.id)
    sc = analytics.score_summary(u.id)
    with db.SessionLocal() as s:
        n_docs = s.query(db.Document).filter_by(status="ready").count()
    plan = latest_plan(u.id)
    today = []
    if plan:
        pending = [i for i in plan.items if not i.done]
        if pending:
            d = pending[0].day
            today = [{"id": i.id, "day": i.day, "kind": i.kind, "title": i.title,
                      "topic": i.topic.name if i.topic else None} for i in pending if i.day == d][:3]
    due = due_topics(u.id)
    return {
        "stats": {
            "documents": n_docs,
            "answers": int(len(df)),
            "accuracy": round(100 * df["is_correct"].mean()) if len(df) else None,
            "weak": int((m["level"] == "Yếu").sum()),
            "good": int((m["level"] == "Tốt").sum()),
            "avg_score": round(float(sc["avg"].mean()), 2) if not sc.empty else None,
        },
        "weak_topics": records(m[m["level"] == "Yếu"].sort_values("mastery").head(5)),
        "thin_topics": records(m[(m["n"] > 0) & (m["n"] < 3)].head(3)),
        "due": records(due.head(5)),
        "today": today,
        "plan": None if not plan else {"id": plan.id, "days": plan.days, "goal": plan.goal,
                                       "done": sum(i.done for i in plan.items), "total": len(plan.items)},
        "assignments": [a for a in classroom.assignments_for_student(u.id) if not a["done"]][:3],
    }


# ============================================================ LEARNING
@router.get("/learning/due", tags=["learning"], summary="Chủ đề đến hạn ôn (spaced repetition SM-2)")
def api_due(subject_id: int | None = None, u: db.User = Depends(current_user)):
    return {"due": records(due_topics(u.id, subject_id)), "schedule": records(review_schedule(u.id, subject_id))}


@router.get("/learning/recommend", tags=["learning"], summary="Đề vừa sức: chủ đề + độ khó hệ thống tự chọn")
def api_recommend(subject_id: int, u: db.User = Depends(current_user)):
    r = recommend_quiz(u.id, subject_id)
    return {"topics": [{"topic_id": t, "topic": n, "why": w} for t, n, w in r["topics"]],
            "difficulty": r["difficulty"], "source": r["source"],
            "blocked": [{"topic_id": t, "topic": n, "needs": b} for t, n, b in r["blocked"]]}


@router.get("/learning/prerequisites", tags=["learning"], summary="Đồ thị kiến thức: chủ đề nào cần nền nào")
def api_prereq(subject_id: int | None = None, u: db.User = Depends(current_user)):
    m = analytics.topic_mastery(u.id, subject_id)
    m_all = prereq_mastery(u.id)          # nền của chủ đề có thể nằm ở môn/lớp khác
    pre = prerequisites()
    shown = set(m["topic_id"].astype(int))
    names = dict(zip(m_all["topic_id"].astype(int), m_all["topic"]))
    subj = dict(zip(m_all["topic_id"].astype(int), m_all["subject"]))

    def need(p: int) -> dict:
        """Tên chủ đề tiên quyết, kèm tên môn khi nó thuộc môn khác môn đang xem."""
        return {"topic": names.get(p, str(p)), "subject": subj.get(p, ""), "other_subject": p not in shown}

    return {"edges": [{"topic_id": t, "topic": names.get(t, t),
                       "needs": [names.get(p, p) for p in ps],
                       "needs_detail": [need(p) for p in ps]}
                      for t, ps in pre.items() if t in shown],
            "blocked": [{"topic_id": int(r["topic_id"]), "topic": r["topic"],
                         "weak_needs": w,
                         "weak_needs_detail": [need(p) for p in pre.get(int(r["topic_id"]), [])
                                               if names.get(p) in w]}
                        for _, r in m.iterrows()
                        if (w := weak_prereqs(int(r["topic_id"]), m_all, pre))]}


# ============================================================ ANALYTICS bổ sung
@router.get("/analytics/progress", tags=["analytics"], summary="Tiến bộ theo thời gian của một chủ đề")
def api_progress(topic_id: int, u: db.User = Depends(current_user)):
    df = analytics.answers_df(u.id)
    if df.empty:
        return []
    d = df[df["topic_id"] == topic_id].sort_values("answered_at").copy()
    if d.empty:
        return []
    d["idx"] = range(1, len(d) + 1)
    d["cum"] = (100 * d["is_correct"].expanding().mean()).round(0)
    return [{"n": int(r.idx), "cum": float(r.cum), "correct": bool(r.is_correct),
             "difficulty": r.difficulty, "at": clean(r.answered_at)} for r in d.itertuples()]


@router.get("/analytics/trend", tags=["analytics"], summary="Xu hướng điểm các bài quiz")
def api_trend(u: db.User = Depends(current_user)):
    return records(analytics.attempt_trend(u.id))


@router.get("/analytics/kt", tags=["analytics"], summary="Dự đoán Deep Knowledge Tracing cho từng chủ đề")
def api_kt(u: db.User = Depends(current_user)):
    from app.ml.kt_app import model_info, predict_user
    info = model_info()
    pred = predict_user(u.id) if info else None
    return {"model": info, "prediction": None if not pred else {str(k): round(100 * v) for k, v in pred.items()}}


# ============================================================ ĐIỂM SỐ
@router.get("/scores", tags=["scores"], summary="Danh sách điểm đã nhập")
def api_scores(u: db.User = Depends(current_user)):
    with db.SessionLocal() as s:
        rows = (s.query(db.Score, db.Subject.name).join(db.Subject, db.Score.subject_id == db.Subject.id)
                .filter(db.Score.user_id == u.id).order_by(db.Score.date.desc()).all())
        return [{"id": sc.id, "subject": name, "subject_id": sc.subject_id, "kind": sc.kind,
                 "value": sc.value, "weight": sc.weight, "date": clean(sc.date)} for sc, name in rows]


@router.delete("/scores/{score_id}", tags=["scores"], summary="Xoá một cột điểm của chính mình")
def api_delete_score(score_id: int, u: db.User = Depends(current_user)):
    with db.SessionLocal() as s:
        sc = s.get(db.Score, score_id)
        if not sc or sc.user_id != u.id:
            raise HTTPException(404, "Không tìm thấy điểm")
        s.delete(sc); s.commit()
    return {"deleted": score_id}


# ============================================================ QUIZ bổ sung
@router.get("/quiz/{quiz_id}", tags=["quiz"], summary="Lấy lại đề đã sinh (không kèm đáp án)")
def api_get_quiz(quiz_id: int, u: db.User = Depends(current_user)):
    own_quiz(quiz_id, u)
    qs = load_quiz(quiz_id)
    if not qs:
        raise HTTPException(404, "Không có đề")
    return {"quiz_id": quiz_id, "questions": [{"id": q.id, "topic_id": q.topic_id, "topic": q.topic.name,
                                               "difficulty": q.difficulty, "content": q.content,
                                               "options": q.options} for q in qs]}


# ============================================================ CHẤM BÀI VIẾT TAY
@router.post("/grade", tags=["grade"], summary="Chấm bài tự luận / ảnh bài làm: chỉ ra bước sai đầu tiên")
async def api_grade(subject_id: int = Form(...), chapter_id: int | None = Form(None),
                    problem: str = Form(""), text: str = Form(""),
                    file: UploadFile | None = File(None), u: db.User = Depends(current_user)):
    with db.SessionLocal() as s:
        if chapter_id:
            topic_ids = [t.id for t in s.query(db.Topic).filter_by(chapter_id=chapter_id)]
        else:
            topic_ids = [t.id for t in s.query(db.Topic).join(db.Chapter).filter(db.Chapter.subject_id == subject_id)]
    data = await file.read() if file else None
    if not data and not text.strip():
        raise HTTPException(400, "Cần ảnh bài làm hoặc nội dung dạng chữ")
    try:
        return grade_work(u.id, subject_id, data, file.content_type if file else "", text, problem, topic_ids)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"Lỗi khi chấm: {e}")


class GradeSaveIn(BaseModel):
    subject_id: int
    result: dict


@router.post("/grade/save", tags=["grade"], summary="Lưu kết quả chấm vào hồ sơ học tập (tính vào mastery)")
def api_grade_save(body: GradeSaveIn, u: db.User = Depends(current_user)):
    return {"attempt_id": save_as_answer(u.id, body.subject_id, body.result)}


# ============================================================ LỚP HỌC
class ClassIn(BaseModel):
    name: str
    subject_id: int | None = None


class JoinIn(BaseModel):
    code: str


class AssignmentIn(BaseModel):
    title: str
    topic_ids: list[int] = Field(min_length=1)
    difficulty: str = "medium"
    n: int = Field(10, ge=3, le=60)
    due: datetime | None = None


class SubmitAssignmentIn(BaseModel):
    quiz_id: int
    answers: dict[int, int | None]


@router.get("/classes", tags=["classroom"], summary="Lớp tôi dạy (giáo viên) và lớp tôi tham gia (học sinh)")
def api_classes(u: db.User = Depends(current_user)):
    teaching = [{"id": c.id, "name": c.name, "code": c.code, "subject_id": c.subject_id,
                 "members": len(c.members), "assignments": len(c.assignments)}
                for c in classroom.my_classes(u.id)] if u.role in ("teacher", "admin") else []
    joined = [{"id": c.id, "name": c.name, "code": c.code, "assignments": len(c.assignments)}
              for c in classroom.classes_of_student(u.id)]
    return {"teaching": teaching, "joined": joined}


@router.post("/classes", tags=["classroom"], summary="[giáo viên] Tạo lớp, trả về mã tham gia")
def api_create_class(body: ClassIn, u: db.User = Depends(teacher_user)):
    c = classroom.create_class(u.id, body.name, body.subject_id)
    return {"id": c.id, "name": c.name, "code": c.code}


@router.post("/classes/join", tags=["classroom"], summary="Học sinh tham gia lớp bằng mã")
def api_join_class(body: JoinIn, u: db.User = Depends(current_user)):
    c, err = classroom.join_class(u.id, body.code)
    if err and not c:
        raise HTTPException(400, err)
    return {"id": c.id, "name": c.name, "note": err}


@router.get("/classes/{class_id}/overview", tags=["classroom"], summary="[giáo viên] Tổng quan + heatmap cả lớp")
def api_class_overview(class_id: int, u: db.User = Depends(teacher_user)):
    own_class(class_id, u)                     # không cho xem lớp của giáo viên khác
    hm = classroom.class_heatmap(class_id)
    avg = classroom.class_topic_avg(class_id)
    return {"students": records(classroom.class_overview(class_id)),
            "heatmap": {"students": list(hm.index), "topics": list(hm.columns),
                        "values": [[clean(v) for v in row] for row in hm.values]} if not hm.empty else None,
            "weakest": records(avg.head(5)) if not avg.empty else []}


@router.post("/classes/{class_id}/assignments", tags=["classroom"], summary="[giáo viên] Soạn đề và giao cho lớp")
def api_create_assignment(class_id: int, body: AssignmentIn, u: db.User = Depends(teacher_user)):
    own_class(class_id, u)                     # không cho giao đề vào lớp người khác
    a = classroom.create_assignment(class_id, u.id, body.title, body.topic_ids, body.difficulty, body.n, body.due)
    return {"id": a.id, "title": a.title}


@router.get("/assignments", tags=["classroom"], summary="Đề được giao cho tôi")
def api_assignments(u: db.User = Depends(current_user)):
    return [{**a, "due": clean(a["due"])} for a in classroom.assignments_for_student(u.id)]


@router.post("/assignments/{assignment_id}/start", tags=["classroom"], summary="Bắt đầu làm đề được giao")
def api_start_assignment(assignment_id: int, u: db.User = Depends(current_user)):
    member_of_assignment(assignment_id, u)     # chỉ học sinh trong lớp mới làm được
    try:
        qid = classroom.start_assignment(assignment_id, u.id)
    except classroom.HetHan as e:
        raise HTTPException(409, str(e)) from e
    except classroom.DaNop as e:
        raise HTTPException(409, str(e)) from e
    qs = load_quiz(qid)
    return {"quiz_id": qid, "questions": [{"id": q.id, "content": q.content, "options": q.options,
                                           "topic": q.topic.name} for q in qs]}


@router.post("/assignments/{assignment_id}/submit", tags=["classroom"], summary="Nộp đề được giao")
def api_submit_assignment(assignment_id: int, body: SubmitAssignmentIn, u: db.User = Depends(current_user)):
    """Chấm và lưu. Đáp án chỉ trả về SAU hạn nộp: trả ngay thì bạn nộp sớm có đáp án
    để đưa cho bạn nộp muộn."""
    member_of_assignment(assignment_id, u)
    own_quiz(body.quiz_id, u)                  # và chỉ nộp được bài làm của chính mình
    for sel in body.answers.values():
        if sel is not None and not (0 <= sel <= 3):
            raise HTTPException(422, "Lựa chọn phải nằm trong khoảng 0-3")
    try:
        r = classroom.submit_assignment(assignment_id, body.quiz_id, u.id, body.answers)
    except classroom.HetHan as e:
        raise HTTPException(409, str(e)) from e
    except classroom.DaNop as e:
        raise HTTPException(409, str(e)) from e
    except quiz_mod.DaLamRoi as e:
        raise HTTPException(409, str(e)) from e
    with db.SessionLocal() as s:
        a = s.get(db.Assignment, assignment_id)
        con_han = bool(a.due) and datetime.utcnow() <= a.due
    if con_han:
        r.pop("per_topic", None)
        r["dap_an_sau_han"] = True
        r["thong_bao"] = ("Đã nộp. Đáp án và lời giải sẽ mở sau hạn nộp "
                          f"({a.due:%H:%M %d/%m/%Y}).")
    return r


@router.get("/assignments/{assignment_id}/results", tags=["classroom"], summary="[giáo viên] Kết quả cả lớp theo từng câu")
def api_assignment_results(assignment_id: int, u: db.User = Depends(teacher_user)):
    own_assignment(assignment_id, u)           # không cho xem kết quả lớp khác
    res, per_q = classroom.assignment_results(assignment_id)
    return {"students": records(res), "per_question": records(per_q)}


# ============================================================ LỘ TRÌNH nâng cao
class PlanIn2(BaseModel):
    subject_id: int | None = None
    goal: str = ""
    days: int = Field(7, ge=3, le=14)
    hours_per_day: float = 1.0
    mode: str = Field("quick", description="quick | agent | multi")


def _plan_json(p) -> dict | None:
    if not p:
        return None
    return {"id": p.id, "goal": p.goal, "days": p.days, "summary": p.summary, "evidence": p.evidence,
            "created_at": clean(p.created_at),
            "items": [{"id": i.id, "day": i.day, "kind": i.kind, "title": i.title, "detail": i.detail,
                       "topic_id": i.topic_id, "topic": i.topic.name if i.topic else None, "done": i.done}
                      for i in p.items]}


@router.post("/plan2", tags=["plan"], summary="Lập lộ trình: quick (1 request) | agent | multi-agent (có phản biện)")
def api_plan2(body: PlanIn2, u: db.User = Depends(current_user)):
    """Chế độ quick trả kết quả ngay. Hai chế độ agent chạy nền (mất vài phút, tunnel cắt ở 100 giây):
    trả job_id, theo dõi bằng GET /jobs/{job_id}, kết quả nằm trong trường result."""
    if body.mode == "quick":
        from app.advisor import build_plan
        build_plan(u.id, body.subject_id, body.goal, body.days, body.hours_per_day)
        return {"plan": _plan_json(latest_plan(u.id)), "trace": [], "critique": None, "violations": []}

    def work(on_step):
        if body.mode == "multi":
            from app.multi_agent import run_pipeline
            out = run_pipeline(u.id, body.subject_id, body.goal, body.days, body.hours_per_day,
                               on_event=lambda stage, text: on_step({"stage": stage, "text": text}))
            trace, critique, violations = out["trace"], out["critique"], out.get("violations", [])
        else:
            from app.agent import run_agent
            msg = (f"Phân tích tình hình học tập và lập kế hoạch {body.days} ngày, {body.hours_per_day} giờ/ngày. "
                   f"Mục tiêu: {body.goal or 'nắm vững chương đang học'}. Nhớ gọi save_study_plan để lưu.")
            _, trace = run_agent(u.id, body.subject_id, msg, on_step=on_step)
            critique, violations = None, []
        return {"plan": _plan_json(latest_plan(u.id)), "trace": trace,
                "critique": critique, "violations": violations}

    return {"job_id": jobs.start(u.id, f"plan-{body.mode}", work), "status": "running"}


@router.get("/plan2/latest", tags=["plan"], summary="Lộ trình gần nhất kèm tiến độ từng ngày")
def api_plan2_latest(u: db.User = Depends(current_user)):
    return _plan_json(latest_plan(u.id))


@router.get("/plan2/{plan_id}/outcome", tags=["plan"], summary="Hiệu quả kế hoạch: % hoàn thành, Δ mastery")
def api_plan_outcome(plan_id: int, u: db.User = Depends(current_user)):
    own_plan(plan_id, u)                       # không cho xem kế hoạch người khác
    from app.reflection import plan_outcome
    o = plan_outcome(plan_id)
    return {k: clean(v) for k, v in o.items()}


# ============================================================ CHAT lịch sử
@router.get("/chat/history", tags=["chat"], summary="Lịch sử hội thoại gần đây")
def api_chat_history(limit: int = 30, u: db.User = Depends(current_user)):
    with db.SessionLocal() as s:
        rows = (s.query(db.ChatMessage).filter_by(user_id=u.id)
                .order_by(db.ChatMessage.id.desc()).limit(limit).all())[::-1]
        return [{"role": m.role, "content": m.content, "citations": m.citations or [],
                 "at": clean(m.created_at)} for m in rows]


@router.delete("/chat/history", tags=["chat"], summary="Xoá lịch sử hội thoại của chính mình")
def api_clear_chat(u: db.User = Depends(current_user)):
    with db.SessionLocal() as s:
        n = s.query(db.ChatMessage).filter_by(user_id=u.id).delete(); s.commit()
    return {"deleted": n}


# ============================================================ GÓP Ý (view "Hỏi Bài")
class FeedbackIn(BaseModel):
    name: str = ""
    email: str = ""
    subject: str = ""
    grade: str = ""
    content: str


@router.post("/feedback", tags=["feedback"], summary="Gửi thắc mắc / góp ý (lưu vào hệ thống)")
def api_feedback(body: FeedbackIn, u: db.User = Depends(current_user)):
    if len(body.content.strip()) < 5:
        raise HTTPException(400, "Nội dung quá ngắn")
    with db.SessionLocal() as s:
        s.add(db.Feedback(user_id=u.id, name=body.name.strip(), email=body.email.strip(),
                          subject=body.subject.strip(), grade=body.grade.strip(), content=body.content.strip()))
        s.commit()
    return {"ok": True, "message": "Đã gửi. Cảm ơn bạn đã góp ý!"}


# ============================================================ QUẢN TRỊ
@router.get("/admin/users", tags=["admin"], summary="[admin] Danh sách người dùng kèm số liệu hoạt động")
def api_admin_users(u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        out = []
        for x in s.query(db.User).order_by(db.User.id):
            out.append({"id": x.id, "username": x.username, "role": x.role, "email": x.email,
                        "created_at": clean(x.created_at),
                        "quizzes": s.query(db.Attempt).filter_by(user_id=x.id).count(),
                        "answers": s.query(db.Answer).filter_by(user_id=x.id).count(),
                        "chats": s.query(db.ChatMessage).filter_by(user_id=x.id, role="user").count()})
        return out


@router.patch("/admin/users/{user_id}/role", tags=["admin"], summary="[admin] Đổi vai trò: user / teacher / admin")
def api_set_role(user_id: int, body: dict, u: db.User = Depends(admin_user)):
    role = body.get("role")
    if role not in ("user", "teacher", "admin"):
        raise HTTPException(400, "Vai trò không hợp lệ")
    with db.SessionLocal() as s:
        x = s.get(db.User, user_id)
        if not x:
            raise HTTPException(404, "Không tìm thấy")
        x.role = role; s.commit()
    return {"id": user_id, "role": role}


@router.post("/admin/users/{user_id}/reset-password", tags=["admin"], summary="[admin] Đặt lại mật khẩu hộ người dùng")
def api_admin_reset(user_id: int, u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        x = s.get(db.User, user_id)
        if not x:
            raise HTTPException(404, "Không tìm thấy")
        x.password_hash = ""; s.commit()
    return {"ok": True, "message": "Đã xoá mật khẩu; lần đăng nhập tới người đó tự đặt mật khẩu mới."}


@router.get("/admin/stats", tags=["admin"], summary="[admin] Thống kê toàn hệ thống và hoạt động theo ngày")
def api_admin_stats(u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        n_q = s.query(db.Question).count()
        per_day = (s.query(func.date(db.Answer.answered_at), func.count(db.Answer.id))
                   .group_by(func.date(db.Answer.answered_at)).order_by(func.date(db.Answer.answered_at)).all())
        return {"users": s.query(db.User).count(), "attempts": s.query(db.Attempt).count(),
                "answers": s.query(db.Answer).count(), "questions": n_q,
                "flagged": s.query(db.Question).filter_by(flagged=True).count(),
                "chats": s.query(db.ChatMessage).filter_by(role="user").count(),
                "documents": s.query(db.Document).filter_by(status="ready").count(),
                "per_day": [{"date": str(d), "n": n} for d, n in per_day]}


@router.get("/admin/documents", tags=["admin"], summary="Toàn bộ tài liệu kèm người tải lên")
def api_admin_docs(u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        rows = (s.query(db.Document, db.User.username, db.Subject.name, db.Chapter.name)
                .join(db.User, db.Document.user_id == db.User.id)
                .join(db.Subject, db.Document.subject_id == db.Subject.id)
                .outerjoin(db.Chapter, db.Document.chapter_id == db.Chapter.id)
                .order_by(db.Subject.name, db.Chapter.order).all())
        return [{"id": d.id, "filename": d.filename, "subject": sn, "chapter": cn, "n_chunks": d.n_chunks,
                 "status": d.status, "error": d.error, "by": un} for d, un, sn, cn in rows]


@router.get("/admin/ml", tags=["admin"], summary="Thông tin mô hình DKT")
def api_admin_ml(u: db.User = Depends(admin_user)):
    from app.ml.kt_app import MIN_ANSWERS, model_info
    with db.SessionLocal() as s:
        n = s.query(db.Answer).count()
    return {"model": model_info(), "n_answers": n, "min_answers": MIN_ANSWERS}


@router.post("/admin/ml/train", tags=["admin"], summary="Huấn luyện lại DKT trên dữ liệu hệ thống")
def api_admin_train(u: db.User = Depends(admin_user)):
    from app.ml.kt_app import TuChoiThayMoHinh, train_app_model
    try:
        meta = train_app_model(log=lambda *_: None)
    except TuChoiThayMoHinh as e:          # mô hình mới kém hơn -> giữ bản cũ
        raise HTTPException(409, str(e)) from e
    if not meta:
        raise HTTPException(400, "Chưa đủ dữ liệu để huấn luyện")
    return meta


@router.get("/admin/agent/runs", tags=["admin"], summary="Nhật ký chạy agent")
def api_agent_runs(limit: int = 50, u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        names = {x.id: x.username for x in s.query(db.User)}
        rows = s.query(db.AgentRun).order_by(db.AgentRun.id.desc()).limit(limit).all()
        return [{"id": r.id, "at": clean(r.created_at), "user": names.get(r.user_id), "mode": r.mode,
                 "tools": r.n_tool_calls, "seconds": round(r.duration_s or 0), "critic": r.critic_score,
                 "violations": r.violations or [], "plan_id": r.plan_id} for r in rows]


@router.get("/admin/agent/lessons", tags=["admin"], summary="Bài học agent tự rút ra")
def api_agent_lessons(u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        names = {x.id: x.username for x in s.query(db.User)}
        return [{"id": l.id, "lesson": l.lesson, "evidence": l.evidence, "active": l.active,
                 "scope": names.get(l.user_id, "chung") if l.user_id else "chung", "at": clean(l.created_at)}
                for l in s.query(db.AgentLesson).order_by(db.AgentLesson.id.desc()).limit(30)]


@router.patch("/admin/agent/lessons/{lesson_id}", tags=["admin"], summary="[admin] Bật/tắt một bài học agent tự rút ra")
def api_toggle_lesson(lesson_id: int, u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        l = s.get(db.AgentLesson, lesson_id)
        if not l:
            raise HTTPException(404, "Không tìm thấy")
        l.active = not l.active; s.commit()
        return {"id": lesson_id, "active": l.active}


@router.post("/admin/agent/reflect", tags=["admin"], summary="Chạy agent phản tư cho một người dùng")
def api_reflect(body: dict, u: db.User = Depends(admin_user)):
    from app.reflection import reflect
    uid = int(body.get("user_id") or u.id)
    return {"lessons": reflect(uid)}


@router.get("/admin/feedback", tags=["admin"], summary="[admin] Góp ý và báo lỗi người dùng gửi lên")
def api_admin_feedback(u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        names = {x.id: x.username for x in s.query(db.User)}
        return [{"id": f.id, "user": names.get(f.user_id), "name": f.name, "email": f.email,
                 "subject": f.subject, "grade": f.grade, "content": f.content, "at": clean(f.created_at)}
                for f in s.query(db.Feedback).order_by(db.Feedback.id.desc()).limit(50)]


# ============================================================ QUẢN LÝ MÔN / CHƯƠNG / CHỦ ĐỀ
class SubjectIn(BaseModel):
    name: str


class ChapterIn(BaseModel):
    subject_id: int
    name: str


class TopicIn(BaseModel):
    chapter_id: int
    name: str


class TopicsBulkIn(BaseModel):
    chapter_id: int
    names: list[str]


def _export_topics_json():
    """Ghi lại data/topics.json để dựng lại được taxonomy nếu CSDL bị tạo mới."""
    import json
    from pathlib import Path
    out = []
    with db.SessionLocal() as s:
        for sub in s.query(db.Subject).order_by(db.Subject.id):
            out.append({"name": sub.name, "chapters": [
                {"name": c.name, "topics": [t.name for t in c.topics]}
                for c in sorted(sub.chapters, key=lambda c: c.order)]})
    f = Path(db.__file__).resolve().parent.parent / "data" / "topics.json"
    f.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


@router.get("/admin/taxonomy", tags=["taxonomy"], summary="Cây môn - chương - chủ đề kèm số liệu sử dụng")
def api_taxonomy(u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        out = []
        for sub in s.query(db.Subject).order_by(db.Subject.id):
            chapters = []
            for c in sub.chapters:
                chapters.append({
                    "id": c.id, "name": c.name, "order": c.order,
                    "topics": [{"id": t.id, "name": t.name,
                                "n_answers": s.query(db.Answer).filter_by(topic_id=t.id).count()} for t in c.topics],
                    "n_docs": s.query(db.Document).filter_by(chapter_id=c.id).count(),
                })
            out.append({"id": sub.id, "name": sub.name, "chapters": chapters,
                        "n_docs": s.query(db.Document).filter_by(subject_id=sub.id).count()})
        return out


@router.post("/admin/subjects", tags=["taxonomy"], summary="Thêm môn học mới, ví dụ 'Toán 8'")
def api_add_subject(body: SubjectIn, u: db.User = Depends(admin_user)):
    name = body.name.strip()
    if len(name) < 2:
        raise HTTPException(400, "Tên môn quá ngắn")
    with db.SessionLocal() as s:
        if s.query(db.Subject).filter(func.lower(db.Subject.name) == name.lower()).first():
            raise HTTPException(400, "Môn này đã có")
        sub = db.Subject(name=name)
        s.add(sub); s.commit()
        _export_topics_json()
        return {"id": sub.id, "name": sub.name}


@router.post("/admin/chapters", tags=["taxonomy"], summary="[admin] Thêm chương vào một môn")
def api_add_chapter(body: ChapterIn, u: db.User = Depends(admin_user)):
    name = body.name.strip()
    if len(name) < 2:
        raise HTTPException(400, "Tên chương quá ngắn")
    with db.SessionLocal() as s:
        if not s.get(db.Subject, body.subject_id):
            raise HTTPException(404, "Không tìm thấy môn")
        order = s.query(db.Chapter).filter_by(subject_id=body.subject_id).count()
        c = db.Chapter(subject_id=body.subject_id, name=name, order=order)
        s.add(c); s.commit()
        _export_topics_json()
        return {"id": c.id, "name": c.name}


@router.post("/admin/topics", tags=["taxonomy"], summary="Thêm nhiều chủ đề cùng lúc (mỗi dòng một chủ đề)")
def api_add_topics(body: TopicsBulkIn, u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        if not s.get(db.Chapter, body.chapter_id):
            raise HTTPException(404, "Không tìm thấy chương")
        added = []
        have = {t.name.lower() for t in s.query(db.Topic).filter_by(chapter_id=body.chapter_id)}
        for n in body.names:
            n = n.strip()
            if len(n) < 2 or n.lower() in have:
                continue
            t = db.Topic(chapter_id=body.chapter_id, name=n)
            s.add(t); have.add(n.lower()); added.append(n)
        s.commit()
        _export_topics_json()
        return {"added": added}


@router.delete("/admin/topics/{topic_id}", tags=["taxonomy"], summary="[admin] Xoá chủ đề (chặn nếu đã có người làm bài)")
def api_del_topic(topic_id: int, u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        n = s.query(db.Answer).filter_by(topic_id=topic_id).count()
        if n:
            raise HTTPException(400, f"Chủ đề đang có {n} câu trả lời, không xoá được")
        t = s.get(db.Topic, topic_id)
        if not t:
            raise HTTPException(404, "Không tìm thấy")
        s.delete(t); s.commit()
    _export_topics_json()
    return {"deleted": topic_id}


@router.delete("/admin/chapters/{chapter_id}", tags=["taxonomy"], summary="[admin] Xoá chương (chặn nếu còn dữ liệu học tập)")
def api_del_chapter(chapter_id: int, u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        c = s.get(db.Chapter, chapter_id)
        if not c:
            raise HTTPException(404, "Không tìm thấy")
        tids = [t.id for t in c.topics]
        if tids and s.query(db.Answer).filter(db.Answer.topic_id.in_(tids)).count():
            raise HTTPException(400, "Chương đang có dữ liệu học tập, không xoá được")
        if s.query(db.Document).filter_by(chapter_id=chapter_id).count():
            raise HTTPException(400, "Hãy xoá tài liệu của chương này trước")
        for t in c.topics:
            s.delete(t)
        s.delete(c); s.commit()
    _export_topics_json()
    return {"deleted": chapter_id}


@router.delete("/admin/subjects/{subject_id}", tags=["taxonomy"], summary="[admin] Xoá môn (chặn nếu còn tài liệu)")
def api_del_subject(subject_id: int, u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        sub = s.get(db.Subject, subject_id)
        if not sub:
            raise HTTPException(404, "Không tìm thấy")
        if s.query(db.Document).filter_by(subject_id=subject_id).count():
            raise HTTPException(400, "Hãy xoá tài liệu của môn này trước")
        tids = [t.id for c in sub.chapters for t in c.topics]
        if tids and s.query(db.Answer).filter(db.Answer.topic_id.in_(tids)).count():
            raise HTTPException(400, "Môn đang có dữ liệu học tập, không xoá được")
        for c in sub.chapters:
            for t in c.topics:
                s.delete(t)
            s.delete(c)
        s.delete(sub); s.commit()
    _export_topics_json()
    return {"deleted": subject_id}


# ============================================================ NGÂN HÀNG CÂU HỎI
@router.get("/admin/bank/stats", tags=["bank"], summary="[admin] Số liệu tổng quan ngân hàng câu hỏi")
def api_bank_stats(u: db.User = Depends(admin_user)):
    from app import bank
    return bank.thong_ke()


@router.get("/admin/bank", tags=["bank"], summary="[admin] Duyệt ngân hàng câu hỏi")
def api_bank_list(subject_id: int | None = None, chapter_id: int | None = None,
                  topic_id: int | None = None, difficulty: str | None = None,
                  flagged: bool | None = None, q: str | None = None,
                  limit: int = 50, offset: int = 0, u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        truy = (s.query(db.BankQuestion, db.Topic.name, db.Chapter.name, db.Subject.name)
                .select_from(db.BankQuestion)
                .join(db.Topic, db.BankQuestion.topic_id == db.Topic.id)
                .join(db.Chapter, db.Topic.chapter_id == db.Chapter.id)
                .join(db.Subject, db.Chapter.subject_id == db.Subject.id))
        if subject_id:
            truy = truy.filter(db.Subject.id == subject_id)
        if chapter_id:
            truy = truy.filter(db.Chapter.id == chapter_id)
        if topic_id:
            truy = truy.filter(db.BankQuestion.topic_id == topic_id)
        if difficulty:
            truy = truy.filter(db.BankQuestion.difficulty == difficulty)
        if flagged is not None:
            truy = truy.filter(db.BankQuestion.flagged.is_(flagged))
        if q:
            truy = truy.filter(db.BankQuestion.content.ilike(f"%{q}%"))
        tong = truy.count()
        rows = truy.order_by(db.BankQuestion.id).limit(min(limit, 200)).offset(offset).all()
        return {"total": tong, "offset": offset, "items": [
            {"id": c.id, "subject": sub, "chapter": ch.split(":")[0], "topic": tp,
             "difficulty": c.difficulty, "content": c.content, "options": c.options,
             "correct": c.correct, "explanation": c.explanation,
             "times_used": c.times_used, "times_answered": c.times_answered,
             "ti_le_dung": c.ti_le_dung, "flagged": c.flagged, "verified": c.verified,
             "source": c.source}
            for c, tp, ch, sub in rows]}


@router.get("/admin/bank/coverage", tags=["bank"], summary="[admin] Chủ đề nào còn ít câu")
def api_bank_coverage(subject_id: int | None = None, u: db.User = Depends(admin_user)):
    """Danh sách chủ đề kèm số câu đang có — để biết cần bổ sung ở đâu."""
    with db.SessionLocal() as s:
        truy = (s.query(db.Topic.id, db.Topic.name, db.Chapter.name, db.Subject.name,
                        func.count(db.BankQuestion.id))
                .select_from(db.Topic)
                .join(db.Chapter, db.Topic.chapter_id == db.Chapter.id)
                .join(db.Subject, db.Chapter.subject_id == db.Subject.id)
                .outerjoin(db.BankQuestion, db.BankQuestion.topic_id == db.Topic.id))
        if subject_id:
            truy = truy.filter(db.Subject.id == subject_id)
        rows = truy.group_by(db.Topic.id).order_by(func.count(db.BankQuestion.id)).all()
        return [{"topic_id": tid, "topic": tp, "chapter": ch.split(":")[0], "subject": sub, "n": n}
                for tid, tp, ch, sub, n in rows]


@router.delete("/admin/bank/{bank_id}", tags=["bank"], summary="[admin] Xoá một câu khỏi ngân hàng")
def api_bank_delete(bank_id: int, u: db.User = Depends(admin_user)):
    with db.SessionLocal() as s:
        c = s.get(db.BankQuestion, bank_id)
        if not c:
            raise HTTPException(404, "Không tìm thấy câu hỏi")
        s.query(db.Question).filter_by(bank_id=bank_id).update({"bank_id": None})
        s.delete(c); s.commit()
    return {"deleted": bank_id}
