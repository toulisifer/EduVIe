"""Phụ thuộc dùng chung cho REST API: JWT, lấy người dùng hiện tại, kiểm tra vai trò."""
from __future__ import annotations

import math
import os
from datetime import datetime, timedelta, timezone

import jwt
import pandas as pd
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import db

JWT_SECRET = os.getenv("JWT_SECRET", "doi-secret-nay-trong-.env")
JWT_TTL_HOURS = 24 * 14          # 14 ngày, khớp với cookie "ghi nhớ đăng nhập" của web
bearer = HTTPBearer(auto_error=True)


def make_token(user: db.User) -> dict:
    payload = {"sub": str(user.id), "name": user.username, "role": user.role,
               "tv": user.token_version or 0,
               "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_TTL_HOURS)}
    return {"access_token": jwt.encode(payload, JWT_SECRET, algorithm="HS256"), "token_type": "bearer",
            "user_id": user.id, "username": user.username, "role": user.role}


def current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> db.User:
    try:
        payload = jwt.decode(cred.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Phiên đăng nhập không hợp lệ hoặc đã hết hạn")
    with db.SessionLocal() as s:
        u = s.get(db.User, int(payload["sub"]))
    if not u:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Người dùng không tồn tại")
    # Đổi mật khẩu làm tăng token_version, nên token phát trước đó mang số cũ -> từ chối.
    # Thiếu bước này thì đổi mật khẩu không đuổi được phiên đăng nhập đã bị lộ.
    if int(payload.get("tv", 0)) != (u.token_version or 0):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,
                            "Mật khẩu đã đổi — hãy đăng nhập lại")
    return u


def admin_user(u: db.User = Depends(current_user)) -> db.User:
    if u.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ quản trị viên được thực hiện")
    return u


def teacher_user(u: db.User = Depends(current_user)) -> db.User:
    if u.role not in ("teacher", "admin"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ giáo viên hoặc quản trị viên được thực hiện")
    return u


# ----------------------------- QUYỀN TRÊN TỪNG BẢN GHI -----------------------------
# Đúng vai trò vẫn chưa đủ: một giáo viên không được xem lớp của giáo viên khác,
# một học sinh không được xem kế hoạch của bạn cùng lớp. Nếu chỉ dựa vào vai trò thì
# đổi số trong URL là đọc được dữ liệu người khác (lỗi IDOR — Broken Access Control).

def _tu_choi(what: str):
    """Trả 404 chứ không phải 403: không tiết lộ rằng bản ghi đó có tồn tại."""
    raise HTTPException(status.HTTP_404_NOT_FOUND, f"Không tìm thấy {what}")


def own_class(class_id: int, u: db.User) -> db.Classroom:
    """Lớp mà người này được quản lý: giáo viên chủ nhiệm của lớp, hoặc quản trị viên."""
    with db.SessionLocal() as s:
        c = s.get(db.Classroom, class_id)
        if not c or (u.role != "admin" and c.teacher_id != u.id):
            _tu_choi("lớp học")
        return c


def own_assignment(assignment_id: int, u: db.User) -> db.Assignment:
    """Đề mà người này được xem kết quả: giáo viên của lớp chứa đề đó, hoặc quản trị viên."""
    with db.SessionLocal() as s:
        a = s.get(db.Assignment, assignment_id)
        if not a:
            _tu_choi("đề được giao")
        if u.role != "admin":
            c = s.get(db.Classroom, a.class_id)
            if not c or c.teacher_id != u.id:
                _tu_choi("đề được giao")
        return a


def member_of_assignment(assignment_id: int, u: db.User) -> db.Assignment:
    """Học sinh chỉ làm được đề của lớp mình đã tham gia."""
    with db.SessionLocal() as s:
        a = s.get(db.Assignment, assignment_id)
        if not a:
            _tu_choi("đề được giao")
        if u.role != "admin":
            la_thanh_vien = s.query(db.ClassMember).filter_by(class_id=a.class_id, user_id=u.id).first()
            c = s.get(db.Classroom, a.class_id)
            if not la_thanh_vien and not (c and c.teacher_id == u.id):
                _tu_choi("đề được giao")
        return a


def own_plan(plan_id: int, u: db.User) -> db.StudyPlan:
    with db.SessionLocal() as s:
        p = s.get(db.StudyPlan, plan_id)
        if not p or (u.role != "admin" and p.user_id != u.id):
            _tu_choi("kế hoạch")
        return p


def own_attempt(attempt_id: int, u: db.User) -> db.Attempt:
    """Chỉ xem lại được bài làm của chính mình — 404 chứ không 403, như các chỗ khác."""
    with db.SessionLocal() as s:
        a = s.get(db.Attempt, attempt_id)
        if not a or (u.role != "admin" and a.user_id != u.id):
            _tu_choi("bài làm")
        return a


def own_quiz(quiz_id: int, u: db.User) -> db.Quiz:
    """Đề của chính mình, hoặc đề mẫu của một lớp mà mình có tham gia."""
    with db.SessionLocal() as s:
        q = s.get(db.Quiz, quiz_id)
        if not q:
            _tu_choi("đề")
        if u.role == "admin" or q.user_id == u.id:
            return q
        # đề do giáo viên soạn và giao cho lớp mà người này là thành viên
        lop = (s.query(db.Assignment.class_id).filter(db.Assignment.quiz_id == quiz_id).all())
        if lop and s.query(db.ClassMember).filter(
                db.ClassMember.user_id == u.id,
                db.ClassMember.class_id.in_([x[0] for x in lop])).first():
            return q
        _tu_choi("đề")


# ----------------------------- tiện ích JSON -----------------------------
def clean(v):
    """NaN / NaT -> None để JSON hợp lệ."""
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, (pd.Timestamp, datetime)):
        return v.isoformat()
    if hasattr(v, "item"):          # numpy scalar
        try:
            return clean(v.item())
        except Exception:  # noqa: BLE001
            return v
    return v


def records(df: pd.DataFrame) -> list[dict]:
    if df is None or getattr(df, "empty", True):
        return []
    return [{k: clean(v) for k, v in r.items()} for r in df.to_dict("records")]
