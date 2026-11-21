"""Hỏi về môn chưa có sách thì trả lời ngắn gọn, không viết bài dài bằng kiến thức chung.

Chỉ lọc theo độ giống nhau của vector là chưa đủ: "tóm tắt hoá lớp 7" vẫn khớp sách
Hoá 12 và Khoa học tự nhiên 8 ở mức trên ngưỡng, nên hệ thống kèm trích dẫn của hai
cuốn đó rồi viết cả bài về chương trình lớp 7 — vừa lâu vừa lạc đề.

Không tốn lượt gọi AI.
  python -m scripts.test_thieu_sach
"""
from app import db
from app.rag.chat import answer, thieu_sach

# (câu hỏi, mong đợi) — None nghĩa là KHÔNG được báo thiếu sách
CASES = [
    # chưa có sách: phải báo thiếu
    ("Tóm tắt hóa lớp 7", "hóa lớp 7"),
    ("hoá 7 có gì", "hóa lớp 7"),      # viết "hoá" hay "hóa" đều nhận ra
    ("cho tôi đề toán lớp 9", "toán lớp 9"),
    ("vật lý lớp 11 học gì", "vật lý lớp 11"),
    ("ngữ văn lớp 12 có bài nào", "ngữ văn lớp 12"),
    # đã có sách: không được báo thiếu
    ("Hằng đẳng thức lớp 8", None),
    ("hóa lớp 8 học gì", None),            # lớp 8 nằm trong Khoa học tự nhiên
    ("sinh học lớp 8", None),
    ("vật lí lớp 8 áp suất", None),
    ("Hoá học 12 chương 1", None),
    ("toán 12 đạo hàm", None),
    ("tiếng anh 8 unit 5", None),
    # không nhắc môn hoặc lớp: không can thiệp
    ("mấy giờ rồi", None),
    ("Áp suất chất lỏng phụ thuộc gì", None),
    ("Hằng đẳng thức lập phương của một tổng", None),
    # SỐ LƯỢNG CÂU KHÔNG PHẢI SỐ LỚP.
    # Trước đây hàm này vơ bất kỳ con số nào trong câu và lấy số ĐẦU TIÊN, nên
    # "tạo cho tôi 3 câu trắc nghiệm toán 12" bị đọc thành "toán lớp 3" rồi từ chối
    # trả lời, dù sách Toán 12 có sẵn. Nhánh dò chữ "lớp" thì viết có dấu trong khi
    # câu hỏi đã được bỏ dấu, nên chưa bao giờ khớp.
    ("tạo cho tôi 3 câu trắc nghiệm toán 12 chương 1", None),
    ("cho tôi 10 câu toán 12 chương 1", None),
    ("giải 5 bài vật lí 12", None),
    ("làm 20 câu tiếng anh 8", None),
    ("cho tôi 8 câu hoá 12", None),
    # vẫn phải báo thiếu khi số lớp đứng sau chữ "lớp", dù trước đó có số khác
    ("cho tôi 4 câu hỏi văn lớp 10", "văn lớp 10"),
    ("soạn 15 câu địa lí lớp 11", "địa lí lớp 11"),
]

dat, sai = [], []
db.init_db()

print("Môn đã có sách: Toán 8, Khoa học tự nhiên 8, Tiếng Anh 8, Toán 12, Vật lí 12, Hoá học 12\n")
for q, mong in CASES:
    ra = thieu_sach(q)
    ok = ra == mong
    (dat if ok else sai).append(q)
    dau = "✓" if ok else "✗"
    print(f"  {dau} {q:<38} → {ra if ra else 'không báo thiếu'}")
    if not ok:
        print(f"      mong đợi: {mong if mong else 'không báo thiếu'}")

print("\nCâu trả lời thật cho câu hỏi thiếu sách (không gọi AI):")
txt, hits = answer("Tóm tắt hóa lớp 7", user_id=1)
print("  " + txt.replace("\n", "\n  "))
print(f"\n  số nguồn trích dẫn: {len(hits)}")
if len(hits) or len(txt) > 400:
    sai.append("câu trả lời vẫn dài hoặc còn kèm nguồn")

print(f"\n{len(dat)}/{len(dat) + len(sai)} phép thử đạt")
for m in sai:
    print("  SAI:", m)
raise SystemExit(1 if sai else 0)
