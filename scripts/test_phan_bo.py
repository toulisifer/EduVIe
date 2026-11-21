"""Phân bổ số câu theo trọng số, và xử lý khi ngân hàng không đủ câu.

Tình huống kiểm thử: yêu cầu 60 câu nhưng chỉ có 50 câu dùng được -> phần thiếu
phải được chia lại cho các chủ đề còn chỗ, không bỏ trống.

Không tốn lượt gọi AI.
  python -m scripts.test_phan_bo
"""
from app.learning import phan_bo_cau_hoi

dat = sai = 0


def thu(mo_ta, duoc, mong):
    global dat, sai
    ok = duoc == mong
    globals().update(dat=dat + ok, sai=sai + (not ok))
    print(f"  {'✓' if ok else '✗'} {mo_ta}")
    print(f"      được  {duoc}")
    if not ok:
        print(f"      mong  {mong}")


print("1. Chia theo trọng số, không giới hạn")
# 20 câu chia theo 90/70/20 (tổng 180): 10,0 / 7,78 / 2,22 -> 10 / 7 / 2, dư 1 câu
# rơi vào chủ đề có phần lẻ lớn nhất là chủ đề 2
thu("ba chủ đề 90/70/20, xin 20 câu -> yếu nhất được nhiều nhất",
    phan_bo_cau_hoi({1: 90, 2: 70, 3: 20}, 20),
    {1: 10, 2: 8, 3: 2})

thu("hai chủ đề bằng điểm, xin 10 câu -> chia đôi",
    phan_bo_cau_hoi({1: 50, 2: 50}, 10),
    {1: 5, 2: 5})

thu("số lẻ không chia hết -> tổng vẫn đúng 7",
    phan_bo_cau_hoi({1: 60, 2: 40}, 7),
    {1: 4, 2: 3})

print("\n2. Ngân hàng không đủ câu")
kq = phan_bo_cau_hoi({1: 50, 2: 50}, 60, kha_dung={1: 20, 2: 40})
thu("xin 60, chủ đề 1 chỉ có 20 -> dồn 10 câu thiếu sang chủ đề 2",
    kq, {1: 20, 2: 40})
print(f"      tổng lấy được: {sum(kq.values())}/60")

kq = phan_bo_cau_hoi({1: 90, 2: 70, 3: 20}, 60, kha_dung={1: 10, 2: 15, 3: 50})
thu("chủ đề ưu tiên cao lại ít câu nhất -> phần thiếu chảy xuống chủ đề 3",
    kq, {1: 10, 2: 15, 3: 35})
print(f"      tổng lấy được: {sum(kq.values())}/60")

kq = phan_bo_cau_hoi({1: 50, 2: 50}, 60, kha_dung={1: 20, 2: 30})
thu("cả ngân hàng chỉ có 50 câu -> lấy hết 50, không bịa thêm",
    kq, {1: 20, 2: 30})
print(f"      tổng lấy được: {sum(kq.values())}/60 — thiếu {60 - sum(kq.values())} câu, hệ thống báo rõ")

print("\n3. Trường hợp biên")
thu("xin 0 câu", phan_bo_cau_hoi({1: 50}, 0), {})
thu("không có chủ đề nào", phan_bo_cau_hoi({}, 10), {})
thu("một chủ đề hết sạch câu -> chủ đề kia gánh",
    phan_bo_cau_hoi({1: 50, 2: 50}, 10, kha_dung={1: 0, 2: 99}),
    {1: 0, 2: 10})

print(f"\n{dat}/{dat + sai} phép thử đạt")
raise SystemExit(1 if sai else 0)
