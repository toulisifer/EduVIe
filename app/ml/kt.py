"""Knowledge Tracing: dự đoán xác suất trả lời đúng câu tiếp theo từ chuỗi (kỹ năng, đúng/sai).

Mô hình:
- Baseline 1: tỷ lệ đúng toàn cục.
- Baseline 2: tỷ lệ đúng theo kỹ năng (học từ train).
- Baseline 3: Logistic Regression trên đặc trưng thủ công (kỹ năng, số lần làm trước, tỷ lệ đúng trước đó...).
- DKT (Piech et al., 2015): LSTM đọc chuỗi one-hot (kỹ năng × đúng/sai) -> xác suất đúng cho từng kỹ năng ở bước kế.

Dữ liệu dạng "triple-line" (chuẩn của DKVMN/pyKT): mỗi học sinh 3 dòng: độ dài, dãy kỹ năng, dãy đúng/sai.
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn

Seq = tuple[list[int], list[int]]  # (skills, corrects)


# ----------------------------- DATA -----------------------------
def load_triples(path: Path, min_len: int = 2) -> list[Seq]:
    lines = [ln.strip().strip(",") for ln in path.read_text().splitlines() if ln.strip()]
    seqs = []
    for i in range(0, len(lines) - 2, 3):
        skills = [int(x) for x in lines[i + 1].split(",") if x != ""]
        corrects = [int(x) for x in lines[i + 2].split(",") if x != ""]
        n = min(len(skills), len(corrects))
        if n >= min_len:
            seqs.append((skills[:n], corrects[:n]))
    return seqs


def n_skills_of(seqs: list[Seq]) -> int:
    return 1 + max(max(s) for s, _ in seqs)


# ----------------------------- BASELINES -----------------------------
def eval_pairs(y_true: list[int], y_prob: list[float]) -> dict:
    from sklearn.metrics import accuracy_score, roc_auc_score
    y_true, y_prob = np.array(y_true), np.array(y_prob)
    return {"auc": float(roc_auc_score(y_true, y_prob)),
            "acc": float(accuracy_score(y_true, (y_prob >= 0.5).astype(int))), "n": int(len(y_true))}


def baseline_global(train: list[Seq], test: list[Seq]) -> dict:
    p = np.mean([c for _, cs in train for c in cs])
    y = [c for _, cs in test for c in cs[1:]]
    return eval_pairs(y, [p] * len(y))


def baseline_skill_mean(train: list[Seq], test: list[Seq], n_skills: int) -> dict:
    tot, ok = np.ones(n_skills), np.full(n_skills, 0.5)  # Laplace smoothing
    for ss, cs in train:
        for s, c in zip(ss, cs):
            tot[s] += 1; ok[s] += c
    rate = ok / tot
    y, p = [], []
    for ss, cs in test:
        for s, c in zip(ss[1:], cs[1:]):
            y.append(c); p.append(rate[s])
    return eval_pairs(y, p)


def _lr_features(seqs: list[Seq], n_skills: int):
    """Đặc trưng cho mỗi bước t>=1: one-hot kỹ năng, số lần đã làm kỹ năng đó, tỷ lệ đúng kỹ năng đó,
    tỷ lệ đúng tổng, đúng/sai câu ngay trước."""
    X, y = [], []
    for ss, cs in seqs:
        cnt, okc = {}, {}
        tot_n = tot_ok = 0
        for t in range(len(ss)):
            s, c = ss[t], cs[t]
            if t >= 1:
                f = np.zeros(n_skills + 5, dtype=np.float32)
                f[s] = 1
                n_s = cnt.get(s, 0)
                f[n_skills] = np.log1p(n_s)
                f[n_skills + 1] = (okc.get(s, 0) + 0.5) / (n_s + 1)
                f[n_skills + 2] = (tot_ok + 0.5) / (tot_n + 1)
                f[n_skills + 3] = cs[t - 1]
                f[n_skills + 4] = np.log1p(tot_n)
                X.append(f); y.append(c)
            cnt[s] = cnt.get(s, 0) + 1; okc[s] = okc.get(s, 0) + c
            tot_n += 1; tot_ok += c
    return np.array(X), np.array(y)


def baseline_logreg(train: list[Seq], test: list[Seq], n_skills: int) -> dict:
    from sklearn.linear_model import LogisticRegression
    Xtr, ytr = _lr_features(train, n_skills)
    Xte, yte = _lr_features(test, n_skills)
    clf = LogisticRegression(max_iter=500, C=1.0).fit(Xtr, ytr)
    return eval_pairs(yte.tolist(), clf.predict_proba(Xte)[:, 1].tolist())


# ----------------------------- DKT -----------------------------
class DKT(nn.Module):
    def __init__(self, n_skills: int, hidden: int = 100, dropout: float = 0.2):
        super().__init__()
        self.n_skills = n_skills
        self.lstm = nn.LSTM(2 * n_skills, hidden, batch_first=True)
        self.drop = nn.Dropout(dropout)
        self.out = nn.Linear(hidden, n_skills)

    def forward(self, x):                 # x: (B, T, 2*n_skills)
        h, _ = self.lstm(x)
        return torch.sigmoid(self.out(self.drop(h)))  # (B, T, n_skills): p(đúng) cho từng kỹ năng ở bước kế


def _encode(seqs: list[Seq], n_skills: int, max_len: int):
    """Trả về X (B,T,2K) one-hot của (skill, correct) tại bước t; nhãn: skill & correct tại t+1; mask."""
    B = len(seqs)
    X = torch.zeros(B, max_len, 2 * n_skills)
    next_skill = torch.zeros(B, max_len, dtype=torch.long)
    next_corr = torch.zeros(B, max_len)
    mask = torch.zeros(B, max_len, dtype=torch.bool)
    for b, (ss, cs) in enumerate(seqs):
        ss, cs = ss[-(max_len + 1):], cs[-(max_len + 1):]  # giữ phần gần nhất
        for t in range(len(ss) - 1):
            X[b, t, ss[t] + n_skills * cs[t]] = 1.0
            next_skill[b, t] = ss[t + 1]; next_corr[b, t] = cs[t + 1]; mask[b, t] = True
    return X, next_skill, next_corr, mask


def _batches(seqs, n_skills, max_len, batch_size, shuffle):
    idx = list(range(len(seqs)))
    if shuffle:
        random.shuffle(idx)
    for i in range(0, len(idx), batch_size):
        chunk = [seqs[j] for j in idx[i:i + batch_size]]
        T = min(max_len, max(len(s) for s, _ in chunk) - 1)
        yield _encode(chunk, n_skills, max(T, 1))


@dataclass
class TrainResult:
    model: DKT
    history: list[dict]
    best_auc: float


def train_dkt(train: list[Seq], valid: list[Seq], n_skills: int, epochs: int = 8, hidden: int = 100,
              max_len: int = 200, batch_size: int = 64, lr: float = 2e-3, log=print) -> TrainResult:
    torch.manual_seed(0); random.seed(0)
    model = DKT(n_skills, hidden)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    bce = nn.BCELoss(reduction="none")
    best, best_state, hist = 0.0, None, []
    for ep in range(1, epochs + 1):
        model.train(); tot = 0.0; nb = 0
        for X, ns, nc, m in _batches(train, n_skills, max_len, batch_size, True):
            p = model(X).gather(2, ns.unsqueeze(2)).squeeze(2)      # p(đúng) của kỹ năng thật sự ở bước kế
            loss = (bce(p, nc) * m).sum() / m.sum()
            opt.zero_grad(); loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 5.0); opt.step()
            tot += loss.item(); nb += 1
        ev = evaluate_dkt(model, valid, n_skills, max_len)
        hist.append({"epoch": ep, "loss": tot / nb, **ev})
        log(f"epoch {ep}: loss={tot/nb:.4f}  val_auc={ev['auc']:.4f}  val_acc={ev['acc']:.4f}")
        if ev["auc"] > best:
            best, best_state = ev["auc"], {k: v.clone() for k, v in model.state_dict().items()}
    model.load_state_dict(best_state)
    return TrainResult(model, hist, best)


@torch.no_grad()
def evaluate_dkt(model: DKT, seqs: list[Seq], n_skills: int, max_len: int = 200) -> dict:
    model.eval(); ys, ps = [], []
    for X, ns, nc, m in _batches(seqs, n_skills, max_len, 128, False):
        p = model(X).gather(2, ns.unsqueeze(2)).squeeze(2)
        ys += nc[m].tolist(); ps += p[m].tolist()
    return eval_pairs([int(v) for v in ys], ps)


@torch.no_grad()
def predict_next(model: DKT, skills: list[int], corrects: list[int]) -> np.ndarray:
    """Cho lịch sử một học sinh -> vector p(đúng) cho MỌI kỹ năng ở câu tiếp theo."""
    model.eval()
    K = model.n_skills
    if not skills:
        return np.full(K, 0.5)
    X = torch.zeros(1, len(skills), 2 * K)
    for t, (s, c) in enumerate(zip(skills, corrects)):
        X[0, t, s + K * c] = 1.0
    return model(X)[0, -1].numpy()


def save(model: DKT, path: Path, meta: dict | None = None):
    torch.save({"state": model.state_dict(), "n_skills": model.n_skills,
                "hidden": model.lstm.hidden_size, "meta": meta or {}}, path)


def load(path: Path) -> tuple[DKT, dict]:
    ck = torch.load(path, map_location="cpu")
    m = DKT(ck["n_skills"], ck["hidden"]); m.load_state_dict(ck["state"]); m.eval()
    return m, ck.get("meta", {})
