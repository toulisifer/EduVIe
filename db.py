"""SQLite + SQLAlchemy models. Đủ cho cả 2 tuần, thêm bảng khi cần."""
import json
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text, create_engine)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from app.config import DB_PATH, TOPICS_FILE

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, default="")   # rỗng = tài khoản tạo trước khi có mật khẩu
    role = Column(String, default="user")        # user / teacher / admin
    email = Column(String, default="")           # tuỳ chọn, để sau này gửi link đặt lại
    recovery_hash = Column(String, default="")   # bcrypt của mã khôi phục (quên mật khẩu)
    # Tăng mỗi lần đổi mật khẩu: token phát trước đó mang số cũ nên bị từ chối ngay.
    # Không có cột này thì JWT cũ vẫn sống tới 14 ngày sau khi đổi mật khẩu.
    token_version = Column(Integer, default=0)
    reset_fails = Column(Integer, default=0)     # số lần nhập sai mã liên tiếp
    reset_locked_until = Column(DateTime, nullable=True)
    goal = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    chapters = relationship("Chapter", back_populates="subject", order_by="Chapter.order")


class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    name = Column(String, nullable=False)
    order = Column(Integer, default=0)
    subject = relationship("Subject", back_populates="chapters")
    topics = relationship("Topic", back_populates="chapter", order_by="Topic.id")


class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    name = Column(String, nullable=False)
    chapter = relationship("Chapter", back_populates="topics")

    @property
    def path(self):
        return f"{self.chapter.subject.name} / {self.chapter.name} / {self.name}"


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=True)
    filename = Column(String, nullable=False)
    path = Column(String, nullable=False)
    n_chunks = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending / processing / ready / failed
    progress = Column(String, default="")       # mô tả bước đang chạy, ví dụ "OCR trang 12/40"
    error = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Score(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    kind = Column(String, default="15p")   # mieng / 15p / giua_ky / cuoi_ky
    value = Column(Float, nullable=False)
    weight = Column(Float, default=1.0)
    date = Column(DateTime, default=datetime.utcnow)


class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    difficulty = Column(String, default="medium")
    # Mã đề dạng M1-A036FD-02: phần nền băm từ (môn, chủ đề, độ khó, số câu, phiên bản
    # thuật toán), phần sau là lượt tạo thứ mấy. Cùng mã thì ĐỀ GIỐNG HỆT NHAU, nhưng mỗi
    # lần tạo đề mới lại ra một mã mới — xem app/quiz.py:ma_de và ma_bien_the.
    code = Column(String, default="", index=True)
    # Đề này thuộc bài tập nào (cả đề mẫu của giáo viên lẫn bản sao của học sinh).
    # Có giá trị = đề kiểm tra: không được mở bằng mã, không được nộp qua đường tự luyện,
    # và không trả đáp án trước hạn nộp.
    assignment_id = Column(Integer, index=True)
    # tu_luyen | sua_sai — đề luyện lại câu sai là riêng của một người, không chia sẻ
    # bằng mã và được ghi nhãn riêng trong lịch sử làm đề.
    loai = Column(String, default="tu_luyen")
    created_at = Column(DateTime, default=datetime.utcnow)
    questions = relationship("Question", back_populates="quiz")


class BankQuestion(Base):
    """NGÂN HÀNG CÂU HỎI — câu hỏi đứng độc lập, không thuộc đề nào.

    Khác với bảng `questions` (một câu nằm trong một đề cụ thể của một học sinh),
    mỗi dòng ở đây là một câu dùng chung: đề nào cũng có thể lấy ra dùng. Nhờ vậy
    mới trả lời được tình huống "ngân hàng chỉ có 50 câu mà đề xin 60".

    Mỗi câu mang theo thống kê thực tế: đã được đưa vào bao nhiêu đề, bao nhiêu
    lượt học sinh trả lời, bao nhiêu lượt đúng — dùng để lọc câu quá dễ, quá khó
    hoặc có vấn đề.
    """
    __tablename__ = "bank_questions"
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), index=True)
    difficulty = Column(String, default="medium", index=True)
    content = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)       # list[str] 4 lựa chọn
    correct = Column(Integer, nullable=False)    # index 0-3
    explanation = Column(Text, default="")
    # vân tay nội dung để không nạp trùng cùng một câu hai lần
    content_hash = Column(String, unique=True, index=True)
    source = Column(String, default="ai")        # ai | import | manual
    verified = Column(Boolean, default=True)     # đã qua bước AI giải lại kiểm tra chéo
    times_used = Column(Integer, default=0)      # số đề đã dùng câu này
    times_answered = Column(Integer, default=0)  # số lượt học sinh trả lời
    times_correct = Column(Integer, default=0)   # trong đó bao nhiêu lượt đúng
    flagged = Column(Boolean, default=False)     # có người báo câu này sai
    created_at = Column(DateTime, default=datetime.utcnow)
    topic = relationship("Topic")

    @property
    def ti_le_dung(self) -> float | None:
        """Tỉ lệ học sinh trả lời đúng (%). None khi chưa ai làm."""
        return None if not self.times_answered else round(100 * self.times_correct / self.times_answered)


class Question(Base):
    """Một câu trong một đề cụ thể. Nội dung được sao từ ngân hàng khi ra đề."""
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    bank_id = Column(Integer, ForeignKey("bank_questions.id"), nullable=True, index=True)
    difficulty = Column(String, default="medium")
    content = Column(Text, nullable=False)
    options = Column(JSON, nullable=False)      # list[str] 4 lựa chọn
    correct = Column(Integer, nullable=False)   # index 0-3
    explanation = Column(Text, default="")
    flagged = Column(Boolean, default=False)    # user báo câu hỏi sai
    quiz = relationship("Quiz", back_populates="questions")
    topic = relationship("Topic")


class Attempt(Base):
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    score = Column(Float, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    answers = relationship("Answer", back_populates="attempt")


class Answer(Base):
    """Dữ liệu quan trọng nhất: kết quả từng câu, gắn topic."""
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True)
    attempt_id = Column(Integer, ForeignKey("attempts.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    topic_id = Column(Integer, ForeignKey("topics.id"))
    difficulty = Column(String, default="medium")
    selected = Column(Integer)
    is_correct = Column(Boolean, default=False)
    answered_at = Column(DateTime, default=datetime.utcnow)
    attempt = relationship("Attempt", back_populates="answers")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)          # user / assistant
    content = Column(Text)
    citations = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class StudyPlan(Base):
    __tablename__ = "study_plans"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    goal = Column(String, default="")
    days = Column(Integer, default=7)
    summary = Column(Text, default="")          # nhận xét tổng quan của AI
    evidence = Column(Text, default="")         # snapshot số liệu lúc tạo (dạng text cho AI đọc)
    snapshot = Column(JSON, default=dict)        # {topic_id: mastery%} lúc tạo — để đo hiệu quả về sau
    # Mã lộ trình: cùng tình trạng học + cùng yêu cầu -> cùng mã -> cùng kế hoạch (app/advisor.py:ma_lo_trinh)
    code = Column(String, default="", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("PlanItem", back_populates="plan", order_by="PlanItem.day")


class PlanItem(Base):
    __tablename__ = "plan_items"
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("study_plans.id"))
    day = Column(Integer, default=1)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    kind = Column(String, default="study")      # study / quiz / review
    title = Column(String, nullable=False)
    detail = Column(Text, default="")
    done = Column(Boolean, default=False)
    plan = relationship("StudyPlan", back_populates="items")
    topic = relationship("Topic")


class Classroom(Base):
    __tablename__ = "classrooms"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)     # mã tham gia, ví dụ 12A1-7F3K
    teacher_id = Column(Integer, ForeignKey("users.id"))
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    members = relationship("ClassMember", back_populates="classroom")
    assignments = relationship("Assignment", back_populates="classroom", order_by="Assignment.id.desc()")


class ClassMember(Base):
    __tablename__ = "class_members"
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classrooms.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)
    classroom = relationship("Classroom", back_populates="members")
    user = relationship("User")


class Assignment(Base):
    """Đề giáo viên giao cho lớp: quiz_id là đề mẫu (của giáo viên); mỗi học sinh làm sẽ được sao chép thành quiz riêng."""
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classrooms.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    title = Column(String, nullable=False)
    due = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    classroom = relationship("Classroom", back_populates="assignments")
    quiz = relationship("Quiz")


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"
    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    attempt_id = Column(Integer, ForeignKey("attempts.id"))
    score = Column(Float, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow)


class AgentRun(Base):
    """Nhật ký mỗi lần agent chạy: để theo dõi chất lượng theo thời gian (bậc 6: tự đánh giá)."""
    __tablename__ = "agent_runs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mode = Column(String)                 # quick / agent / multi
    plan_id = Column(Integer, ForeignKey("study_plans.id"), nullable=True)
    n_tool_calls = Column(Integer, default=0)
    critic_score = Column(Integer, nullable=True)
    critic_approved = Column(Boolean, nullable=True)
    violations = Column(JSON, default=list)   # vi phạm theo validator cứng
    duration_s = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentLesson(Base):
    """Bài học agent tự rút ra từ hậu quả (reflection) — được chèn vào prompt lần sau."""
    __tablename__ = "agent_lessons"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)   # None = bài học chung
    lesson = Column(Text, nullable=False)
    evidence = Column(Text, default="")
    source_plan_id = Column(Integer, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    """Thắc mắc / góp ý gửi từ view "Hỏi Bài" trên giao diện web."""
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String, default="")
    email = Column(String, default="")
    subject = Column(String, default="")
    grade = Column(String, default="")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)
    _migrate()
    seed_topics()


def _migrate():
    """Thêm cột mới cho DB cũ (SQLite không tự thêm cột khi model đổi)."""
    from sqlalchemy import inspect, text
    cols = {c["name"] for c in inspect(engine).get_columns("users")}
    if "password_hash" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR DEFAULT ''"))
    if "role" not in cols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'"))
    for col, ddl in [("email", "VARCHAR DEFAULT ''"), ("recovery_hash", "VARCHAR DEFAULT ''"),
                     ("reset_fails", "INTEGER DEFAULT 0"), ("reset_locked_until", "DATETIME"),
                     ("token_version", "INTEGER DEFAULT 0")]:
        if col not in cols:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {ddl}"))
    pcols2 = {c["name"] for c in inspect(engine).get_columns("study_plans")} if inspect(engine).has_table("study_plans") else set()
    if pcols2 and "code" not in pcols2:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE study_plans ADD COLUMN code VARCHAR DEFAULT ''"))
    qucols = {c["name"] for c in inspect(engine).get_columns("questions")} if inspect(engine).has_table("questions") else set()
    if qucols and "bank_id" not in qucols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE questions ADD COLUMN bank_id INTEGER"))
    qcols = {c["name"] for c in inspect(engine).get_columns("quizzes")} if inspect(engine).has_table("quizzes") else set()
    if qcols and "code" not in qcols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE quizzes ADD COLUMN code VARCHAR DEFAULT ''"))
    if qcols and "loai" not in qcols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE quizzes ADD COLUMN loai VARCHAR DEFAULT 'tu_luyen'"))
    if qcols and "assignment_id" not in qcols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE quizzes ADD COLUMN assignment_id INTEGER"))
            # đề đã giao từ trước: nối ngược lại để chúng cũng được bảo vệ
            conn.execute(text("UPDATE quizzes SET assignment_id = ("
                              "SELECT a.id FROM assignments a WHERE a.quiz_id = quizzes.id) "
                              "WHERE assignment_id IS NULL"))
    dcols = {c["name"] for c in inspect(engine).get_columns("documents")} if inspect(engine).has_table("documents") else set()
    if dcols and "progress" not in dcols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE documents ADD COLUMN progress VARCHAR DEFAULT ''"))
    pcols = {c["name"] for c in inspect(engine).get_columns("study_plans")} if inspect(engine).has_table("study_plans") else set()
    if pcols and "snapshot" not in pcols:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE study_plans ADD COLUMN snapshot JSON"))


def seed_topics():
    """Nạp taxonomy từ data/topics.json nếu bảng còn trống."""
    if not TOPICS_FILE.exists():
        return
    with SessionLocal() as s:
        if s.query(Subject).first():
            return
        data = json.loads(TOPICS_FILE.read_text(encoding="utf-8"))
        for subj in data:
            subject = Subject(name=subj["name"])
            s.add(subject)
            for i, ch in enumerate(subj["chapters"]):
                chapter = Chapter(name=ch["name"], order=i, subject=subject)
                s.add(chapter)
                for t in ch["topics"]:
                    s.add(Topic(name=t, chapter=chapter))
        s.commit()


def _hash(pw: str) -> str:
    import bcrypt
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def _check(pw: str, h: str) -> bool:
    import bcrypt
    return bool(h) and bcrypt.checkpw(pw.encode(), h.encode())


def _new_recovery_code() -> str:
    """Mã 8 ký tự dễ đọc (bỏ 0/O/1/I), dạng ABCD-EFGH."""
    import secrets
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    raw = "".join(secrets.choice(alphabet) for _ in range(8))
    return raw[:4] + "-" + raw[4:]


def register(username: str, password: str, confirm: str, email: str = "") -> tuple[User | None, str, str]:
    """Tạo tài khoản mới. Trả về (user, lỗi, mã khôi phục — chỉ hiện đúng 1 lần)."""
    username = username.strip().lower()
    if len(username) < 2:
        return None, "Tên đăng nhập cần ít nhất 2 ký tự", ""
    if len(password) < 4:
        return None, "Mật khẩu cần ít nhất 4 ký tự", ""
    if password != confirm:
        return None, "Mật khẩu nhập lại không khớp", ""
    with SessionLocal() as s:
        if s.query(User).filter_by(username=username).first():
            return None, "Tên đăng nhập đã tồn tại", ""
        code = _new_recovery_code()
        u = User(username=username, password_hash=_hash(password), email=email.strip(), recovery_hash=_hash(code))
        s.add(u); s.commit()
        return u, "", code


def login(username: str, password: str) -> tuple[User | None, str]:
    """Đăng nhập. Tài khoản cũ chưa có mật khẩu sẽ nhận mật khẩu này làm mật khẩu chính thức."""
    username = username.strip().lower()
    with SessionLocal() as s:
        u = s.query(User).filter_by(username=username).first()
        if not u:
            return None, "Tài khoản không tồn tại — hãy Đăng ký"
        if not u.password_hash:
            if len(password) < 4:
                return None, "Tài khoản này chưa có mật khẩu. Nhập mật khẩu ≥ 4 ký tự để đặt."
            u.password_hash = _hash(password); s.commit()
            return u, ""
        if _check(password, u.password_hash):
            return u, ""
        return None, "Sai mật khẩu"


def change_password(user_id: int, old: str, new: str, confirm: str) -> str:
    """Đổi mật khẩu khi đang đăng nhập. Trả về '' nếu ok, ngược lại là thông báo lỗi."""
    if len(new) < 4:
        return "Mật khẩu mới cần ít nhất 4 ký tự"
    if new != confirm:
        return "Mật khẩu nhập lại không khớp"
    with SessionLocal() as s:
        u = s.get(User, user_id)
        if not _check(old, u.password_hash):
            return "Mật khẩu hiện tại không đúng"
        u.password_hash = _hash(new)
        u.token_version = (u.token_version or 0) + 1   # đuổi mọi phiên đăng nhập cũ
        s.commit()
    return ""


def issue_recovery_code(user_id: int, password: str | None = None) -> tuple[str, str]:
    """Cấp (lại) mã khôi phục. Nếu truyền password thì phải đúng. Trả về (mã, lỗi)."""
    with SessionLocal() as s:
        u = s.get(User, user_id)
        if password is not None and not _check(password, u.password_hash):
            return "", "Mật khẩu không đúng"
        code = _new_recovery_code()
        u.recovery_hash = _hash(code); u.reset_fails = 0; u.reset_locked_until = None; s.commit()
        return code, ""


def has_recovery_code(user_id: int) -> bool:
    with SessionLocal() as s:
        return bool(s.get(User, user_id).recovery_hash)


def reset_password_with_code(username: str, code: str, new: str, confirm: str) -> tuple[bool, str, str]:
    """Quên mật khẩu: tên + mã khôi phục -> mật khẩu mới. Sai 5 lần liên tiếp -> khoá 15 phút.
    Sau khi dùng, mã cũ bị vô hiệu và cấp mã mới. Trả về (ok, lỗi, mã mới)."""
    from datetime import timedelta
    username = username.strip().lower()
    code = code.strip().upper().replace(" ", "")
    if "-" not in code and len(code) == 8:
        code = code[:4] + "-" + code[4:]
    with SessionLocal() as s:
        u = s.query(User).filter_by(username=username).first()
        if not u:
            return False, "Tài khoản không tồn tại", ""
        if u.reset_locked_until and u.reset_locked_until > datetime.utcnow():
            left = int((u.reset_locked_until - datetime.utcnow()).total_seconds() // 60) + 1
            return False, f"Nhập sai quá nhiều lần. Thử lại sau {left} phút hoặc liên hệ quản trị viên.", ""
        if not u.recovery_hash:
            return False, "Tài khoản này chưa có mã khôi phục — liên hệ quản trị viên để đặt lại.", ""
        if not _check(code, u.recovery_hash):
            u.reset_fails = (u.reset_fails or 0) + 1
            if u.reset_fails >= 5:
                u.reset_locked_until = datetime.utcnow() + timedelta(minutes=15); u.reset_fails = 0
            s.commit()
            return False, "Mã khôi phục không đúng", ""
        if len(new) < 4:
            return False, "Mật khẩu mới cần ít nhất 4 ký tự", ""
        if new != confirm:
            return False, "Mật khẩu nhập lại không khớp", ""
        new_code = _new_recovery_code()
        u.password_hash = _hash(new); u.recovery_hash = _hash(new_code)
        u.token_version = (u.token_version or 0) + 1   # đuổi mọi phiên đăng nhập cũ
        u.reset_fails = 0; u.reset_locked_until = None; s.commit()
        return True, "", new_code


# ----------------------------- GHI NHỚ ĐĂNG NHẬP (cookie) -----------------------------
def make_remember_token(user: User, days: int = 14) -> str:
    """JWT ký bằng JWT_SECRET; kèm 12 ký tự cuối của password_hash để đổi mật khẩu là token cũ hết hiệu lực."""
    import os
    from datetime import timedelta, timezone
    import jwt
    secret = os.getenv("JWT_SECRET", "doi-secret-nay-trong-.env")
    return jwt.encode({"sub": str(user.id), "ph": (user.password_hash or "")[-12:],
                       "exp": datetime.now(timezone.utc) + timedelta(days=days)}, secret, algorithm="HS256")


def user_from_remember_token(token: str) -> User | None:
    import os
    import jwt
    secret = os.getenv("JWT_SECRET", "doi-secret-nay-trong-.env")
    try:
        data = jwt.decode(token, secret, algorithms=["HS256"])
    except Exception:  # noqa: BLE001
        return None
    with SessionLocal() as s:
        u = s.get(User, int(data["sub"]))
        if u and (u.password_hash or "")[-12:] == data.get("ph"):
            return u
    return None
