"""OCR vài trang mục lục của một cuốn sách để biết tên chương và khoảng trang.

Dùng:  python -m scripts.read_toc "/tmp/sgk8/ten_sach.pdf" 3 4 140 141
"""
import sys
from pathlib import Path

import pymupdf

from app.rag.ocr import ocr_pdf

path = Path(sys.argv[1])
doc = pymupdf.open(path)
pages = [int(x) for x in sys.argv[2:]] or [3, 4, doc.page_count - 1, doc.page_count]
pages = [p for p in pages if 1 <= p <= doc.page_count]
print(f"{path.name} — {doc.page_count} trang; OCR các trang {pages}\n")

out = ocr_pdf(path, pages, progress=lambda i, n, p: print(f"  … {i + 1}/{n} (trang {p})", file=sys.stderr))
for p in pages:
    print(f"########## TRANG {p} ##########")
    print((out.get(p) or "(trống)").strip()[:2500])
    print()
