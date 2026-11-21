"""Cứu công thức LaTeX bị JSON nuốt dấu gạch chéo — và không phá nội dung lành.

Người dùng báo: đề hiện chữ đỏ "rac{A'B'}{AB}" thay vì phân số. Nguyên nhân: mô hình
viết "\\frac" bằng MỘT gạch chéo trong JSON, mà "\\f" là escape hợp lệ (form feed),
nên json.loads đổi nó thành U+000C + "rac".

Chạy:  .venv/bin/python -m scripts.test_sua_latex      (không gọi AI, không đụng DB)
"""
import json

from app.sua_latex import sua, sua_chuoi

dat = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dat, sai
    if dk:
        dat += 1
        print(f"  dat  | {ten}")
    else:
        sai += 1
        print(f"  SAI  | {ten}" + (f"\n       | {chi_tiet}" if chi_tiet else ""))


print("=" * 74)
print(" CUU CONG THUC LATEX BI JSON NUOT")
print("=" * 74)

print("\n[1] Dung lai duoc lenh bi cut dau")
TRUONG_HOP = [
    ("\x0crac{A'B'}{AB}", r"\frac{A'B'}{AB}", "frac (U+000C)"),
    ("$y = -\x0crac{1}{3}x^3$", r"$y = -\frac{1}{3}x^3$", "frac trong cong thuc"),
    ("\x09ext{ g}", r"\text{ g}", "text (TAB)"),
    ("5\x09imes 3", r"5\times 3", "times (TAB)"),
    ("\x09heta", r"\theta", "theta (TAB)"),
    ("\x0dight)", r"\right)", "right (CR)"),
    ("\x0dho", r"\rho", "rho (CR)"),
    ("\x08inom{5}{2}", r"\binom{5}{2}", "binom (U+0008)"),
]
for hong, mong, ten in TRUONG_HOP:
    ra = sua_chuoi(hong)
    kiem(f"{ten:24s} -> {mong}", ra == mong, f"ra: {ra!r}")

print("\n[2] Khong pha noi dung lanh")
GIU_NGUYEN = [
    (r"$y = \frac{1}{3}x^3$", "cong thuc da dung (hai gach cheo)"),
    ("Cho tam giác $ABC$ vuông tại $A$.", "cau binh thuong"),
    ("Các phản ứng xảy ra như sau:\n(1) Fe + 2HCl", "xuong dong THAT ngoai cong thuc"),
    ("Dòng 1\nDòng 2\nDòng 3", "nhieu dong van ban"),
    ("cột1\tcột2", "tab that giua hai cot chu"),
    ("Bảng:\tGiá trị", "tab roi chu hoa"),
    ("a\t1 b\t2", "tab roi chu so"),
    ("", "chuoi rong"),
]
for goc, ten in GIU_NGUYEN:
    ra = sua_chuoi(goc)
    kiem(f"{ten}", ra == goc, f"doi thanh: {ra!r}")

print("\n[3] Xuong dong trong vung cong thuc moi duoc sua")
kiem("trong $...$ thi \\n la lenh bi cut",
     sua_chuoi("$a \x0aeq b$") == r"$a \neq b$", repr(sua_chuoi("$a \x0aeq b$")))
kiem("ngoai $...$ thi giu nguyen xuong dong",
     sua_chuoi("Câu a\neq nhau") == "Câu a\neq nhau", repr(sua_chuoi("Câu a\neq nhau")))

print("\n[4] Sua de quy ca cau truc JSON")
goc = {"question": "$\x0crac{1}{2}$", "options": ["\x09ext{A}", "ổn", {"x": "\x0dight"}],
       "n": 5, "ok": True, "rong": None}
ra = sua(goc)
kiem("sua trong dict", ra["question"] == r"$\frac{1}{2}$", ra["question"])
kiem("sua trong list", ra["options"][0] == r"\text{A}", ra["options"][0])
kiem("sua trong dict long nhau", ra["options"][2]["x"] == r"\right")
kiem("khong doi phan tu lanh", ra["options"][1] == "ổn")
kiem("giu nguyen so / bool / None",
     ra["n"] == 5 and ra["ok"] is True and ra["rong"] is None)

print("\n[5] Dung lai dung canh nguoi dung gap")
# Mo phong: mo hinh viet mot gach cheo, json.loads nuot mat
tho = '{"q": "Cho tam giác đồng dạng. $\\frac{A\'B\'}{AB} = \\frac{B\'C\'}{BC}$"}'
doc_ra = json.loads(tho)
kiem("json.loads qua that lam hong", "\x0crac" in doc_ra["q"], repr(doc_ra["q"])[:60])
cuu = sua(doc_ra)
kiem("sua xong khong con ky tu dieu khien",
     not any(c in cuu["q"] for c in "\x08\x09\x0b\x0c\x0d"), repr(cuu["q"])[:70])
kiem("ra dung cong thuc ban dau",
     cuu["q"] == "Cho tam giác đồng dạng. $\\frac{A'B'}{AB} = \\frac{B'C'}{BC}$",
     repr(cuu["q"]))

print("\n" + "=" * 74)
print(f" {dat}/{dat + sai} phep thu dat")
print("=" * 74)
raise SystemExit(0 if sai == 0 else 1)
