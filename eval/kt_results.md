# Knowledge Tracing — ASSISTments 2009 — 15/09/2026 22:10

- Dữ liệu: 2548 học sinh train, 283 valid, 1198 test; 111 kỹ năng; 325,515 tương tác.
- Bài toán: dự đoán đúng/sai câu tiếp theo từ lịch sử (kỹ năng, kết quả).

| Mô hình | AUC | Accuracy | Thời gian |
|---|---|---|---|
| Tỷ lệ đúng toàn cục | **0.5000** | 0.6603 | 1s |
| Tỷ lệ đúng theo kỹ năng | **0.6199** | 0.6647 | 0s |
| Logistic Regression (đặc trưng thủ công) | **0.7611** | 0.7376 | 11s |
| DKT (LSTM hidden=100, 8 epoch) | **0.8246** | 0.7666 | 42s |

## Quá trình huấn luyện DKT

| Epoch | Loss | Val AUC | Val Acc |
|---|---|---|---|
| 1 | 0.6403 | 0.6897 | 0.6708 |
| 2 | 0.5821 | 0.7765 | 0.7244 |
| 3 | 0.5403 | 0.7977 | 0.7443 |
| 4 | 0.5076 | 0.8171 | 0.7584 |
| 5 | 0.4875 | 0.8215 | 0.7624 |
| 6 | 0.4764 | 0.8257 | 0.7649 |
| 7 | 0.4711 | 0.8271 | 0.7665 |
| 8 | 0.4676 | 0.8287 | 0.7663 |

Tham khảo: DKT gốc (Piech et al., 2015) báo cáo AUC ≈ 0.86 trên ASSISTments 2009 với phiên bản dữ liệu cũ; các nghiên cứu sau trên bản đã làm sạch (updated) thường đạt 0.75–0.82.