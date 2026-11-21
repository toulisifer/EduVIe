"""Dựng lại từng lỗ hổng đã tìm thấy và chứng minh nó đã bị bịt.

Mỗi mục dưới đây tương ứng một đường tấn công đã CHẠY ĐƯỢC trước khi sửa.
Chạy:  .venv/bin/python -m scripts.test_chong_gian_lan     (không gọi AI)
"""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from api import chan_dap
from api.deps import make_token
from api.main import app
from app import classroom, db
from app.quiz import de_theo_ma, generate_quiz

cl = TestClient(app)
TEN = ["_gl_gv", "_gl_hs", "_gl_hs2"]
dat = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dat, sai
    if dk:
        dat += 1
        print(f"  dat  | {ten}")
    else:
        sai += 1
        print(f"  SAI  | {ten}" + (f"\n       | {chi_tiet}" if chi_tiet else ""))


def don():
    with db.SessionLocal() as s:
        for t in TEN:
            u = s.query(db.User).filter_by(username=t).first()
            if not u:
                continue
            for a in s.query(db.Attempt).filter_by(user_id=u.id):
                s.query(db.Answer).filter_by(attempt_id=a.id).delete()
                s.delete(a)
            s.query(db.AssignmentSubmission).filter_by(user_id=u.id).delete()
            for q in s.query(db.Quiz).filter_by(user_id=u.id):
                s.query(db.Question).filter_by(quiz_id=q.id).delete()
                s.delete(q)
            s.query(db.Answer).filter_by(user_id=u.id).delete()
            s.query(db.ClassMember).filter_by(user_id=u.id).delete()
            for c in s.query(db.Classroom).filter_by(teacher_id=u.id):
                for a in s.query(db.Assignment).filter_by(class_id=c.id):
                    s.query(db.AssignmentSubmission).filter_by(assignment_id=a.id).delete()
                    s.delete(a)
                s.query(db.ClassMember).filter_by(class_id=c.id).delete()
                s.delete(c)
            s.delete(u)
        s.commit()
    chan_dap.xoa_dau_vet()


def nguoi(ten, role):
    with db.SessionLocal() as s:
        u = db.User(username=ten, password_hash="x", role=role)
        s.add(u)
        s.commit()
        t = make_token(u)
        tok = t if isinstance(t, str) else t["access_token"]
        return u.id, {"Authorization": "Bearer " + tok}


def chu_de():
    from sqlalchemy import func
    with db.SessionLocal() as s:
        tid, _ = (s.query(db.BankQuestion.topic_id, func.count(db.BankQuestion.id))
                  .filter(db.BankQuestion.flagged.is_(False),
                          db.BankQuestion.difficulty == "medium")
                  .group_by(db.BankQuestion.topic_id)
                  .order_by(func.count(db.BankQuestion.id).desc()).first())
        t = s.get(db.Topic, tid)
        _ = t.path
        return t, t.chapter.subject_id


def main():
    db.init_db()
    don()
    gv, h_gv = nguoi(TEN[0], "teacher")
    hs, h_hs = nguoi(TEN[1], "user")
    hs2, h_hs2 = nguoi(TEN[2], "user")
    t, sub = chu_de()

    print("=" * 72)
    print(" CHONG GIAN LAN VA SIET LUONG BAI KIEM TRA")
    print("=" * 72)

    c = classroom.create_class(gv, "_gl_lop", sub)
    cl.post("/classes/join", json={"code": c.code}, headers=h_hs)
    cl.post("/classes/join", json={"code": c.code}, headers=h_hs2)
    a = classroom.create_assignment(c.id, gv, "_gl_kt", [t.id], "medium", 3,
                                    datetime.utcnow() + timedelta(days=7))
    with db.SessionLocal() as s:
        de_mau = s.get(db.Assignment, a.id).quiz_id
        ma_mau = s.get(db.Quiz, de_mau).code
        kiem("de mau duoc danh dau la de kiem tra",
             s.get(db.Quiz, de_mau).assignment_id == a.id)

    print("\n[1] Ba duong lay dap an truoc khi nop")
    with db.SessionLocal() as s:
        ids = [x.id for x in s.query(db.Question).filter_by(quiz_id=de_mau)]
    r = cl.post(f"/quiz/{de_mau}/submit", json={"answers": {str(i): 0 for i in ids}}, headers=h_hs)
    kiem("nop thang vao de mau cua GV -> chan", r.status_code == 409, str(r.status_code))
    kiem("khong he tra dap an", "review" not in r.json(), str(r.json())[:80])

    r2 = cl.post("/quiz/by-code", json={"code": ma_mau}, headers=h_hs)
    kiem("mo de kiem tra bang ma -> khong tim thay", r2.status_code == 404, str(r2.status_code))
    kiem("de_theo_ma() cung tu choi", de_theo_ma(ma_mau, hs) is None)

    st = cl.post(f"/assignments/{a.id}/start", headers=h_hs)
    qid = st.json()["quiz_id"]
    with db.SessionLocal() as s:
        kiem("ban sao cua hoc sinh cung duoc danh dau",
             s.get(db.Quiz, qid).assignment_id == a.id)
        ids3 = [x.id for x in s.query(db.Question).filter_by(quiz_id=qid)]
    r3 = cl.post(f"/quiz/{qid}/submit", json={"answers": {str(i): 0 for i in ids3}}, headers=h_hs)
    kiem("nop ban sao qua duong tu luyen -> chan", r3.status_code == 409, str(r3.status_code))
    kiem("khong he tra dap an (duong 3)", "review" not in r3.json())

    print("\n[2] Nop bai tap: dung mot lan, va giau dap an toi han")
    n1 = cl.post(f"/assignments/{a.id}/submit",
                 json={"quiz_id": qid, "answers": {str(i): 0 for i in ids3}}, headers=h_hs)
    kiem("nop lan dau -> duoc", n1.status_code == 200, str(n1.status_code))
    kiem("chua toi han thi KHONG tra dap an", "review" not in n1.json(), str(n1.json())[:90])
    kiem("co bao khi nao mo dap an", n1.json().get("dap_an_sau_han") is True)
    kiem("van tra diem cho hoc sinh biet", "score" in n1.json())
    n2 = cl.post(f"/assignments/{a.id}/submit",
                 json={"quiz_id": qid, "answers": {str(i): 1 for i in ids3}}, headers=h_hs)
    kiem("nop lan hai -> chan", n2.status_code == 409, str(n2.status_code))
    with db.SessionLocal() as s:
        kiem("chi co dung 1 ban ghi nop",
             s.query(db.AssignmentSubmission).filter_by(
                 assignment_id=a.id, user_id=hs).count() == 1)
    kiem("bam lam lai sau khi da nop -> chan",
         cl.post(f"/assignments/{a.id}/start", headers=h_hs).status_code == 409)

    print("\n[3] Het han thi khong lam, khong nop")
    b = classroom.create_assignment(c.id, gv, "_gl_hethan", [t.id], "medium", 3,
                                    datetime.utcnow() - timedelta(days=3))
    rb = cl.post(f"/assignments/{b.id}/start", headers=h_hs2)
    kiem("bat dau lam bai da het han -> chan", rb.status_code == 409, str(rb.status_code))
    chi_tiet = rb.json().get("detail", "")
    kiem("thong bao noi ro het han", "hạn" in chi_tiet, chi_tiet)

    print("\n[4] Tu luyen: mot de mot luot nop")
    with db.SessionLocal() as s:
        q = generate_quiz(hs2, sub, [s.merge(t)], "medium", 4)
        dap = {x.id: x.correct for x in s.query(db.Question).filter_by(quiz_id=q)}
    p1 = cl.post(f"/quiz/{q}/submit", json={"answers": {str(k): None for k in dap}}, headers=h_hs2)
    p2 = cl.post(f"/quiz/{q}/submit",
                 json={"answers": {str(k): v for k, v in dap.items()}}, headers=h_hs2)
    kiem("nop lan dau -> duoc", p1.status_code == 200, str(p1.status_code))
    kiem("nop lai cung de -> chan", p2.status_code == 409, str(p2.status_code))
    with db.SessionLocal() as s:
        kiem("chi sinh 1 attempt", s.query(db.Attempt).filter_by(quiz_id=q).count() == 1)
        n_ans = s.query(db.Answer).filter_by(user_id=hs2).count()
        kiem("chi ghi 4 Answer cho de 4 cau", n_ans == 4, str(n_ans))

    print("\n[5] Lua chon ngoai khoang 0-3")
    with db.SessionLocal() as s:
        q2 = generate_quiz(hs2, sub, [s.merge(t)], "medium", 3)
        ids5 = [x.id for x in s.query(db.Question).filter_by(quiz_id=q2)]
    r5 = cl.post(f"/quiz/{q2}/submit", json={"answers": {str(ids5[0]): 99}}, headers=h_hs2)
    kiem("chon 99 -> tu choi o lop kiem tra du lieu", r5.status_code == 422, str(r5.status_code))
    with db.SessionLocal() as s:
        kiem("khong co ban ghi selected=99 nao trong DB",
             s.query(db.Answer).filter(db.Answer.selected == 99).count() == 0)

    print("\n[6] Doi mat khau duoi duoc phien dang nhap cu")
    with db.SessionLocal() as s:
        u = s.query(db.User).filter_by(username=TEN[2]).first()
        u.password_hash = db._hash("matkhaucu")
        s.commit()
    chan_dap.xoa_dau_vet()
    tok_cu = cl.post("/auth/login", json={"username": TEN[2], "password": "matkhaucu"}).json()
    h_cu = {"Authorization": "Bearer " + tok_cu["access_token"]}
    kiem("token moi dung duoc", cl.get("/me", headers=h_cu).status_code == 200)
    cl.post("/auth/change-password", json={"old": "matkhaucu", "new": "matkhaumoi"}, headers=h_cu)
    r6 = cl.get("/me", headers=h_cu)
    kiem("sau khi doi mat khau, token cu bi tu choi", r6.status_code == 401, str(r6.status_code))
    moi = cl.post("/auth/login", json={"username": TEN[2], "password": "matkhaumoi"})
    kiem("dang nhap bang mat khau moi -> duoc", moi.status_code == 200, str(moi.status_code))

    print("\n[7] Chan do mat khau")
    chan_dap.xoa_dau_vet()
    ma = [cl.post("/auth/login", json={"username": TEN[2], "password": "sai"}).status_code
          for _ in range(12)]
    kiem("thu sai lien tuc -> bi chan 429", 429 in ma, str(ma))
    kiem("chan sau khoang 10 lan", ma.count(401) <= 10, f"{ma.count(401)} lan 401")
    chan_dap.xoa_dau_vet()

    don()
    print("\n" + "=" * 72)
    print(f" {dat}/{dat + sai} phep thu dat")
    print("=" * 72)
    raise SystemExit(0 if sai == 0 else 1)


if __name__ == "__main__":
    main()
