"""Ngân hàng câu hỏi: kho câu dùng chung, đề được ghép ra từ đây.

Trước đây mỗi lần ra đề là một lần gọi AI sinh câu mới, câu hỏi gắn cứng vào đề
của một học sinh. Nay câu hỏi vào kho chung:

    ra đề  ->  lấy câu sẵn có trong kho (theo chủ đề + độ khó)
           ->  thiếu bao nhiêu mới gọi AI sinh bù
           ->  câu mới sinh được nạp ngược vào kho

Nhờ vậy: tình huống "kho chỉ có 50 câu mà đề xin 60" là có thật và xử lý được,
số lượt gọi AI giảm dần theo thời gian, và mỗi câu tích luỹ được thống kê
bao nhiêu học sinh làm đúng.

CHỌN CÂU PHẢI ỔN ĐỊNH: luôn lấy theo thứ tự id tăng dần, không bốc ngẫu nhiên.
Hai học sinh cùng tình trạng học phải nhận đúng cùng một bộ câu (xem app/quiz.py).
"""
import hashlib

from sqlalchemy import func

from app.db import Answer, BankQuestion, Question, SessionLocal, Topic


def van_tay(content: str) -> str:
    """Vân tay nội dung câu hỏi, để không nạp trùng một câu hai lần."""
    chuan = " ".join(content.lower().split())
    return hashlib.sha256(chuan.encode()).hexdigest()[:32]


def them_cau(topic_id: int, difficulty: str, content: str, options: list[str],
             correct: int, explanation: str = "", source: str = "ai",
             verified: bool = True) -> int | None:
    """Nạp một câu vào kho. Trả về id, hoặc None nếu câu đã có sẵn."""
    if len(options) != 4 or not (0 <= correct < 4) or not content.strip():
        return None
    h = van_tay(content)
    with SessionLocal() as s:
        if s.query(BankQuestion).filter_by(content_hash=h).first():
            return None
        c = BankQuestion(topic_id=topic_id, difficulty=difficulty, content=content,
                         options=[str(o) for o in options], correct=correct,
                         explanation=explanation, content_hash=h, source=source,
                         verified=verified)
        s.add(c); s.commit()
        return c.id


def dem_kha_dung(topic_ids: list[int], difficulty: str | None = None,
                 tru: set[int] | None = None) -> dict[int, int]:
    """Mỗi chủ đề còn bao nhiêu câu dùng được — đầu vào cho việc chia số câu.

    Bỏ qua câu đã bị báo sai. Không lọc theo độ khó thì đếm tất cả.
    """
    if not topic_ids:
        return {}
    with SessionLocal() as s:
        q = (s.query(BankQuestion.topic_id, func.count(BankQuestion.id))
             .filter(BankQuestion.topic_id.in_(topic_ids), BankQuestion.flagged.is_(False)))
        if tru:
            q = q.filter(~BankQuestion.id.in_(tru))
        if difficulty:
            q = q.filter(BankQuestion.difficulty == difficulty)
        co = dict(q.group_by(BankQuestion.topic_id).all())
    return {t: co.get(t, 0) for t in topic_ids}


def lay_cau(topic_id: int, difficulty: str | None, n: int,
            tru: set[int] | None = None) -> list[BankQuestion]:
    """Lấy n câu của một chủ đề, ƯU TIÊN CÂU ÍT ĐƯỢC DÙNG NHẤT.

    Ưu tiên đúng độ khó yêu cầu; thiếu thì lấy thêm câu độ khó khác của chính chủ đề đó.

    tru: tập id không được lấy (câu người học đã gặp, câu đã có trong đề đang dựng).

    Vì sao xếp theo times_used chứ không theo id: xếp theo id thì mọi đề cùng chủ đề
    đều rút đúng mấy câu id nhỏ nhất — chủ đề có 57 câu mà chỉ 5 câu đầu được dùng tới.
    Xếp theo số lần đã dùng thì kho tự xoay vòng: câu vừa vào đề có times_used tăng lên
    nên lần sau tụt xuống cuối hàng, câu chưa ai dùng được lấy trước. Vừa làm đề lần sau
    khác đề lần trước, vừa dàn đều tải thống kê (times_answered) trên cả kho.
    """
    if n <= 0:
        return []
    with SessionLocal() as s:
        def truy(loc_do_kho):
            q = s.query(BankQuestion).filter(BankQuestion.topic_id == topic_id,
                                             BankQuestion.flagged.is_(False))
            if tru:
                q = q.filter(~BankQuestion.id.in_(tru))
            if loc_do_kho and difficulty:
                q = q.filter(BankQuestion.difficulty == difficulty)
            elif difficulty:
                q = q.filter(BankQuestion.difficulty != difficulty)
            # times_used có thể NULL ở dữ liệu cũ; trong SQLite NULL xếp trước khi tăng dần,
            # đúng ý: câu chưa dùng lần nào được lấy trước.
            #
            # Hoà thì bốc NGẪU NHIÊN, không theo id. Phá hoà bằng id nghe thì ổn định,
            # nhưng khi mọi câu đã được dùng số lần như nhau thì nó quay về đúng "lấy
            # mấy câu id nhỏ nhất" — hai lần tạo đề ra y hệt nhau. Đo được: hai đề cùng
            # bản thiết kế trùng 59/60 câu.
            return (q.order_by(BankQuestion.times_used.asc(), func.random())
                    .limit(n).all())

        ra = truy(True)
        if len(ra) < n and difficulty:
            ra += truy(False)[: n - len(ra)]
        for c in ra:
            _ = c.topic.name              # nạp sẵn trước khi đóng session
        return ra[:n]


def ghi_nhan_dung(bank_id: int, n_them: int = 1) -> None:
    """Câu này vừa được đưa vào thêm một đề."""
    with SessionLocal() as s:
        c = s.get(BankQuestion, bank_id)
        if c:
            c.times_used = (c.times_used or 0) + n_them
            s.commit()


def ghi_nhan_tra_loi(bank_id: int, dung: bool) -> None:
    """Một học sinh vừa trả lời câu này."""
    with SessionLocal() as s:
        c = s.get(BankQuestion, bank_id)
        if c:
            c.times_answered = (c.times_answered or 0) + 1
            c.times_correct = (c.times_correct or 0) + (1 if dung else 0)
            s.commit()


def danh_dau_sai(bank_id: int) -> None:
    with SessionLocal() as s:
        c = s.get(BankQuestion, bank_id)
        if c:
            c.flagged = True
            s.commit()


def thong_ke() -> dict:
    """Số liệu tổng quan của kho, để hiển thị ở trang Quản trị."""
    with SessionLocal() as s:
        tong = s.query(BankQuestion).count()
        theo_kho = dict(s.query(BankQuestion.difficulty, func.count(BankQuestion.id))
                        .group_by(BankQuestion.difficulty).all())
        co_cau = s.query(BankQuestion.topic_id).distinct().count()
        tong_chu_de = s.query(Topic).count()
        bi_bao = s.query(BankQuestion).filter_by(flagged=True).count()
        da_dung = s.query(func.coalesce(func.sum(BankQuestion.times_used), 0)).scalar()
        luot = s.query(func.coalesce(func.sum(BankQuestion.times_answered), 0)).scalar()
        dung = s.query(func.coalesce(func.sum(BankQuestion.times_correct), 0)).scalar()
    return {"tong": tong, "theo_do_kho": theo_kho, "chu_de_co_cau": co_cau,
            "tong_chu_de": tong_chu_de, "bi_bao_sai": bi_bao,
            "luot_dua_vao_de": int(da_dung), "luot_tra_loi": int(luot),
            "ti_le_dung_chung": round(100 * dung / luot) if luot else None}


def nap_tu_de_cu() -> dict:
    """Chuyển những câu đã sinh trước đây (nằm rải trong các đề) vào kho chung.

    Chạy một lần khi mới bật ngân hàng. Câu trùng nội dung chỉ vào kho một lần,
    và thống kê trả lời của tất cả các bản sao được cộng dồn về câu gốc.
    """
    them = bo_qua = 0
    with SessionLocal() as s:
        cu = s.query(Question).order_by(Question.id).all()
        for q in cu:
            if not q.topic_id or not q.options or len(q.options) != 4:
                bo_qua += 1
                continue
            h = van_tay(q.content)
            goc = s.query(BankQuestion).filter_by(content_hash=h).first()
            if not goc:
                goc = BankQuestion(topic_id=q.topic_id, difficulty=q.difficulty,
                                   content=q.content, options=q.options, correct=q.correct,
                                   explanation=q.explanation or "", content_hash=h,
                                   source="ai", flagged=bool(q.flagged))
                s.add(goc); s.flush()
                them += 1
            q.bank_id = goc.id
            goc.times_used = (goc.times_used or 0) + 1
            tl = s.query(Answer).filter_by(question_id=q.id).all()
            goc.times_answered = (goc.times_answered or 0) + len(tl)
            goc.times_correct = (goc.times_correct or 0) + sum(1 for a in tl if a.is_correct)
            if q.flagged:
                goc.flagged = True
        s.commit()
    return {"da_nap": them, "bo_qua": bo_qua, "tong_cau_cu": len(cu)}


def khung_cau(content: str) -> str:
    """Vân tay "DẠNG BÀI" của một câu: bỏ số và công thức, chỉ giữ phần lời.

    Hai câu khác nhau từng chữ số nhưng cùng khung thì với người học là cùng một dạng:

        Cho hàm số $y = x^4 - 2x^2 + 3$. Số điểm cực trị của hàm số này là:
        Cho hàm số $y = x^3 - 3x^2 + 3x - 1$. Số điểm cực trị của hàm số này là:

    Đo trên kho: chủ đề "Cực trị của hàm số" có 59 câu nhưng chỉ 52 dạng — 13 câu
    dồn vào 6 dạng. Đề 60 câu vì thế đọc lên có cảm giác lặp, dù không câu nào trùng.
    Dùng vân tay này để giới hạn mỗi dạng chỉ xuất hiện vài lần trong một đề.
    """
    import re
    import unicodedata

    s = unicodedata.normalize("NFD", (content or "").lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\$[^$]*\$", " ", s)        # bỏ công thức LaTeX
    s = re.sub(r"[0-9]+", " ", s)           # bỏ số
    s = re.sub(r"[^a-z ]", " ", s)
    return " ".join(s.split())
