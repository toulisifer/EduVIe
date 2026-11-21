#!/usr/bin/env bash
# Nạp trọn bộ sách lớp 8 theo từng chương.
# Khoảng trang lấy từ mục lục sách; Toán 8 tập một lệch +1 so với số trang in, hai cuốn kia trùng.
# Chạy lại được: trang nào đã OCR thì dùng lại kết quả cũ, không gọi Gemini nữa.
cd "$(dirname "$0")/.." || exit 1
U="phan ngọc vương"

echo "########## TOÁN 8 — TẬP MỘT ##########"
.venv/bin/python -m scripts.ingest_book --user "$U" --subject "Toán 8" \
  --file data/uploads/1_SGK_Toan_8_Tap_1.pdf \
  --chapters "1:6-29" "2:30-48" "3:49-76" "4:77-90" "5:91-111" "6:112-122"

echo "########## TOÁN 8 — TẬP HAI ##########"
.venv/bin/python -m scripts.ingest_book --user "$U" --subject "Toán 8" \
  --file data/uploads/1_SGK_Toan_8_Tap_2.pdf \
  --chapters "7:5-28" "8:29-56" "9:57-75" "10:76-111" "11:112-124" "12:125-138"

echo "########## TIẾNG ANH 8 ##########"
.venv/bin/python -m scripts.ingest_book --user "$U" --subject "Tiếng Anh 8" \
  --file data/uploads/1_SGK_Tieng_Anh_8.pdf \
  --chapters "1:9-40" "2:41-72" "3:73-104" "4:105-136"

echo "########## XONG ##########"
