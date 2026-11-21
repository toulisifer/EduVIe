"""Nạp ngân hàng câu hỏi từ data/ngan_hang_cau_hoi.json vào cơ sở dữ liệu.

Khác với câu do AI sinh lúc chạy, những câu này nằm sẵn trong tệp dữ liệu của dự án:
mở ra đọc được toàn bộ, sửa được, theo dõi được qua git. Khi người chấm hỏi "câu hỏi
này có thật không", mở tệp ra là thấy.

Chạy lại nhiều lần được: câu đã có trong kho sẽ bị bỏ qua, không nạp trùng.

  python -m scripts.nap_tu_file --thu    # kiểm tra tệp, không ghi vào CSDL
  python -m scripts.nap_tu_file          # nạp thật
"""
import json
import sys
from pathlib import Path

from app import bank, db

DATA = Path(__file__).resolve().parent.parent / "data"
TEP_GOC = DATA / "ngan_hang_cau_hoi.json"      # tệp đầu tiên, giữ cho tương thích
THU_MUC = DATA / "cau_hoi"                     # mỗi môn một tệp


def doc_het() -> list[dict]:
    """Gom câu hỏi từ tệp gốc và mọi tệp trong data/cau_hoi/."""
    ds, nguon = [], []
    tep = ([TEP_GOC] if TEP_GOC.exists() else []) + sorted(THU_MUC.glob("*.json"))
    for f in tep:
        phan = json.loads(f.read_text(encoding="utf-8")).get("cau_hoi", [])
        ds += phan
        nguon.append((f.name, len(phan)))
    for ten, n in nguon:
        print(f"   {ten:<28} {n:>3} câu")
    return ds


def main():
    chi_xem = "--thu" in sys.argv
    db.init_db()

    print("Đọc từ:")
    ds = doc_het()
    print(f"\nTổng cộng {len(ds)} câu hỏi\n")

    # dựng bảng tra: (môn, chương, chủ đề) -> topic_id
    with db.SessionLocal() as s:
        tra = {}
        for mon in s.query(db.Subject):
            for ch in mon.chapters:
                for t in ch.topics:
                    tra[(mon.name, ch.name, t.name)] = t.id

    hop_le, khong_khop, loi = [], [], []
    for i, c in enumerate(ds, 1):
        khoa = (c["mon"], c["chuong"], c["chu_de"])
        tid = tra.get(khoa)
        if tid is None:
            khong_khop.append((i, khoa))
            continue
        if len(c["lua_chon"]) != 4 or not 0 <= c["dap_an"] < 4:
            loi.append((i, c["cau_hoi"][:50], "phải có đúng 4 lựa chọn và đáp án 0–3"))
            continue
        hop_le.append((tid, c))

    # thống kê theo môn
    theo_mon = {}
    for _, c in hop_le:
        theo_mon[c["mon"]] = theo_mon.get(c["mon"], 0) + 1
    print("Phân bố theo môn:")
    for m, n in sorted(theo_mon.items()):
        print(f"   {m:<24} {n} câu")

    if khong_khop:
        print(f"\n{len(khong_khop)} câu KHÔNG khớp chủ đề nào trong CSDL:")
        for i, khoa in khong_khop[:10]:
            print(f"   câu #{i}: {khoa[0]} / {khoa[1][:34]} / {khoa[2]}")
    if loi:
        print(f"\n{len(loi)} câu sai định dạng:")
        for i, cau, vi_sao in loi:
            print(f"   câu #{i}: {cau} — {vi_sao}")

    if chi_xem:
        print(f"\n{len(hop_le)}/{len(ds)} câu sẵn sàng nạp. (bỏ --thu để nạp thật)")
        return 1 if (khong_khop or loi) else 0

    them = trung = 0
    for tid, c in hop_le:
        moi = bank.them_cau(tid, c.get("do_kho", "medium"), c["cau_hoi"],
                            c["lua_chon"], c["dap_an"], c.get("giai_thich", ""),
                            source="soan_san", verified=True)
        if moi:
            them += 1
        else:
            trung += 1

    t = bank.thong_ke()
    print(f"\nĐã nạp {them} câu mới, {trung} câu đã có sẵn nên bỏ qua.")
    print(f"Kho hiện có {t['tong']} câu, phủ {t['chu_de_co_cau']}/{t['tong_chu_de']} chủ đề.")
    return 1 if (khong_khop or loi) else 0


if __name__ == "__main__":
    raise SystemExit(main())
