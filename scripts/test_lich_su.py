"""Lịch sử làm đề: mã đề, điểm, ngày làm — và không ai xem được bài của người khác.

Chạy:  .venv/bin/python -m scripts.test_lich_su
Không gọi AI. Dữ liệu thử được xoá sau khi chạy.
"""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from api.deps import make_token
from api.main import app
from app import db
from app.quiz import de_theo_ma, generate_quiz, lich_su, submit_attempt, xem_lai

TEN = ["_ls_an", "_ls_binh"]
dat = sai = 0
cl = TestClient(app)


def kiem(ten, dieu_kien, chi_tiet=""):
    global dat, sai
    if dieu_kien:
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
            for q in s.query(db.Quiz).filter_by(user_id=u.id):
                s.query(db.Question).filter_by(quiz_id=q.id).delete()
                s.delete(q)
            s.query(db.Answer).filter_by(user_id=u.id).delete()
            s.delete(u)
        s.commit()


def nguoi(ten):
    with db.SessionLocal() as s:
        u = db.User(username=ten, password_hash="x", role="user")
        s.add(u); s.commit()
        t = make_token(u)
        return u.id, (t if isinstance(t, str) else t.get("access_token"))


def main():
    db.init_db()
    don()
    an, tok_an = nguoi(TEN[0])
    binh, tok_binh = nguoi(TEN[1])
    dau_an = {"Authorization": f"Bearer {tok_an}"}
    dau_binh = {"Authorization": f"Bearer {tok_binh}"}

    with db.SessionLocal() as s:
        from sqlalchemy import func
        tid, _ = (s.query(db.BankQuestion.topic_id, func.count(db.BankQuestion.id))
                  .filter(db.BankQuestion.flagged.is_(False),
                          db.BankQuestion.difficulty == "medium")
                  .group_by(db.BankQuestion.topic_id)
                  .order_by(func.count(db.BankQuestion.id).desc()).first())
        t = s.get(db.Topic, tid)
        _ = t.path
        sub = t.chapter.subject_id

    print("=" * 70)
    print(" LỊCH SỬ LÀM ĐỀ")
    print("=" * 70)

    # ---------------------------------------------------------------- 1
    print("\n[1] Chưa làm bài nào thì lịch sử rỗng, không lỗi")
    r = cl.get("/quiz/history", headers=dau_an)
    kiem("trả 200", r.status_code == 200, str(r.status_code))
    kiem("danh sách rỗng", r.json() == [], str(r.json())[:80])

    # ---------------------------------------------------------------- 2
    print("\n[2] Làm hai đề thì lịch sử ghi đủ hai, mới nhất lên đầu")
    with db.SessionLocal() as s:
        tt = s.merge(t)
        q1 = generate_quiz(an, sub, [tt], "medium", 4)
        q2 = generate_quiz(an, sub, [tt], "medium", 4)
    with db.SessionLocal() as s:
        ma1 = s.get(db.Quiz, q1).code
        cau1 = [q.id for q in s.query(db.Question).filter_by(quiz_id=q1).order_by(db.Question.id)]
        cau2 = [q.id for q in s.query(db.Question).filter_by(quiz_id=q2).order_by(db.Question.id)]
        dap1 = {q.id: q.correct for q in s.query(db.Question).filter_by(quiz_id=q1)}

    submit_attempt(q1, an, {i: dap1[i] for i in cau1})          # đúng hết -> 10
    submit_attempt(q2, an, {i: None for i in cau2})             # bỏ trống hết -> 0
    # cho hai lần cách nhau để kiểm thứ tự
    with db.SessionLocal() as s:
        xs = s.query(db.Attempt).filter_by(user_id=an).order_by(db.Attempt.id).all()
        xs[0].submitted_at = datetime.utcnow() - timedelta(hours=2)
        s.commit()

    ds = cl.get("/quiz/history", headers=dau_an).json()
    kiem("ghi đủ 2 lần làm", len(ds) == 2, f"có {len(ds)}")
    kiem("mới nhất lên đầu", ds[0]["score"] == 0.0 and ds[1]["score"] == 10.0,
         str([x["score"] for x in ds]))
    kiem("điểm đúng hết = 10", ds[1]["score"] == 10.0, str(ds[1]["score"]))
    kiem("điểm bỏ trống hết = 0", ds[0]["score"] == 0.0, str(ds[0]["score"]))
    kiem("có mã đề", bool(ds[1]["code"]), str(ds[1]["code"]))
    kiem("hai lần mang hai mã khác nhau", ds[0]["code"] != ds[1]["code"])
    kiem("đếm đúng số câu", ds[1]["n"] == 4 and ds[1]["n_correct"] == 4,
         f"{ds[1]['n_correct']}/{ds[1]['n']}")
    kiem("ghi nguồn là tự luyện", ds[0]["assignment"] is None)
    kiem("có ngày làm", bool(ds[0]["submitted_at"]))

    # ---------------------------------------------------------------- 3
    print("\n[3] Xem lại một lần làm bài")
    aid = ds[1]["attempt_id"]
    r = cl.get(f"/quiz/history/{aid}", headers=dau_an)
    kiem("trả 200", r.status_code == 200, str(r.status_code))
    d = r.json()
    kiem("đủ số câu", len(d["questions"]) == 4, str(len(d["questions"])))
    kiem("câu nào cũng ghi mình chọn gì",
         all(q["selected"] is not None for q in d["questions"]))
    kiem("câu nào cũng ghi đáp án đúng",
         all(isinstance(q["correct"], int) for q in d["questions"]))
    kiem("đánh dấu đúng/sai khớp với điểm",
         sum(1 for q in d["questions"] if q["is_correct"]) == d["n_correct"])

    # ---------------------------------------------------------------- 4
    print("\n[4] Không xem được bài làm của người khác")
    r = cl.get(f"/quiz/history/{aid}", headers=dau_binh)
    kiem("Bình mở bài của An -> 404", r.status_code == 404, str(r.status_code))
    kiem("404 chứ không 403 (không lộ là có tồn tại)", r.status_code != 403)
    r = cl.get("/quiz/history", headers=dau_binh)
    kiem("lịch sử của Bình vẫn rỗng", r.json() == [], str(r.json())[:80])
    r = cl.get(f"/quiz/history/{aid}")
    kiem("chưa đăng nhập -> 401", r.status_code == 401, str(r.status_code))

    # ---------------------------------------------------------------- 5
    print("\n[5] Làm lại đúng đề cũ bằng mã trong lịch sử")
    q3 = de_theo_ma(ma1, binh)
    with db.SessionLocal() as s:
        c_moi = [x.content for x in s.query(db.Question).filter_by(quiz_id=q3).order_by(db.Question.id)]
        c_cu = [x.content for x in s.query(db.Question).filter_by(quiz_id=q1).order_by(db.Question.id)]
    kiem("mã trong lịch sử mở ra đúng đề đó", c_moi == c_cu)
    dap3 = {}
    with db.SessionLocal() as s:
        for x in s.query(db.Question).filter_by(quiz_id=q3):
            dap3[x.id] = x.correct
    ids = sorted(dap3)
    submit_attempt(q3, binh, {i: (dap3[i] if k < 2 else None) for k, i in enumerate(ids)})
    lb = lich_su(binh)
    kiem("Bình có 1 lần làm", len(lb) == 1, str(len(lb)))
    kiem("đúng 2/4 -> 5 điểm", lb[0]["score"] == 5.0, str(lb[0]["score"]))
    kiem("cùng mã đề với An", lb[0]["code"] == ma1, f"{lb[0]['code']} vs {ma1}")
    kiem("điểm hai người tách biệt", lich_su(an)[1]["score"] == 10.0)

    # ---------------------------------------------------------------- 6
    print("\n[6] Giới hạn số dòng")
    kiem("limit cắt đúng", len(cl.get("/quiz/history?limit=1", headers=dau_an).json()) == 1)
    kiem("xem lại bài không tồn tại -> 404",
         cl.get("/quiz/history/99999999", headers=dau_an).status_code == 404)
    kiem("xem_lai() của id lạ trả None", xem_lai(99999999) is None)

    don()
    print("\n" + "=" * 70)
    print(f" {dat}/{dat + sai} phép thử đạt")
    print("=" * 70)
    raise SystemExit(0 if sai == 0 else 1)


if __name__ == "__main__":
    main()
