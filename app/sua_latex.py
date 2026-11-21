"""Cứu công thức LaTeX bị JSON nuốt mất dấu gạch chéo.

VẤN ĐỀ
Mô hình trả về JSON, trong đó công thức viết bằng LaTeX:

    {"question": "Cho hàm số $y = \\frac{1}{3}x^3$ ..."}

Nhưng nó thường chỉ viết MỘT dấu gạch chéo. Trong JSON, `\\f` là một escape hợp lệ
(form feed), nên json.loads lặng lẽ đổi `\\frac` thành ký tự U+000C rồi "rac". Câu hỏi
lưu vào kho mất luôn tên lệnh, và KaTeX in ra chữ đỏ `rac{A'B'}{AB}`.

Dính nhiều nhất là những lệnh hay dùng nhất:
    \\frac \\f -> U+000C        \\text \\times \\theta \\tan \\t -> TAB
    \\right \\rho \\r -> CR      \\neq \\nu \\n -> xuống dòng       \\binom \\b -> U+0008

ĐO TRÊN KHO THẬT (1552 câu): 10 lần U+000C, 14 lần TAB, 8 lần CR — 9 câu hỏng hẳn.

CÁCH SỬA
Đổi ngược ký tự điều khiển về `\\` + chữ cái. An toàn vì:
  - U+0008, U+000B, U+000C không bao giờ là nội dung thật của một câu hỏi.
  - TAB và CR chỉ đổi khi NGAY SAU là chữ cái — tab thật dùng để thụt lề thì theo sau
    là khoảng trắng hoặc dấu câu.
  - Xuống dòng là ký tự hợp lệ trong đề bài nhiều dòng, nên CHỈ đổi khi nó nằm giữa
    hai dấu $ — trong vùng công thức thì một dòng mới không có nghĩa gì.
"""
from __future__ import annotations

import re

# Ký tự điều khiển không bao giờ là nội dung thật của câu hỏi -> đổi ngược vô điều kiện.
LUON_SUA = {"\x08": "b", "\x0b": "v", "\x0c": "f"}

# TAB, CR và xuống dòng thì KHÁC: chúng có thể là định dạng thật. Chỉ đổi khi phần
# ngay sau ghép lại thành đúng một tên lệnh LaTeX có thật. Nhờ vậy "cột1<TAB>cột2"
# giữ nguyên là tab, còn "<TAB>ext{ g}" mới được trả về "\text{ g}".
LENH_SAU = {
    "\x09": ("t", ["extstyle", "extbf", "extit", "ext", "imes", "heta", "anh", "an",
                   "riangle", "frac", "herefore", "op", "o"]),
    "\x0d": ("r", ["ightarrow", "ightleftharpoons", "ight", "angle", "ceil", "floor",
                   "ho", "m", "ad"]),
    "\x0a": ("n", ["abla", "eq", "eg", "ot", "u", "mid", "leq", "geq", "e"]),
}
CO_KY_TU_HONG = re.compile(r"[\x08\x09\x0a\x0b\x0c\x0d]")


def _sua_lenh(s: str, ch: str, chu: str, ten_lenh: list[str]) -> str:
    """Đổi `ch` thành "\\" + chu, nhưng chỉ khi ngay sau là một tên lệnh trong danh sách."""
    if ch not in s:
        return s
    mau = "|".join(re.escape(t) for t in ten_lenh)      # danh sách đã xếp dài trước
    return re.sub(re.escape(ch) + rf"(?=(?:{mau})(?![A-Za-z]))",
                  lambda _: "\\" + chu, s)


def sua_chuoi(s: str) -> str:
    """Trả lại chuỗi đã khôi phục dấu gạch chéo. Chuỗi không dính gì thì giữ nguyên."""
    if not isinstance(s, str) or not CO_KY_TU_HONG.search(s):
        return s
    for ch, chu in LUON_SUA.items():
        s = s.replace(ch, "\\" + chu)
    for ch, (chu, ten_lenh) in LENH_SAU.items():
        if ch == "\x0a":
            continue                              # xuống dòng xử lý riêng ở dưới
        s = _sua_lenh(s, ch, chu, ten_lenh)
    # Xuống dòng là ký tự hợp lệ trong đề bài nhiều dòng, nên chỉ đụng tới phần nằm
    # giữa hai dấu $ — trong vùng công thức thì một dòng mới không có nghĩa gì.
    if "$" in s and "\x0a" in s:
        chu, ten_lenh = LENH_SAU["\x0a"]
        phan = s.split("$")
        for i in range(1, len(phan), 2):
            phan[i] = _sua_lenh(phan[i], "\x0a", chu, ten_lenh)
        s = "$".join(phan)
    return s


def sua(obj):
    """Sửa đệ quy mọi chuỗi trong một cấu trúc dict/list vừa đọc từ JSON."""
    if isinstance(obj, str):
        return sua_chuoi(obj)
    if isinstance(obj, list):
        return [sua(x) for x in obj]
    if isinstance(obj, dict):
        return {k: sua(v) for k, v in obj.items()}
    return obj
