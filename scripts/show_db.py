"""Trình diễn CSDL cho người chấm: in code kết nối (kèm file:dòng) rồi kết nối thật và truy vấn.

    python -m scripts.show_db            # tổng quan
    python -m scripts.show_db --sql "select username, role from users"   # chạy SQL tuỳ ý
    python -m scripts.show_db --table answers        # cấu trúc cột + 10 dòng dữ liệu của 1 bảng
    python -m scripts.show_db --table all            # tất cả bảng, mỗi bảng 3 dòng
    python -m scripts.show_db --join                 # minh hoạ khoá ngoại nối 6 bảng thành thông tin đầy đủ
"""
import argparse
import re
import sqlite3
from pathlib import Path

from app.config import CHROMA_DIR, DB_PATH

ROOT = Path(__file__).resolve().parent.parent


def show_code(path: str, pattern: str, before: int = 0, after: int = 0):
    """In các dòng code khớp pattern, kèm số dòng — để chỉ đích danh cho người xem."""
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    for i, ln in enumerate(lines):
        if re.search(pattern, ln):
            lo, hi = max(0, i - before), min(len(lines), i + after + 1)
            print(f"  📄 {path}")
            for j in range(lo, hi):
                print(f"  {j + 1:4d} │ {lines[j]}")
            print()
            break


def show_table(name: str, n_rows: int):
    con = sqlite3.connect(DB_PATH)
    names = [r[0] for r in con.execute("select name from sqlite_master where type='table' order by name")]
    targets = names if name == "all" else [name]
    for t in targets:
        if t not in names:
            print(f"Không có bảng '{t}'. Có: {', '.join(names)}"); return
        fks = {f[3]: f"{f[2]}.{f[4]}" for f in con.execute(f"pragma foreign_key_list({t})")}
        total = con.execute(f"select count(*) from {t}").fetchone()[0]
        print("=" * 70); print(f" BẢNG {t}   ({total} dòng)"); print("=" * 70)
        print(f"  {'cột':22s} {'kiểu':10s} {'khoá':28s} {'null':5s} mặc định")
        for cid, cname, ctype, notnull, dflt, pk in con.execute(f"pragma table_info({t})"):
            key = "PK" if pk else (f"FK → {fks[cname]}" if cname in fks else "")
            print(f"  {cname:22s} {(ctype or '').lower():10s} {key:28s} {'no' if notnull else 'yes':5s} {dflt or ''}")
        k = 3 if name == "all" else n_rows
        cur = con.execute(f"select * from {t} limit {k}")
        cols = [d[0] for d in cur.description]
        rows = cur.fetchall()
        print(f"\n  Dữ liệu ({len(rows)}/{total} dòng đầu):")
        if rows:
            width = {c: min(28, max(len(c), *(len(str(r[i])) for r in rows))) for i, c in enumerate(cols)}
            print("  " + " │ ".join(c[:width[c]].ljust(width[c]) for c in cols))
            print("  " + "─┼─".join("─" * width[c] for c in cols))
            for r in rows:
                cells = []
                for i, c in enumerate(cols):
                    v = "" if r[i] is None else str(r[i]).replace(chr(10), " ")
                    if c in ("password_hash", "recovery_hash") and v:
                        v = v[:12] + "…(bcrypt)"
                    cells.append(v[:width[c]].ljust(width[c]))
                print("  " + " │ ".join(cells))
        print()
    con.close()


def show_join():
    """Một dòng answers chỉ có id -> JOIN 6 bảng -> ai, làm câu gì, chủ đề nào, chương/môn nào, đúng hay sai."""
    con = sqlite3.connect(DB_PATH)
    print("=" * 70); print(" A. Dòng thô trong bảng answers (chỉ toàn khoá ngoại — không tự đọc được)"); print("=" * 70)
    cur = con.execute("select id, user_id, attempt_id, question_id, topic_id, selected, is_correct from answers where is_correct=1 limit 1")
    cols = [d[0] for d in cur.description]; row = cur.fetchone()
    for c, v in zip(cols, row):
        print(f"  {c:12s} = {v}")
    aid = row[0]
    sql = """
        select u.username            as hoc_sinh,
               s.name                as mon,
               c.name                as chuong,
               t.name                as chu_de,
               substr(q.content,1,60) as cau_hoi,
               q.options             as lua_chon,
               q.correct             as dap_an_dung,
               a.selected            as da_chon,
               a.is_correct          as dung,
               at.score              as diem_bai,
               a.answered_at         as luc
        from answers a
        join users     u  on u.id  = a.user_id
        join questions q  on q.id  = a.question_id
        join topics    t  on t.id  = a.topic_id
        join chapters  c  on c.id  = t.chapter_id
        join subjects  s  on s.id  = c.subject_id
        join attempts  at on at.id = a.attempt_id
        where a.id = ?"""
    print(); print("=" * 70); print(" B. Cùng dòng đó sau khi JOIN 6 bảng qua khoá ngoại"); print("=" * 70)
    print("  SQL:" + sql.replace(chr(10), chr(10) + "      "))
    cur = con.execute(sql, (aid,)); cols = [d[0] for d in cur.description]; r = cur.fetchone()
    print()
    for c, v in zip(cols, r):
        print(f"  {c:12s} = {v}")
    print()
    print("=" * 70); print(" C. Nhờ vậy mới tính được mastery theo chủ đề (1 câu SQL trên 3 bảng)"); print("=" * 70)
    sql2 = """
        select t.name as chu_de, count(*) as so_cau, round(100.0*avg(a.is_correct)) as ty_le_dung
        from answers a join topics t on t.id = a.topic_id join users u on u.id = a.user_id
        where u.username = 'demo' group by t.name order by ty_le_dung"""
    print("  SQL:" + sql2.replace(chr(10), chr(10) + "      ")); print()
    for r in con.execute(sql2):
        bar = "█" * int((r[2] or 0) / 5)
        print(f"  {r[0]:34s} {r[1]:3d} câu  {r[2]:5.0f}%  {bar}")
    con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", help="câu SQL tuỳ ý để chạy trên app.db")
    ap.add_argument("--table", help="tên bảng (hoặc 'all') để xem cấu trúc + dữ liệu")
    ap.add_argument("--rows", type=int, default=10)
    ap.add_argument("--join", action="store_true", help="minh hoạ khoá ngoại nối các bảng thành thông tin đầy đủ")
    a = ap.parse_args()
    if a.table:
        return show_table(a.table, a.rows)
    if a.join:
        return show_join()

    print("=" * 70)
    print(" 1. CODE KẾT NỐI (đúng file và số dòng trong dự án)")
    print("=" * 70)
    show_code("app/config.py", r"^DB_PATH", before=3)
    show_code("app/db.py", r"engine = create_engine", after=1)
    show_code("app/rag/ingest.py", r"_chroma = chromadb", after=0)
    show_code("app/rag/ingest.py", r"def collection", after=1)
    show_code("app/db.py", r"def init_db", after=3)

    print("=" * 70)
    print(" 2. KẾT NỐI THẬT VÀO SQLite")
    print("=" * 70)
    print(f"  File      : {DB_PATH}  ({DB_PATH.stat().st_size / 1024:.0f} KB)")
    print(f"  Chuỗi     : sqlite:///{DB_PATH}")
    con = sqlite3.connect(DB_PATH)
    print(f"  Phiên bản : SQLite {sqlite3.sqlite_version}")
    tables = [r[0] for r in con.execute("select name from sqlite_master where type='table' order by name")]
    print(f"  Bảng      : {len(tables)}")
    for t in tables:
        n = con.execute(f"select count(*) from {t}").fetchone()[0]
        cols = [c[1] for c in con.execute(f"pragma table_info({t})")]
        fks = [(f[3], f[2]) for f in con.execute(f"pragma foreign_key_list({t})")]
        fk_s = ("  FK: " + ", ".join(f"{c}→{r}" for c, r in fks)) if fks else ""
        print(f"    {t:24s} {n:5d} dòng  {len(cols):2d} cột{fk_s}")

    print()
    print("=" * 70)
    print(" 3. TRUY VẤN MẪU")
    print("=" * 70)
    sql = a.sql or """
        select u.username, count(a.id) as so_cau, round(100.0*avg(a.is_correct)) as ty_le_dung
        from answers a join users u on u.id = a.user_id
        group by u.username order by so_cau desc limit 5"""
    print("  SQL:", " ".join(sql.split()))
    cur = con.execute(sql)
    print("  " + " | ".join(d[0] for d in cur.description))
    for row in cur.fetchall():
        print("  " + " | ".join(str(x) for x in row))
    con.close()

    print()
    print("=" * 70)
    print(" 4. KẾT NỐI THẬT VÀO ChromaDB (vector store)")
    print("=" * 70)
    from app.rag.ingest import collection
    col = collection()
    print(f"  Thư mục   : {CHROMA_DIR}")
    print(f"  Collection: {col.name}  ·  {col.count():,} vector  ·  metric: cosine")
    r = col.peek(1)
    print(f"  Chiều     : {len(r['embeddings'][0])}")
    print(f"  Metadata  : {r['metadatas'][0]}")
    print(f"  Đoạn mẫu  : {r['documents'][0][:120].replace(chr(10), ' ')}…")
    print()
    print("  Cách đọc/ghi trong code:  with SessionLocal() as s: s.query(...) / s.add(...); s.commit()")
    print("                            collection().query(query_embeddings=[v], n_results=k, where={...})")


if __name__ == "__main__":
    main()
