"""Trình diễn PHÂN QUYỀN cho người chấm: in code theo thứ tự thực thi rồi chạy thật.

    python -m scripts.show_auth --map            # bản đồ: endpoint nào cần quyền gì (64 endpoint)
    python -m scripts.show_auth --flow role      # học sinh gọi API quản trị -> bị chặn ở dòng nào
    python -m scripts.show_auth --flow owner     # giáo viên B xem lớp giáo viên A -> chặn bởi quyền sở hữu
    python -m scripts.show_auth --flow scope     # dữ liệu luôn lọc theo u.id lấy từ token

Không tốn request LLM nào.
"""
import argparse
import inspect
from collections import Counter
from pathlib import Path

from fastapi.routing import APIRoute

ROOT = Path(__file__).resolve().parent.parent
W = 78


def head(t):
    print("\n" + "=" * W); print(" " + t); print("=" * W)


def step(n, t):
    print(f"\n── Bước {n}: {t} " + "─" * max(0, W - 12 - len(t)))


def code(obj, grep: str | None = None):
    """In mã nguồn kèm file:dòng để người chấm mở đúng chỗ."""
    src, start = inspect.getsourcelines(obj)
    path = Path(inspect.getsourcefile(obj)).relative_to(ROOT)
    print(f"  📄 {path}:{start}  ({obj.__name__})")
    for i, line in enumerate(src):
        if grep and grep not in line:
            continue
        print(f"  {start + i:>4} │ {line.rstrip()}")


def quyen_cua(route: APIRoute) -> str:
    """Đọc cây dependency của endpoint để biết nó đòi quyền gì.

    FastAPI lồng dependency: api_xxx -> admin_user -> current_user -> HTTPBearer,
    nên phải duyệt đệ quy chứ không chỉ nhìn tầng đầu tiên.
    """
    tat_ca: set[str] = set()

    def duyet(dep):
        for d in dep.dependencies:
            ten = getattr(d.call, "__name__", None)
            if ten:
                tat_ca.add(ten)
            duyet(d)

    duyet(route.dependant)
    if "admin_user" in tat_ca:
        return "admin"
    if "teacher_user" in tat_ca:
        return "teacher"
    if "current_user" in tat_ca:
        return "đăng nhập"
    return "công khai"


def ban_do():
    from api.main import app
    head("BẢN ĐỒ PHÂN QUYỀN — mỗi endpoint đòi quyền gì")
    rows, dem = [], Counter()

    def thu_thap(routes):
        """Bản FastAPI này giữ router được include thành đối tượng lồng, phải duyệt vào trong."""
        for r in routes:
            if isinstance(r, APIRoute):
                if r.path.startswith("/static"):
                    continue
                q = quyen_cua(r)
                dem[q] += 1
                rows.append((q, ",".join(sorted(r.methods - {"HEAD", "OPTIONS"})), r.path))
            elif getattr(r, "original_router", None) is not None:
                thu_thap(r.original_router.routes)      # router được include (api/extra.py)
            elif hasattr(r, "routes"):
                thu_thap(r.routes)

    thu_thap(app.routes)

    for nhan in ("admin", "teacher", "đăng nhập", "công khai"):
        nhom = [x for x in rows if x[0] == nhan]
        if not nhom:
            continue
        print(f"\n▌ {nhan.upper()}  ({len(nhom)} endpoint)")
        for _, m, p in sorted(nhom, key=lambda x: x[2])[:24]:
            print(f"    {m:<7} {p}")
        if len(nhom) > 24:
            print(f"    … và {len(nhom) - 24} endpoint nữa")

    print("\n" + "-" * W)
    print("  Tổng:", sum(dem.values()), "endpoint  |  " +
          "  ".join(f"{k}: {v}" for k, v in dem.most_common()))
    print("  Quyền đọc từ chính dependency của endpoint, không phải gõ tay bảng này.")


def luong_role():
    from api import deps
    from fastapi.testclient import TestClient
    from api.main import app
    from app import db

    head("LUỒNG 1 — PHÂN QUYỀN THEO VAI TRÒ (học sinh gọi API quản trị)")

    step(1, "Vai trò lưu ở đâu")
    print("  📄 app/db.py  (bảng users)")
    print("     role = Column(String, default='user')   # user | teacher | admin")

    step(2, "Endpoint khai báo quyền ngay trên chữ ký hàm")
    from api.extra import api_admin_users
    code(api_admin_users)
    print("\n  → 'Depends(admin_user)' là toàn bộ phần phân quyền. Không có câu if nào")
    print("    trong thân hàm. Thiếu dòng này thì hàm không có đối tượng u để chạy.")

    step(3, "admin_user kiểm tra gì")
    code(deps.admin_user)
    code(deps.teacher_user)

    step(4, "Chạy thật: học sinh demo gọi /admin/users")
    db.init_db()
    with db.SessionLocal() as s:
        hs = s.query(db.User).filter_by(role="user").first()
        ad = s.query(db.User).filter_by(role="admin").first()
    c = TestClient(app)
    for u in (hs, ad):
        h = {"Authorization": "Bearer " + deps.make_token(u)["access_token"]}
        r = c.get("/admin/users", headers=h)
        d = r.json()
        ket = d.get("detail") if isinstance(d, dict) else f"trả về danh sách {len(d)} người dùng"
        print(f"  {u.username:<18} (role={u.role:<7}) → HTTP {r.status_code}  {ket}")


def luong_owner():
    from api import deps
    from fastapi.testclient import TestClient
    from api.main import app
    from app import db

    head("LUỒNG 2 — QUYỀN TRÊN TỪNG BẢN GHI (giáo viên B xem lớp của giáo viên A)")

    step(1, "Vì sao vai trò thôi chưa đủ")
    print("  Giáo viên A và giáo viên B CÙNG role='teacher'.")
    print("  Nếu chỉ kiểm tra vai trò, B đổi số trong URL là xem được lớp của A.")
    print("  Lỗi này tên IDOR — OWASP Top 10, mục Broken Access Control.")

    step(2, "Bảng classrooms có sẵn cột teacher_id để đối chiếu")
    print("  📄 app/db.py  (bảng classrooms)")
    print("     teacher_id = Column(Integer, ForeignKey('users.id'))")

    step(3, "Hàm kiểm tra quyền sở hữu")
    code(deps.own_class)

    step(4, "Endpoint gọi nó — đúng một dòng")
    from api.extra import api_class_overview
    code(api_class_overview)

    step(5, "Chạy thật: dựng 2 giáo viên, 2 lớp rồi thử chéo")
    db.init_db()
    with db.SessionLocal() as s:
        for t in ("_demo_gv_a", "_demo_gv_b"):
            cu = s.query(db.User).filter_by(username=t).first()
            if cu:
                s.query(db.Classroom).filter_by(teacher_id=cu.id).delete()
                s.delete(cu)
        s.commit()
        a = db.User(username="_demo_gv_a", password_hash="x", role="teacher")
        b = db.User(username="_demo_gv_b", password_hash="x", role="teacher")
        s.add_all([a, b]); s.commit()
        lop = db.Classroom(name="Lớp của GV A", code="_DEMO_A", teacher_id=a.id)
        s.add(lop); s.commit()
        ids = (a.id, b.id, lop.id)
        ha = {"Authorization": "Bearer " + deps.make_token(a)["access_token"]}
        hb = {"Authorization": "Bearer " + deps.make_token(b)["access_token"]}

    c = TestClient(app)
    print(f"  Lớp #{ids[2]} thuộc giáo viên A (id={ids[0]})\n")
    print(f"  GV A xem lớp của mình      → HTTP {c.get(f'/classes/{ids[2]}/overview', headers=ha).status_code}")
    rb = c.get(f"/classes/{ids[2]}/overview", headers=hb)
    print(f"  GV B xem lớp của GV A      → HTTP {rb.status_code}  {rb.json().get('detail', '')}")
    print("\n  Trả 404 chứ không phải 403: 403 sẽ xác nhận lớp đó có thật,")
    print("  giúp người tấn công dò ID. 404 không lộ gì.")

    with db.SessionLocal() as s:
        s.query(db.Classroom).filter_by(id=ids[2]).delete()
        s.query(db.User).filter(db.User.id.in_(ids[:2])).delete()
        s.commit()
    print("\n  (đã xoá dữ liệu demo)")


def luong_scope():
    from api import extra
    head("LUỒNG 3 — DỮ LIỆU LUÔN LỌC THEO NGƯỜI ĐANG ĐĂNG NHẬP")
    print("\n  Người dùng KHÔNG gửi user_id lên. Mọi truy vấn dùng u.id lấy từ token,")
    print("  nên không thể đổi tham số để đọc dữ liệu của người khác.\n")
    for fn in (extra.api_dashboard, extra.api_due, extra.api_scores):
        code(fn, grep="u.id")
    print("\n  Riêng xoá điểm còn đối chiếu chủ sở hữu trước khi xoá:")
    code(extra.api_delete_score)


def in_code():
    """Chỉ IN MÃ NGUỒN của 5 chỗ làm nên phân quyền — không chạy gì cả.

    Dùng khi người chấm muốn đọc code thật trong file chứ không xem kết quả chạy.
    """
    def doan(tieu_de: str, duong_dan: str, tu: int, den: int, ghi_chu: str = ""):
        print("\n" + "=" * W)
        print(f" {tieu_de}")
        print(f" 📄 {duong_dan}  (dòng {tu}–{den})")
        print("=" * W)
        lines = (ROOT / duong_dan).read_text(encoding="utf-8").splitlines()
        for i in range(tu - 1, min(den, len(lines))):
            print(f"  {i + 1:>4} │ {lines[i]}")
        if ghi_chu:
            print("\n  → " + ghi_chu.replace("\n", "\n    "))

    head("MÃ NGUỒN PHÂN QUYỀN — 5 chỗ, 3 tệp")

    import re
    db_src = (ROOT / "app/db.py").read_text(encoding="utf-8").splitlines()
    dong_role = next(i for i, l in enumerate(db_src, 1) if re.search(r'role\s*=\s*Column', l))
    doan("1. VAI TRÒ LƯU Ở ĐÂU", "app/db.py", dong_role - 1, dong_role + 1,
         "Một cột duy nhất trong bảng users. Đây là mô hình RBAC:\n"
         "quyền gắn vào vai trò, vai trò gắn vào tài khoản.")

    doan("2. HAI HÀM KIỂM TRA VAI TRÒ", "api/deps.py", 39, 48,
         "Dòng 39: Depends(current_user) chạy trước, lấy người dùng từ token.\n"
         "Dòng 40: so sánh vai trò, sai thì 403 (biết anh là ai nhưng không đủ quyền).\n"
         "Dòng 46: admin nằm trong danh sách -> quản trị làm được việc của giáo viên.")

    doan("3. ENDPOINT KHAI BÁO QUYỀN NGAY TRÊN CHỮ KÝ HÀM", "api/extra.py", 381, 384,
         "Phân quyền ở dòng 382. Thân hàm từ 383 trở đi KHÔNG có câu if kiểm tra quyền nào.\n"
         "Không thể quên: bỏ Depends đi thì biến u không tồn tại, hàm chạy là lỗi.")

    doan("4. QUYỀN TRÊN TỪNG BẢN GHI (chống IDOR)", "api/deps.py", 51, 67,
         "Dòng 51–54 nêu vấn đề: cùng vai trò teacher nhưng khác chủ sở hữu.\n"
         "Dòng 65 là trái tim: đối chiếu classrooms.teacher_id với người đang gọi.\n"
         "Dòng 57–58 trả 404 thay vì 403 để không tiết lộ bản ghi đó có thật.")

    doan("5. NƠI GỌI: HAI TẦNG, HAI DÒNG", "api/extra.py", 238, 241,
         "Dòng 239 kiểm tra VAI TRÒ, dòng 240 kiểm tra QUYỀN SỞ HỮU.")

    print("\n" + "=" * W)
    print(" Tóm lại: toàn bộ phân quyền nằm trong api/deps.py (dòng 39–119).")
    print(" Các tệp khác chỉ gọi lại, mỗi endpoint một dòng.")
    print("=" * W)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--code", action="store_true", help="IN MÃ NGUỒN 5 chỗ làm nên phân quyền (không chạy gì)")
    ap.add_argument("--map", action="store_true", help="bản đồ quyền của toàn bộ endpoint")
    ap.add_argument("--flow", choices=["role", "owner", "scope"], help="diễn giải một luồng")
    a = ap.parse_args()
    if a.map:
        ban_do()
    elif a.code:
        in_code()
    elif a.flow == "role":
        luong_role()
    elif a.flow == "owner":
        luong_owner()
    elif a.flow == "scope":
        luong_scope()
    else:
        ap.print_help()
