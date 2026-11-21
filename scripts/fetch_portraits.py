"""Tải ảnh chân dung cho khung animation ở trang chủ, từ Wikimedia Commons.

Khung animation trước đây dùng chung ảnh với thẻ môn học nên nhìn bị lặp.
Script lấy một ảnh KHÁC cho mỗi nhà bác học, đều là ảnh đã hết hạn bản quyền
(public domain) hoặc giấy phép tự do trên Commons.

  python -m scripts.fetch_portraits            # tải những ảnh còn thiếu
  python -m scripts.fetch_portraits --force    # tải lại tất cả
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent.parent / "web" / "static" / "images" / "portraits"
API = "https://api.wikimedia.org/core/v1/commons/file/File%3A"
UA = "VuongEdu-student-project/1.0 (educational; contact: vuongphan090106@gmail.com)"

# tên tệp trong dự án -> tên tệp trên Wikimedia Commons
PORTRAITS = {
    "curie":       "Marie_Curie_c._1920s.jpg",
    "darwin":      "Charles_Darwin_seated_crop.jpg",
    "tolstoy":     "L.N.Tolstoy_Prokudin-Gorsky.jpg",
    "turing":      "Alan_Turing_Aged_16.jpg",
    "shakespeare": "Shakespeare.jpg",
    "herodotus":   "Herodotos_Met_91.8.jpg",
    "humboldt":    "Alexander_von_Humboldt-selfportrait.jpg",
    "socrates":    "Socrates_Louvre.jpg",
    "tesla":       "N.Tesla.JPG",
    "hippocrates": "Hippocrates_rubens.jpg",
    "ho_chi_minh": "Ho_Chi_Minh_-_1946_Portrait.jpg",
}


def fetch(commons_name: str) -> tuple[bytes, str, str]:
    """Trả về (dữ liệu ảnh, đuôi tệp, đường dẫn trang mô tả) — dùng bản rộng 1200px."""
    req = urllib.request.Request(API + urllib.parse.quote(commons_name, safe=""),
                                 headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        meta = json.load(r)

    # Commons chỉ phục vụ một số bề rộng thumbnail cố định, nên không tự chế URL:
    # lấy ảnh gốc nếu vừa phải, còn ảnh quá nặng thì dùng bản thu nhỏ có sẵn.
    orig = meta.get("original") or {}
    pref = meta.get("preferred") or {}
    url = orig.get("url") if (orig.get("size") or 0) <= 4_000_000 else (pref.get("url") or orig.get("url"))
    if url.startswith("//"):
        url = "https:" + url

    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    ext = ".png" if data[:4] == b"\x89PNG" else ".jpg"
    return data, ext, "https:" + meta["file_description_url"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="tải lại cả ảnh đã có")
    a = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    credits, failed = {}, []
    for key, commons_name in PORTRAITS.items():
        existing = list(OUT_DIR.glob(f"{key}.*"))
        if existing and not a.force:
            print(f"  bỏ qua {key} (đã có)")
            continue
        try:
            data, ext, page = fetch(commons_name)
            for old in existing:
                old.unlink()
            (OUT_DIR / f"{key}{ext}").write_bytes(data)
            credits[key] = {"commons_file": commons_name, "page": page}
            print(f"✓ {key}{ext}  {len(data) / 1024:.0f} KB")
        except Exception as e:  # noqa: BLE001
            print(f"✗ {key}: {type(e).__name__}: {e}", file=sys.stderr)
            failed.append(key)
        time.sleep(0.6)                      # lịch sự với máy chủ Wikimedia

    if credits:
        f = OUT_DIR / "NGUON.json"
        old = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        old.update(credits)
        f.write_text(json.dumps(old, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nĐã ghi nguồn ảnh vào {f}")
    if failed:
        print("Không tải được:", ", ".join(failed))


if __name__ == "__main__":
    main()
