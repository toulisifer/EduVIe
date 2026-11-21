"""Tạo ảnh một bài giải có lỗi cố ý, dùng để thử chức năng Chấm bài.

Lỗi gài: dòng 3 khai triển (x+2)^2 thiếu số hạng 4x.
  python -m scripts.make_test_homework  ->  /tmp/bai_lam_thu.png
"""
from PIL import Image, ImageDraw, ImageFont

LINES = [
    "Bai 1. Rut gon bieu thuc:",
    "    A = (x + 2)^2 - (x - 1)(x + 3)",
    "",
    "Bai lam:",
    "    (x + 2)^2 = x^2 + 4          <-- thieu 4x",
    "    (x - 1)(x + 3) = x^2 + 2x - 3",
    "    A = x^2 + 4 - (x^2 + 2x - 3)",
    "      = 4 - 2x + 3",
    "      = 7 - 2x",
    "",
    "Vay A = 7 - 2x",
]


def main():
    img = Image.new("RGB", (900, 560), "white")
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    except OSError:
        font = ImageFont.load_default()
    for i, line in enumerate(LINES):
        d.text((40, 30 + i * 46), line, fill="black", font=font)
    out = "/tmp/bai_lam_thu.png"
    img.save(out)
    print("đã tạo", out)


if __name__ == "__main__":
    main()
