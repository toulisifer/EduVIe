"""Thu nhỏ và nén ảnh chân dung cho web.

Khung hiển thị cao 520px, rộng khoảng 520px. Ảnh gốc từ Commons tới 3000px và
11 tấm cộng lại hơn 11 MB — tải trang chủ sẽ rất chậm. Script thu về vừa đủ nét
trên màn hình retina (cao tối đa 1100px) và lưu JPEG progressive.

  python -m scripts.optimize_portraits
"""
from pathlib import Path

from PIL import Image

DIR = Path(__file__).resolve().parent.parent / "web" / "static" / "images" / "portraits"
MAX_H = 1100
QUALITY = 80

truoc = sau = 0
for f in sorted(list(DIR.glob("*.jpg")) + list(DIR.glob("*.png"))):
    cu = f.stat().st_size
    truoc += cu
    im = Image.open(f)
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    if im.height > MAX_H:
        w = round(im.width * MAX_H / im.height)
        im = im.resize((w, MAX_H), Image.LANCZOS)
    out = f.with_suffix(".jpg")
    im.save(out, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    if out != f:
        f.unlink()
    moi = out.stat().st_size
    sau += moi
    print(f"{out.name:<20} {im.size[0]:>4}x{im.size[1]:<5} {cu / 1024:>7.0f} KB -> {moi / 1024:>6.0f} KB")

print(f"\ntổng: {truoc / 1024 / 1024:.1f} MB -> {sau / 1024 / 1024:.1f} MB")
