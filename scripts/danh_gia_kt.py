"""So DKT với ba phương pháp đối chứng TRÊN CHÍNH DỮ LIỆU CỦA HỆ THỐNG.

Khác scripts/train_kt.py (chạy trên ASSISTments 2009, 325 nghìn tương tác), script này
đo trên bảng `answers` của hệ thống đang chạy. Dùng để trả lời câu "huấn luyện xong thì
có tốt hơn không" bằng số, chứ không bằng cảm giác.

Cách đo:
  - Chia tập THEO NGƯỜI, không theo câu. Người trong tập huấn luyện không xuất hiện ở
    tập chấm; nếu chia theo câu thì mô hình chỉ cần nhớ thói quen của từng người là đã
    có AUC cao, và con số đó không nói lên khả năng tổng quát.
  - Dữ liệu đi qua lớp lọc chống đầu độc (app/ml/kt_app.loc_dau_doc) trước khi chia.
  - Lặp nhiều lần với các cách chia khác nhau rồi lấy trung bình, vì dữ liệu còn ít.

Chạy:  .venv/bin/python -m scripts.danh_gia_kt
       .venv/bin/python -m scripts.danh_gia_kt --lan 5 --epochs 30
"""
from __future__ import annotations

import argparse
import random
import statistics

from app.ml import kt, kt_app

# Dưới mức này thì con số đo được chỉ mang tính minh hoạ cách đo, không kết luận được gì.
DU_DE_KET_LUAN_NGUOI = 10
DU_DE_KET_LUAN_CAU = 300


def im(*_):
    pass


def chia_theo_nguoi(seqs: list[kt.Seq], ti_le_cham: float, hat: int):
    """Trả về (tập huấn luyện, tập chấm) — tách rời theo người."""
    thu_tu = list(range(len(seqs)))
    random.Random(hat).shuffle(thu_tu)
    n_cham = max(1, int(len(seqs) * ti_le_cham))
    cham = [seqs[i] for i in thu_tu[:n_cham]]
    train = [seqs[i] for i in thu_tu[n_cham:]]
    return train, cham


def mot_lan(seqs: list[kt.Seq], K: int, hat: int, epochs: int, hidden: int) -> dict[str, float] | None:
    train, cham = chia_theo_nguoi(seqs, 0.3, hat)
    if len(train) < 2 or not cham:
        return None
    ket: dict[str, float] = {}
    try:
        ket["Đoán theo tỉ lệ đúng chung"] = kt.baseline_global(train, cham)["auc"]
    except ValueError:      # tập chấm chỉ có một loại nhãn -> AUC không định nghĩa được
        return None
    try:
        ket["Tỉ lệ đúng theo chủ đề"] = kt.baseline_skill_mean(train, cham, K)["auc"]
        ket["Logistic Regression"] = kt.baseline_logreg(train, cham, K)["auc"]
    except Exception:       # noqa: BLE001 - dữ liệu quá ít cho sklearn
        pass
    res = kt.train_dkt(train, cham, K, epochs=epochs, hidden=hidden,
                       max_len=100, batch_size=16, lr=3e-3, log=im)
    ket["DKT (LSTM)"] = kt.evaluate_dkt(res.model, cham, K, max_len=100)["auc"]
    # mô hình chưa huấn luyện: cùng kiến trúc, trọng số khởi tạo ngẫu nhiên
    ket["DKT chưa huấn luyện"] = kt.evaluate_dkt(kt.DKT(K, hidden), cham, K, max_len=100)["auc"]
    return ket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lan", type=int, default=5, help="số lần chia lại để lấy trung bình")
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--hidden", type=int, default=32)
    a = ap.parse_args()

    tho, idx = kt_app._chuoi_tho()
    sach, bao_cao = kt_app.loc_dau_doc(tho, log=im)
    seqs = [v for v in sach.values() if len(v[0]) >= 2]
    K = len(idx)
    n_cau = sum(len(s) for s, _ in seqs)

    print("=" * 72)
    print(" ĐÁNH GIÁ KNOWLEDGE TRACING TRÊN DỮ LIỆU CỦA HỆ THỐNG")
    print("=" * 72)
    print(f"  Thô              : {bao_cao['cau_tho']} câu")
    print(f"  Sau lớp lọc      : {n_cau} câu · {len(seqs)} người · {K} chủ đề")
    if bao_cao["nguoi_bi_loai"]:
        print(f"  Bị loại          : {bao_cao['nguoi_bi_loai']} người")
    if bao_cao["bi_cat_bot"]:
        print(f"  Bị cắt cho cân   : {bao_cao['bi_cat_bot']} (trần {bao_cao['tran_moi_nguoi']} câu/người)")
    print(f"  Cách chia        : theo NGƯỜI, 70% huấn luyện / 30% chấm, lặp {a.lan} lần")

    if len(seqs) < 4:
        print("\n  Chưa đủ người để chia tập. Cần ít nhất 4 người.")
        raise SystemExit(1)

    gom: dict[str, list[float]] = {}
    for i in range(a.lan):
        print(f"  ... lần {i + 1}/{a.lan}", end="\r")
        r = mot_lan(seqs, K, hat=i, epochs=a.epochs, hidden=a.hidden)
        if not r:
            continue
        for ten, auc in r.items():
            gom.setdefault(ten, []).append(auc)
    print(" " * 30, end="\r")

    if not gom:
        print("\n  Không lần chia nào cho kết quả hợp lệ (tập chấm quá nhỏ).")
        raise SystemExit(1)

    print()
    print(f"  {'Mô hình':<30} {'AUC trung bình':>15} {'Độ lệch':>10} {'n lần':>7}")
    print("  " + "-" * 66)
    thu_tu = ["Đoán theo tỉ lệ đúng chung", "DKT chưa huấn luyện", "Tỉ lệ đúng theo chủ đề",
              "Logistic Regression", "DKT (LSTM)"]
    for ten in thu_tu:
        if ten not in gom:
            continue
        v = gom[ten]
        lech = statistics.stdev(v) if len(v) > 1 else 0.0
        sao = "  ★" if ten == "DKT (LSTM)" else ""
        print(f"  {ten:<30} {statistics.mean(v):>15.4f} {lech:>10.4f} {len(v):>7}{sao}")

    print()
    if "DKT (LSTM)" in gom and "DKT chưa huấn luyện" in gom:
        truoc = statistics.mean(gom["DKT chưa huấn luyện"])
        sau = statistics.mean(gom["DKT (LSTM)"])
        print(f"  Huấn luyện mang lại: {sau - truoc:+.4f} AUC "
              f"({truoc:.4f} khi chưa học -> {sau:.4f} sau khi học)")

    du = len(seqs) >= DU_DE_KET_LUAN_NGUOI and n_cau >= DU_DE_KET_LUAN_CAU
    print()
    if du:
        print("  Dữ liệu đã đủ để kết luận trên hệ thống này.")
    else:
        print(f"  ⚠ Dữ liệu còn nhỏ ({len(seqs)} người, {n_cau} câu; cần ≥ {DU_DE_KET_LUAN_NGUOI} người")
        print(f"    và ≥ {DU_DE_KET_LUAN_CAU} câu). Con số trên minh hoạ CÁCH ĐO, chưa kết luận được")
        print("    mô hình nào tốt hơn. Kết luận về chất lượng DKT nằm ở eval/kt_results.md —")
        print("    ASSISTments 2009, 325.515 tương tác, train/test tách rời.")
    print("=" * 72)


if __name__ == "__main__":
    main()
