"""Kiểm tra upload chạy nền: POST trả 202 ngay, trạng thái chuyển sang ready."""
import time

from fastapi.testclient import TestClient

from api.deps import make_token
from api.main import app
from app import db

db.init_db()
with db.SessionLocal() as s:
    admin = s.query(db.User).filter_by(role="admin").first()
    h = {"Authorization": "Bearer " + make_token(admin)["access_token"]}
    sub = s.query(db.Subject).first()
    print("admin:", admin.username, "| môn:", sub.name)

c = TestClient(app)
txt = ("Hằng đẳng thức đáng nhớ: bình phương của một tổng bằng bình phương số thứ nhất "
       "cộng hai lần tích hai số cộng bình phương số thứ hai. " * 6).encode()

t0 = time.time()
r = c.post("/documents", files={"file": ("kiem_tra_nen.txt", txt, "text/plain")},
           data={"subject_id": sub.id}, headers=h)
print(f"POST trả về sau {time.time() - t0:.2f}s:", r.status_code, r.json())
assert r.status_code == 202, "phải trả 202 ngay, không chờ xử lý"
doc_id = r.json()["id"]

for _ in range(40):
    d = c.get(f"/documents/{doc_id}", headers=h).json()
    print("   ", d["status"], "|", d["progress"] or "—")
    if d["status"] in ("ready", "failed"):
        break
    time.sleep(1)

print("kết quả:", d["status"], d.get("error", ""), "| đoạn:", d["n_chunks"])
print("dọn dẹp:", c.delete(f"/documents/{doc_id}", headers=h).status_code)
