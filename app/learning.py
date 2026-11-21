"""Ba cơ chế "học thông minh" dùng chung dữ liệu Answer + mastery:

1. Spaced repetition (SM-2 rút gọn theo chủ đề): mỗi chủ đề có khoảng ôn; làm đúng -> giãn, sai -> co lại.
2. Adaptive quiz: chọn chủ đề & độ khó "vừa sức" (vùng 45–75 %) — dùng DKT nếu có, không thì mastery thống kê.
3. Knowledge graph: quan hệ tiên quyết giữa chủ đề (data/prerequisites.json) -> không luyện chủ đề mà nền còn yếu.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import pandas as pd

from app import analytics
from app.config import DATA_DIR
from app.db import Answer, SessionLocal, Topic
from app.ml.kt_app import predict_user

PREREQ_FILE = DATA_DIR / "prerequisites.json"

# ----------------------------- KNOWLEDGE GRAPH -----------------------------

def prerequisites() -> dict[int, list[int]]:
    """{topic_id: [topic_id tiên quyết]} — đọc từ prerequisites.json (tên chủ đề), ánh xạ sang id."""
    if not PREREQ_FILE.exists():
        return {}
    raw = json.loads(PREREQ_FILE.read_text(encoding="utf-8"))
    with SessionLocal() as s:
        by_name = {t.name: t.id for t in s.query(Topic)}
    out = {}
    for name, pres in raw.items():
        if name in by_name:
            out[by_name[name]] = [by_name[p] for p in pres if p in by_name]
    return out


def prereq_mastery(user_id: int) -> pd.DataFrame:
    """Mastery của TẤT CẢ các môn, dùng riêng cho việc xét tiên quyết.

    Nền của một chủ đề lớp 12 có thể nằm ở lớp 8 (ví dụ "Đường tiệm cận" cần
    "Phân thức đại số"), nên không được lọc theo môn đang học. Chủ đề chưa làm
    bài nào xếp mức "Chưa đủ dữ liệu" nên không bị coi là yếu.
    """
    return analytics.topic_mastery(user_id, None)


def weak_prereqs(topic_id: int, mastery: pd.DataFrame, pre: dict[int, list[int]] | None = None) -> list[str]:
    """Tên các chủ đề tiên quyết đang Yếu của một chủ đề."""
    pre = pre if pre is not None else prerequisites()
    m = mastery.set_index("topic_id")
    return [m.loc[p, "topic"] for p in pre.get(topic_id, []) if p in m.index and m.loc[p, "level"] == "Yếu"]


def topological_order(topic_ids: list[int], pre: dict[int, list[int]] | None = None) -> list[int]:
    """Sắp xếp chủ đề sao cho tiên quyết đứng trước (dùng khi lập lộ trình)."""
    pre = pre if pre is not None else prerequisites()
    ids, seen, out = set(topic_ids), set(), []

    def visit(t):
        if t in seen:
            return
        seen.add(t)
        for p in pre.get(t, []):
            if p in ids:
                visit(p)
        out.append(t)

    for t in topic_ids:
        visit(t)
    return out


# ----------------------------- SPACED REPETITION -----------------------------
# SM-2 rút gọn theo chủ đề: mỗi lần "ôn" = một attempt có câu thuộc chủ đề đó.
# Chất lượng q = tỷ lệ đúng của chủ đề trong attempt đó. q >= 0.6 -> tăng khoảng; q < 0.6 -> reset về 1 ngày.

def review_schedule(user_id: int, subject_id: int | None = None) -> pd.DataFrame:
    """Một dòng / chủ đề đã học: lần ôn cuối, khoảng cách (ngày), ngày ôn tới, quá hạn?"""
    df = analytics.answers_df(user_id)
    if df.empty:
        return pd.DataFrame(columns=["topic_id", "topic", "last_review", "interval", "due", "overdue_days", "ease"])
    if subject_id:
        df = df[df["subject_id"] == subject_id]
    with SessionLocal() as s:
        att = dict(s.query(Answer.id, Answer.attempt_id).filter(Answer.user_id == user_id).all())
    df = df.assign(attempt_id=df["id"].map(att)).sort_values("answered_at")
    rows = []
    for tid, g in df.groupby("topic_id"):
        ease, interval, last = 2.5, 0.0, None
        for _, ga in g.groupby("attempt_id", sort=False):
            q = ga["is_correct"].mean()
            last = ga["answered_at"].max()
            if q >= 0.6:
                interval = 1 if interval == 0 else (3 if interval < 3 else round(interval * ease, 1))
                ease = max(1.3, ease + (0.1 - (1 - q) * 0.8))
            else:
                interval, ease = 1, max(1.3, ease - 0.2)
        due = pd.to_datetime(last) + timedelta(days=float(interval))
        rows.append({"topic_id": int(tid), "topic": g["topic"].iloc[0], "last_review": last,
                     "interval": interval, "due": due,
                     "overdue_days": round((datetime.utcnow() - due).total_seconds() / 86400, 1), "ease": round(ease, 2)})
    out = pd.DataFrame(rows).sort_values("due")
    return out


def due_topics(user_id: int, subject_id: int | None = None) -> pd.DataFrame:
    sch = review_schedule(user_id, subject_id)
    return sch[sch["overdue_days"] >= 0] if not sch.empty else sch


# ----------------------------- ADAPTIVE QUIZ -----------------------------
ZONE_LOW, ZONE_HIGH = 45, 75   # vùng "vừa sức" (%)


def phan_bo_cau_hoi(uu_tien: dict[int, float], n: int,
                    kha_dung: dict[int, int] | None = None) -> dict[int, int]:
    """Chia n câu cho các chủ đề theo trọng số ưu tiên, tôn trọng số câu còn có được.

    Chủ đề càng yếu thì trọng số càng cao nên được nhiều câu hơn. Khi một chủ đề không
    còn đủ câu (ngân hàng chỉ có 20 câu mà phần của nó là 30), phần thiếu được chia lại
    cho những chủ đề còn chỗ, theo đúng tỉ lệ ưu tiên giữa chúng — chứ không bỏ trống.

    uu_tien : {topic_id: trọng số > 0}
    kha_dung: {topic_id: số câu nhiều nhất có thể lấy}; None = không giới hạn
    Trả về {topic_id: số câu}. Tổng = n, trừ khi tổng khả dụng nhỏ hơn n.
    """
    if n <= 0 or not uu_tien:
        return {}
    con_lai = {t: w for t, w in uu_tien.items() if w > 0}
    tran = dict(kha_dung or {})
    ket: dict[int, int] = {t: 0 for t in uu_tien}
    chua_chia = n

    while chua_chia > 0 and con_lai:
        tong_w = sum(con_lai.values())
        # chia theo tỉ lệ, phần lẻ dồn cho chủ đề có phần dư lớn nhất (quy tắc dư lớn nhất)
        tho = {t: chua_chia * w / tong_w for t, w in con_lai.items()}
        chia = {t: int(v) for t, v in tho.items()}
        du = chua_chia - sum(chia.values())
        for t, _ in sorted(tho.items(), key=lambda x: -(x[1] - int(x[1])))[:du]:
            chia[t] += 1

        tien_bo = False
        for t, so in chia.items():
            if so <= 0:
                continue
            gioi_han = tran.get(t)
            nhan = so if gioi_han is None else max(0, min(so, gioi_han - ket[t]))
            if nhan:
                ket[t] += nhan
                chua_chia -= nhan
                tien_bo = True
            if gioi_han is not None and ket[t] >= gioi_han:
                con_lai.pop(t, None)        # chủ đề này hết chỗ, lần sau chia cho người khác
        if not tien_bo:
            break                            # không ai nhận thêm được nữa
    return ket


def _diem_uu_tien(p: float | None, den_han: bool) -> tuple[int, str]:
    """Thang điểm ưu tiên dùng chung cho cả gợi ý chủ đề lẫn chia số câu trong một đề.

    p = xác suất/tỉ lệ làm đúng ước lượng (%), None nghĩa là chưa có dữ liệu.
    Để một chỗ duy nhất vì trước đây số này được tính ở recommend_quiz rồi trả về
    trường "weights" mà KHÔNG AI DÙNG: đề vẫn chia đều số câu cho mọi chủ đề, nên
    chủ đề đang yếu không hề được luyện nhiều hơn.
    """
    if den_han:
        return 100, "đến hạn ôn lại"
    if p is None:
        return 80, "chưa có dữ liệu"
    if p < ZONE_LOW:
        return 90, f"đang yếu ({p:.0f}%)"
    if p <= ZONE_HIGH:
        return 70, f"vừa sức ({p:.0f}%)"
    return 20, f"đã tốt ({p:.0f}%)"


def trong_so_uu_tien(user_id: int, topic_ids: list[int],
                     subject_id: int | None = None) -> dict[int, float]:
    """{topic_id: trọng số} để chia số câu trong một đề — chủ đề yếu được nhiều câu hơn."""
    if not topic_ids:
        return {}
    m = analytics.topic_mastery(user_id, None).set_index("topic_id")
    try:
        den_han = set(due_topics(user_id, subject_id)["topic_id"])
    except Exception:          # noqa: BLE001 - chưa có dữ liệu thì coi như không chủ đề nào đến hạn
        den_han = set()
    ra = {}
    for tid in topic_ids:
        p = None
        if tid in m.index and int(m.loc[tid, "n"] or 0) > 0 and pd.notna(m.loc[tid, "mastery"]):
            p = float(m.loc[tid, "mastery"])
        ra[tid] = float(_diem_uu_tien(p, tid in den_han)[0])
    return ra


def recommend_quiz(user_id: int, subject_id: int, n_topics: int = 2) -> dict:
    """Chọn chủ đề + độ khó cho đề tiếp theo. Trả về {topics: [(id, tên, lý do)], difficulty, source}."""
    m = analytics.topic_mastery(user_id, subject_id)
    m_all = prereq_mastery(user_id)   # nền có thể nằm ở lớp dưới
    pre = prerequisites()
    kt = predict_user(user_id)
    use_kt = kt is not None and analytics.answers_df(user_id).shape[0] >= 300  # DKT chỉ tin khi đủ dữ liệu
    due = set(due_topics(user_id, subject_id)["topic_id"])

    cands = []
    for _, r in m.iterrows():
        tid = int(r["topic_id"])
        p = 100 * kt[tid] if use_kt and tid in kt else (r["mastery"] if r["n"] else None)
        blocked = weak_prereqs(tid, m_all, pre)
        if blocked:
            continue  # nền còn yếu -> chưa luyện chủ đề này
        # điểm ưu tiên: đến hạn ôn > yếu > chưa đủ dữ liệu > vừa sức > tốt
        score, why = _diem_uu_tien(p, tid in due)
        cands.append((score, tid, r["topic"], why, p))
    cands.sort(key=lambda x: -x[0])
    chosen = cands[:n_topics]
    ps = [c[4] for c in chosen if c[4] is not None]
    avg = sum(ps) / len(ps) if ps else 55
    difficulty = "easy" if avg < ZONE_LOW else "hard" if avg > ZONE_HIGH else "medium"
    return {"topics": [(t, name, why) for _, t, name, why, _ in chosen], "difficulty": difficulty,
            "source": "DKT" if use_kt else "mastery thống kê",
            # trọng số để chia số câu: chủ đề điểm ưu tiên cao (yếu, đến hạn ôn) được nhiều câu hơn
            "weights": {int(t): float(score) for score, t, _, _, _ in chosen},
            # Phải dùng m_all y như bộ lọc phía trên. Trước đây chỗ này dùng m (chỉ môn
            # đang học) nên chủ đề bị khoá vì nền ở lớp dưới bị bỏ qua trong im lặng:
            # học sinh không được luyện mà màn hình không giải thích tại sao.
            "blocked": [(int(r["topic_id"]), r["topic"], weak_prereqs(int(r["topic_id"]), m_all, pre))
                        for _, r in m.iterrows() if weak_prereqs(int(r["topic_id"]), m_all, pre)]}
