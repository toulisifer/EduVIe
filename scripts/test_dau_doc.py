"""Kiểm thử chống đầu độc dữ liệu huấn luyện DKT.

Tập huấn luyện của DKT là bảng `answers`, mà bảng đó do chính người dùng sinh ra.
Ai đăng ký được là bơm dữ liệu vào được. Bộ kiểm thử này dựng lại bốn kiểu tấn công
rồi kiểm xem lớp lọc trong app/ml/kt_app.py có chặn được không.

Chạy:  .venv/bin/python -m scripts.test_dau_doc
Không đụng tới cơ sở dữ liệu thật — mọi dữ liệu ở đây là dựng trong bộ nhớ.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from app.ml import kt_app

dat = sai = 0


def kiem(ten: str, dieu_kien: bool, chi_tiet: str = ""):
    global dat, sai
    if dieu_kien:
        dat += 1
        print(f"  dat  | {ten}")
    else:
        sai += 1
        print(f"  SAI  | {ten}" + (f"\n       | {chi_tiet}" if chi_tiet else ""))


def nguoi_that(uid: int, n: int, ti_le_dung: float = 0.6, giay_moi_cau: int = 45):
    """Một học sinh thật: đúng sai xen kẽ, mỗi câu mất vài chục giây."""
    moc = datetime(2026, 11, 1, 8, 0)
    ss = [uid % 20 + i % 5 for i in range(n)]
    cs = [1 if (i * 7) % 10 < ti_le_dung * 10 else 0 for i in range(n)]
    ts = [moc + timedelta(seconds=giay_moi_cau * i) for i in range(n)]
    return uid, (ss, cs, ts)


def may_lam(uid: int, n: int, dung_het: bool = True, giay_moi_cau: float = 0.3):
    """Tài khoản bot: trả lời rất nhanh, và thường đúng hết hoặc sai hết."""
    moc = datetime(2026, 11, 1, 8, 0)
    ss = [7 for _ in range(n)]
    cs = [1 if dung_het else 0] * n
    ts = [moc + timedelta(seconds=giay_moi_cau * i) for i in range(n)]
    return uid, (ss, cs, ts)


def im(*_):     # nuốt log cho đầu ra gọn
    pass


print("=" * 70)
print(" CHỐNG ĐẦU ĐỘC DỮ LIỆU HUẤN LUYỆN DKT")
print("=" * 70)

# ---------------------------------------------------------------- 1
print("\n[1] Người học thật thì phải được giữ lại")
tho = dict([nguoi_that(1, 40), nguoi_that(2, 35), nguoi_that(3, 30)])
sach, bc = kt_app.loc_dau_doc(tho, log=im)
kiem("giữ đủ 3 người học thật", len(sach) == 3, f"còn {len(sach)}")
kiem("không loại nhầm ai", bc["nguoi_bi_loai"] == 0, str(bc["ly_do_loai"]))

# ---------------------------------------------------------------- 2
print("\n[2] Chuỗi quá ngắn là nhiễu, phải loại")
tho = dict([nguoi_that(1, 40), nguoi_that(2, 35), nguoi_that(9, 2)])
sach, bc = kt_app.loc_dau_doc(tho, log=im)
kiem(f"loại người chỉ có 2 câu (ngưỡng {kt_app.TOI_THIEU_MOI_NGUOI})", 9 not in sach)
kiem("hai người thật vẫn còn", 1 in sach and 2 in sach)

# ---------------------------------------------------------------- 3
print("\n[3] Tấn công: bot trả lời đúng hết một chủ đề")
tho = dict([nguoi_that(1, 40), nguoi_that(2, 35),
            may_lam(101, 60, dung_het=True), may_lam(102, 60, dung_het=False)])
sach, bc = kt_app.loc_dau_doc(tho, log=im)
kiem("loại bot đúng hết", 101 not in sach)
kiem("loại bot sai hết", 102 not in sach)
kiem("hai người thật vẫn còn", 1 in sach and 2 in sach)
kiem("báo cáo ghi rõ lý do loại", all(str(u) in bc["ly_do_loai"] for u in (101, 102)),
     str(bc["ly_do_loai"]))

# ---------------------------------------------------------------- 4
print("\n[4] Tấn công: bot trả lời nhanh bất thường (đúng sai xen kẽ để né lọc [3])")
moc = datetime(2026, 11, 1, 8, 0)
nhanh = ([5] * 50, [i % 2 for i in range(50)], [moc + timedelta(seconds=0.4 * i) for i in range(50)])
tho = dict([nguoi_that(1, 40), nguoi_that(2, 35)])
tho[103] = nhanh
sach, bc = kt_app.loc_dau_doc(tho, log=im)
kiem(f"loại chuỗi dưới {kt_app.TOC_DO_NGHI_NGO} giây/câu", 103 not in sach,
     "bot né được lọc đúng-hết nhưng không né được lọc tốc độ")
kiem("người thật trả lời chậm vẫn được giữ", 1 in sach and 2 in sach)

# ---------------------------------------------------------------- 5
print("\n[5] Tấn công: một người bơm dữ liệu áp đảo (Sybil gộp)")
tho = dict([nguoi_that(1, 30), nguoi_that(2, 30), nguoi_that(3, 30)])
tho[200] = nguoi_that(200, 900)[1]          # kẻ tấn công: 900 câu, hợp lệ về hình thức
sach, bc = kt_app.loc_dau_doc(tho, log=im)
tong = sum(len(ss) for ss, _ in sach.values())
phan_ke_tan_cong = len(sach[200][0]) / tong
kiem(f"kẻ tấn công bị cắt xuống ≤ {kt_app.TRAN_TI_TRONG:.0%} tập huấn luyện",
     phan_ke_tan_cong <= kt_app.TRAN_TI_TRONG + 0.01,
     f"đang chiếm {phan_ke_tan_cong:.1%}")
kiem("không bị loại hẳn, chỉ bị cắt bớt", 200 in sach)
kiem("ba người thật giữ nguyên số câu",
     all(len(sach[u][0]) == 30 for u in (1, 2, 3)))
print(f"       → trước lọc kẻ tấn công chiếm {900 / (900 + 90):.1%}, sau lọc còn {phan_ke_tan_cong:.1%}")

# ---------------------------------------------------------------- 6
print("\n[6] Trần cắt phần cũ, giữ phần gần nhất")
moc = datetime(2026, 11, 1, 8, 0)
n = kt_app.TOI_DA_MOI_NGUOI + 50
dai = (list(range(n)), [1] * (n - 10) + [0] * 10,        # 10 câu gần nhất là câu sai
       [moc + timedelta(seconds=60 * i) for i in range(n)])
tho = {1: dai, 2: nguoi_that(2, 400)[1], 3: nguoi_that(3, 400)[1]}
sach, bc = kt_app.loc_dau_doc(tho, log=im)
kiem(f"không ai vượt trần {kt_app.TOI_DA_MOI_NGUOI} câu",
     all(len(ss) <= kt_app.TOI_DA_MOI_NGUOI for ss, _ in sach.values()))
kiem("giữ phần gần nhất chứ không phải phần đầu",
     1 in sach and sum(sach[1][1][-10:]) == 0,
     "10 câu cuối phải là 10 câu sai mới nhất")

# ---------------------------------------------------------------- 7
print("\n[7] Dữ liệu sạch không bị cắt oan")
tho = dict([nguoi_that(1, 50), nguoi_that(2, 50), nguoi_that(3, 50), nguoi_that(4, 50)])
sach, bc = kt_app.loc_dau_doc(tho, log=im)
kiem("giữ nguyên toàn bộ 200 câu", bc["cau_vao"] == 200, f"còn {bc['cau_vao']}")
kiem("không ai bị cắt", not bc["bi_cat_bot"], str(bc["bi_cat_bot"]))

# ---------------------------------------------------------------- 8
print("\n[8] Báo cáo đủ để truy vết")
tho = dict([nguoi_that(1, 40), nguoi_that(2, 35), may_lam(101, 60)])
sach, bc = kt_app.loc_dau_doc(tho, log=im)
for khoa in ("nguoi_vao", "nguoi_bi_loai", "cau_vao", "cau_tho", "tran_moi_nguoi",
             "ly_do_loai", "bi_cat_bot"):
    kiem(f"báo cáo có trường '{khoa}'", khoa in bc)

print("\n" + "=" * 70)
print(f" {dat}/{dat + sai} phép thử đạt")
print("=" * 70)
raise SystemExit(0 if sai == 0 else 1)
