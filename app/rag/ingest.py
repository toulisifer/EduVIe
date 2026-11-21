"""PDF/DOCX/TXT/MD -> chunks -> embedding -> ChromaDB."""
from pathlib import Path

import chromadb
import pymupdf

from app.config import CHROMA_DIR, CHUNK_OVERLAP, CHUNK_SIZE
from app.llm import embed
from app.rag.ocr import ocr_pdf

_chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
MIN_TEXT_CHARS = 30  # dưới mức này coi như trang scan


def collection():
    return _chroma.get_or_create_collection("chunks", metadata={"hnsw:space": "cosine"})


def _read_docx(path: Path) -> str:
    import docx  # python-docx
    d = docx.Document(str(path))
    parts = [para.text for para in d.paragraphs]
    for tbl in d.tables:  # bảng -> từng dòng, ô cách nhau bởi ' | '
        parts += [" | ".join(c.text for c in row.cells) for row in tbl.rows]
    return "\n".join(parts)


def extract_pages(path: Path, pages: list[int] | None = None, progress=None) -> list[tuple[int, str]]:
    """Trả về [(số trang, text)] — giữ số trang để trích dẫn. Trang PDF scan sẽ được OCR bằng Gemini."""
    ext = path.suffix.lower()
    if ext == ".docx":
        return [(1, _read_docx(path))]
    if ext != ".pdf":
        return [(1, path.read_text(encoding="utf-8", errors="ignore"))]

    with pymupdf.open(path) as doc:
        targets = pages or list(range(1, len(doc) + 1))
        result = {p: doc[p - 1].get_text() for p in targets}
    scanned = [p for p, t in result.items() if len(t.strip()) < MIN_TEXT_CHARS]
    if scanned:
        result.update(ocr_pdf(path, scanned, progress))
    return [(p, result[p]) for p in targets]


def split_text(text: str) -> list[str]:
    """Cắt theo đoạn văn, gộp đến CHUNK_SIZE, có overlap."""
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks, buf = [], ""
    for p in paras:
        if len(buf) + len(p) > CHUNK_SIZE and buf:
            chunks.append(buf)
            buf = buf[-CHUNK_OVERLAP:] + "\n" + p
        else:
            buf = (buf + "\n" + p) if buf else p
    if buf.strip():
        chunks.append(buf)
    return [c for c in chunks if len(c) > 50]


def ingest(doc_id: int, path: Path, user_id: int, subject_id: int, chapter_id: int | None,
           pages: list[int] | None = None, progress=None) -> int:
    ids, docs, metas = [], [], []
    for page_no, text in extract_pages(path, pages, progress):
        for j, chunk in enumerate(split_text(text)):
            ids.append(f"{doc_id}-{page_no}-{j}")
            docs.append(chunk)
            metas.append({
                "doc_id": doc_id, "page": page_no, "user_id": user_id,
                "subject_id": subject_id, "chapter_id": chapter_id or 0,
                "filename": path.name,
            })
    if not docs:
        raise ValueError("Không trích xuất được văn bản")
    vectors = embed(docs, task="RETRIEVAL_DOCUMENT")
    col = collection()
    for i in range(0, len(ids), 500):
        col.upsert(ids=ids[i:i + 500], documents=docs[i:i + 500],
                   embeddings=vectors[i:i + 500], metadatas=metas[i:i + 500])
    return len(ids)


def delete_document(doc_id: int):
    collection().delete(where={"doc_id": doc_id})
