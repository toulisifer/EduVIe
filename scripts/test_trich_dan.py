"""Câu hỏi lạc đề thì không được kèm trích dẫn sách giáo khoa.

Kho vector luôn trả về k đoạn gần nhất, kể cả khi câu hỏi chẳng dính gì tới sách.
Bài này kiểm tra bộ lọc theo độ liên quan có tách đúng hai nhóm không.

  python -m scripts.test_trich_dan          # chỉ đo truy hồi, không tốn lượt gọi AI sinh chữ
  python -m scripts.test_trich_dan --that   # hỏi thật, xem câu trả lời có kèm [1] không
"""
import re
import sys

from app import db
from app.rag.chat import NGUONG_LIEN_QUAN, _loc_lien_quan, answer, retrieve

LIEN_QUAN = [
    "Hằng đẳng thức lập phương của một tổng viết thế nào?",
    "Áp suất chất lỏng phụ thuộc vào những yếu tố nào?",
    "Định lí Thalès phát biểu ra sao?",
]
LAC_DE = [
    "hôm nay trời đẹp không",
    "bạn tên gì vậy",
    "cách nấu phở bò ngon",
    "mấy giờ rồi",
    "kể chuyện cười đi",
]

dat, sai = [], []


def thu(mo_ta, ok, chi_tiet=""):
    (dat if ok else sai).append(mo_ta)
    print(f"  {'✓' if ok else '✗'} {mo_ta}")
    if chi_tiet:
        print(f"      {chi_tiet}")


def main():
    db.init_db()
    print(f"Ngưỡng liên quan đang đặt: {NGUONG_LIEN_QUAN}\n")

    print("1. Câu hỏi về bài — phải có nguồn")
    for q in LIEN_QUAN:
        con = _loc_lien_quan(retrieve(q, user_id=1))
        diem = max((h["score"] for h in con), default=0)
        thu(f"{q[:44]}", len(con) > 0, f"{len(con)} đoạn, điểm cao nhất {diem:.3f}")

    print("\n2. Câu lạc đề — không được có nguồn")
    for q in LAC_DE:
        tho = retrieve(q, user_id=1)
        con = _loc_lien_quan(tho)
        cao = max((h["score"] for h in tho), default=0)
        thu(f"{q[:44]}", len(con) == 0,
            f"kho trả về {len(tho)} đoạn, lọc còn {len(con)}; điểm cao nhất {cao:.3f}")

    if "--that" in sys.argv:
        print("\n3. Hỏi thật, xem câu trả lời")
        for q in ("mấy giờ rồi", "Hằng đẳng thức lập phương của một tổng viết thế nào?"):
            txt, hits = answer(q, user_id=1)
            co_dau = bool(re.search(r"\[\d+\]", txt))      # [1] [2] … bất kỳ số nào
            nen_co = len(hits) > 0
            print(f"\n  Hỏi: {q}")
            print(f"  → {len(hits)} nguồn, câu trả lời {'CÓ' if co_dau else 'không'} đánh dấu [n]")
            print(f"  {txt[:200]}")
            thu(f"đánh dấu [n] khớp với việc có nguồn hay không ({q[:24]})", co_dau == nen_co)

    print(f"\n{len(dat)}/{len(dat) + len(sai)} phép thử đạt")
    for m in sai:
        print("  SAI:", m)
    return 1 if sai else 0


if __name__ == "__main__":
    raise SystemExit(main())
