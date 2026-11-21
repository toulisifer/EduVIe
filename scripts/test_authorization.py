"""Kiểm thử phân quyền: vai trò và quyền trên từng bản ghi (chống IDOR).

Dựng dữ liệu thử riêng (2 giáo viên, 2 học sinh, 2 lớp), chạy 12 phép thử rồi xoá sạch.
  python -m scripts.test_authorization
"""
from fastapi.testclient import TestClient

from api.deps import make_token
from api.main import app
from app import db

c = TestClient(app)
ket_qua: list[tuple[bool, str]] = []


def thu(mo_ta: str, response, mong_doi: int):
    ok = response.status_code == mong_doi
    ket_qua.append((ok, f"{mo_ta}: nhận {response.status_code}, mong đợi {mong_doi}"))
    print(f"  {'✓' if ok else '✗'} {mo_ta}  ->  {response.status_code} (mong đợi {mong_doi})")


def auth(u):
    return {"Authorization": "Bearer " + make_token(u)["access_token"]}


db.init_db()
TEN = ["_kt_gv_a", "_kt_gv_b", "_kt_hs_a", "_kt_hs_b"]

with db.SessionLocal() as s:
    for t in TEN:                                  # dọn tàn dư lần chạy trước
        cu = s.query(db.User).filter_by(username=t).first()
        if cu:
            for cl in s.query(db.Classroom).filter_by(teacher_id=cu.id):
                s.query(db.ClassMember).filter_by(class_id=cl.id).delete()
                s.query(db.Assignment).filter_by(class_id=cl.id).delete()
                s.delete(cl)
            s.query(db.ClassMember).filter_by(user_id=cu.id).delete()
            s.query(db.StudyPlan).filter_by(user_id=cu.id).delete()
            s.delete(cu)
    s.commit()

    gv_a, gv_b, hs_a, hs_b = (db.User(username=t, password_hash="x",
                                      role="teacher" if "gv" in t else "user") for t in TEN)
    s.add_all([gv_a, gv_b, hs_a, hs_b]); s.commit()

    lop_a = db.Classroom(name="Lớp của GV A", code="_KT_A", teacher_id=gv_a.id)
    lop_b = db.Classroom(name="Lớp của GV B", code="_KT_B", teacher_id=gv_b.id)
    s.add_all([lop_a, lop_b]); s.commit()
    s.add(db.ClassMember(class_id=lop_a.id, user_id=hs_a.id))     # hs_a thuộc lớp A

    quiz_a = db.Quiz(user_id=hs_a.id, subject_id=1)
    s.add(quiz_a); s.commit()
    topic = s.query(db.Topic).first()            # đề phải có câu hỏi thì mới tải lại được
    s.add(db.Question(quiz_id=quiz_a.id, topic_id=topic.id, content="1 + 1 = ?",
                      options=["1", "2", "3", "4"], correct=1, difficulty="easy"))
    s.commit()
    de_a = db.Assignment(class_id=lop_a.id, quiz_id=quiz_a.id, title="Đề lớp A")
    ke_hoach_a = db.StudyPlan(user_id=hs_a.id, goal="kiểm thử")
    s.add_all([de_a, ke_hoach_a]); s.commit()

    ids = dict(gv_a=gv_a.id, gv_b=gv_b.id, hs_a=hs_a.id, hs_b=hs_b.id, lop_a=lop_a.id,
               lop_b=lop_b.id, de_a=de_a.id, quiz_a=quiz_a.id, plan_a=ke_hoach_a.id)
    admin = s.query(db.User).filter_by(role="admin").first()
    H = {k: auth(v) for k, v in
         [("gv_a", gv_a), ("gv_b", gv_b), ("hs_a", hs_a), ("hs_b", hs_b), ("admin", admin)]}

print("\n--- 1. Phân quyền theo vai trò ---")
thu("học sinh gọi API quản trị", c.get("/admin/users", headers=H["hs_a"]), 403)
thu("giáo viên gọi API quản trị", c.get("/admin/users", headers=H["gv_a"]), 403)
thu("học sinh tạo lớp (cần vai trò giáo viên)", c.post("/classes", json={"name": "x"}, headers=H["hs_a"]), 403)
thu("quản trị viên gọi API quản trị", c.get("/admin/users", headers=H["admin"]), 200)

print("\n--- 2. Không có token / token sai ---")
thu("không gửi token", c.get("/documents"), 401)
thu("token giả mạo", c.get("/documents", headers={"Authorization": "Bearer abc.def.ghi"}), 401)

print("\n--- 3. Quyền trên từng bản ghi (IDOR) ---")
thu("GV B xem lớp của GV A", c.get(f"/classes/{ids['lop_a']}/overview", headers=H["gv_b"]), 404)
thu("GV A xem lớp của chính mình", c.get(f"/classes/{ids['lop_a']}/overview", headers=H["gv_a"]), 200)
thu("GV B giao đề vào lớp của GV A",
    c.post(f"/classes/{ids['lop_a']}/assignments",
           json={"title": "x", "topic_ids": [1], "n": 3}, headers=H["gv_b"]), 404)
thu("GV B xem kết quả đề của lớp A", c.get(f"/assignments/{ids['de_a']}/results", headers=H["gv_b"]), 404)
thu("HS B (ngoài lớp) làm đề của lớp A",
    c.post(f"/assignments/{ids['de_a']}/start", headers=H["hs_b"]), 404)
thu("HS B xem kế hoạch của HS A", c.get(f"/plan2/{ids['plan_a']}/outcome", headers=H["hs_b"]), 404)
thu("HS B mở đề của HS A", c.get(f"/quiz/{ids['quiz_a']}", headers=H["hs_b"]), 404)
thu("HS A mở đề của chính mình", c.get(f"/quiz/{ids['quiz_a']}", headers=H["hs_a"]), 200)

with db.SessionLocal() as s:                       # dọn sạch dữ liệu thử
    s.query(db.Assignment).filter_by(id=ids["de_a"]).delete()
    s.query(db.StudyPlan).filter_by(id=ids["plan_a"]).delete()
    s.query(db.Question).filter_by(quiz_id=ids["quiz_a"]).delete()
    s.query(db.Quiz).filter_by(id=ids["quiz_a"]).delete()
    s.query(db.ClassMember).filter(db.ClassMember.class_id.in_([ids["lop_a"], ids["lop_b"]])).delete()
    s.query(db.Classroom).filter(db.Classroom.id.in_([ids["lop_a"], ids["lop_b"]])).delete()
    s.query(db.User).filter(db.User.username.in_(TEN)).delete()
    s.commit()

sai = [m for ok, m in ket_qua if not ok]
print(f"\n{len(ket_qua) - len(sai)}/{len(ket_qua)} phép thử đạt")
for m in sai:
    print("  SAI:", m)
raise SystemExit(1 if sai else 0)
