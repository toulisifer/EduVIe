"""Đánh giá RAG trên bộ câu hỏi mẫu eval/questions.json.

Mỗi câu: {"q": câu hỏi, "pages": [trang chứa đáp án trong SGK], "answer": đáp án tham chiếu}

Chạy:
  python -m eval.rag_eval              # chỉ đo truy xuất (Hit@k, MRR) — KHÔNG tốn quota LLM
  python -m eval.rag_eval --judge      # thêm: sinh câu trả lời + LLM chấm điểm (2 request / câu)
  python -m eval.rag_eval --subject 1  # lọc theo môn

Kết quả ghi vào eval/results_<thời gian>.md để đưa vào báo cáo.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

from app.llm import generate_json
from app.rag.chat import SYSTEM, build_prompt, retrieve
from app.llm import generate

HERE = Path(__file__).parent
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "faithful": {"type": "integer"},   # 0-2: câu trả lời có bám tài liệu, không bịa?
        "correct": {"type": "integer"},    # 0-2: đúng so với đáp án tham chiếu?
        "note": {"type": "string"},
    },
    "required": ["faithful", "correct", "note"],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--subject", type=int, default=None)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    qs = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    rows, hits_at_k, rr_sum = [], 0, 0.0
    judge_f = judge_c = 0

    for i, item in enumerate(qs, 1):
        hits = retrieve(item["q"], user_id=0, subject_id=args.subject, k=args.k)
        pages = [h["page"] for h in hits]
        rank = next((r for r, p in enumerate(pages, 1) if p in item["pages"]), None)
        hit = rank is not None
        hits_at_k += hit
        rr_sum += (1 / rank) if hit else 0
        row = {"#": i, "q": item["q"], "expected": item["pages"], "got": pages, "hit": hit, "rank": rank}

        if args.judge:
            ans = generate(build_prompt(item["q"], hits, None), system=SYSTEM)
            ctx = "\n\n".join(h["text"] for h in hits)
            j = generate_json(
                f"""TÀI LIỆU:\n{ctx}\n\nCÂU HỎI: {item['q']}\nĐÁP ÁN THAM CHIẾU: {item['answer']}\nCÂU TRẢ LỜI CỦA HỆ THỐNG:\n{ans}\n
Chấm: faithful (0=bịa/không dựa tài liệu, 1=một phần, 2=hoàn toàn bám tài liệu), correct (0=sai, 1=đúng một phần, 2=đúng). Ghi chú ngắn.""",
                JUDGE_SCHEMA, system="Bạn là giám khảo nghiêm khắc, khách quan.", temperature=0.0)
            row.update(answer=ans, faithful=j["faithful"], correct=j["correct"], note=j["note"])
            judge_f += j["faithful"]; judge_c += j["correct"]
        rows.append(row)
        print(f"[{i}/{len(qs)}] {'✅' if hit else '❌'} rank={rank} expected={item['pages']} got={pages}")

    n = len(qs)
    lines = [f"# Kết quả đánh giá RAG — {datetime.now():%d/%m/%Y %H:%M}", "",
             f"- Số câu hỏi: {n}", f"- Hit@{args.k}: **{100*hits_at_k/n:.0f}%** ({hits_at_k}/{n})",
             f"- MRR: **{rr_sum/n:.2f}**"]
    if args.judge:
        lines += [f"- Faithfulness (0-2): **{judge_f/n:.2f}**", f"- Correctness (0-2): **{judge_c/n:.2f}**"]
    lines += ["", "| # | Câu hỏi | Trang đúng | Trang lấy được | Hit | Rank |" + (" Faithful | Correct | Ghi chú |" if args.judge else ""),
              "|---|---|---|---|---|---|" + ("---|---|---|" if args.judge else "")]
    for r in rows:
        line = f"| {r['#']} | {r['q']} | {r['expected']} | {r['got']} | {'✅' if r['hit'] else '❌'} | {r['rank'] or '-'} |"
        if args.judge:
            line += f" {r['faithful']} | {r['correct']} | {r['note']} |"
        lines.append(line)
    out = HERE / f"results_{datetime.now():%Y%m%d_%H%M}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("\n" + "\n".join(lines[:7]))
    print(f"\nĐã ghi: {out}")


if __name__ == "__main__":
    main()
