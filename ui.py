"""Hàm dùng chung cho các trang Streamlit: đăng nhập/đăng ký/quên mật khẩu, ghi nhớ đăng nhập, menu tài khoản."""
import streamlit as st

from app.db import (SessionLocal, Subject, change_password, has_recovery_code, init_db, issue_recovery_code, login,
                    make_remember_token, register, reset_password_with_code, user_from_remember_token)

COOKIE = "ala_remember"
REMEMBER_DAYS = 14


def _cookies():
    """CookieController render 1 component; lần render đầu có thể chưa đọc được cookie -> trả None."""
    try:
        from streamlit_cookies_controller import CookieController
        if "_cookie_ctl" not in st.session_state:
            st.session_state._cookie_ctl = CookieController(key="ala_cookies")
        return st.session_state._cookie_ctl
    except Exception:  # noqa: BLE001
        return None


def _show_recovery_code(code: str, first_time: bool):
    st.warning("**Lưu mã khôi phục này lại** (ghi vào sổ / chụp màn hình). Đây là cách duy nhất tự lấy lại tài khoản khi quên mật khẩu. "
               "Mã chỉ hiện **một lần**." if first_time else "Mã khôi phục mới của bạn (mã cũ đã hết hiệu lực):")
    st.code(code, language=None)


def require_login():
    """Màn hình Đăng nhập / Đăng ký / Quên mật khẩu, có ghi nhớ đăng nhập bằng cookie. Trả về User."""
    init_db()
    ctl = _cookies()

    # --- Tự đăng nhập từ cookie ---
    if "user" not in st.session_state and ctl is not None:
        tok = ctl.get(COOKIE)
        if tok:
            u = user_from_remember_token(tok)
            if u:
                st.session_state.user = u
            else:
                ctl.remove(COOKIE)

    if "user" not in st.session_state:
        st.title("🎓 AI Learning Assistant")
        tab_in, tab_up, tab_forgot = st.tabs(["Đăng nhập", "Đăng ký", "Quên mật khẩu"])

        with tab_in:
            with st.form("login"):
                name = st.text_input("Tên đăng nhập")
                pw = st.text_input("Mật khẩu", type="password")
                remember = st.checkbox(f"Ghi nhớ đăng nhập ({REMEMBER_DAYS} ngày) — bỏ tick nếu dùng máy chung", value=True)
                if st.form_submit_button("Đăng nhập", type="primary"):
                    user, err = login(name, pw)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.user = user
                        if remember and ctl is not None:
                            ctl.set(COOKIE, make_remember_token(user, REMEMBER_DAYS), max_age=REMEMBER_DAYS * 86400)
                        if not has_recovery_code(user.id):          # tài khoản cũ: cấp mã 1 lần
                            code, _ = issue_recovery_code(user.id)
                            st.session_state.pending_code = (code, True)
                        st.rerun()

        with tab_up:
            with st.form("register"):
                name = st.text_input("Tên đăng nhập", placeholder="ví dụ: an")
                email = st.text_input("Email (tuỳ chọn)")
                pw = st.text_input("Mật khẩu", type="password")
                pw2 = st.text_input("Nhập lại mật khẩu", type="password")
                if st.form_submit_button("Tạo tài khoản", type="primary"):
                    user, err, code = register(name, pw, pw2, email)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.user = user
                        st.session_state.pending_code = (code, True)
                        if ctl is not None:
                            ctl.set(COOKIE, make_remember_token(user, REMEMBER_DAYS), max_age=REMEMBER_DAYS * 86400)
                        st.rerun()

        with tab_forgot:
            st.caption("Nhập mã khôi phục được cấp lúc đăng ký. Không còn mã? Liên hệ quản trị viên để đặt lại.")
            with st.form("forgot"):
                name = st.text_input("Tên đăng nhập")
                code = st.text_input("Mã khôi phục", placeholder="ABCD-EFGH")
                pw = st.text_input("Mật khẩu mới", type="password")
                pw2 = st.text_input("Nhập lại mật khẩu mới", type="password")
                if st.form_submit_button("Đặt lại mật khẩu", type="primary"):
                    ok, err, new_code = reset_password_with_code(name, code, pw, pw2)
                    if not ok:
                        st.error(err)
                    else:
                        st.success("Đã đổi mật khẩu. Đăng nhập lại ở tab Đăng nhập.")
                        _show_recovery_code(new_code, first_time=False)
        st.stop()

    u = st.session_state.user

    # --- Mã khôi phục cần hiện 1 lần (tài khoản mới / tài khoản cũ vừa được cấp) ---
    if st.session_state.get("pending_code"):
        code, first = st.session_state.pending_code
        _show_recovery_code(code, first)
        if st.button("Tôi đã lưu mã"):
            st.session_state.pending_code = None
            st.rerun()

    # --- Sidebar: thông tin + menu tài khoản ---
    with st.sidebar:
        icon = {"admin": "👑 ", "teacher": "🎓 "}.get(u.role, "👤 ")
        st.caption(icon + u.username + ({"admin": " (admin)", "teacher": " (giáo viên)"}.get(u.role, "")))
        if u.role != "admin":
            st.markdown("<style>[data-testid=stSidebarNav] a[href*=Quan_tri]{display:none}</style>", unsafe_allow_html=True)
        with st.expander("⚙️ Tài khoản"):
            with st.form("chpw"):
                st.markdown("**Đổi mật khẩu**")
                old = st.text_input("Mật khẩu hiện tại", type="password")
                new = st.text_input("Mật khẩu mới", type="password")
                new2 = st.text_input("Nhập lại", type="password")
                if st.form_submit_button("Đổi"):
                    err = change_password(u.id, old, new, new2)
                    if err:
                        st.error(err)
                    else:
                        with SessionLocal() as s:
                            from app.db import User
                            st.session_state.user = s.get(User, u.id)
                        if ctl is not None:                       # làm mới cookie với hash mới
                            ctl.set(COOKIE, make_remember_token(st.session_state.user, REMEMBER_DAYS), max_age=REMEMBER_DAYS * 86400)
                        st.success("Đã đổi mật khẩu")
            with st.form("recode"):
                st.markdown("**Cấp lại mã khôi phục**")
                pwc = st.text_input("Mật khẩu hiện tại", type="password", key="pwc")
                if st.form_submit_button("Cấp mã mới"):
                    code, err = issue_recovery_code(u.id, pwc)
                    if err:
                        st.error(err)
                    else:
                        st.session_state.pending_code = (code, False)
                        st.rerun()
        if st.button("Đăng xuất"):
            if ctl is not None:
                ctl.remove(COOKIE)
            st.session_state.clear()
            st.rerun()
    return u


def subject_selector(label="Môn học", allow_all=False):
    with SessionLocal() as s:
        subjects = s.query(Subject).all()
    options = ([None] if allow_all else []) + subjects
    return st.selectbox(label, options, format_func=lambda x: "Tất cả" if x is None else x.name)
