"""Trích dẫn phải thuộc đúng môn người học đang hỏi, và không lặp một trang.

Lỗi gốc: màn Chat không có ô chọn môn nên subject_id = None, truy vấn chạy trên
TOÀN BỘ kho sách. Hỏi "tạo cho tôi 10 câu toán 12 chương 1" thì đoạn sách Hoá 12
đạt 0,769 — cao hơn mọi đoạn Toán 12 — nên câu trả lời kèm trích dẫn sai sách.

Chạy:  .venv/bin/python -m scripts.test_trich_dan_dung_mon    (gọi embedding, không gọi LLM sinh chữ)
"""
from app import db
from app.rag.chat import retrieve, suy_ra_mon

dat = sai = 0


def kiem(ten, dk, chi_tiet=""):
    global dat, sai
    if dk:
        dat += 1
        print(f"  dat  | {ten}")
    else:
        sai += 1
        print(f"  SAI  | {ten}" + (f"\n       | {chi_tiet}" if chi_tiet else ""))


def main():
    db.init_db()
    with db.SessionLocal() as s:
        u = s.query(db.User).order_by(db.User.id).first()
        if not u:
            print("Chua co nguoi dung nao de thu.")
            raise SystemExit(1)
        uid = u.id
        ten_mon = {x.id: x.name for x in s.query(db.Subject)}
    theo_ten = {v: k for k, v in ten_mon.items()}

    print("=" * 72)
    print(" TRICH DAN DUNG MON")
    print("=" * 72)

    print("\n[1] Doan mon tu cau hoi khi nguoi dung khong chon")
    mong_doi = [
        ("tạo cho tôi 10 câu toán 12 chương 1", "Toán 12"),
        ("cho tôi 10 câu trắc nghiệm toán 12 chương 1", "Toán 12"),
        ("cho tôi bài tập hoá 12 chương 1", "Hoá học 12"),
        ("unit 9 tiếng anh 8 nói về gì", "Tiếng Anh 8"),
        ("tóm tắt khoa học tự nhiên 8 bài 3", "Khoa học tự nhiên 8"),
    ]
    for cau, mon in mong_doi:
        if mon not in theo_ten:
            continue
        kiem(f"{cau[:46]:46s} -> {mon}", suy_ra_mon(cau) == theo_ten[mon],
             f"doan ra: {ten_mon.get(suy_ra_mon(cau))}")

    print("\n[2] Cau mo ho thi KHONG doan bua, giu nguyen toan kho")
    for cau in ("giải thích cực trị của hàm số", "hôm nay trời đẹp không",
                "giúp mình với", "bài này khó quá"):
        kiem(f"khong doan: {cau[:40]}", suy_ra_mon(cau) is None,
             f"lai doan ra {ten_mon.get(suy_ra_mon(cau))}")

    print("\n[3] Trich dan cho dung cau nguoi dung da bao loi")
    hits = retrieve("tạo cho tôi 10 câu toán 12 chương 1", uid, None, k=6)
    kiem("co lay duoc doan nao", bool(hits), "khong co doan nao")
    ngoai = [h["filename"] for h in hits if "Toán 12" not in h["filename"]]
    kiem("khong trich dan sach mon khac", not ngoai, str(ngoai))
    kiem("khong trich dan sach Tieng Anh",
         not any("Tieng_Anh" in h["filename"] for h in hits))

    print("\n[4] Khong dan mot trang nhieu lan")
    trang = [(h["filename"], h["page"]) for h in hits]
    kiem("moi trang chi xuat hien mot lan", len(trang) == len(set(trang)),
         f"{len(trang)} doan nhung chi {len(set(trang))} trang")
    noi_dung = [h["text"].strip()[:200] for h in hits]
    kiem("khong co hai doan noi dung y het", len(noi_dung) == len(set(noi_dung)))

    print("\n[5] Chon mon ro rang thi van ton trong lua chon do")
    if "Tiếng Anh 8" in theo_ten:
        h2 = retrieve("cực trị của hàm số", uid, theo_ten["Tiếng Anh 8"], k=4)
        kiem("chon Tieng Anh 8 -> chi ra sach Tieng Anh 8",
             all("Tieng_Anh" in h["filename"] for h in h2) if h2 else True,
             str([h["filename"] for h in h2]))

    print("\n[6] Hoi dung mon nhung khong ghi so lop")
    h3 = retrieve("cực trị của hàm số là gì", uid, theo_ten.get("Toán 12"), k=4)
    kiem("van lay duoc tai lieu Toan 12", bool(h3) and all("Toán 12" in h["filename"] for h in h3),
         str([h["filename"] for h in h3]))

    print("\n" + "=" * 72)
    print(f" {dat}/{dat + sai} phep thu dat")
    print("=" * 72)
    raise SystemExit(0 if sai == 0 else 1)


if __name__ == "__main__":
    main()
