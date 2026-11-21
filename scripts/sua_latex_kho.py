"""Chữa những câu đã lưu trong kho bị mất dấu gạch chéo của LaTeX.

Lỗi gốc đã vá ở app/llm.py (mọi JSON do AI sinh ra đều đi qua app.sua_latex), nhưng
câu lưu TRƯỚC khi vá vẫn hỏng: người học thấy chữ đỏ "rac{A'B'}{AB}" thay vì phân số.

Chữa cả ngân hàng câu hỏi lẫn những câu đã nằm trong đề đã phát.

  .venv/bin/python -m scripts.sua_latex_kho          # chỉ xem sẽ sửa gì
  .venv/bin/python -m scripts.sua_latex_kho --that   # sửa thật (sao lưu DB trước)
"""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime

from app import db
from app.config import DATA_DIR
from app.sua_latex import CO_KY_TU_HONG, sua_chuoi

FILE_DB = DATA_DIR / "app.db"


def _sua_mot(doi_tuong) -> list[tuple[str, str, str]]:
    """Sửa tại chỗ 3 trường văn bản. Trả về danh sách (tên trường, trước, sau)."""
    doi = []
    for truong in ("content", "explanation"):
        cu = getattr(doi_tuong, truong, None)
        if isinstance(cu, str) and CO_KY_TU_HONG.search(cu):
            moi = sua_chuoi(cu)
            if moi != cu:
                setattr(doi_tuong, truong, moi)
                doi.append((truong, cu, moi))
    ops = doi_tuong.options
    if isinstance(ops, list) and any(isinstance(o, str) and CO_KY_TU_HONG.search(o) for o in ops):
        moi = [sua_chuoi(o) if isinstance(o, str) else o for o in ops]
        if moi != ops:
            doi_tuong.options = moi
            doi.append(("options", str(ops)[:70], str(moi)[:70]))
    return doi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--that", action="store_true", help="sửa thật (mặc định chỉ xem)")
    a = ap.parse_args()
    db.init_db()

    print("=" * 74)
    print(" CHỮA CÔNG THỨC BỊ MẤT DẤU GẠCH CHÉO")
    print("=" * 74)

    bao_cao = []
    with db.SessionLocal() as s:
        for ten_bang, Model in (("ngân hàng", db.BankQuestion), ("câu trong đề", db.Question)):
            n_sua = 0
            for x in s.query(Model):
                doi = _sua_mot(x)
                if doi:
                    n_sua += 1
                    if len(bao_cao) < 6:
                        bao_cao.append((ten_bang, x.id, doi[0]))
            print(f"  {ten_bang:14s}: {n_sua} bản ghi cần chữa")
        if a.that:
            if FILE_DB.exists():
                sao = FILE_DB.with_name(f"app_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
                shutil.copy2(FILE_DB, sao)
                print(f"\n  đã sao lưu CSDL: {sao}")
            s.commit()
        else:
            s.rollback()

    if bao_cao:
        print("\n  vài chỗ sẽ đổi:")
        for bang, bid, (truong, cu, moi) in bao_cao:
            print(f"\n   {bang} #{bid} ({truong})")
            print(f"     trước: {cu[:72]!r}")
            print(f"     sau  : {moi[:72]!r}")

    if not a.that:
        print("\n  (chỉ mới xem — thêm --that để sửa thật)")
        return

    # kiểm chứng
    with db.SessionLocal() as s:
        con = 0
        for Model in (db.BankQuestion, db.Question):
            for x in s.query(Model):
                phan = [x.content or "", x.explanation or ""] + \
                       [str(o) for o in (x.options or [])]
                if any(c in p for p in phan for c in "\x08\x09\x0b\x0c\x0d"):
                    con += 1
    print(f"\n  còn bản ghi dính ký tự điều khiển: {con}")
    print("  Xong." if con == 0 else "  ⚠ Vẫn còn — xem lại danh sách tên lệnh trong app/sua_latex.py")


if __name__ == "__main__":
    main()
