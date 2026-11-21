"""Đóng gói mã nguồn thành .zip để gửi cho người khác.

LOẠI BỎ: .env (khoá API), data/app.db (tài khoản và điểm của người dùng thật),
         data/uploads + data/ocr_cache (sách giáo khoa có bản quyền),
         data/chroma (vector của chính sách đó), .git (lịch sử có chứa sách), .venv, log.
GIỮ LẠI: toàn bộ mã nguồn, giao diện, danh mục môn học, đồ thị kiến thức, bộ câu hỏi đánh giá.

  python -m scripts.dong_goi                    # ra ~/VuongEdu_source.zip
  python -m scripts.dong_goi /duong/dan/ten.zip
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Thư mục bỏ qua hoàn toàn (so theo đường dẫn tương đối, tính cả thư mục con)
THU_MUC_BO = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules",
    "data/uploads", "data/ocr_cache", "data/chroma",
}
# Tệp bỏ qua
TEP_BO = {".env", "data/app.db", "learn/memory.json", "data/quota_exhausted.json"}
DUOI_BO = {".pyc", ".pyo", ".db", ".sqlite", ".sqlite3"}


def bi_loai(rel: Path) -> bool:
    s = rel.as_posix()
    if s in TEP_BO or rel.suffix in DUOI_BO:
        return True
    if s.startswith("logs_") and s.endswith(".txt"):
        return True
    if s.startswith("eval/results_"):
        return True
    for phan in THU_MUC_BO:
        if s == phan or s.startswith(phan + "/"):
            return True
    return False


def main():
    dich = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "VuongEdu_source.zip"
    dich.unlink(missing_ok=True)

    n, tong = 0, 0
    with zipfile.ZipFile(dich, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in sorted(ROOT.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(ROOT)
            if bi_loai(rel):
                continue
            z.write(f, Path("ai-learning-assistant") / rel)
            n += 1
            tong += f.stat().st_size

    print(f"Đã tạo: {dich}")
    print(f"{n} tệp, nguồn {tong / 1024 / 1024:.1f} MB -> nén còn {dich.stat().st_size / 1024 / 1024:.1f} MB\n")

    print("Kiểm tra không lọt thứ nhạy cảm:")
    with zipfile.ZipFile(dich) as z:
        ten = z.namelist()
    # .env.example là tệp mẫu, chỉ chứa chỗ trống — phải có trong gói, nên không tính là lọt
    kiem_tra = [(".env (khoá API)", lambda t: t.endswith("/.env")),
                ("CSDL người dùng", lambda t: "app.db" in t),
                ("sách đã OCR", lambda t: "ocr_cache" in t),
                ("PDF sách", lambda t: t.endswith(".pdf")),
                ("vector của sách", lambda t: "chroma" in t),
                ("lịch sử git", lambda t: "/.git/" in t)]
    for nhan, khop in kiem_tra:
        dinh = [t for t in ten if khop(t)]
        print(f"  {nhan:<22} {'sạch' if not dinh else 'CÒN ' + str(len(dinh)) + ' tệp — DỪNG LẠI: ' + dinh[0]}")

    print("\nCòn lại trong gói, theo thư mục:")
    dem: dict[str, int] = {}
    for t in ten:
        p = t.split("/")
        khoa = p[1] if len(p) > 2 else "(gốc)"
        dem[khoa] = dem.get(khoa, 0) + 1
    for k, v in sorted(dem.items(), key=lambda x: -x[1]):
        print(f"  {k:<14} {v} tệp")


if __name__ == "__main__":
    main()
