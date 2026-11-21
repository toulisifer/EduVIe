"""Gỡ câu hỏi giả khỏi ngân hàng câu hỏi.

scripts/seed_demo.py tạo lịch sử học tập hai tuần cho tài khoản demo bằng những câu
có nội dung "[Demo] Câu hỏi về ..." và bốn lựa chọn A/B/C/D. Khi gộp câu hỏi cũ vào
kho chung, chúng theo vào luôn.

Ở đây chỉ ĐÁNH DẤU chúng là không dùng được (flagged), không xoá: lịch sử làm bài
của tài khoản demo vẫn nguyên nên các trang Phân tích, Điểm số vẫn có dữ liệu để
trình bày, còn kho đề thì chỉ còn câu thật.

  python -m scripts.don_cau_demo --thu   # xem trước
  python -m scripts.don_cau_demo         # làm thật
"""
import sys

from app import db

DAU_HIEU = "[Demo]"


def main():
    chi_xem = "--thu" in sys.argv
    db.init_db()

    with db.SessionLocal() as s:
        tong = s.query(db.BankQuestion).count()
        gia = (s.query(db.BankQuestion)
               .filter(db.BankQuestion.content.like(f"%{DAU_HIEU}%"),
                       db.BankQuestion.flagged.is_(False)).all())

        print(f"Kho có {tong} câu, trong đó {len(gia)} câu giả cần gỡ\n")
        for c in gia[:8]:
            print(f"  #{c.id:<4} [{c.difficulty:<6}] {c.content[:62]}")
        if len(gia) > 8:
            print(f"  … và {len(gia) - 8} câu nữa")

        if chi_xem:
            print("\n(chạy không có --thu để làm thật)")
            return 0

        for c in gia:
            c.flagged = True
        s.commit()

        con = (s.query(db.BankQuestion)
               .filter(db.BankQuestion.flagged.is_(False)).count())
        print(f"\nĐã gỡ {len(gia)} câu giả. Kho còn {con} câu thật dùng được.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
