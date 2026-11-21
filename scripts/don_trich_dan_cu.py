"""Dọn trích dẫn thừa trong lịch sử chat đã lưu trước khi có bộ lọc độ liên quan.

Bộ lọc mới chỉ áp dụng cho câu hỏi từ nay về sau. Những câu lạc đề hỏi trước đó
đã lưu kèm 5 nguồn vào bảng chat_messages, nên mở lại trang vẫn thấy khối
"5 nguồn trích dẫn" dưới câu trả lời về chuyện trời mưa hay nấu phở.

  python -m scripts.don_trich_dan_cu --thu    # chỉ xem sẽ dọn những gì
  python -m scripts.don_trich_dan_cu          # dọn thật
"""
import sys

from app import db
from app.rag.chat import NGUONG_LIEN_QUAN


def main():
    chi_xem = "--thu" in sys.argv
    db.init_db()

    with db.SessionLocal() as s:
        ds = s.query(db.ChatMessage).filter_by(role="assistant").order_by(db.ChatMessage.id).all()
        can_don = []
        for m in ds:
            c = m.citations
            if not isinstance(c, list) or not c:
                continue
            cao = max((x.get("score", 0) for x in c), default=0)
            if cao < NGUONG_LIEN_QUAN:
                can_don.append((m, cao, len(c)))

        print(f"Ngưỡng liên quan: {NGUONG_LIEN_QUAN}")
        print(f"{len(ds)} câu trả lời đã lưu, {len(can_don)} câu lạc đề còn kèm nguồn\n")

        for m, cao, n in can_don:
            cau = (m.content or "").strip().replace("\n", " ")[:62]
            print(f"  #{m.id:<4} {n} nguồn, điểm cao nhất {cao:.3f}   {cau}…")

        if chi_xem:
            print("\n(chạy không có --thu để dọn thật)")
            return 0

        for m, _, _ in can_don:
            m.citations = []
        s.commit()
        print(f"\nĐã gỡ nguồn khỏi {len(can_don)} câu. Nội dung câu trả lời giữ nguyên.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
