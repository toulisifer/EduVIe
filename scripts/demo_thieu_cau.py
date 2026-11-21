"""Xin nhiều câu hơn số câu đang có trong ngân hàng thì hệ thống xử lý thế nào.

Chạy trên kho thật, KHÔNG gọi AI — chỉ cho thấy phần chia câu và phần còn thiếu.

  python -m scripts.demo_thieu_cau
  python -m scripts.demo_thieu_cau --mon "Toán 8" --chuong 2
"""
import argparse

from app import bank, db
from app.learning import phan_bo_cau_hoi
from app.quiz import _lay_tu_ngan_hang, ma_de

W = 72


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mon", default="Toán 8")
    ap.add_argument("--chuong", type=int, default=2, help="chương thứ mấy (1 = chương đầu)")
    ap.add_argument("--do-kho", default="medium")
    a = ap.parse_args()

    db.init_db()
    with db.SessionLocal() as s:
        mon = s.query(db.Subject).filter_by(name=a.mon).first()
        ch = sorted(mon.chapters, key=lambda c: c.order)[a.chuong - 1]
        topics = list(ch.topics)
        for t in topics:
            _ = t.path
        sid, ten_ch = mon.id, ch.name

    tids = [t.id for t in topics]
    co = bank.dem_kha_dung(tids, a.do_kho)
    tong_co = sum(co.values())

    print("=" * W)
    print(f" {a.mon} — {ten_ch}")
    print("=" * W)
    print(f"\nNgân hàng đang có (độ khó {a.do_kho}):")
    for t in topics:
        print(f"   {t.name[:46]:<48} {co.get(t.id, 0):>2} câu")
    print(f"   {'TỔNG':<48} {tong_co:>2} câu")

    for xin in (tong_co // 2, tong_co, tong_co + 6):
        if xin <= 0:
            continue
        print("\n" + "-" * W)
        print(f"Học sinh xin {xin} câu")
        print("-" * W)

        bo = phan_bo_cau_hoi({t: 1.0 for t in tids}, xin, kha_dung=co)
        print("  Bước 1 — chia câu theo trọng số, dồn phần thiếu sang chủ đề còn chỗ:")
        for t in topics:
            phan = bo.get(t.id, 0)
            san = co.get(t.id, 0)
            ghi = ""
            if san and phan >= san:
                ghi = "  ← lấy hết, không còn câu"
            elif phan > 0:
                ghi = f"  (còn dư {san - phan})"
            print(f"     {t.name[:40]:<42} {phan:>2}/{san:<2}{ghi}")

        cau_kho, thieu = _lay_tu_ngan_hang(topics, a.do_kho, xin)
        print(f"\n  Bước 2 — lấy từ kho: {len(cau_kho)} câu")
        if thieu <= 0:
            print("  Bước 3 — đủ rồi, KHÔNG gọi AI lần nào. Đề dựng xong.")
        else:
            print(f"  Bước 3 — còn thiếu {thieu} câu → gọi AI sinh ĐÚNG {thieu} câu đó")
            print(f"           (2 lượt gọi: 1 sinh + 1 kiểm tra chéo), rồi nạp ngược vào kho")
            print(f"           lần sau xin {xin} câu sẽ không phải gọi AI nữa")

        print(f"\n  Mã đề: {ma_de(sid, tids, a.do_kho, xin)}")

    print("\n" + "=" * W)
    print(" Tóm lại: chia lại trọng số trước. Chỉ khi cả kho cạn mới gọi AI,")
    print(" và chỉ gọi cho đúng phần còn thiếu chứ không sinh lại từ đầu.")
    print("=" * W)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
