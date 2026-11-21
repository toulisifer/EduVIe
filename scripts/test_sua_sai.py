"""Luyện lại câu sai: lấy đúng câu đang sai, và tự rút khi người học sửa được.

Chạy:  .venv/bin/python -m scripts.test_sua_sai      (không gọi AI)
"""
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func

from api.deps import make_token
from api.main import app
from app import db, sua_sai
from app.quiz import load_quiz, submit_attempt

cl = TestClient(app)
TEN = ["_ss_an", "_ss_binh"]
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
            for q in s.query(db.Quiz).filter_by(user_id=u.id):
                s.query(db.Question).filter_by(quiz_id=q.id).delete()
                s.delete(q)
            s.query(db.Answer).filter_by(user_id=u.id).delete()
            s.delete(u)
        s.commit()


def nguoi(ten):
    with db.SessionLocal() as s:
        u = db.User(username=ten, password_hash="x", role="user")
        s.add(u)
        s.commit()
        t = make_token(u)
        tok = t if isinstance(t, str) else t["access_token"]
        return u.id, {"Authorization": "Bearer " + tok}


def de_tu_kho(uid, cau):
    """Dựng một đề thẳng từ danh sách BankQuestion, trả (quiz_id, [question_id])."""
    with db.SessionLocal() as s:
        q = db.Quiz(user_id=uid, subject_id=None, difficulty="medium", code="")
        s.add(q)
        s.flush()
        ids = []
        for c in cau:
            x = db.Question(quiz_id=q.id, topic_id=c.topic_id, bank_id=c.id,
                            difficulty=c.difficulty, content=c.content, options=c.options,
                            correct=c.correct, explanation=c.explanation)
            s.add(x)
            s.flush()
            ids.append(x.id)
        s.commit()
        return q.id, ids


def main():
    db.init_db()
    don()
    an, h_an = nguoi(TEN[0])
    binh, h_binh = nguoi(TEN[1])

    with db.SessionLocal() as s:
        tid, _ = (s.query(db.BankQuestion.topic_id, func.count(db.BankQuestion.id))
                  .filter(db.BankQuestion.flagged.is_(False))
                  .group_by(db.BankQuestion.topic_id)
                  .order_by(func.count(db.BankQuestion.id).desc()).first())
        kho = (s.query(db.BankQuestion).filter_by(topic_id=tid, flagged=False)
               .order_by(db.BankQuestion.id).limit(6).all())
        for c in kho:
            _ = c.topic.name
        dap = {c.id: c.correct for c in kho}

    print("=" * 72)
    print(" LUYEN LAI CAU SAI")
    print("=" * 72)

    print("\n[1] Chua lam gi thi danh sach rong, khong loi")
    r = cl.get("/quiz/mistakes", headers=h_an)
    kiem("tra 200", r.status_code == 200, str(r.status_code))
    kiem("tong = 0", r.json()["tong"] == 0, str(r.json())[:80])
    kiem("dung de luyen lai -> 404",
         cl.post("/quiz/mistakes/practice", json={"n": 5}, headers=h_an).status_code == 404)

    print("\n[2] Lam sai 3 cau, dung 3 cau")
    qid, qs = de_tu_kho(an, kho)
    ds = load_quiz(qid)
    chon = {}
    sai_bank, dung_bank = [], []
    for i, q in enumerate(ds):
        if i < 3:
            chon[q.id] = (q.correct + 1) % 4          # cố tình sai
            sai_bank.append(q.bank_id)
        else:
            chon[q.id] = q.correct
            dung_bank.append(q.bank_id)
    submit_attempt(qid, an, chon)
    d = cl.get("/quiz/mistakes", headers=h_an).json()
    kiem("dem dung 3 cau sai", d["tong"] == 3, str(d["tong"]))
    got = {c["bank_id"] for c in d["cau"]}
    kiem("dung 3 cau da lam sai", got == set(sai_bank), f"{sorted(got)} vs {sorted(sai_bank)}")
    kiem("cau lam dung khong bi tinh", not (got & set(dung_bank)))
    kiem("co gom theo chu de", bool(d["theo_chu_de"]), str(d["theo_chu_de"])[:80])

    print("\n[3] De luyen lai gom dung nhung cau do")
    r2 = cl.post("/quiz/mistakes/practice", json={"n": 10}, headers=h_an)
    kiem("tra 200", r2.status_code == 200, str(r2.status_code))
    q2 = r2.json()
    kiem("de co dung 3 cau", len(q2["questions"]) == 3, str(len(q2["questions"])))
    kiem("khong lo dap an", "correct" not in str(q2["questions"]))
    kiem("de luyen lai KHONG co ma", not q2.get("code"), str(q2.get("code")))
    with db.SessionLocal() as s:
        z = s.get(db.Quiz, q2["quiz_id"])
        kiem("duoc ghi nhan la de sua sai", z.loai == sua_sai.LOAI, str(z.loai))
        bank2 = {x.bank_id for x in s.query(db.Question).filter_by(quiz_id=q2["quiz_id"])}
    kiem("dung bo cau dang sai", bank2 == set(sai_bank), f"{sorted(bank2)}")

    print("\n[4] Nguoi khac khong thay cau sai cua minh")
    kiem("Binh chua lam gi -> rong", cl.get("/quiz/mistakes", headers=h_binh).json()["tong"] == 0)
    kiem("chua dang nhap -> 401", cl.get("/quiz/mistakes").status_code == 401)

    print("\n[5] Sua duoc thi cau do rut khoi danh sach")
    ds2 = load_quiz(q2["quiz_id"])
    # lam dung 2 trong 3 cau
    chon2, van_sai = {}, None
    for i, q in enumerate(ds2):
        if i < 2:
            chon2[q.id] = q.correct
        else:
            chon2[q.id] = (q.correct + 1) % 4
            van_sai = q.bank_id
    submit_attempt(q2["quiz_id"], an, chon2)
    d3 = cl.get("/quiz/mistakes", headers=h_an).json()
    kiem("con dung 1 cau", d3["tong"] == 1, str(d3["tong"]))
    kiem("la cau van con lam sai", d3["cau"][0]["bank_id"] == van_sai,
         f"{d3['cau'][0]['bank_id']} vs {van_sai}")

    print("\n[6] Dung roi lai sai thi quay vao danh sach")
    dung_lai = dung_bank[0]
    with db.SessionLocal() as s:
        c = s.get(db.BankQuestion, dung_lai)
        qz = db.Quiz(user_id=an, subject_id=None, difficulty="medium", code="")
        s.add(qz); s.flush()
        x = db.Question(quiz_id=qz.id, topic_id=c.topic_id, bank_id=c.id, difficulty=c.difficulty,
                        content=c.content, options=c.options, correct=c.correct, explanation="")
        s.add(x); s.flush()
        s.commit()
        qz_id, x_id, dung_dap = qz.id, x.id, c.correct
    submit_attempt(qz_id, an, {x_id: (dung_dap + 1) % 4})
    d4 = cl.get("/quiz/mistakes", headers=h_an).json()
    kiem("cau tung dung nay quay lai danh sach",
         dung_lai in {c["bank_id"] for c in d4["cau"]}, str(d4["tong"]))

    print("\n[7] Cau bi bao sai thi khong bat luyen lai")
    with db.SessionLocal() as s:
        s.get(db.BankQuestion, van_sai).flagged = True
        s.commit()
    d5 = cl.get("/quiz/mistakes", headers=h_an).json()
    kiem("cau flagged bi loai", van_sai not in {c["bank_id"] for c in d5["cau"]}, str(d5["tong"]))
    with db.SessionLocal() as s:
        s.get(db.BankQuestion, van_sai).flagged = False
        s.commit()

    print("\n[8] Gioi han so cau")
    r8 = cl.post("/quiz/mistakes/practice", json={"n": 1}, headers=h_an)
    kiem("xin 1 cau -> de 1 cau", len(r8.json()["questions"]) == 1, str(r8.status_code))
    kiem("xin 999 cau -> tu choi",
         cl.post("/quiz/mistakes/practice", json={"n": 999}, headers=h_an).status_code == 422)

    print("\n[9] Hien trong lich su voi nhan rieng")
    ls = cl.get("/quiz/history", headers=h_an).json()
    kiem("co dong ghi loai sua_sai", any(x.get("loai") == sua_sai.LOAI for x in ls),
         str([x.get("loai") for x in ls]))

    don()
    print("\n" + "=" * 72)
    print(f" {dat}/{dat + sai} phep thu dat")
    print("=" * 72)
    raise SystemExit(0 if sai == 0 else 1)


if __name__ == "__main__":
    main()
