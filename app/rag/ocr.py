"""OCR trang PDF scan bằng Gemini (đọc ảnh -> Markdown + LaTeX).

Kết quả cache theo hash nội dung file (data/ocr_cache/<hash>.json) nên upload lại
cùng một PDF không phải OCR lại.
"""
import hashlib
import json
from pathlib import Path

import pymupdf
from google.genai import types

from app.config import DATA_DIR
from app.llm import OCR_MODELS, call_with_fallback

CACHE_DIR = DATA_DIR / "ocr_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

OCR_PROMPT = """Đây là ảnh một trang sách giáo khoa tiếng Việt. Hãy chép lại TOÀN BỘ nội dung văn bản trên trang:
- Giữ nguyên tiếng Việt, đúng chính tả, đúng thứ tự đọc.
- Công thức toán viết bằng LaTeX trong $...$ (inline) hoặc $$...$$ (block).
- Dùng Markdown: tiêu đề (#, ##), danh sách, bảng nếu có.
- Với hình vẽ/đồ thị, chỉ ghi ngắn gọn [Hình: mô tả 1 dòng].
- Bỏ qua số trang, header/footer trang trí.
- Chỉ trả về nội dung, không thêm lời dẫn."""


def _file_hash(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()[:16]


def _ocr_image(png: bytes) -> str:
    res = call_with_fallback(
        OCR_MODELS,
        [types.Part.from_bytes(data=png, mime_type="image/png"), OCR_PROMPT],
        types.GenerateContentConfig(temperature=0.0),
    )
    return res.text or ""


def ocr_pdf(path: Path, pages: list[int] | None = None, progress=None) -> dict[int, str]:
    """Trả về {số trang (1-based): text}. `pages` = danh sách trang cần OCR (1-based), None = tất cả."""
    cache_file = CACHE_DIR / f"{_file_hash(path)}.json"
    cache: dict[int, str] = {}
    if cache_file.exists():
        cache = {int(k): v for k, v in json.loads(cache_file.read_text(encoding="utf-8")).items()}

    with pymupdf.open(path) as doc:
        targets = pages or list(range(1, len(doc) + 1))
        todo = [p for p in targets if p not in cache]
        for i, page_no in enumerate(todo):
            if progress:
                progress(i, len(todo), page_no)
            pix = doc[page_no - 1].get_pixmap(matrix=pymupdf.Matrix(1.6, 1.6))  # ~115 dpi, đủ đọc
            cache[page_no] = _ocr_image(pix.tobytes("png"))
            cache_file.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    return {p: cache[p] for p in targets if p in cache}
