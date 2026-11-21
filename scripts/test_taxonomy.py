"""Kiểm tra các endpoint quản lý môn / chương / chủ đề.

AN TOÀN: chỉ thao tác trên một môn thử mang tên riêng, và chỉ xoá đúng những gì
nó vừa tạo. Bản trước dùng tên "Toán 8" trùng môn thật rồi xoá chương đầu tiên
của môn đó — làm mất 5 chủ đề thật.

  python -m scripts.test_taxonomy
"""
from fastapi.testclient import TestClient

from api.deps import make_token
from api.main import app
from app import db

MON_THU = "_Kiem thu mon 9"        # tên riêng, không trùng môn thật nào

db.init_db()
with db.SessionLocal() as s:
    admin = s.query(db.User).filter_by(role="admin").first()
    assert admin, "chưa có tài khoản admin"
    h = {"Authorization": "Bearer " + make_token(admin)["access_token"]}
    print("admin:", admin.username)
    assert not s.query(db.Subject).filter_by(name=MON_THU).first(), \
        f"còn sót môn thử {MON_THU} từ lần chạy trước — xoá thủ công rồi chạy lại"
    mon_that = {x.name for x in s.query(db.Subject)}

c = TestClient(app)

print("1) thêm môn        ", end="")
r = c.post("/admin/subjects", json={"name": MON_THU}, headers=h)
print(r.status_code, r.json())
assert r.status_code == 200, "không tạo được môn thử"
sid = r.json()["id"]

print("2) trùng tên bị chặn", c.post("/admin/subjects", json={"name": MON_THU.lower()},
                                    headers=h).status_code, "(mong đợi 400)")

print("3) thêm chương     ", end="")
r = c.post("/admin/chapters", json={"subject_id": sid, "name": "Chương thử"}, headers=h)
print(r.status_code, r.json())
cid = r.json()["id"]

print("4) thêm chủ đề     ", end="")
r = c.post("/admin/topics", json={"chapter_id": cid,
                                  "names": ["Chủ đề A", "Chủ đề B", "Chủ đề A"]}, headers=h)
print(r.status_code, r.json(), "(dòng trùng tự bỏ)")

print("5) cây môn học     ", end="")
t = [x for x in c.get("/admin/taxonomy", headers=h).json() if x["id"] == sid][0]
print(t["name"], "->", [(ch["name"], [tp["name"] for tp in ch["topics"]]) for ch in t["chapters"]])

print("6) /subjects thấy  ", end="")
print([x["name"] for x in c.get("/subjects").json()])

print("7) dọn dẹp         ", end="")
cua_minh = next(ch for ch in t["chapters"] if ch["id"] == cid)   # đúng chương vừa tạo
for tp in cua_minh["topics"]:
    c.delete(f"/admin/topics/{tp['id']}", headers=h)
print("chương:", c.delete(f"/admin/chapters/{cid}", headers=h).status_code,
      "· môn:", c.delete(f"/admin/subjects/{sid}", headers=h).status_code)

con_lai = {x["name"] for x in c.get("/subjects").json()}
print("8) còn lại         ", sorted(con_lai))
assert MON_THU not in con_lai, "môn thử chưa được xoá"
assert con_lai == mon_that, f"dữ liệu thật bị thay đổi: {con_lai ^ mon_that}"
print("\n✓ Các môn thật còn nguyên vẹn")
