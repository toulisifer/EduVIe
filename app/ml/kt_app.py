"""DKT trên dữ liệu của chính hệ thống: kỹ năng = topic, chuỗi = các câu trả lời của mỗi user theo thời gian.

- train_app_model(): gom Answer của MỌI user -> huấn luyện -> lưu data/kt/dkt_app.pt (kèm ánh xạ topic_id -> index).
- predict_user(user_id): xác suất trả lời đúng câu tiếp theo cho từng topic của một user.

Lưu ý trung thực: dữ liệu hệ thống còn nhỏ, DKT ở đây mang tính minh hoạ tích hợp; độ tin cậy tăng khi có ≥ vài nghìn câu.
Mô hình chuẩn đã được kiểm chứng riêng trên ASSISTments (xem eval/kt_results.md).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.config import DATA_DIR
from app.db import Answer, Question, SessionLocal, Topic
from app.ml import kt

MODEL_PATH = DATA_DIR / "kt" / "dkt_app.pt"
MIN_ANSWERS = 40   # dưới mức này không huấn luyện

# ----------------------------- CHỐNG ĐẦU ĐỘC DỮ LIỆU -----------------------------
# Tập huấn luyện của DKT là bảng `answers`, mà bảng đó do CHÍNH NGƯỜI DÙNG sinh ra:
# ai đăng ký được là bơm dữ liệu vào được. Không lọc thì một người tạo 50 tài khoản,
# mỗi tài khoản trả lời đúng hết một chủ đề, là mô hình tưởng ai cũng giỏi chủ đề đó
# và học sinh thật đang yếu sẽ không được xếp vào lộ trình ôn.
#
# Năm bộ lọc dưới đây chặn ở tầng dữ liệu; tầng thứ hai (champion/challenger) nằm
# trong train_app_model: mô hình mới phải không tệ hơn mô hình cũ thì mới được thay.
TOI_THIEU_MOI_NGUOI = 5      # dưới mức này là nhiễu, không đủ thành một chuỗi học tập
TOI_DA_MOI_NGUOI = 200       # giữ 200 câu gần nhất; phần cũ hơn bỏ
TRAN_TI_TRONG = 0.30         # không ai được chiếm quá 30% tập huấn luyện
DAI_NGHI_NGO = 30            # chuỗi dài hơn mức này mà toàn đúng/toàn sai -> loại
DAI_DE_XET_TOC_DO = 20       # từ mức này mới xét tốc độ trả lời
TOC_DO_NGHI_NGO = 2.0        # dưới 2 giây/câu trên cả chuỗi dài -> máy làm, không phải người

# Cửa ải thay mô hình (tầng C). Dữ liệu còn nhỏ thì chưa chấm được, nên có ngưỡng bật.
TOI_THIEU_NGUOI_DE_CHAM = 10
TOI_THIEU_CAU_DE_CHAM = 300
NGUONG_TUT_AUC = 0.02        # mô hình mới tụt quá mức này so với mô hình cũ -> từ chối


class TuChoiThayMoHinh(Exception):
    """Mô hình mới kém hơn mô hình đang dùng -> không thay, giữ nguyên bản cũ."""


def _chuoi_tho() -> tuple[dict[int, tuple[list[int], list[int], list]], dict[int, int]]:
    """{user_id: (skills, corrects, thời điểm)} và map topic_id -> index.

    Đã loại sẵn câu trả lời gắn với câu hỏi bị người dùng báo sai (`questions.flagged`):
    câu hỏi sai thì kết quả đúng/sai của nó không nói lên điều gì về năng lực học sinh.
    """
    with SessionLocal() as s:
        topic_ids = [t.id for t in s.query(Topic).order_by(Topic.id)]
        idx = {tid: i for i, tid in enumerate(topic_ids)}
        rows = (s.query(Answer.user_id, Answer.topic_id, Answer.is_correct, Answer.answered_at)
                .join(Question, Answer.question_id == Question.id)
                .filter(Question.flagged.is_(False))
                .order_by(Answer.user_id, Answer.answered_at, Answer.id).all())
    out: dict[int, tuple[list[int], list[int], list]] = {}
    for uid, tid, ok, luc in rows:
        if tid not in idx:
            continue
        s_, c_, t_ = out.setdefault(uid, ([], [], []))
        s_.append(idx[tid]); c_.append(int(bool(ok))); t_.append(luc)
    return out, idx


def _qua_nhanh(times: list) -> bool:
    """Chuỗi dài mà trung bình dưới TOC_DO_NGHI_NGO giây/câu thì coi là máy làm."""
    if len(times) < DAI_DE_XET_TOC_DO:
        return False
    moc = [t for t in times if t is not None]
    if len(moc) < 2:
        return False
    giay = (max(moc) - min(moc)).total_seconds()
    return giay / (len(moc) - 1) < TOC_DO_NGHI_NGO


def loc_dau_doc(tho: dict[int, tuple[list[int], list[int], list]],
                log=print) -> tuple[dict[int, kt.Seq], dict]:
    """Lọc dữ liệu huấn luyện. Trả về ({user_id: (skills, corrects)}, báo cáo).

    Báo cáo ghi rõ ai bị loại vì lý do gì — để truy vết khi mô hình có vấn đề.
    """
    bo: dict[int, str] = {}
    cat: dict[int, int] = {}
    giu: dict[int, tuple[list[int], list[int]]] = {}

    # 1-3. lọc theo từng người
    for uid, (ss, cs, ts) in tho.items():
        if len(ss) < TOI_THIEU_MOI_NGUOI:
            bo[uid] = f"chỉ có {len(ss)} câu, dưới {TOI_THIEU_MOI_NGUOI}"
            continue
        if len(ss) >= DAI_NGHI_NGO and len(set(cs)) == 1:
            bo[uid] = f"{len(ss)} câu mà {'đúng' if cs[0] else 'sai'} hết — không phải hành vi học thật"
            continue
        if _qua_nhanh(ts):
            bo[uid] = f"{len(ss)} câu trong thời gian quá ngắn — nghi là máy làm"
            continue
        if len(ss) > TOI_DA_MOI_NGUOI:          # giữ phần gần nhất
            cat[uid] = len(ss) - TOI_DA_MOI_NGUOI
            ss, cs = ss[-TOI_DA_MOI_NGUOI:], cs[-TOI_DA_MOI_NGUOI:]
        giu[uid] = (ss, cs)

    # 4. trần tỉ trọng: không ai được chiếm quá TRAN_TI_TRONG tập huấn luyện.
    #
    # Cắt bớt một người thì tổng cũng nhỏ đi, nên tỉ trọng của người đó lại nhích lên —
    # tính một lần là chưa đủ. Lặp cho tới khi trần đứng yên (hội tụ sau vài vòng).
    #
    # Sàn "phần chia đều": với ít người thì ràng buộc 30% là bất khả thi (3 người thì
    # mỗi người đã 33%), nên không bao giờ cắt ai xuống dưới mức chia đều — người đóng
    # góp ngang bằng mọi người khác thì không phải là kẻ đầu độc.
    tran = max((len(ss) for ss, _ in giu.values()), default=0)
    for _ in range(30):
        tong = sum(min(len(ss), tran) for ss, _ in giu.values())
        if not tong:
            break
        chia_deu = -(-tong // max(len(giu), 1))          # làm tròn lên
        moi = max(TOI_THIEU_MOI_NGUOI, chia_deu, int(tong * TRAN_TI_TRONG))
        if moi >= tran:
            break
        tran = moi
    for uid, (ss, cs) in list(giu.items()):
        if len(ss) > tran:
            cat[uid] = cat.get(uid, 0) + len(ss) - tran
            giu[uid] = (ss[-tran:], cs[-tran:])

    bao_cao = {
        "nguoi_vao": len(giu), "nguoi_bi_loai": len(bo),
        "cau_vao": sum(len(ss) for ss, _ in giu.values()),
        "cau_tho": sum(len(ss) for ss, _, _ in tho.values()),
        "tran_moi_nguoi": tran,
        "ly_do_loai": {str(k): v for k, v in bo.items()},
        "bi_cat_bot": {str(k): v for k, v in cat.items()},
    }
    if bo:
        log(f"Loại {len(bo)} người khỏi tập huấn luyện:")
        for uid, ly_do in bo.items():
            log(f"  - user {uid}: {ly_do}")
    if cat:
        log(f"Cắt bớt {len(cat)} người cho khỏi lệch (trần {tran} câu/người).")
    return giu, bao_cao


def _auc_mo_hinh_cu(giu_lai: list[kt.Seq], K: int) -> float | None:
    """AUC của mô hình đang dùng trên tập người bị giữ lại. None nếu chưa có / không so được."""
    if not MODEL_PATH.exists():
        return None
    try:
        cu, _ = kt.load(MODEL_PATH)
        if cu.n_skills != K:        # danh mục chủ đề đã đổi -> không so được
            return None
        return kt.evaluate_dkt(cu, giu_lai, K, max_len=100)["auc"]
    except Exception:               # noqa: BLE001 - mô hình cũ hỏng thì coi như chưa có
        return None


def train_app_model(epochs: int = 20, hidden: int = 32, log=print) -> dict | None:
    tho, idx = _chuoi_tho()
    sach, bao_cao = loc_dau_doc(tho, log=log)
    all_seqs = [v for v in sach.values() if len(v[0]) >= 2]
    n_ans = sum(len(s) for s, _ in all_seqs)
    if n_ans < MIN_ANSWERS or len(all_seqs) < 2:
        log(f"Chưa đủ dữ liệu sau khi lọc ({n_ans} câu, {len(all_seqs)} chuỗi); "
            f"cần ≥ {MIN_ANSWERS} câu và ≥ 2 người.")
        return None
    K = len(idx)

    du_de_cham = len(all_seqs) >= TOI_THIEU_NGUOI_DE_CHAM and n_ans >= TOI_THIEU_CAU_DE_CHAM
    if du_de_cham:
        # Chia THEO NGƯỜI, không theo câu: người trong tập train không xuất hiện ở tập chấm,
        # nếu không thì mô hình chỉ cần nhớ thói quen của từng người là đã có AUC cao.
        n_giu = max(2, len(all_seqs) // 5)
        giu_lai, tap_train = all_seqs[:n_giu], all_seqs[n_giu:]
        res = kt.train_dkt(tap_train, giu_lai, K, epochs=epochs, hidden=hidden,
                           max_len=100, batch_size=16, lr=3e-3, log=log)
        auc_moi = res.best_auc
        auc_cu = _auc_mo_hinh_cu(giu_lai, K)
        if auc_cu is not None and auc_moi < auc_cu - NGUONG_TUT_AUC:
            thong_bao = (f"Từ chối thay mô hình: AUC mới {auc_moi:.4f} thấp hơn AUC cũ {auc_cu:.4f} "
                         f"quá {NGUONG_TUT_AUC}. Dữ liệu huấn luyện có thể đã bị đầu độc. "
                         f"Giữ nguyên mô hình đang dùng.")
            log(thong_bao)
            raise TuChoiThayMoHinh(thong_bao)
        loai_auc, ghi_chu = "holdout_auc", "AUC đo trên nhóm người mô hình chưa từng thấy"
    else:
        # Dữ liệu còn nhỏ: dùng chính tập train làm valid (chỉ để chọn epoch), nói rõ trong meta
        res = kt.train_dkt(all_seqs, all_seqs, K, epochs=epochs, hidden=hidden,
                           max_len=100, batch_size=16, lr=3e-3, log=log)
        auc_moi, auc_cu = res.best_auc, None
        loai_auc = "fit_auc"
        ghi_chu = ("valid = train (dữ liệu nhỏ); AUC là độ khớp, không phải độ tổng quát. "
                   f"Cần ≥ {TOI_THIEU_NGUOI_DE_CHAM} người và ≥ {TOI_THIEU_CAU_DE_CHAM} câu "
                   "mới bật được cửa ải so với mô hình cũ.")

    meta = {"trained_at": datetime.now().isoformat(timespec="minutes"), "n_answers": n_ans,
            "n_users": len(all_seqs), "n_topics": K,
            "topic_index": {str(t): i for t, i in idx.items()},
            "fit_auc": auc_moi, "loai_auc": loai_auc, "auc_mo_hinh_cu": auc_cu,
            "loc_du_lieu": bao_cao, "note": ghi_chu}
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    kt.save(res.model, MODEL_PATH, meta)
    return meta


def model_info() -> dict | None:
    if not MODEL_PATH.exists():
        return None
    _, meta = kt.load(MODEL_PATH)
    return meta


def predict_user(user_id: int) -> dict[int, float] | None:
    """{topic_id: p(đúng câu tiếp theo)} hoặc None nếu chưa có model / user chưa có dữ liệu."""
    if not MODEL_PATH.exists():
        return None
    model, meta = kt.load(MODEL_PATH)
    idx = {int(t): i for t, i in meta["topic_index"].items()}
    with SessionLocal() as s:
        rows = s.query(Answer.topic_id, Answer.is_correct).filter_by(user_id=user_id) \
                .order_by(Answer.answered_at, Answer.id).all()
    skills = [idx[t] for t, _ in rows if t in idx]
    corr = [int(bool(c)) for t, c in rows if t in idx]
    if not skills:
        return None
    p = kt.predict_next(model, skills[-100:], corr[-100:])
    return {tid: float(p[i]) for tid, i in idx.items()}
