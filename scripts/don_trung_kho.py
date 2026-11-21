"""Dọn đoạn trùng trong kho vector — mặc định chỉ XEM, không sửa gì.

Vì sao kho bị trùng: mỗi lần tải sách lên là một bản ghi tài liệu riêng, và cùng một
cuốn đã được tải nhiều lần. Phần lớn là tải theo từng khoảng trang (tr.1-40, rồi
tr.41-46...) — việc này hợp lệ, không phải trùng. Trùng thật nằm ở ba chỗ:

  1. BẢN GHI RỖNG — tải lên hỏng, không sinh đoạn nào. Chỉ làm rối thư viện.
  2. TRANG BỊ NẠP HAI LẦN — ví dụ Hoá 12 có một lần nạp cả cuốn (tr.1-103) và bảy
     lần nạp theo lát (tr.22-147). Vùng tr.22-103 nằm trong cả hai, mà hai lần nạp
     cắt đoạn ở vị trí khác nhau nên văn bản không giống hệt — so chuỗi không bắt được.
  3. ĐOẠN Y HỆT NHAU — cùng tệp, cùng trang, cùng nội dung.

Nguyên tắc: MỖI TRANG CHỈ GIỮ ĐOẠN CỦA ĐÚNG MỘT LẦN NẠP. Khi một trang được nhiều
lần nạp phủ, giữ lần nạp có khoảng trang HẸP NHẤT — lần nạp theo lát bám sát nội
dung hơn lần nạp cả cuốn. Nhờ vậy số trang được phủ không đổi, chỉ bớt bản sao.

  .venv/bin/python -m scripts.don_trung_kho          # xem sẽ xoá gì
  .venv/bin/python -m scripts.don_trung_kho --that   # xoá thật (tự sao lưu trước)
"""
from __future__ import annotations

import argparse
import shutil
from collections import defaultdict
from datetime import datetime

from app import db
from app.config import DATA_DIR
from app.rag.ingest import collection

KHO = DATA_DIR / "chroma"


def doc_kho():
    col = collection()
    res = col.get(include=["metadatas", "documents"], limit=1000000)
    return col, res["ids"], res["metadatas"], res["documents"]


def _khoang_trang(theo_doc):
    """{doc_id: (trang nhỏ nhất, trang lớn nhất, số đoạn)}"""
    ra = {}
    for did, ds in theo_doc.items():
        trang = [p for p, _, _ in ds]
        ra[did] = (min(trang), max(trang), len(ds)) if trang else (0, 0, 0)
    return ra


def phan_tich():
    _, ids, metas, docs = doc_kho()
    theo_doc = defaultdict(list)
    for cid, m, d in zip(ids, metas, docs):
        theo_doc[m["doc_id"]].append((m["page"], cid, d.strip()))
    khoang = _khoang_trang(theo_doc)

    with db.SessionLocal() as s:
        ban_ghi = {d.id: d.filename for d in s.query(db.Document)}

    # ---- 1. bản ghi tài liệu không có đoạn nào
    rong = sorted(did for did in ban_ghi if did not in theo_doc)

    # ---- 2. mỗi (tệp, trang) giữ đúng một lần nạp
    phu = defaultdict(set)                      # (tên tệp, trang) -> {doc_id}
    for did, ds in theo_doc.items():
        ten = ban_ghi.get(did, f"?{did}")
        for p, _, _ in ds:
            phu[(ten, p)].add(did)

    giu_cho_trang = {}
    for khoa, dids in phu.items():
        if len(dids) == 1:
            giu_cho_trang[khoa] = next(iter(dids))
            continue
        # khoảng trang hẹp nhất trước; hoà thì lấy bản nạp mới hơn (doc_id lớn hơn)
        giu_cho_trang[khoa] = min(dids, key=lambda d: (khoang[d][1] - khoang[d][0], -d))

    xoa_trung_trang = []
    for did, ds in theo_doc.items():
        ten = ban_ghi.get(did, f"?{did}")
        for p, cid, _ in ds:
            if giu_cho_trang[(ten, p)] != did:
                xoa_trung_trang.append(cid)
    bo_xoa = set(xoa_trung_trang)

    # ---- 3. trong phần còn lại, bỏ đoạn y hệt nhau
    nhom = defaultdict(list)
    for cid, m, d in zip(ids, metas, docs):
        if cid in bo_xoa:
            continue
        ten = ban_ghi.get(m["doc_id"], f"?{m['doc_id']}")
        nhom[(ten, m["page"], d.strip())].append(cid)
    xoa_y_het = [c for v in nhom.values() if len(v) > 1 for c in sorted(v)[1:]]
    bo_xoa |= set(xoa_y_het)

    # ---- kiểm: không trang nào bị xoá sạch
    con_lai = defaultdict(int)
    for cid, m in zip(ids, metas):
        if cid not in bo_xoa:
            con_lai[(ban_ghi.get(m["doc_id"], "?"), m["page"])] += 1
    mat_trang = [k for k in phu if con_lai.get(k, 0) == 0]

    return {
        "tong": len(ids),
        "rong": rong,
        "ban_ghi": ban_ghi,
        "khoang": khoang,
        "xoa_trung_trang": xoa_trung_trang,
        "xoa_y_het": xoa_y_het,
        "bo_xoa": bo_xoa,
        "mat_trang": mat_trang,
        "trang_truoc": set(phu),
    }


def in_bao_cao(kq):
    print("=" * 72)
    print(" DỌN KHO VECTOR")
    print("=" * 72)
    print(f"  đoạn hiện có                 : {kq['tong']}")
    print(f"  bản ghi tài liệu không có đoạn: {len(kq['rong'])} "
          f"{[f'#{d}' for d in kq['rong']]}")
    print(f"  đoạn thuộc trang đã có lần nạp khác: {len(kq['xoa_trung_trang'])}")
    print(f"  đoạn y hệt nhau còn sót      : {len(kq['xoa_y_het'])}")
    print(f"  TỔNG SẼ XOÁ                  : {len(kq['bo_xoa'])}")
    print(f"  còn lại sau khi dọn          : {kq['tong'] - len(kq['bo_xoa'])}")
    if kq["mat_trang"]:
        print(f"  ⚠ CẢNH BÁO: {len(kq['mat_trang'])} trang sẽ không còn đoạn nào!")
    else:
        print(f"  số trang được phủ            : {len(kq['trang_truoc'])} (KHÔNG đổi)")

    theo_tep = defaultdict(int)
    for did, ds in _gom_theo_doc(kq):
        theo_tep[kq["ban_ghi"].get(did, "?")] += ds
    if theo_tep:
        print("\n  xoá theo tài liệu:")
        for ten, n in sorted(theo_tep.items(), key=lambda x: -x[1]):
            if n:
                print(f"     {n:5d}  {ten[:52]}")


def _gom_theo_doc(kq):
    """[(doc_id, số đoạn bị xoá)] — đọc lại metadata để quy đoạn về tài liệu."""
    _, ids, metas, _ = doc_kho()
    dem = defaultdict(int)
    for cid, m in zip(ids, metas):
        if cid in kq["bo_xoa"]:
            dem[m["doc_id"]] += 1
    return list(dem.items())


def sao_luu() -> str:
    dich = KHO.parent / f"chroma_backup_{datetime.now():%Y%m%d_%H%M%S}"
    shutil.copytree(KHO, dich)
    return str(dich)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--that", action="store_true", help="xoá thật (mặc định chỉ xem)")
    a = ap.parse_args()

    db.init_db()
    kq = phan_tich()
    in_bao_cao(kq)

    if kq["mat_trang"]:
        print("\n  Dừng lại: phép dọn này làm mất trang. Không xoá gì cả.")
        raise SystemExit(1)
    if not kq["bo_xoa"] and not kq["rong"]:
        print("\n  Kho đã sạch, không có gì để dọn.")
        raise SystemExit(0)
    if not a.that:
        print("\n  (chỉ mới xem — thêm --that để xoá thật)")
        raise SystemExit(0)

    print(f"\n  đang sao lưu kho…")
    print(f"  bản sao lưu: {sao_luu()}")

    col = collection()
    ds = sorted(kq["bo_xoa"])
    for i in range(0, len(ds), 500):
        col.delete(ids=ds[i:i + 500])
    with db.SessionLocal() as s:
        for did in kq["rong"]:
            d = s.get(db.Document, did)
            if d:
                s.delete(d)
        s.commit()

    # ---- kiểm chứng sau khi xoá
    _, ids2, metas2, docs2 = doc_kho()
    with db.SessionLocal() as s:
        ten2 = {d.id: d.filename for d in s.query(db.Document)}
    trang_sau = {(ten2.get(m["doc_id"], "?"), m["page"]) for m in metas2}
    con_trung = len(docs2) - len({(ten2.get(m["doc_id"], "?"), m["page"], d.strip())
                                  for m, d in zip(metas2, docs2)})
    print()
    print("=" * 72)
    print(" SAU KHI DỌN")
    print("=" * 72)
    print(f"  đoạn còn lại     : {len(ids2)}  (trước: {kq['tong']})")
    print(f"  trang được phủ   : {len(trang_sau)}  (trước: {len(kq['trang_truoc'])})")
    print(f"  đoạn còn trùng   : {con_trung}")
    thieu = kq["trang_truoc"] - trang_sau
    print(f"  trang bị mất     : {len(thieu)}" + (f"  {sorted(thieu)[:5]}" if thieu else ""))
    with db.SessionLocal() as s:
        print(f"  bản ghi tài liệu : {s.query(db.Document).count()}")
    if thieu or con_trung:
        print("\n  ⚠ Kết quả không như mong đợi — khôi phục từ bản sao lưu ở trên.")
        raise SystemExit(1)
    print("\n  Xong.")


if __name__ == "__main__":
    main()
