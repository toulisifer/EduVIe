"""Huấn luyện & đánh giá Knowledge Tracing trên ASSISTments 2009.

  python -m scripts.train_kt                 # đầy đủ (~5-10 phút CPU)
  python -m scripts.train_kt --epochs 3      # nhanh

Kết quả: data/kt/dkt_assist.pt (model) và eval/kt_results.md (bảng so sánh baseline vs DKT).
"""
import argparse
import random
import time
from datetime import datetime
from pathlib import Path

from app.ml import kt

DATA = Path("data/kt")
OUT = Path("eval/kt_results.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--hidden", type=int, default=100)
    a = ap.parse_args()

    train_all = kt.load_triples(DATA / "assist2009_updated_train.csv")
    test = kt.load_triples(DATA / "assist2009_updated_test.csv")
    random.seed(0); random.shuffle(train_all)
    n_val = len(train_all) // 10
    valid, train = train_all[:n_val], train_all[n_val:]
    K = max(kt.n_skills_of(train_all), kt.n_skills_of(test))
    n_inter = sum(len(s) for s, _ in train_all + test)
    print(f"train {len(train)} hs, valid {len(valid)} hs, test {len(test)} hs, {K} kỹ năng, {n_inter} tương tác")

    rows = []
    t0 = time.time(); r = kt.baseline_global(train, test); rows.append(("Tỷ lệ đúng toàn cục", r, time.time() - t0))
    t0 = time.time(); r = kt.baseline_skill_mean(train, test, K); rows.append(("Tỷ lệ đúng theo kỹ năng", r, time.time() - t0))
    print("baselines xong; logistic regression...")
    t0 = time.time(); r = kt.baseline_logreg(train, test, K); rows.append(("Logistic Regression (đặc trưng thủ công)", r, time.time() - t0))
    print(f"  LR: auc={r['auc']:.4f}")
    print("DKT...")
    t0 = time.time()
    res = kt.train_dkt(train, valid, K, epochs=a.epochs, hidden=a.hidden)
    r = kt.evaluate_dkt(res.model, test, K)
    rows.append((f"DKT (LSTM hidden={a.hidden}, {a.epochs} epoch)", r, time.time() - t0))
    kt.save(res.model, DATA / "dkt_assist.pt", {"dataset": "assist2009", "test": r, "history": res.history})

    lines = [f"# Knowledge Tracing — ASSISTments 2009 — {datetime.now():%d/%m/%Y %H:%M}", "",
             f"- Dữ liệu: {len(train)} học sinh train, {len(valid)} valid, {len(test)} test; {K} kỹ năng; {n_inter:,} tương tác.",
             "- Bài toán: dự đoán đúng/sai câu tiếp theo từ lịch sử (kỹ năng, kết quả).", "",
             "| Mô hình | AUC | Accuracy | Thời gian |", "|---|---|---|---|"]
    for name, r, sec in rows:
        lines.append(f"| {name} | **{r['auc']:.4f}** | {r['acc']:.4f} | {sec:.0f}s |")
    lines += ["", "## Quá trình huấn luyện DKT", "", "| Epoch | Loss | Val AUC | Val Acc |", "|---|---|---|---|"]
    lines += [f"| {h['epoch']} | {h['loss']:.4f} | {h['auc']:.4f} | {h['acc']:.4f} |" for h in res.history]
    lines += ["", "Tham khảo: DKT gốc (Piech et al., 2015) báo cáo AUC ≈ 0.86 trên ASSISTments 2009 với "
              "phiên bản dữ liệu cũ; các nghiên cứu sau trên bản đã làm sạch (updated) thường đạt 0.75–0.82."]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:12]))
    print(f"\nĐã ghi {OUT} và {DATA / 'dkt_assist.pt'}")


if __name__ == "__main__":
    main()
