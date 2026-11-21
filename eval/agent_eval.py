"""Đánh giá agent lập kế hoạch bằng bộ kiểm tra cứng (không tốn LLM) — dùng làm regression test.

  python -m eval.agent_eval            # chấm lại MỌI kế hoạch trong DB theo 5 luật -> pass rate, vi phạm theo luật
  python -m eval.agent_eval --live     # thêm: tạo 1 kế hoạch mới cho user demo bằng chế độ nhanh rồi chấm (1 request)

Dùng khi đổi prompt/tool của agent: chạy trước & sau, so pass rate. Kết quả ghi eval/agent_results.md
"""
import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path

from app.db import SessionLocal, StudyPlan, User
from app.reflection import RULES, auto_repair, validate_plan

OUT = Path("eval/agent_results.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    a = ap.parse_args()

    if a.live:
        from app.advisor import build_plan
        with SessionLocal() as s:
            uid = s.query(User).filter_by(username="demo").first().id
        pid = build_plan(uid, 1, "eval", 5, 1.0)
        print(f"đã tạo plan #{pid} (quick) cho demo")

    with SessionLocal() as s:
        plans = s.query(StudyPlan).order_by(StudyPlan.id).all()
        data = [(p.id, p.user_id, p.subject_id, p.days, p.created_at,
                 [{"day": i.day, "topic_id": i.topic_id, "kind": i.kind} for i in p.items]) for p in plans]
    rows, per_rule, n_after = [], Counter(), 0
    for pid, uid, sid, days, at, items in data:
        v = validate_plan(items, uid, sid, days)
        for x in v:
            per_rule[x.split(":")[0]] += 1
        fixed, _ = auto_repair(items, uid, sid, days)
        va = validate_plan(fixed, uid, sid, days)
        n_after += len(va)
        rows.append((pid, uid, at, len(items), v, va))
    n = len(rows)
    n_pass = sum(1 for r in rows if not r[4])
    n_pass_after = sum(1 for r in rows if not r[5])
    lines = [f"# Đánh giá agent lập kế hoạch — {datetime.now():%d/%m/%Y %H:%M}", "",
             f"- Số kế hoạch: {n}", f"- Pass (không vi phạm luật nào): **{n_pass}/{n}** ({100*n_pass/max(n,1):.0f}%)",
             f"- Tổng vi phạm (LLM thuần): {sum(per_rule.values())}",
             f"- Sau bước code tự sửa (auto_repair): pass **{n_pass_after}/{n}** ({100*n_pass_after/max(n,1):.0f}%), còn {n_after} vi phạm",
             "", "| Luật | Mô tả | Số vi phạm (LLM thuần) |", "|---|---|---|"]
    lines += [f"| {k} | {RULES[k]} | {per_rule.get(k, 0)} |" for k in RULES]
    lines += ["", "| Plan | User | Tạo lúc | Việc | Vi phạm (LLM) | Sau code sửa |", "|---|---|---|---|---|---|"]
    lines += [f"| {pid} | {uid} | {at:%d/%m %H:%M} | {ni} | {'✅' if not v else '<br>'.join(v)} | {'✅' if not va else len(va)} |" for pid, uid, at, ni, v, va in rows]
    lines += ["", "Lưu ý: luật R3 (đến hạn ôn) được chấm theo trạng thái HIỆN TẠI, nên kế hoạch cũ có thể bị tính vi phạm dù lúc tạo là đúng."]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:12]))
    print(f"\nĐã ghi {OUT}")


if __name__ == "__main__":
    main()
