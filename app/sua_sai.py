"""Luyện lại câu làm sai.

Hệ thống đã ghi từng câu sai kèm chủ đề và lựa chọn đã chọn, nhưng dữ liệu đó chỉ
có agent đọc được (app/agent.py: get_recent_mistakes). Người học không có đường nào
mở ra. Tệp này biến nó thành một vòng khép kín: sai -> luyện lại đúng những câu đó
-> đo lại.

ĐÂU LÀ "CÂU CẦN LUYỆN LẠI"
Xét theo LẦN TRẢ LỜI GẦN NHẤT của từng câu, không phải theo "đã từng sai". Sai rồi
làm đúng lại nghĩa là đã sửa được, rút khỏi danh sách; đúng rồi lại sai thì quay vào.
Nhờ vậy danh sách tự ngắn đi khi người học tiến bộ, chứ không phình mãi.

Một câu được nhận diện qua bank_id — id trong ngân hàng — chứ không qua id của câu
trong một đề cụ thể, vì cùng một câu nằm trong nhiều đề thì mang nhiều id khác nhau.
"""
from __future__ import annotations

from datetime import datetime

from app.db import (Answer, BankQuestion, Chapter, Question, Quiz, SessionLocal,
                    Topic)

LOAI = "sua_sai"
TOI_DA_MOI_DE = 30          # một lần luyện lại không nên quá dài


def _lich_su_theo_cau(user_id: int, subject_id: int | None):
    """{bank_id: [(thời điểm, đúng/sai), ...]} theo thứ tự thời gian."""
    with SessionLocal() as s:
        q = (s.query(Question.bank_id, Answer.is_correct, Answer.answered_at)
             .join(Answer, Answer.question_id == Question.id)
             .filter(Answer.user_id == user_id, Question.bank_id.isnot(None)))
        if subject_id:
            q = (q.join(Topic, Question.topic_id == Topic.id)
                 .join(Chapter, Topic.chapter_id == Chapter.id)
                 .filter(Chapter.subject_id == subject_id))
        rows = q.order_by(Answer.answered_at, Answer.id).all()
    theo_cau: dict[int, list] = {}
    for bank_id, dung, luc in rows:
        theo_cau.setdefault(bank_id, []).append((luc or datetime.min, bool(dung)))
    return theo_cau


def cau_sai(user_id: int, subject_id: int | None = None, gioi_han: int = 50) -> list[dict]:
    """Những câu lần gần nhất vẫn trả lời sai. Sai nhiều lần nhất xếp trước.

    Bỏ qua câu đã bị báo sai (flagged): bắt người học luyện lại một câu có vấn đề
    thì sai càng thêm sai.
    """
    theo_cau = _lich_su_theo_cau(user_id, subject_id)
    con_sai = {}
    for bank_id, ds in theo_cau.items():
        if ds[-1][1]:
            continue                       # lần gần nhất đã đúng -> coi như sửa được
        con_sai[bank_id] = {
            "so_lan_sai": sum(1 for _, dung in ds if not dung),
            "so_lan_lam": len(ds),
            "lan_cuoi": ds[-1][0],
        }
    if not con_sai:
        return []
    with SessionLocal() as s:
        cau = (s.query(BankQuestion)
               .filter(BankQuestion.id.in_(list(con_sai)), BankQuestion.flagged.is_(False)).all())
        ra = []
        for c in cau:
            t = con_sai[c.id]
            ra.append({
                "bank_id": c.id,
                "topic_id": c.topic_id,
                "topic": c.topic.name if c.topic else "",
                "difficulty": c.difficulty,
                "content": c.content,
                "so_lan_sai": t["so_lan_sai"],
                "so_lan_lam": t["so_lan_lam"],
                "lan_cuoi": t["lan_cuoi"],
            })
    ra.sort(key=lambda x: (-x["so_lan_sai"], -x["lan_cuoi"].timestamp()))
    return ra[:gioi_han]


def tom_tat(user_id: int, subject_id: int | None = None) -> dict:
    """Số câu cần luyện lại, gom theo chủ đề — để vẽ tấm thẻ ngoài màn hình."""
    ds = cau_sai(user_id, subject_id, gioi_han=1000)
    theo_chu_de: dict[str, int] = {}
    for c in ds:
        theo_chu_de[c["topic"]] = theo_chu_de.get(c["topic"], 0) + 1
    xep = sorted(theo_chu_de.items(), key=lambda x: -x[1])
    return {"tong": len(ds),
            "theo_chu_de": [{"topic": k, "n": v} for k, v in xep],
            "cau": [{k: v for k, v in c.items() if k != "lan_cuoi"} for c in ds[:TOI_DA_MOI_DE]]}


def de_sua_sai(user_id: int, subject_id: int | None = None, n: int = 10) -> int | None:
    """Dựng một đề gồm đúng những câu người này đang làm sai. Trả quiz_id, None nếu không có.

    Đề này KHÔNG có mã: nó riêng của một người, chia sẻ cho người khác thì vừa vô
    nghĩa vừa để lộ người đó yếu chỗ nào.
    """
    from app.bank import ghi_nhan_dung

    n = max(1, min(int(n), TOI_DA_MOI_DE))
    ds = cau_sai(user_id, subject_id, gioi_han=n)
    if not ds:
        return None
    ids = [c["bank_id"] for c in ds]
    with SessionLocal() as s:
        goc = {c.id: c for c in s.query(BankQuestion).filter(BankQuestion.id.in_(ids))}
        mon = subject_id
        if not mon:
            t = s.get(Topic, ds[0]["topic_id"])
            mon = t.chapter.subject_id if t and t.chapter else None
        quiz = Quiz(user_id=user_id, subject_id=mon, difficulty="medium", code="", loai=LOAI)
        s.add(quiz); s.flush()
        for bid in ids:                     # giữ đúng thứ tự đã xếp: sai nhiều nhất trước
            c = goc.get(bid)
            if not c:
                continue
            s.add(Question(quiz_id=quiz.id, topic_id=c.topic_id, bank_id=c.id,
                           difficulty=c.difficulty, content=c.content, options=c.options,
                           correct=c.correct, explanation=c.explanation))
        s.commit()
        qid = quiz.id
    for bid in ids:
        ghi_nhan_dung(bid)
    return qid
