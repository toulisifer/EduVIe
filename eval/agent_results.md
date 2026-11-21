# Đánh giá agent lập kế hoạch — 04/10/2026 10:40

- Số kế hoạch: 16
- Pass (không vi phạm luật nào): **3/16** (19%)
- Tổng vi phạm (LLM thuần): 30
- Sau bước code tự sửa (auto_repair): pass **12/16** (75%), còn 10 vi phạm

| Luật | Mô tả | Số vi phạm (LLM thuần) |
|---|---|---|
| R1_prereq | Không luyện chủ đề khi tiên quyết của nó còn Yếu trước khi có việc củng cố tiên quyết đó | 5 |
| R2_cover | Mọi chủ đề Yếu phải xuất hiện trong kế hoạch | 4 |
| R3_due | Chủ đề đến hạn ôn phải nằm trong 2 ngày đầu | 14 |
| R4_load | Mỗi ngày 1–3 việc, không ngày trống ở giữa | 0 |
| R5_mix | Có quiz ít nhất mỗi 2 ngày | 7 |

| Plan | User | Tạo lúc | Việc | Vi phạm (LLM) | Sau code sửa |
|---|---|---|---|---|---|
| 1 | 1 | 15/09 10:26 | 11 | R3_due: 'Giá trị lớn nhất và nhỏ nhất' đến hạn ôn nhưng xếp ngày 3 | ✅ |
| 2 | 3 | 15/09 11:09 | 9 | R3_due: 'Tính đơn điệu của hàm số' đến hạn ôn nhưng không có trong kế hoạch<br>R3_due: 'Khảo sát và vẽ đồ thị hàm số' đến hạn ôn nhưng bị chặn bởi tiên quyết yếu 'Đường tiệm cận' — phải củng cố 'Đường tiệm cận' trong 2 ngày đầu (hiện ngày 3) | ✅ |
| 3 | 5 | 15/09 14:16 | 14 | R5_mix: không có quiz trong 2 ngày liên tiếp (tới ngày 8) | 1 |
| 4 | 7 | 15/09 14:29 | 7 | ✅ | ✅ |
| 5 | 3 | 15/09 16:15 | 11 | R3_due: 'Khảo sát và vẽ đồ thị hàm số' đến hạn ôn nhưng bị chặn bởi tiên quyết yếu 'Đường tiệm cận' — phải củng cố 'Đường tiệm cận' trong 2 ngày đầu (hiện ngày 3) | ✅ |
| 6 | 3 | 16/09 04:07 | 8 | R1_prereq: 'Giá trị lớn nhất và nhỏ nhất' ngày 1 nhưng tiên quyết 'Cực trị của hàm số' còn yếu chưa được củng cố trước<br>R1_prereq: 'Khảo sát và vẽ đồ thị hàm số' ngày 2 nhưng tiên quyết 'Cực trị của hàm số' còn yếu chưa được củng cố trước<br>R1_prereq: 'Khảo sát và vẽ đồ thị hàm số' ngày 2 nhưng tiên quyết 'Đường tiệm cận' còn yếu chưa được củng cố trước<br>R1_prereq: 'Khảo sát và vẽ đồ thị hàm số' ngày 5 nhưng tiên quyết 'Đường tiệm cận' còn yếu chưa được củng cố trước<br>R2_cover: chủ đề yếu 'Đường tiệm cận' không có trong kế hoạch<br>R3_due: 'Khảo sát và vẽ đồ thị hàm số' đến hạn ôn nhưng bị chặn bởi tiên quyết yếu 'Cực trị của hàm số' — phải củng cố 'Cực trị của hàm số' trong 2 ngày đầu (hiện ngày 3)<br>R3_due: 'Khảo sát và vẽ đồ thị hàm số' đến hạn ôn nhưng bị chặn bởi tiên quyết yếu 'Đường tiệm cận' — phải củng cố 'Đường tiệm cận' trong 2 ngày đầu (hiện không có)<br>R3_due: 'Cực trị của hàm số' đến hạn ôn nhưng xếp ngày 3 | ✅ |
| 7 | 3 | 16/09 04:15 | 10 | R3_due: 'Khảo sát và vẽ đồ thị hàm số' đến hạn ôn nhưng bị chặn bởi tiên quyết yếu 'Đường tiệm cận' — phải củng cố 'Đường tiệm cận' trong 2 ngày đầu (hiện ngày 4) | ✅ |
| 8 | 3 | 16/09 04:22 | 10 | R3_due: 'Khảo sát và vẽ đồ thị hàm số' đến hạn ôn nhưng bị chặn bởi tiên quyết yếu 'Đường tiệm cận' — phải củng cố 'Đường tiệm cận' trong 2 ngày đầu (hiện ngày 3) | ✅ |
| 9 | 3 | 16/09 04:31 | 7 | R1_prereq: 'Khảo sát và vẽ đồ thị hàm số' ngày 2 nhưng tiên quyết 'Đường tiệm cận' còn yếu chưa được củng cố trước<br>R3_due: 'Khảo sát và vẽ đồ thị hàm số' đến hạn ôn nhưng bị chặn bởi tiên quyết yếu 'Đường tiệm cận' — phải củng cố 'Đường tiệm cận' trong 2 ngày đầu (hiện ngày 3) | ✅ |
| 10 | 12 | 16/09 05:00 | 14 | R5_mix: không có quiz trong 2 ngày liên tiếp (tới ngày 2)<br>R5_mix: không có quiz trong 2 ngày liên tiếp (tới ngày 5)<br>R5_mix: không có quiz trong 2 ngày liên tiếp (tới ngày 8)<br>R5_mix: không có quiz trong 2 ngày liên tiếp (tới ngày 11) | 4 |
| 11 | 14 | 21/09 10:33 | 6 | ✅ | ✅ |
| 12 | 1 | 26/09 05:15 | 3 | R3_due: 'Giá trị lớn nhất và nhỏ nhất' đến hạn ôn nhưng không có trong kế hoạch | ✅ |
| 13 | 3 | 26/09 11:22 | 3 | R2_cover: chủ đề yếu 'Giá trị lớn nhất và nhỏ nhất' không có trong kế hoạch<br>R2_cover: chủ đề yếu 'Đường tiệm cận' không có trong kế hoạch<br>R2_cover: chủ đề yếu 'Khảo sát và vẽ đồ thị hàm số' không có trong kế hoạch<br>R3_due: 'Khảo sát và vẽ đồ thị hàm số' đến hạn ôn nhưng bị chặn bởi tiên quyết yếu 'Đường tiệm cận' — phải củng cố 'Đường tiệm cận' trong 2 ngày đầu (hiện không có) | 2 |
| 14 | 3 | 26/09 11:27 | 6 | ✅ | ✅ |
| 15 | 1 | 02/10 01:12 | 14 | R3_due: 'Giá trị lớn nhất và nhỏ nhất' đến hạn ôn nhưng xếp ngày 3 | ✅ |
| 16 | 1 | 02/10 01:12 | 7 | R3_due: 'Giá trị lớn nhất và nhỏ nhất' đến hạn ôn nhưng xếp ngày 4<br>R5_mix: không có quiz trong 2 ngày liên tiếp (tới ngày 2)<br>R5_mix: không có quiz trong 2 ngày liên tiếp (tới ngày 5) | 3 |

Lưu ý: luật R3 (đến hạn ôn) được chấm theo trạng thái HIỆN TẠI, nên kế hoạch cũ có thể bị tính vi phạm dù lúc tạo là đúng.