"""Nạp một cuốn SGK theo từng chương (OCR nếu scan). Dùng khi nạp cả sách từ dòng lệnh.

Ví dụ:
  python -m scripts.ingest_book --user "phan ngọc vương" --subject "Vật lí 12" \
      --file data/uploads/1_SGK_Vat_li_12_KNTT.pdf --chapters "1:7-34" "2:35-56" "3:57-91" "4:92-124"
(chapters: <số thứ tự chương>:<trang PDF đầu>-<trang PDF cuối>)
"""
import argparse
from pathlib import Path

from app.db import Chapter, Document, SessionLocal, Subject, User
from app.rag.ingest import ingest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--chapters", nargs="+", required=True)
    a = ap.parse_args()
    pdf = Path(a.file)

    with SessionLocal() as s:
        uid = s.query(User).filter_by(username=a.user.lower()).first().id
        subj = s.query(Subject).filter_by(name=a.subject).first()
        chapters = s.query(Chapter).filter_by(subject_id=subj.id).order_by(Chapter.order).all()
        ch_ids = {i + 1: c.id for i, c in enumerate(chapters)}
        ch_names = {i + 1: c.name for i, c in enumerate(chapters)}

    for spec in a.chapters:
        idx, rng = spec.split(":")
        lo, hi = map(int, rng.split("-"))
        idx = int(idx)
        with SessionLocal() as s:
            d = Document(user_id=uid, subject_id=subj.id, chapter_id=ch_ids[idx],
                         filename=pdf.name.split("_", 1)[-1], path=str(pdf), status="pending")
            s.add(d); s.commit(); did = d.id
        print(f"== {ch_names[idx]}: trang {lo}-{hi}", flush=True)
        try:
            n = ingest(did, pdf, uid, subj.id, ch_ids[idx], pages=list(range(lo, hi + 1)),
                       progress=lambda i, t, p: print(f"  OCR trang {p} ({i + 1}/{t})", flush=True))
            st, err = "ready", ""
        except Exception as e:  # noqa: BLE001
            n, st, err = 0, "failed", str(e)
            print("  LỖI:", e, flush=True)
        with SessionLocal() as s:
            d = s.get(Document, did); d.n_chunks, d.status, d.error = n, st, err; s.commit()
        print(f"  -> {st}, {n} đoạn", flush=True)


if __name__ == "__main__":
    main()
