/* ===========================================================================
   VuongEdu — lớp ứng dụng: nối giao diện với REST API (FastAPI + JWT).
   Nạp SAU ui.js nên có thể ghi đè vài hàm của giao diện (đăng nhập, chat…).
   =========================================================================== */
(() => {
  "use strict";

  const TOKEN_KEY = "vuongedu_token";
  const state = {
    user: null,
    subjects: [],
    quiz: null,           // {quiz_id, questions, selections}
    assignmentQuiz: null, // {assignment_id, quiz_id, questions}
    analytics: null,
    plan: null,
    gradeResult: null,
    classDetail: null,
  };

  /* ------------------------------------------------------------------ tiện ích */
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /** Viết hoa chữ đầu mỗi tiếng của tên người: "phan ngọc vương" -> "Phan Ngọc Vương".
   *  Tên đăng nhập trong CSDL vẫn là chữ thường (dùng để so khớp), đây chỉ là cách hiển thị. */
  const tenDep = (s) => String(s ?? "").trim().split(/\s+/)
    .map((t) => (t ? t[0].toLocaleUpperCase("vi") + t.slice(1) : t)).join(" ");
  const token = {
    get: () => { try { return localStorage.getItem(TOKEN_KEY); } catch { return null; } },
    set: (v) => { try { localStorage.setItem(TOKEN_KEY, v); } catch { /* chế độ riêng tư */ } },
    clear: () => { try { localStorage.removeItem(TOKEN_KEY); } catch { /* bỏ qua */ } },
  };

  function toast(msg, kind = "ok") {
    let box = $("toastBox");
    if (!box) { box = document.createElement("div"); box.id = "toastBox"; document.body.appendChild(box); }
    const t = document.createElement("div");
    t.className = `toast ${kind}`;
    t.textContent = msg;
    box.appendChild(t);
    setTimeout(() => t.remove(), 4200);
  }

  function setStatus(id, msg, kind = "busy") {
    const el = $(id);
    if (el) { el.textContent = msg; el.className = `status-line ${kind}`; }
  }

  // Tên người-đọc-được cho từng trường, dùng khi máy chủ báo lỗi dữ liệu gửi lên.
  const TEN_O = {
    n: "Số câu", topic_ids: "Chủ đề", subject_id: "Môn học", difficulty: "Độ khó",
    email: "Email", password: "Mật khẩu", username: "Tên đăng nhập", title: "Tiêu đề",
  };

  /** Đổi phần thân lỗi của máy chủ thành MỘT CÂU đọc được.
   *
   *  FastAPI trả lỗi kiểm tra dữ liệu (422) với `detail` là MẢNG object
   *  [{loc:["body","n"], msg:"Input should be less than or equal to 15"}].
   *  Trước đây chỗ này nối thẳng vào chuỗi nên màn hình chỉ hiện "[object Object]",
   *  người dùng không biết sai ở đâu mà sửa. */
  function moTaLoi(data, status) {
    const d = data && (data.detail ?? data.message);
    if (typeof d === "string" && d) return d;
    if (Array.isArray(d) && d.length) {
      return d.map((e) => {
        const o = Array.isArray(e?.loc) ? e.loc[e.loc.length - 1] : null;
        const ten = TEN_O[o] || o;
        return [ten, e?.msg].filter(Boolean).join(": ") || JSON.stringify(e);
      }).join(" · ");
    }
    if (d && typeof d === "object" && !Array.isArray(d)) return d.msg || JSON.stringify(d);
    return `Lỗi ${status}`;
  }

  async function api(path, { method = "GET", body, form, auth = true } = {}) {
    const headers = {};
    const t = token.get();
    if (auth && t) headers.Authorization = `Bearer ${t}`;
    let payload;
    if (form) { payload = form; }
    else if (body !== undefined) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }
    const res = await fetch(path, { method, headers, body: payload });
    if (res.status === 401) { token.clear(); state.user = null; paintUser(); throw new Error("Bạn cần đăng nhập"); }
    let data = null;
    try { data = await res.json(); } catch { /* không phải JSON */ }
    if (!res.ok) throw new Error(moTaLoi(data, res.status));
    return data;
  }

  const fmtPct = (v) => (v === null || v === undefined ? "—" : `${Math.round(v)}%`);
  const lvlClass = (lvl) => ({ "Yếu": "lvl-weak", "Trung bình": "lvl-mid", "Tốt": "lvl-good" }[lvl] || "lvl-na");
  const masteryColor = (v) => (v === null || v === undefined ? "var(--input-bg)"
    : v < 50 ? "#d9534f" : v < 75 ? "#f0ad4e" : "#5cb85c");
  const dstr = (s) => (s ? new Date(s).toLocaleDateString("vi-VN") : "—");

  /* ------------------------------------------------------------------ xác thực */
  function paintUser() {
    const u = state.user;
    const loginBtn = $("topLoginBtn"), pill = $("topUserPill"), name = $("topUserName");
    const title = $("dropdownUserTitle"), welcome = $("welcomeUserName");
    if (u) {
      if (loginBtn) loginBtn.style.display = "none";
      if (pill) pill.style.display = "flex";
      if (name) name.textContent = tenDep(u.username);
      if (title) title.textContent = `${tenDep(u.username)}${u.role === "admin" ? " · quản trị" : u.role === "teacher" ? " · giáo viên" : ""}`;
      const av = $("topUserAvatar"); if (av) av.textContent = u.username.charAt(0).toUpperCase();
      if (welcome) welcome.textContent = tenDep(u.username);
    } else {
      if (loginBtn) loginBtn.style.display = "";
      if (pill) pill.style.display = "none";
    }
    document.querySelectorAll(".nav-admin-only").forEach((el) => { el.hidden = !(u && u.role === "admin"); });
    const t = $("clsTeacher"); if (t) t.hidden = !(u && (u.role === "teacher" || u.role === "admin"));
    const d = $("docAdminBox"); if (d) d.hidden = !(u && u.role === "admin");
  }

  async function boot() {
    if (!token.get()) { paintUser(); return; }
    try { state.user = await api("/me"); } catch { state.user = null; }
    paintUser();
    if (state.user) { loadSubjects().then(() => renderHomeStats()); }
  }

  window.handleLoginSubmit = async function (e) {
    if (e && e.preventDefault) e.preventDefault();
    const username = ($("loginUsername") || {}).value || "";
    const password = ($("loginPassword") || {}).value || "";
    try {
      const r = await api("/auth/login", { method: "POST", body: { username, password }, auth: false });
      token.set(r.access_token);
      state.user = { id: r.user_id, username: r.username, role: r.role };
      paintUser();
      if (typeof closeAuthModal === "function") closeAuthModal();
      toast(`Xin chào ${tenDep(r.username)}!`);
      await loadSubjects(); renderHomeStats();
    } catch (err) {
      if (typeof showAuthAlert === "function") showAuthAlert(err.message, "error"); else toast(err.message, "err");
    }
    return false;
  };

  window.handleRegisterSubmit = async function (e) {
    if (e && e.preventDefault) e.preventDefault();
    const username = ($("regUsername") || {}).value || "";
    const password = ($("regPassword") || {}).value || "";
    const confirm = ($("regConfirmPassword") || {}).value || "";
    if (password !== confirm) {
      const m = "Mật khẩu nhập lại không khớp";
      if (typeof showAuthAlert === "function") showAuthAlert(m, "error"); else toast(m, "err");
      return false;
    }
    try {
      const r = await api("/auth/register", { method: "POST", body: { username, password }, auth: false });
      token.set(r.access_token);
      state.user = { id: r.user_id, username: r.username, role: r.role };
      paintUser();
      if (typeof closeAuthModal === "function") closeAuthModal();
      if (r.recovery_code) showRecoveryCode(r.recovery_code);
      await loadSubjects(); renderHomeStats();
    } catch (err) {
      if (typeof showAuthAlert === "function") showAuthAlert(err.message, "error"); else toast(err.message, "err");
    }
    return false;
  };

  function showRecoveryCode(code) {
    const wrap = document.createElement("div");
    wrap.className = "auth-modal-overlay";
    wrap.style.cssText = "display:flex;position:fixed;inset:0;z-index:10000;align-items:center;justify-content:center;background:rgba(0,0,0,.45)";
    wrap.innerHTML = `<div class="panel" style="max-width:430px;margin:0">
      <h3 class="panel-title">🔑 Mã khôi phục của bạn</h3>
      <p class="hint">Lưu lại mã này. Đây là cách duy nhất tự lấy lại tài khoản khi quên mật khẩu — mã chỉ hiện <b>một lần</b>.</p>
      <div style="font-size:1.6rem;font-weight:800;letter-spacing:.12em;text-align:center;padding:14px;border-radius:12px;background:var(--input-bg);color:var(--apple-blue)">${esc(code)}</div>
      <button class="btn btn-primary" style="margin-top:14px;width:100%">Tôi đã lưu mã</button></div>`;
    wrap.querySelector("button").onclick = () => wrap.remove();
    document.body.appendChild(wrap);
  }

  window.logoutFromDropdown = function () {
    token.clear(); state.user = null; paintUser();
    toast("Đã đăng xuất");
    if (typeof switchTab === "function") switchTab("home", document.querySelector(".nav-item"));
  };

  function requireLogin() {
    if (state.user) return true;
    toast("Bạn cần đăng nhập để dùng chức năng này", "err");
    if (typeof openAuthModal === "function") openAuthModal();
    return false;
  }

  /* ------------------------------------------------------------------ dữ liệu chung */
  async function loadSubjects() {
    if (state.subjects.length) return state.subjects;
    try { state.subjects = await api("/subjects", { auth: false }); } catch { state.subjects = []; }
    fillSubjectSelects();
    return state.subjects;
  }

  function fillSubjectSelects() {
    const ids = ["docSubject", "quizSubject", "scSubject", "anSubject", "plSubject", "grSubject", "clsSubject", "fb-subject"];
    ids.forEach((id) => {
      const el = $(id); if (!el || el.dataset.filled) return;
      el.innerHTML = state.subjects.map((s) => `<option value="${s.id}">${esc(s.name)}</option>`).join("");
      el.dataset.filled = "1";
    });
    // Ô chọn môn của màn Chat có thêm lựa chọn "Tự đoán": trước đây màn này không
    // có ô nào, nên mở Chat thẳng từ thanh điều hướng là hỏi trên TOÀN BỘ kho sách
    // và câu trả lời kèm trích dẫn của môn chẳng liên quan.
    const ch = $("chatSubject");
    if (ch && !ch.dataset.filled) {
      ch.innerHTML = `<option value="">Tự đoán theo câu hỏi</option>` +
        state.subjects.map((s) => `<option value="${s.id}">${esc(s.name)}</option>`).join("");
      ch.dataset.filled = "1";
      if (window.__chatSubjectId) ch.value = String(window.__chatSubjectId);
    }
    linkChapters("docSubject", "docChapter", true);
    linkChapters("quizSubject", "quizChapter", false, renderQuizTopics);
    linkChapters("grSubject", "grChapter", true);
  }

  function chaptersOf(subjectId) {
    const s = state.subjects.find((x) => String(x.id) === String(subjectId));
    return s ? s.chapters : [];
  }

  function linkChapters(subSelId, chapSelId, allowEmpty, after) {
    const sub = $(subSelId), chap = $(chapSelId);
    if (!sub || !chap) return;
    const fill = () => {
      const list = chaptersOf(sub.value);
      chap.innerHTML = (allowEmpty ? '<option value="">— Cả môn —</option>' : "") +
        list.map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
      if (after) after();
    };
    sub.onchange = fill; fill();
  }

  /* ------------------------------------------------------------------ TRANG CHỦ */
  async function renderHomeStats() {
    if (!state.user) return;
    let d; try { d = await api("/dashboard"); } catch { return; }
    const host = $("homeQuickStats") || (() => {
      const hero = document.querySelector("#view-home .hero-home-text") || document.querySelector("#view-home");
      const div = document.createElement("div"); div.id = "homeQuickStats"; div.className = "stat-row";
      div.style.marginTop = "18px"; hero.appendChild(div); return div;
    })();
    const s = d.stats;
    host.innerHTML = [
      ["📚", s.documents, "tài liệu"],
      ["📝", s.answers, "câu đã làm"],
      ["✅", s.accuracy === null ? "—" : `${s.accuracy}%`, "tỷ lệ đúng"],
      ["🔴", s.weak, "chủ đề yếu"],
      ["🎯", s.avg_score ?? "—", "điểm TB"],
    ].map(([ic, v, l]) => `<div class="stat"><b>${esc(v)}</b><span>${ic} ${l}</span></div>`).join("");

    let extra = $("homeTodo");
    if (!extra) { extra = document.createElement("div"); extra.id = "homeTodo"; host.parentElement.appendChild(extra); }
    const blocks = [];
    if (d.weak_topics.length) {
      blocks.push(`<div class="panel"><h3 class="panel-title">🔴 Cần ưu tiên</h3><div class="mini-list">${
        d.weak_topics.map((t) => `<div class="mini-item"><span>${esc(t.topic)}</span><span class="r">${fmtPct(t.mastery)} · ${t.n_correct}/${t.n} câu</span></div>`).join("")
      }</div></div>`);
    }
    if (d.due.length) {
      blocks.push(`<div class="panel"><h3 class="panel-title">🔁 Đến hạn ôn lại</h3><div class="mini-list">${
        d.due.slice(0, 4).map((t) => `<div class="mini-item"><span>${esc(t.topic)}</span><span class="r">quá hạn ${Math.round(t.overdue_days)} ngày</span></div>`).join("")
      }</div></div>`);
    }
    if (d.today.length) {
      blocks.push(`<div class="panel"><h3 class="panel-title">🗺️ Việc hôm nay</h3><div class="mini-list">${
        d.today.map((i) => `<div class="mini-item"><span>${({ study: "📖", quiz: "📝", review: "🔁" }[i.kind] || "•")} ${esc(i.title)}</span><span class="r">${esc(i.topic || "")}</span></div>`).join("")
      }</div></div>`);
    }
    if (d.assignments.length) {
      blocks.push(`<div class="panel"><h3 class="panel-title">📌 Đề giáo viên giao</h3><div class="mini-list">${
        d.assignments.map((a) => `<div class="mini-item"><span>${esc(a.title)} · ${esc(a.class)}</span><span class="r">${a.n_questions} câu</span></div>`).join("")
      }</div></div>`);
    }
    extra.innerHTML = blocks.length ? `<div class="two-col">${blocks.join("")}</div>` : "";
  }

  /* ------------------------------------------------------------------ TÀI LIỆU */
  async function renderLibrary() {
    const host = $("docLibrary"); if (!host) return;
    host.innerHTML = '<div class="skeleton">Đang tải thư viện…</div>';
    let docs;
    try { docs = await api("/documents"); } catch (e) { host.innerHTML = `<div class="empty-note">${esc(e.message)}</div>`; return; }
    if (!docs.length) { host.innerHTML = '<div class="empty-note">Thư viện chưa có tài liệu.</div>'; return; }
    const byId = Object.fromEntries(state.subjects.map((s) => [s.id, s]));
    const chapName = {};
    state.subjects.forEach((s) => s.chapters.forEach((c) => { chapName[c.id] = c.name; }));
    const groups = {};
    docs.forEach((d) => { (groups[d.subject_id] ||= []).push(d); });
    const isAdmin = state.user && state.user.role === "admin";
    host.innerHTML = Object.entries(groups).map(([sid, list]) => `
      <div class="lib-subject">
        <h3><span>${esc((byId[sid] || {}).name || "Khác")}</span>
          <span class="meta" style="font-weight:400;font-size:.8rem">${list.length} tài liệu · ${list.reduce((a, b) => a + b.n_chunks, 0)} đoạn</span></h3>
        ${list.map((d) => `<div class="lib-doc">
            <span>📄</span><span class="name">${esc(d.filename)}${d.chapter_id ? ` · ${esc((chapName[d.chapter_id] || "").split(":")[0])}` : ""}</span>
            <span class="meta">${d.n_chunks} đoạn</span>
            ${isAdmin ? `<button class="btn btn-ghost btn-sm" onclick="deleteDocument(${d.id})">Xoá</button>` : ""}
          </div>`).join("")}
      </div>`).join("");
  }

  window.uploadDocument = async function () {
    if (!requireLogin()) return;
    const f = $("docFile").files[0];
    if (!f) { setStatus("docUploadStatus", "Chưa chọn tệp", "err"); return; }
    const fd = new FormData();
    fd.append("file", f);
    fd.append("subject_id", $("docSubject").value);
    if ($("docChapter").value) fd.append("chapter_id", $("docChapter").value);
    fd.append("page_from", $("docFrom").value || 1);
    fd.append("page_to", $("docTo").value || 0);
    setStatus("docUploadStatus", "Đang xử lý (PDF scan sẽ OCR, có thể vài phút)…");
    try {
      const r = await api("/documents", { method: "POST", form: fd });
      setStatus("docUploadStatus", `Xong: ${r.n_chunks} đoạn đã được index`, "ok");
      toast("Đã nạp tài liệu");
      renderLibrary();
    } catch (e) { setStatus("docUploadStatus", e.message, "err"); }
  };

  window.deleteDocument = async function (id) {
    if (!confirm("Xoá tài liệu này khỏi thư viện?")) return;
    try { await api(`/documents/${id}`, { method: "DELETE" }); toast("Đã xoá"); renderLibrary(); }
    catch (e) { toast(e.message, "err"); }
  };

  /* ------------------------------------------------------------------ HỎI AI (RAG) */
  function bubble(role, html) {
    const box = $("chatBox"); if (!box) return null;
    const d = document.createElement("div");
    d.className = `bubble ${role}`;
    d.innerHTML = html;
    box.appendChild(d); box.scrollTop = box.scrollHeight;
    return d;
  }

  function citationsHtml(cites) {
    if (!cites || !cites.length) return "";
    const id = `c${Math.random().toString(36).slice(2, 8)}`;
    return `<div class="citations">
      <button class="cite-toggle" onclick="document.getElementById('${id}').hidden=!document.getElementById('${id}').hidden">
        📎 ${cites.length} nguồn trích dẫn</button>
      <div class="cite-list" id="${id}" hidden>${cites.map((c, i) =>
        `<div class="cite"><b>[${i + 1}] ${esc(c.filename)} — trang ${c.page}</b>${esc((c.text || "").slice(0, 220))}…</div>`).join("")}</div>
    </div>`;
  }

  window.sendMessage = async function () {
    if (!requireLogin()) return;
    const input = $("userInput"); const text = (input.value || "").trim();
    if (!text) return;
    input.value = "";
    bubble("user", esc(text));
    const think = bubble("assistant thinking", '<div class="typing-dots"><span></span><span></span><span></span></div>');
    try {
      const oMon = $("chatSubject");
      const sid = oMon && oMon.value ? +oMon.value : (window.__chatSubjectId || null);
      const r = await api("/chat", { method: "POST", body: { message: text, subject_id: sid } });
      think.remove();
      bubble("assistant", mdToHtml(r.answer) + citationsHtml(r.citations));
    } catch (e) {
      think.remove();
      bubble("assistant", `<span style="color:#d9534f">${esc(e.message)}</span>`);
    }
  };

  function mdToHtml(s) {
    let h = esc(s || "");
    h = h.replace(/```([\s\S]*?)```/g, (m, c) => `<pre style="white-space:pre-wrap">${c}</pre>`);
    h = h.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/(^|\W)\*(?!\s)(.+?)\*(?=\W|$)/g, "$1<i>$2</i>");
    h = h.replace(/^### (.+)$/gm, "<h4>$1</h4>").replace(/^## (.+)$/gm, "<h3>$1</h3>");
    h = h.replace(/^\s*[-•] (.+)$/gm, "<li>$1</li>").replace(/(<li>[\s\S]*?<\/li>)/g, "<ul>$1</ul>");
    return h.replace(/\n{2,}/g, "<br><br>").replace(/\n/g, "<br>");
  }

  async function loadChatHistory() {
    if (!state.user) return;
    const box = $("chatBox"); if (!box || box.dataset.loaded) return;
    try {
      const hist = await api("/chat/history?limit=20");
      if (hist.length) {
        box.innerHTML = "";
        hist.forEach((m) => bubble(m.role === "user" ? "user" : "assistant",
          m.role === "user" ? esc(m.content) : mdToHtml(m.content) + citationsHtml(m.citations)));
      }
      box.dataset.loaded = "1";
    } catch { /* bỏ qua */ }
  }

  /* ------------------------------------------------------------------ LUYỆN ĐỀ */
  function renderQuizTopics() {
    const host = $("quizTopics"); const chap = $("quizChapter"); if (!host || !chap) return;
    const list = chaptersOf($("quizSubject").value).find((c) => String(c.id) === String(chap.value));
    host.innerHTML = (list ? list.topics : []).map((t) =>
      `<span class="chip" data-id="${t.id}" onclick="this.classList.toggle('on')">${esc(t.name)}</span>`).join("");
  }
  window.renderQuizTopics = renderQuizTopics;
  document.addEventListener("change", (e) => { if (e.target && e.target.id === "quizChapter") renderQuizTopics(); });

  window.suggestQuiz = async function () {
    if (!requireLogin()) return;
    const host = $("quizReco"); host.innerHTML = '<div class="skeleton">Đang xem hồ sơ học tập…</div>';
    try {
      const r = await api(`/learning/recommend?subject_id=${$("quizSubject").value}`);
      if (!r.topics.length) { host.innerHTML = '<div class="empty-note">Chưa đủ dữ liệu để gợi ý. Hãy làm vài đề trước.</div>'; return; }
      host.innerHTML = `<div class="mini-list" style="margin-top:10px">${
        r.topics.map((t) => `<div class="mini-item"><span>${esc(t.topic)}</span><span class="r">${esc(t.why)}</span></div>`).join("")}
        </div>
        <p class="hint" style="margin-top:10px">Độ khó đề xuất: <b>${({ easy: "dễ", medium: "trung bình", hard: "khó" }[r.difficulty])}</b> · nguồn: ${esc(r.source)}</p>
        ${r.blocked.length ? `<p class="hint">Tạm hoãn (nền còn yếu): ${r.blocked.slice(0, 3).map((b) => `${esc(b.topic)} ← cần ${b.needs.map(esc).join(", ")}`).join("; ")}</p>` : ""}
        <button class="btn btn-primary" onclick='applyReco(${JSON.stringify(r).replace(/'/g, "&#39;")})'>Tạo đề theo gợi ý</button>`;
    } catch (e) { host.innerHTML = `<div class="empty-note">${esc(e.message)}</div>`; }
  };

  window.applyReco = function (r) {
    $("quizDiff").value = r.difficulty;
    const ids = r.topics.map((t) => String(t.topic_id));
    const chaps = chaptersOf($("quizSubject").value);
    const chap = chaps.find((c) => c.topics.some((t) => ids.includes(String(t.id))));
    if (chap) { $("quizChapter").value = chap.id; renderQuizTopics(); }
    document.querySelectorAll("#quizTopics .chip").forEach((c) => c.classList.toggle("on", ids.includes(c.dataset.id)));
    createQuiz();
  };

  // Phải khớp với QuizIn trong api/main.py (n: ge=3, le=60).
  const QUIZ_N_MIN = 3, QUIZ_N_MAX = 60;

  window.createQuiz = async function () {
    if (!requireLogin()) return;
    let ids = [...document.querySelectorAll("#quizTopics .chip.on")].map((c) => +c.dataset.id);
    if (!ids.length) ids = [...document.querySelectorAll("#quizTopics .chip")].map((c) => +c.dataset.id);
    if (!ids.length) { setStatus("quizStatus", "Chương này chưa có chủ đề", "err"); return; }
    // Ô "Số câu" là input number: thuộc tính max chỉ chặn nút tăng/giảm, gõ tay vẫn
    // vượt được. Kẹp tại đây để không phải đợi máy chủ trả 422 rồi mới biết.
    const nGo = +$("quizN").value;
    const n = Math.min(QUIZ_N_MAX, Math.max(QUIZ_N_MIN, nGo || QUIZ_N_MIN));
    if (n !== nGo) {
      $("quizN").value = n;
      toast(`Mỗi đề tối đa ${QUIZ_N_MAX} câu — đã chỉnh về ${n}.`);
    }
    // Đo thực tế: 15 câu ~26 giây, 60 câu ~50 giây, và còn thêm lượt xin bù nếu bước
    // kiểm tra chéo loại bớt câu. Ước lượng để người học biết còn phải chờ bao lâu.
    const uoc = Math.round(20 + n * 0.9);
    setStatus("quizStatus", `AI đang soạn ${n} câu (khoảng ${uoc}–${uoc * 2} giây)…`);
    try {
      const body = { subject_id: +$("quizSubject").value, topic_ids: ids,
                     difficulty: $("quizDiff").value, n };
      // /quiz2 chạy nền: đề dài có thể vượt 100 giây, ngưỡng Cloudflare tunnel cắt kết nối.
      const d = await api("/quiz2", { method: "POST", body });
      const r = await window.theoDoiJob(d.job_id, (_steps, giay) => {
        setStatus("quizStatus", `AI đang soạn ${n} câu — đã ${giay} giây…`);
      });
      state.quiz = { quiz_id: r.quiz_id, questions: r.questions, selections: {},
                     code: r.code, n_requested: r.n_requested, n_actual: r.n_actual,
                     shared_with: r.shared_with, difficulty: body.difficulty };
      setStatus("quizStatus", "", "ok");
      paintQuizPaper();
    } catch (e) { setStatus("quizStatus", e.message, "err"); }
  };

  const DO_KHO_VI = { easy: "Dễ", medium: "Trung bình", hard: "Khó" };

  function ngayGio(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (isNaN(d)) return String(iso).slice(0, 16).replace("T", " ");
    const hai = (x) => String(x).padStart(2, "0");
    return `${hai(d.getDate())}/${hai(d.getMonth() + 1)}/${d.getFullYear()} ${hai(d.getHours())}:${hai(d.getMinutes())}`;
  }

  function mauDiem(d) {
    return d >= 8 ? "#2ecc71" : d >= 6.5 ? "#f0ad4e" : d >= 5 ? "#e8a33d" : "#e74c3c";
  }

  /** Bảng các lần đã làm đề: mã đề, điểm, ngày — mở lại hoặc xem lại từng câu. */
  window.renderQuizHistory = async function () {
    const host = $("quizHistory");
    if (!host) return;
    if (!state.user) { host.innerHTML = ""; return; }
    host.innerHTML = '<div class="skeleton">Đang tải lịch sử làm đề…</div>';
    let ds;
    try { ds = await api("/quiz/history?limit=50"); }
    catch (e) { host.innerHTML = `<div class="status-line err">${esc(e.message)}</div>`; return; }

    if (!ds.length) {
      host.innerHTML = `<h3 class="panel-title">🕘 Lịch sử làm đề</h3>
        <p class="hint">Chưa có bài nào. Làm xong một đề là nó hiện ở đây, kèm mã đề để mở lại.</p>`;
      return;
    }
    const tb = ds.reduce((a, x) => a + (x.score || 0), 0) / ds.length;
    host.innerHTML = `<h3 class="panel-title">🕘 Lịch sử làm đề</h3>
      <p class="hint">${ds.length} lần làm · điểm trung bình
        <b style="color:${mauDiem(tb)}">${tb.toFixed(2)}</b>.
        Bấm <b>Làm lại</b> để nhận đúng đề đó và so với lần trước.</p>
      <div class="table-wrap"><table>
        <thead><tr><th>Ngày làm</th><th>Mã đề</th><th>Nguồn</th><th>Độ khó</th>
          <th>Đúng</th><th>Điểm</th><th></th></tr></thead>
        <tbody>${ds.map((x) => `
          <tr>
            <td>${esc(ngayGio(x.submitted_at))}</td>
            <td><code>${esc(x.code || "—")}</code></td>
            <td>${x.assignment ? "📘 " + esc(x.assignment)
                  : x.loai === "sua_sai" ? "🔁 Luyện lại câu sai" : "Tự luyện"}</td>
            <td>${esc(DO_KHO_VI[x.difficulty] || x.difficulty || "—")}</td>
            <td>${x.n_correct}/${x.n}</td>
            <td><b style="color:${mauDiem(x.score)}">${(x.score ?? 0).toFixed(2)}</b></td>
            <td>
              <button class="btn btn-ghost" onclick="reviewAttempt(${x.attempt_id})">Xem lại</button>
              ${x.code ? `<button class="btn btn-ghost" onclick="redoQuiz('${esc(x.code)}')">Làm lại</button>` : ""}
            </td>
          </tr>`).join("")}</tbody>
      </table></div>`;
  };

  /** Làm lại đúng đề cũ: điền mã vào ô rồi mở. */
  window.redoQuiz = function (code) {
    $("quizCode").value = code;
    $("quizCode").scrollIntoView({ behavior: "smooth", block: "center" });
    openQuizByCode();
  };

  /** Xem lại một lần làm bài: từng câu, mình chọn gì, đúng hay sai. */
  window.reviewAttempt = async function (attemptId) {
    const host = $("quizResult");
    $("quizPaper").hidden = true;
    host.hidden = false;
    host.innerHTML = '<div class="skeleton">Đang mở bài làm…</div>';
    host.scrollIntoView({ behavior: "smooth", block: "start" });
    let r;
    try { r = await api(`/quiz/history/${attemptId}`); }
    catch (e) { host.innerHTML = `<div class="status-line err">${esc(e.message)}</div>`; return; }

    host.innerHTML = `<div class="page-head">
        <h2>🕘 Bài làm ngày ${esc(ngayGio(r.submitted_at))}</h2>
        <p>Mã đề <b>${esc(r.code || "—")}</b> · đúng ${r.n_correct}/${r.n} ·
           điểm <b style="color:${mauDiem(r.score)}">${(r.score ?? 0).toFixed(2)}</b></p></div>` +
      r.questions.map((q, i) => `
        <div class="q-card">
          <div class="q-head"><span class="q-num">Câu ${i + 1}</span>
            <span class="tag">${esc((q.topic || "").split(" / ").pop())}</span>
            <span class="tag">${q.is_correct ? "✅ Đúng" : q.selected === null ? "⬜ Bỏ trống" : "❌ Sai"}</span></div>
          <div class="q-text">${mdToHtml(q.content)}</div>
          <div class="q-opts">${(q.options || []).map((o, j) => {
            const cls = j === q.correct ? "q-opt sel" : j === q.selected ? "q-opt wrong" : "q-opt";
            const dau = j === q.correct ? "✔ " : j === q.selected ? "✗ " : "";
            return `<div class="${cls}"><span>${dau}${mdToHtml(o)}</span></div>`;
          }).join("")}</div>
          ${q.explanation ? `<div class="q-explain">${mdToHtml(q.explanation)}</div>` : ""}
        </div>`).join("") +
      `<div class="q-actions">
         <button class="btn btn-ghost" onclick="cancelQuiz()">Đóng</button>
         ${r.code ? `<button class="btn btn-primary" onclick="redoQuiz('${esc(r.code)}')">Làm lại đề này</button>` : ""}
       </div>`;
    if (window.renderMath) window.renderMath(host);
  };

  /** Thẻ "Luyện lại câu sai": số câu đang sai, gom theo chủ đề. */
  window.renderMistakes = async function () {
    const host = $("quizMistakes");
    if (!host) return;
    if (!state.user) { host.innerHTML = ""; return; }
    host.innerHTML = '<div class="skeleton">Đang xem lại các câu bạn làm sai…</div>';
    let d;
    try { d = await api("/quiz/mistakes"); }
    catch (e) { host.innerHTML = `<div class="status-line err">${esc(e.message)}</div>`; return; }

    if (!d.tong) {
      host.innerHTML = `<h3 class="panel-title">🔁 Luyện lại câu sai</h3>
        <p class="hint">Chưa có câu nào cần luyện lại — những câu từng sai bạn đều đã
           làm đúng ở lần gần nhất. Làm thêm đề để hệ thống biết bạn yếu chỗ nào.</p>`;
      return;
    }
    const chips = d.theo_chu_de.slice(0, 8).map((x) =>
      `<span class="tag">${esc(x.topic)} · ${x.n}</span>`).join(" ");
    const soCau = Math.min(d.tong, 30);
    host.innerHTML = `<h3 class="panel-title">🔁 Luyện lại câu sai</h3>
      <p class="hint">Bạn đang sai <b>${d.tong}</b> câu. Chỉ tính câu mà
         <b>lần trả lời gần nhất</b> vẫn sai — làm đúng lại là câu đó tự rút khỏi danh sách.</p>
      <div class="chip-group" style="margin-bottom:10px">${chips}</div>
      <div class="form-grid">
        <label class="field"><span>Số câu luyện lại</span>
          <input id="mistakeN" class="ctl" type="number" min="1" max="${soCau}"
                 value="${Math.min(10, soCau)}"></label>
      </div>
      <button class="btn btn-primary" onclick="practiceMistakes()">Luyện lại ${soCau > 10 ? "10" : soCau} câu sai</button>
      <div id="mistakeStatus" class="status-line"></div>`;
  };

  /** Dựng đề gồm đúng những câu đang làm sai rồi mở ra làm luôn. */
  window.practiceMistakes = async function () {
    if (!requireLogin()) return;
    setStatus("mistakeStatus", "Đang dựng đề từ các câu bạn làm sai…");
    try {
      const n = +($("mistakeN") || {}).value || 10;
      const r = await api("/quiz/mistakes/practice", { method: "POST", body: { n } });
      state.quiz = { quiz_id: r.quiz_id, questions: r.questions, selections: {},
                     code: r.code, n_requested: r.n_requested, n_actual: r.n_actual,
                     shared_with: r.shared_with, sua_sai: true };
      setStatus("mistakeStatus", "", "ok");
      paintQuizPaper();
    } catch (e) { setStatus("mistakeStatus", e.message, "err"); }
  };

  /** Mở lại đúng đề mang mã người dùng gõ vào. */
  window.openQuizByCode = async function () {
    if (!requireLogin()) return;
    const ma = ($("quizCode").value || "").trim();
    if (!ma) { setStatus("quizCodeStatus", "Chưa nhập mã đề", "err"); return; }
    setStatus("quizCodeStatus", "Đang tìm đề…");
    try {
      const r = await api("/quiz/by-code", { method: "POST", body: { code: ma } });
      state.quiz = { quiz_id: r.quiz_id, questions: r.questions, selections: {},
                     code: r.code, n_requested: r.n_requested, n_actual: r.n_actual,
                     shared_with: r.shared_with };
      setStatus("quizCodeStatus", "", "ok");
      paintQuizPaper();
    } catch (e) { setStatus("quizCodeStatus", e.message, "err"); }
  };

  function paintQuizPaper() {
    const q = state.quiz; if (!q) return;
    $("quizSetup").hidden = true; $("quizResult").hidden = true;
    const host = $("quizPaper"); host.hidden = false;
    const thieu = q.n_requested && q.n_actual && q.n_actual < q.n_requested
      ? ` · <span style="color:var(--warn,#f0ad4e)">${q.n_actual}/${q.n_requested} câu`
        + ` — kho chưa đủ câu cho phần này, AI đang soạn bổ sung ở nền, lát nữa tạo lại sẽ đủ</span>` : "";
    const chung = q.shared_with > 1 ? ` · ${q.shared_with} học sinh cùng làm đề này` : "";
    // Kho có thể không đủ câu ĐÚNG độ khó đã chọn, khi đó hệ thống lấy bù từ độ khó
    // khác thay vì bắt chờ AI soạn. Nói rõ ra, kẻo người học tưởng mình chọn sai.
    const demDK = {};
    q.questions.forEach((x) => { if (x.difficulty) demDK[x.difficulty] = (demDK[x.difficulty] || 0) + 1; });
    const tenDK = { easy: "dễ", medium: "trung bình", hard: "khó" };
    const pha = Object.keys(demDK).length > 1 || (q.difficulty && !demDK[q.difficulty]);
    const ghiDK = pha
      ? ` · <span style="color:var(--warn,#f0ad4e)">độ khó thực tế: `
        + Object.entries(demDK).sort((a, b) => b[1] - a[1])
            .map(([k, v]) => `${v} câu ${tenDK[k] || k}`).join(", ")
        + ` (kho chưa đủ câu đúng mức bạn chọn)</span>` : "";
    host.innerHTML = (q.sua_sai
      ? `<div class="page-head"><h2>🔁 Luyện lại ${q.questions.length} câu sai</h2>
         <p>Đúng những câu bạn đang làm sai, câu sai nhiều lần xếp trước.
            Làm đúng câu nào thì câu đó rút khỏi danh sách.</p></div>`
      : `<div class="page-head"><h2>📝 Đề ${q.questions.length} câu</h2>
         <p>Mã đề <b>${esc(q.code || "—")}</b>${chung}${thieu}${ghiDK}<br>
         Mỗi lần tạo là một đề mới. Giữ lại mã này để mở lại đúng đề, hoặc đưa cho bạn khác cùng làm.</p></div>`) +
      q.questions.map((item, i) => `
        <div class="q-card" data-q="${item.id}">
          <div class="q-head"><span class="q-num">Câu ${i + 1}</span><span class="tag">${esc(item.topic || "")}</span></div>
          <div class="q-text">${mdToHtml(item.content)}</div>
          <div class="q-opts">${item.options.map((o, j) => `
            <label class="q-opt"><input type="radio" name="q${item.id}" value="${j}"
              onchange="pickAnswer(${item.id},${j},this)"><span>${mdToHtml(o)}</span></label>`).join("")}</div>
        </div>`).join("") +
      `<div class="q-actions">
         <button class="btn btn-primary" onclick="submitQuiz()">Nộp bài</button>
         <button class="btn btn-ghost" onclick="cancelQuiz()">Huỷ, tạo đề khác</button>
         <span id="quizSubmitStatus" class="status-line"></span></div>`;
    host.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  window.pickAnswer = function (qid, idx, el) {
    state.quiz.selections[qid] = idx;
    const card = el.closest(".q-card");
    card.querySelectorAll(".q-opt").forEach((o) => o.classList.remove("sel"));
    el.closest(".q-opt").classList.add("sel");
  };

  window.cancelQuiz = function () {
    state.quiz = null; $("quizPaper").hidden = true; $("quizResult").hidden = true; $("quizSetup").hidden = false;
  };

  window.submitQuiz = async function () {
    const q = state.quiz; if (!q) return;
    const answers = {};
    q.questions.forEach((item) => { answers[item.id] = q.selections[item.id] ?? null; });
    setStatus("quizSubmitStatus", "Đang chấm…");
    try {
      const r = await api(`/quiz/${q.quiz_id}/submit`, { method: "POST", body: { answers } });
      paintQuizResult(r);
      renderQuizHistory();            // bài vừa nộp phải có mặt trong lịch sử ngay
      renderMistakes();               // làm đúng câu nào thì câu đó phải rút khỏi thẻ
    } catch (e) { setStatus("quizSubmitStatus", e.message, "err"); }
  };

  function paintQuizResult(r) {
    const q = state.quiz;
    const review = Object.fromEntries(r.review.map((x) => [x.id, x]));
    $("quizPaper").hidden = true;
    const host = $("quizResult"); host.hidden = false;
    const perTopic = Object.entries(r.per_topic).map(([path, arr]) => {
      const ok = arr.reduce((a, b) => a + b, 0), pct = Math.round(100 * ok / arr.length);
      const ic = pct >= 75 ? "🟢" : pct >= 50 ? "🟡" : "🔴";
      return `<div class="mini-item"><span>${ic} ${esc(path.split(" / ").pop())}</span><span class="r">${ok}/${arr.length} (${pct}%)</span></div>`;
    }).join("");
    host.innerHTML = `
      <div class="score-hero"><div class="big">${r.score}/10</div>
        <div class="sub">${r.n_correct}/${r.n} câu đúng</div></div>
      <div class="panel"><h3 class="panel-title">Kết quả theo chủ đề</h3><div class="mini-list">${perTopic}</div></div>
      <div class="panel"><h3 class="panel-title">Chi tiết từng câu</h3>
        ${q.questions.map((item, i) => {
          const rv = review[item.id] || {}; const sel = rv.selected; const ok = sel === rv.correct;
          return `<div class="q-card">
            <div class="q-head"><span class="q-num">${ok ? "✅" : "❌"} Câu ${i + 1}</span><span class="tag">${esc(item.topic || "")}</span></div>
            <div class="q-text">${mdToHtml(item.content)}</div>
            <div class="q-opts">${item.options.map((o, j) => {
              const cls = j === rv.correct ? "correct" : (j === sel ? "wrong" : "");
              return `<div class="q-opt ${cls}"><span>${j === rv.correct ? "✅" : j === sel ? "❌" : "▫️"}</span><span>${mdToHtml(o)}</span></div>`;
            }).join("")}</div>
            ${rv.explanation ? `<div class="q-explain">${mdToHtml(rv.explanation)}</div>` : ""}
            <div class="q-actions"><button class="btn btn-ghost btn-sm" onclick="flagQuestion(${item.id},this)">🚩 Báo câu hỏi sai</button></div>
          </div>`;
        }).join("")}</div>
      <div class="q-actions"><button class="btn btn-primary" onclick="cancelQuiz()">Làm đề mới</button>
        <button class="btn btn-ghost" onclick="switchTab('phan-tich', null); loadAnalytics()">Xem phân tích</button></div>`;
    host.scrollIntoView({ behavior: "smooth", block: "start" });
    toast(`Điểm: ${r.score}/10`);
  }

  window.flagQuestion = async function (id, btn) {
    try { await api(`/questions/${id}/flag`, { method: "POST" }); btn.textContent = "✅ Đã báo, cảm ơn bạn"; btn.disabled = true; }
    catch (e) { toast(e.message, "err"); }
  };

  /* ------------------------------------------------------------------ PHÂN TÍCH */
  window.loadAnalytics = async function () {
    if (!requireLogin()) return;
    const sid = $("anSubject").value;
    $("anHeatmap").innerHTML = '<div class="skeleton">Đang tính…</div>';
    try {
      const [mastery, prereq, due, kt] = await Promise.all([
        api(`/analytics/mastery?subject_id=${sid}`),
        api(`/learning/prerequisites?subject_id=${sid}`),
        api(`/learning/due?subject_id=${sid}`),
        api("/analytics/kt").catch(() => ({ model: null, prediction: null })),
      ]);
      state.analytics = { mastery, prereq, due, kt };
      const chapters = [...new Set(mastery.map((m) => m.chapter))];
      const sel = $("anChapter");
      sel.innerHTML = '<option value="">Tất cả chương</option>' + chapters.map((c) => `<option>${esc(c)}</option>`).join("");
      const tsel = $("anProgressTopic");
      const done = mastery.filter((m) => m.n > 0);
      tsel.innerHTML = done.length ? done.map((m) => `<option value="${m.topic_id}">${esc(m.topic)}</option>`).join("")
        : '<option value="">(chưa có dữ liệu)</option>';
      renderAnalytics();
      if (done.length) loadProgress();
    } catch (e) { $("anHeatmap").innerHTML = `<div class="empty-note">${esc(e.message)}</div>`; }
  };

  window.renderAnalytics = function () {
    const a = state.analytics; if (!a) return;
    const chap = $("anChapter").value;
    const rows = chap ? a.mastery.filter((m) => m.chapter === chap) : a.mastery;
    const withData = rows.filter((m) => m.n > 0);
    const total = withData.reduce((s, m) => s + m.n, 0);
    const corr = withData.reduce((s, m) => s + m.n_correct, 0);
    $("anStats").innerHTML = [
      ["câu đã làm", total, ""],
      ["tỷ lệ đúng", total ? `${Math.round(100 * corr / total)}%` : "—", ""],
      ["chủ đề yếu", rows.filter((m) => m.level === "Yếu").length, "warn"],
      ["chủ đề tốt", rows.filter((m) => m.level === "Tốt").length, "good"],
    ].map(([l, v, k]) => `<div class="stat ${k}"><b>${esc(v)}</b><span>${l}</span></div>`).join("");

    // heatmap theo chương
    const byChap = {};
    rows.forEach((m) => { (byChap[m.chapter] ||= []).push(m); });
    $("anHeatmap").innerHTML = Object.entries(byChap).map(([c, list]) => `
      <div class="hm-chapter">${esc(c)}</div>
      ${list.map((m) => `<div class="hm-row">
        <span class="hm-name" title="${esc(m.topic)}">${esc(m.topic)}</span>
        <span class="hm-bar"><span class="hm-fill" style="width:${m.n ? m.mastery : 0}%;background:${masteryColor(m.n ? m.mastery : null)}"></span></span>
        <span class="hm-val">${m.n ? `${fmtPct(m.mastery)} · ${m.n} câu` : "chưa làm"}</span>
      </div>`).join("")}`).join("");

    const weak = rows.filter((m) => m.level === "Yếu").sort((x, y) => x.mastery - y.mastery);
    const good = rows.filter((m) => m.level === "Tốt").sort((x, y) => y.mastery - x.mastery);
    const thin = rows.filter((m) => m.n > 0 && m.n < 3);
    $("anWeak").innerHTML = (weak.length ? `<div class="mini-list">${weak.map((m) =>
      `<div class="mini-item"><span>${esc(m.topic)}</span><span class="r">${fmtPct(m.mastery)} · ${m.n_correct}/${m.n}</span></div>`).join("")}</div>`
      : '<div class="empty-note">Chưa phát hiện chủ đề yếu.</div>') +
      (thin.length ? `<p class="hint" style="margin-top:10px">Chưa đủ dữ liệu: ${thin.map((m) => `${esc(m.topic)} (${m.n} câu)`).join(", ")}</p>` : "");
    $("anGood").innerHTML = good.length ? `<div class="mini-list">${good.map((m) =>
      `<div class="mini-item"><span>${esc(m.topic)}</span><span class="r">${fmtPct(m.mastery)} · ${m.n_correct}/${m.n}</span></div>`).join("")}</div>`
      : '<div class="empty-note">Chưa có.</div>';

    $("anPrereq").innerHTML = a.prereq.blocked.length
      ? `<div class="mini-list">${a.prereq.blocked.map((b) =>
          `<div class="mini-item"><span><b>${esc(b.topic)}</b></span><span class="r">cần vững: ${
            (b.weak_needs_detail || b.weak_needs.map((t) => ({ topic: t })))
              .map((d) => esc(d.topic) + (d.other_subject ? ` <i class="hint">(${esc(d.subject)})</i>` : ""))
              .join(", ")}</span></div>`).join("")}</div>`
      : '<div class="empty-note">Không có chủ đề nào bị chặn bởi kiến thức nền.</div>';

    const sch = a.due.schedule || [];
    $("anReview").innerHTML = sch.length ? `<div class="table-scroll"><table class="data-table">
      <thead><tr><th>Chủ đề</th><th>Ôn tới</th><th>Khoảng (ngày)</th><th>Trạng thái</th></tr></thead><tbody>
      ${sch.map((r) => `<tr><td>${esc(r.topic)}</td><td>${dstr(r.due)}</td><td>${r.interval}</td>
        <td>${r.overdue_days >= 0 ? `<span class="lvl lvl-weak">quá hạn ${Math.round(r.overdue_days)} ngày</span>`
          : `<span class="lvl lvl-good">còn ${Math.round(-r.overdue_days)} ngày</span>`}</td></tr>`).join("")}
      </tbody></table></div>` : '<div class="empty-note">Chưa có lịch ôn — hãy làm quiz trước.</div>';

    const kt = a.kt;
    $("anKT").innerHTML = !kt.model
      ? '<div class="empty-note">Chưa có mô hình DKT. Quản trị viên huấn luyện ở trang Quản trị khi đủ dữ liệu.</div>'
      : !kt.prediction ? '<div class="empty-note">Bạn chưa có dữ liệu quiz để mô hình dự đoán.</div>'
      : `<div class="table-scroll"><table class="data-table">
          <thead><tr><th>Chủ đề</th><th>Mastery thống kê</th><th>DKT: P(đúng câu tiếp theo)</th><th>Số câu</th></tr></thead><tbody>
          ${rows.filter((m) => m.n > 0 && kt.prediction[m.topic_id] !== undefined).map((m) =>
            `<tr><td>${esc(m.topic)}</td><td>${fmtPct(m.mastery)}</td><td>${kt.prediction[m.topic_id]}%</td><td>${m.n}</td></tr>`).join("")}
          </tbody></table></div>
          <p class="hint" style="margin-top:10px">Mô hình huấn luyện lúc ${esc(kt.model.trained_at)} trên ${kt.model.n_answers} câu của ${kt.model.n_users} người.
          Dữ liệu còn nhỏ nên chỉ mang tính tham khảo; cùng kiến trúc đạt AUC 0.825 trên ASSISTments 2009.</p>`;
  };

  window.loadProgress = async function () {
    const tid = $("anProgressTopic").value; if (!tid) return;
    const host = $("anProgress");
    try {
      const d = await api(`/analytics/progress?topic_id=${tid}`);
      host.innerHTML = d.length < 2 ? '<div class="empty-note">Cần ít nhất 2 câu để vẽ tiến bộ.</div>' : lineChart(d.map((x) => x.cum), d.map((x) => x.correct));
    } catch (e) { host.innerHTML = `<div class="empty-note">${esc(e.message)}</div>`; }
  };

  function lineChart(values, flags) {
    const w = 560, h = 150, pad = 26;
    const n = values.length;
    const x = (i) => pad + (i * (w - pad * 2)) / Math.max(n - 1, 1);
    const y = (v) => h - pad - ((v / 100) * (h - pad * 2));
    const pts = values.map((v, i) => `${x(i)},${y(v)}`).join(" L ");
    const area = `M ${x(0)},${h - pad} L ${pts} L ${x(n - 1)},${h - pad} Z`;
    const grid = [0, 50, 100].map((g) => `<line class="grid" x1="${pad}" y1="${y(g)}" x2="${w - pad}" y2="${y(g)}"/>
      <text x="2" y="${y(g) + 3}">${g}%</text>`).join("");
    const dots = values.map((v, i) => `<circle cx="${x(i)}" cy="${y(v)}" r="3.4" fill="${flags && flags[i] ? "#5cb85c" : "#d9534f"}"/>`).join("");
    return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="xMidYMid meet" role="img"
      aria-label="Tỷ lệ đúng luỹ kế theo số câu đã làm">
      ${grid}<path class="area" d="${area}"/><path class="line" d="M ${pts}"/>${dots}</svg>
      <p class="hint">Đường đi lên = đang tiến bộ. Mỗi điểm là một câu (xanh đúng, đỏ sai).</p>`;
  }

  /* ------------------------------------------------------------------ SỔ ĐIỂM */
  window.addScore = async function () {
    if (!requireLogin()) return;
    const kind = $("scKind").value;
    const weight = { mieng: 1, "15p": 1, giua_ky: 2, cuoi_ky: 3 }[kind] || 1;
    setStatus("scStatus", "Đang lưu…");
    try {
      await api("/scores", {
        method: "POST",
        body: { subject_id: +$("scSubject").value, kind, value: +$("scValue").value, weight,
                date: $("scDate").value ? new Date($("scDate").value).toISOString() : null },
      });
      setStatus("scStatus", "Đã lưu điểm", "ok");
      renderScores();
    } catch (e) { setStatus("scStatus", e.message, "err"); }
  };

  async function renderScores() {
    if (!state.user) return;
    const KIND = { mieng: "Miệng", "15p": "15 phút", giua_ky: "Giữa kỳ", cuoi_ky: "Cuối kỳ" };
    try {
      const [list, sum] = await Promise.all([api("/scores"), api("/scores/summary")]);
      $("scSummary").innerHTML = sum.length
        ? sum.map((s) => `<div class="stat"><b>${s.avg}</b><span>${esc(s.subject)} · ${s.n} đầu điểm</span></div>`).join("")
        : "";
      $("scList").innerHTML = list.length ? `<h3 class="panel-title">Điểm đã nhập</h3><div class="table-scroll"><table class="data-table">
        <thead><tr><th>Ngày</th><th>Môn</th><th>Loại</th><th>Điểm</th><th>Hệ số</th><th></th></tr></thead><tbody>
        ${list.map((s) => `<tr><td>${dstr(s.date)}</td><td>${esc(s.subject)}</td><td>${esc(KIND[s.kind] || s.kind)}</td>
          <td><b>${s.value}</b></td><td>${s.weight}</td>
          <td><button class="btn btn-ghost btn-sm" onclick="deleteScore(${s.id})">Xoá</button></td></tr>`).join("")}
        </tbody></table></div>` : '<div class="empty-note">Chưa có điểm nào.</div>';
      // biểu đồ xu hướng
      if (list.length >= 2) {
        const vals = [...list].reverse().map((s) => s.value * 10);
        $("scChart").hidden = false;
        $("scChartBody").innerHTML = lineChart(vals, list.map(() => true));
      } else { $("scChart").hidden = true; }
    } catch (e) { $("scList").innerHTML = `<div class="empty-note">${esc(e.message)}</div>`; }
  }

  window.deleteScore = async function (id) {
    try { await api(`/scores/${id}`, { method: "DELETE" }); renderScores(); toast("Đã xoá"); }
    catch (e) { toast(e.message, "err"); }
  };

  /* ------------------------------------------------------------------ LỘ TRÌNH */
  const TOOL_VI = {
    get_student_overview: "Xem tổng quan học tập", get_topic_mastery: "Lấy mastery từng chủ đề",
    get_recent_mistakes: "Xem các câu làm sai gần đây", get_review_and_prerequisites: "Xem lịch ôn & kiến thức nền",
    search_documents: "Tra cứu sách giáo khoa", save_study_plan: "Lưu kế hoạch",
  };

  window.createPlan = async function () {
    if (!requireLogin()) return;
    const mode = (document.querySelector('input[name=planmode]:checked') || {}).value || "quick";
    const est = { quick: "khoảng 30 giây", agent: "1–2 phút", multi: "3–6 phút" }[mode];
    setStatus("plStatus", `Đang chạy chế độ ${mode} (${est})…`);
    $("plTrace").hidden = true; $("plTrace").innerHTML = "";
    try {
      const r = await api("/plan2", {
        method: "POST",
        body: { subject_id: +$("plSubject").value || null, goal: $("plGoal").value,
                days: +$("plDays").value, hours_per_day: +$("plHours").value, mode },
      });
      setStatus("plStatus", "Xong", "ok");
      if (r.trace && r.trace.length) {
        $("plTrace").hidden = false;
        $("plTrace").innerHTML = r.trace.map((t) =>
          `<div class="tl">🔧 <b>${esc(TOOL_VI[t.tool] || t.tool)}</b> <code>${esc(t.tool)}()</code>${t.agent ? ` · ${esc(t.agent)}` : ""}</div>`).join("");
      }
      if (r.critique) {
        toast(`Agent phản biện chấm ${r.critique.score}/10${r.violations && r.violations.length ? ` · còn ${r.violations.length} vi phạm` : " · validator ✅"}`);
      }
      state.plan = r.plan; paintPlan();
    } catch (e) { setStatus("plStatus", e.message, "err"); }
  };

  async function loadPlan() {
    if (!state.user) return;
    try { state.plan = await api("/plan2/latest"); paintPlan(); }
    catch { $("plBody").innerHTML = '<div class="empty-note">Chưa có lộ trình.</div>'; }
  }

  async function paintPlan() {
    const p = state.plan;
    if (!p) { $("plBody").innerHTML = '<div class="empty-note">Chưa có lộ trình. Hãy bấm “Phân tích và lập kế hoạch”.</div>'; return; }
    const done = p.items.filter((i) => i.done).length;
    try {
      const o = await api(`/plan2/${p.id}/outcome`);
      $("plOutcome").innerHTML = [
        ["việc hoàn thành", `${o.done}/${o.n_items}`, ""],
        ["Δ mastery chủ đề nhắm tới", o.avg_delta === null ? "—" : `${o.avg_delta > 0 ? "+" : ""}${o.avg_delta}`, o.avg_delta > 0 ? "good" : ""],
        ["tuổi kế hoạch", `${Math.round(o.age_days)} ngày`, ""],
      ].map(([l, v, k]) => `<div class="stat ${k}"><b>${esc(v)}</b><span>${l}</span></div>`).join("");
    } catch { $("plOutcome").innerHTML = ""; }

    const byDay = {};
    p.items.forEach((i) => { (byDay[i.day] ||= []).push(i); });
    $("plBody").innerHTML = `
      <div class="panel"><h3 class="panel-title">Nhận xét của AI</h3>
        <div style="font-size:.9rem;line-height:1.65">${mdToHtml(p.summary)}</div>
        <details style="margin-top:12px"><summary class="cite-toggle">Số liệu AI đã dùng</summary>
          <pre style="white-space:pre-wrap;font-size:.8rem;color:var(--text-sub);margin-top:8px">${esc(p.evidence || "")}</pre></details>
      </div>
      <div class="panel"><h3 class="panel-title">Kế hoạch ${p.days} ngày</h3>
        <div class="progress-track"><div class="progress-fill" style="width:${p.items.length ? (100 * done / p.items.length) : 0}%"></div></div>
        <p class="hint">Hoàn thành ${done}/${p.items.length} việc</p>
        ${Object.keys(byDay).sort((a, b) => a - b).map((d) => `
          <div class="plan-day"><h4>Ngày ${d}</h4>
          ${byDay[d].map((i) => `<div class="plan-item ${i.done ? "done" : ""}">
            <input type="checkbox" ${i.done ? "checked" : ""} onchange="togglePlanItem(${i.id}, this.checked)">
            <div class="pi-body">
              <div class="pi-title">${({ study: "📖", quiz: "📝", review: "🔁" }[i.kind] || "•")} ${esc(i.title)}</div>
              ${i.topic ? `<div class="pi-topic">${esc(i.topic)}</div>` : ""}
              ${i.detail ? `<div class="pi-detail">${esc(i.detail)}</div>` : ""}
            </div>
            ${i.kind === "quiz" && i.topic_id && !i.done ? `<button class="btn btn-ghost btn-sm" onclick="quizFromPlan(${i.topic_id})">Làm ngay</button>` : ""}
          </div>`).join("")}</div>`).join("")}
      </div>`;
  }

  window.togglePlanItem = async function (id, done) {
    try { await api(`/plan/items/${id}?done=${done}`, { method: "PATCH" }); loadPlan(); }
    catch (e) { toast(e.message, "err"); }
  };

  window.quizFromPlan = function (topicId) {
    switchTab("quizz", null);
    const chaps = chaptersOf($("quizSubject").value);
    const chap = chaps.find((c) => c.topics.some((t) => t.id === topicId));
    if (chap) { $("quizChapter").value = chap.id; renderQuizTopics(); }
    document.querySelectorAll("#quizTopics .chip").forEach((c) => c.classList.toggle("on", +c.dataset.id === topicId));
    toast("Đã chọn sẵn chủ đề — bấm Tạo đề");
  };

  /* ------------------------------------------------------------------ GIA SƯ AI */
  const TUTOR_SUGGEST = [
    "Em đang yếu nhất chỗ nào? Vì sao?",
    "Em hay sai kiểu gì ở phần cực trị?",
    "Tối nay có 45 phút, em nên học gì?",
    "So với tuần trước em có tiến bộ không?",
  ];

  function paintTutorSuggest() {
    const host = $("tutorSuggest"); if (!host || host.dataset.done) return;
    host.innerHTML = TUTOR_SUGGEST.map((q) => `<button onclick="askTutor('${q.replace(/'/g, "\\'")}')">${esc(q)}</button>`).join("");
    host.dataset.done = "1";
  }

  window.askTutor = function (q) { $("tutorInput").value = q; window.sendTutor(); };

  window.sendTutor = async function () {
    if (!requireLogin()) return;
    const input = $("tutorInput"); const text = (input.value || "").trim();
    if (!text) return;
    input.value = "";
    const box = $("tutorBox");
    const add = (role, html) => { const d = document.createElement("div"); d.className = `bubble ${role}`; d.innerHTML = html; box.appendChild(d); box.scrollTop = box.scrollHeight; return d; };
    add("user", esc(text));
    const think = add("assistant thinking", '<div class="typing-dots"><span></span><span></span><span></span></div>');
    $("tutorTools").innerHTML = '<div class="tl">đang tra cứu…</div>';
    try {
      const r = await api("/agent", { method: "POST", body: { message: text, subject_id: +($("anSubject") || {}).value || null } });
      think.remove();
      add("assistant", mdToHtml(r.answer));
      $("tutorTools").innerHTML = (r.trace || []).map((t) =>
        `<div class="tl">🔧 <b>${esc(TOOL_VI[t.tool] || t.tool)}</b><br><code>${esc(t.tool)}(${esc(JSON.stringify(t.args || {}))})</code></div>`).join("")
        || '<div class="tl">(không gọi công cụ nào)</div>';
    } catch (e) {
      think.remove(); add("assistant", `<span style="color:#d9534f">${esc(e.message)}</span>`);
      $("tutorTools").innerHTML = "";
    }
  };

  /* ------------------------------------------------------------------ CHẤM BÀI */
  window.previewWork = function () {
    const f = $("grFile").files[0]; const host = $("grPreview");
    if (!f) { host.innerHTML = ""; return; }
    const url = URL.createObjectURL(f);
    host.innerHTML = `<img src="${url}" alt="Ảnh bài làm">`;
  };

  window.gradeWork = async function () {
    if (!requireLogin()) return;
    const f = $("grFile").files[0]; const text = $("grText").value.trim();
    if (!f && !text) { setStatus("grStatus", "Cần ảnh bài làm hoặc lời giải dạng chữ", "err"); return; }
    const fd = new FormData();
    fd.append("subject_id", $("grSubject").value);
    if ($("grChapter").value) fd.append("chapter_id", $("grChapter").value);
    fd.append("problem", $("grProblem").value);
    fd.append("text", text);
    if (f) fd.append("file", f);
    setStatus("grStatus", "AI đang đọc và chấm…");
    try {
      const r = await api("/grade", { method: "POST", form: fd });
      state.gradeResult = r;
      setStatus("grStatus", "", "ok");
      paintGrade(r);
    } catch (e) { setStatus("grStatus", e.message, "err"); }
  };

  function paintGrade(r) {
    const host = $("grResult");
    host.innerHTML = `
      <div class="stat-row">
        <div class="stat"><b>${r.score}/10</b><span>điểm</span></div>
        <div class="stat"><b style="font-size:1rem">${esc(r.error_type)}</b><span>loại lỗi</span></div>
        <div class="stat"><b>${r.first_error_step > 0 ? "Bước " + r.first_error_step : "—"}</b><span>bước sai đầu tiên</span></div>
      </div>
      <p class="hint"><b>Đề:</b> ${esc(r.problem)}</p>
      ${r.steps.map((s, i) => `<div class="step-row ${s.correct ? "" : "bad"} ${i + 1 === r.first_error_step ? "first-bad" : ""}">
          <span class="step-ic">${s.correct ? "✅" : "❌"}</span>
          <span class="step-body"><b>Bước ${i + 1}. ${esc(s.step)}</b><span>${esc(s.comment)}</span></span></div>`).join("")}
      <div class="q-explain" style="margin-top:12px"><b>Nhận xét:</b> ${esc(r.feedback)}</div>
      <div class="q-explain" style="border-left-color:#1f9d55"><b>Cách làm đúng:</b> ${mdToHtml(r.correct_solution_hint)}</div>
      <div class="q-actions"><button class="btn btn-primary" onclick="saveGrade()">💾 Lưu vào hồ sơ học tập</button></div>`;
  }

  window.saveGrade = async function () {
    if (!state.gradeResult) return;
    try {
      await api("/grade/save", { method: "POST", body: { subject_id: +$("grSubject").value, result: state.gradeResult } });
      toast("Đã lưu — sẽ tính vào mastery và lịch ôn");
      state.gradeResult = null;
      $("grResult").innerHTML = '<div class="empty-note">Đã lưu. Chấm bài tiếp theo?</div>';
    } catch (e) { toast(e.message, "err"); }
  };

  /* ------------------------------------------------------------------ LỚP HỌC */
  async function renderClasses() {
    if (!state.user) return;
    try {
      const d = await api("/classes");
      $("clsTeaching").innerHTML = d.teaching.length ? `<div class="mini-list">${d.teaching.map((c) =>
        `<div class="mini-item"><span><b>${esc(c.name)}</b> · mã <code>${esc(c.code)}</code></span>
         <span class="r">${c.members} học sinh · ${c.assignments} đề
         <button class="btn btn-ghost btn-sm" onclick="openClass(${c.id})">Xem</button></span></div>`).join("")}</div>`
        : '<div class="empty-note">Chưa có lớp nào. Tạo lớp và gửi mã cho học sinh.</div>';
      $("clsJoined").innerHTML = d.joined.length ? `<div class="mini-list" style="margin-top:10px">${d.joined.map((c) =>
        `<div class="mini-item"><span>${esc(c.name)}</span><span class="r">mã ${esc(c.code)} · ${c.assignments} đề</span></div>`).join("")}</div>` : "";
      const asg = await api("/assignments");
      $("clsAssignments").innerHTML = asg.length ? `<div class="mini-list">${asg.map((a) =>
        `<div class="mini-item"><span>${esc(a.title)} · ${esc(a.class)} · ${a.n_questions} câu</span>
         <span class="r">${a.done ? `✅ ${a.score}/10` : (a.due ? `hạn ${dstr(a.due)} ` : "") +
           `<button class="btn btn-primary btn-sm" onclick="startAssignment(${a.id})">Làm</button>`}</span></div>`).join("")}</div>`
        : '<div class="empty-note">Chưa có đề nào được giao.</div>';
    } catch (e) { $("clsJoined").innerHTML = `<div class="empty-note">${esc(e.message)}</div>`; }
  }

  window.createClass = async function () {
    if (!requireLogin()) return;
    try {
      const r = await api("/classes", { method: "POST", body: { name: $("clsName").value, subject_id: +$("clsSubject").value || null } });
      toast(`Đã tạo lớp ${r.name} — mã ${r.code}`);
      $("clsName").value = ""; renderClasses();
    } catch (e) { toast(e.message, "err"); }
  };

  window.joinClass = async function () {
    if (!requireLogin()) return;
    setStatus("clsJoinStatus", "Đang kiểm tra mã…");
    try {
      const r = await api("/classes/join", { method: "POST", body: { code: $("clsCode").value } });
      setStatus("clsJoinStatus", r.note || `Đã vào lớp ${r.name}`, "ok");
      renderClasses();
    } catch (e) { setStatus("clsJoinStatus", e.message, "err"); }
  };

  window.openClass = async function (id) {
    const host = $("clsDetail"); host.innerHTML = '<div class="skeleton">Đang tải…</div>';
    try {
      const d = await api(`/classes/${id}/overview`);
      state.classDetail = { id, ...d };
      const hm = d.heatmap;
      host.innerHTML = `
        <div class="panel"><h3 class="panel-title">Tổng quan học sinh</h3>
          <div class="table-scroll"><table class="data-table">
            <thead><tr><th>Học sinh</th><th>Câu đã làm</th><th>Tỷ lệ đúng</th><th>Chủ đề yếu</th><th>Yếu nhất</th></tr></thead>
            <tbody>${d.students.map((s) => `<tr><td>${esc(tenDep(s["Học sinh"]))}</td><td>${s["Câu đã làm"]}</td>
              <td>${s["Tỷ lệ đúng (%)"] === null ? "—" : s["Tỷ lệ đúng (%)"] + "%"}</td>
              <td>${s["Chủ đề yếu"]}</td><td>${esc(s["Yếu nhất"])}</td></tr>`).join("")}</tbody></table></div></div>
        ${hm ? `<div class="panel"><h3 class="panel-title">Bản đồ năng lực cả lớp</h3><div class="class-hm"><table>
            <tr><th></th>${hm.topics.map((t) => `<th title="${esc(t)}">${esc(t.slice(0, 14))}</th>`).join("")}</tr>
            ${hm.students.map((s, i) => `<tr><th>${esc(tenDep(s))}</th>${hm.values[i].map((v) =>
              `<td class="cell" style="background:${v === null ? "var(--input-bg)" : masteryColor(v)};color:${v === null ? "var(--text-sub)" : "#fff"}">${v === null ? "" : Math.round(v)}</td>`).join("")}</tr>`).join("")}
          </table></div></div>` : ""}
        ${d.weakest.length ? `<div class="panel"><h3 class="panel-title">Chủ đề cả lớp yếu nhất</h3><div class="mini-list">${
          d.weakest.map((w) => `<div class="mini-item"><span>${esc(w["Chủ đề"])}</span><span class="r">${Math.round(w["Mastery TB (%)"] ?? w[0] ?? 0)}%</span></div>`).join("")}</div></div>` : ""}
        <div class="panel"><h3 class="panel-title">Giao đề mới</h3>
          <div class="form-grid">
            <label class="field"><span>Tên đề</span><input id="asgTitle" class="ctl" placeholder="Kiểm tra 15 phút — Chương 1"></label>
            <label class="field"><span>Chương</span><select id="asgChapter" class="ctl"></select></label>
            <label class="field"><span>Độ khó</span><select id="asgDiff" class="ctl"><option value="easy">Dễ</option><option value="medium" selected>Trung bình</option><option value="hard">Khó</option></select></label>
            <label class="field"><span>Số câu</span><input id="asgN" class="ctl" type="number" min="3" max="60" value="10"></label>
          </div>
          <button class="btn btn-primary" onclick="createAssignment(${id})">Tạo và giao đề</button>
          <div id="asgStatus" class="status-line"></div></div>`;
      const sel = $("asgChapter");
      const subj = state.subjects[0];
      sel.innerHTML = (subj ? subj.chapters : []).map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
    } catch (e) { host.innerHTML = `<div class="empty-note">${esc(e.message)}</div>`; }
  };

  window.createAssignment = async function (classId) {
    const chapId = +$("asgChapter").value;
    const chap = state.subjects.flatMap((s) => s.chapters).find((c) => c.id === chapId);
    if (!chap) return;
    setStatus("asgStatus", "AI đang soạn đề…");
    try {
      await api(`/classes/${classId}/assignments`, {
        method: "POST",
        body: { title: $("asgTitle").value || "Bài kiểm tra", topic_ids: chap.topics.map((t) => t.id),
                difficulty: $("asgDiff").value,
                n: Math.min(QUIZ_N_MAX, Math.max(QUIZ_N_MIN, +$("asgN").value || 10)) },
      });
      setStatus("asgStatus", "Đã giao đề", "ok"); toast("Đã giao đề cho lớp");
      renderClasses();
    } catch (e) { setStatus("asgStatus", e.message, "err"); }
  };

  window.startAssignment = async function (id) {
    try {
      const r = await api(`/assignments/${id}/start`, { method: "POST" });
      state.assignmentQuiz = { assignment_id: id, quiz_id: r.quiz_id, questions: r.questions, selections: {} };
      const host = $("clsPaper"); host.hidden = false;
      host.innerHTML = `<div class="page-head"><h2>📝 Bài được giao</h2></div>` +
        r.questions.map((item, i) => `<div class="q-card">
          <div class="q-head"><span class="q-num">Câu ${i + 1}</span><span class="tag">${esc(item.topic || "")}</span></div>
          <div class="q-text">${mdToHtml(item.content)}</div>
          <div class="q-opts">${item.options.map((o, j) => `<label class="q-opt">
            <input type="radio" name="a${item.id}" onchange="pickAssignmentAnswer(${item.id},${j},this)"><span>${mdToHtml(o)}</span></label>`).join("")}</div>
        </div>`).join("") +
        `<div class="q-actions"><button class="btn btn-primary" onclick="submitAssignment()">Nộp bài</button>
          <span id="asgSubmitStatus" class="status-line"></span></div>`;
      host.scrollIntoView({ behavior: "smooth" });
    } catch (e) { toast(e.message, "err"); }
  };

  window.pickAssignmentAnswer = function (qid, idx, el) {
    state.assignmentQuiz.selections[qid] = idx;
    const card = el.closest(".q-card");
    card.querySelectorAll(".q-opt").forEach((o) => o.classList.remove("sel"));
    el.closest(".q-opt").classList.add("sel");
  };

  window.submitAssignment = async function () {
    const a = state.assignmentQuiz; if (!a) return;
    const answers = {};
    a.questions.forEach((q) => { answers[q.id] = a.selections[q.id] ?? null; });
    setStatus("asgSubmitStatus", "Đang nộp…");
    try {
      const r = await api(`/assignments/${a.assignment_id}/submit`, { method: "POST", body: { quiz_id: a.quiz_id, answers } });
      $("clsPaper").hidden = true; state.assignmentQuiz = null;
      toast(`Điểm: ${r.score}/10 (${r.n_correct}/${r.n} đúng)`);
      // Trước hạn nộp thì máy chủ giữ lại đáp án, nói rõ cho học sinh khỏi tưởng lỗi.
      if (r.dap_an_sau_han && r.thong_bao) toast(r.thong_bao);
      renderClasses();
      if (window.renderQuizHistory) renderQuizHistory();
    } catch (e) { setStatus("asgSubmitStatus", e.message, "err"); }
  };

  /* ------------------------------------------------------------------ HỎI BÀI / GÓP Ý */
  window.handleWtfSubmit = async function (e) {
    if (e && e.preventDefault) e.preventDefault();
    if (!requireLogin()) return false;
    const content = ($("fb-question") || {}).value || "";
    try {
      const r = await api("/feedback", {
        method: "POST",
        body: { name: ($("fb-name") || {}).value || "", email: ($("fb-email") || {}).value || "",
                subject: ($("fb-subject") || {}).value || "", grade: ($("fb-grade") || {}).value || "", content },
      });
      toast(r.message);
      if ($("fb-question")) $("fb-question").value = "";
    } catch (err) { toast(err.message, "err"); }
    return false;
  };

  /* ------------------------------------------------------------------ QUẢN TRỊ */
  let adminCurrent = "users";
  window.adminTab = function (name, btn) {
    adminCurrent = name;
    document.querySelectorAll("#adminTabs .tab-btn").forEach((b) => b.classList.remove("active"));
    if (btn) btn.classList.add("active");
    renderAdmin();
  };

  async function renderAdmin() {
    if (!state.user || state.user.role !== "admin") { $("adminBody").innerHTML = '<div class="empty-note">Chỉ quản trị viên.</div>'; return; }
    const host = $("adminBody"); host.innerHTML = '<div class="skeleton">Đang tải…</div>';
    try {
      if (adminCurrent === "users") {
        const us = await api("/admin/users");
        host.innerHTML = `<div class="panel"><div class="table-scroll"><table class="data-table">
          <thead><tr><th>Tên</th><th>Vai trò</th><th>Quiz</th><th>Câu</th><th>Chat</th><th>Tạo lúc</th><th>Thao tác</th></tr></thead><tbody>
          ${us.map((u) => `<tr><td>${esc(tenDep(u.username))}</td>
            <td><span class="tag ${u.role === "admin" ? "tag-admin" : u.role === "teacher" ? "tag-teacher" : ""}">${esc(u.role)}</span></td>
            <td>${u.quizzes}</td><td>${u.answers}</td><td>${u.chats}</td><td>${dstr(u.created_at)}</td>
            <td style="white-space:nowrap">
              <select class="ctl" style="width:auto;display:inline-block;padding:4px 8px;font-size:.78rem" onchange="setRole(${u.id}, this.value)">
                ${["user", "teacher", "admin"].map((r) => `<option ${u.role === r ? "selected" : ""}>${r}</option>`).join("")}
              </select>
              <button class="btn btn-ghost btn-sm" onclick="resetUserPw(${u.id})">Reset MK</button></td></tr>`).join("")}
          </tbody></table></div></div>`;
      } else if (adminCurrent === "docs") {
        const ds = await api("/admin/documents");
        host.innerHTML = `<div class="panel"><div class="table-scroll"><table class="data-table">
          <thead><tr><th>Môn</th><th>Chương</th><th>Tệp</th><th>Đoạn</th><th>Trạng thái</th><th>Người tải</th></tr></thead><tbody>
          ${ds.map((d) => `<tr><td>${esc(d.subject)}</td><td>${esc((d.chapter || "—").split(":")[0])}</td><td>${esc(d.filename)}</td>
            <td>${d.n_chunks}</td><td>${d.status === "ready" ? "✅" : "❌"} ${esc(d.error || "")}</td><td>${esc(tenDep(d.by))}</td></tr>`).join("")}
          </tbody></table></div></div>`;
      } else if (adminCurrent === "stats") {
        const s = await api("/admin/stats");
        const maxN = Math.max(...s.per_day.map((d) => d.n), 1);
        host.innerHTML = `<div class="stat-row">
            <div class="stat"><b>${s.users}</b><span>người dùng</span></div>
            <div class="stat"><b>${s.attempts}</b><span>bài quiz</span></div>
            <div class="stat"><b>${s.answers}</b><span>câu đã làm</span></div>
            <div class="stat warn"><b>${s.flagged}/${s.questions}</b><span>câu bị 🚩</span></div>
            <div class="stat"><b>${s.chats}</b><span>lượt chat</span></div>
            <div class="stat"><b>${s.documents}</b><span>tài liệu</span></div>
          </div>
          <div class="panel"><h3 class="panel-title">Hoạt động theo ngày</h3>
            <div style="display:flex;gap:4px;align-items:flex-end;height:120px">${s.per_day.map((d) =>
              `<div title="${d.date}: ${d.n} câu" style="flex:1;background:var(--btn-primary-bg);border-radius:4px 4px 0 0;height:${100 * d.n / maxN}%"></div>`).join("")}</div>
            <p class="hint" style="margin-top:8px">${s.per_day.length} ngày có hoạt động</p></div>`;
      } else if (adminCurrent === "ml") {
        const m = await api("/admin/ml");
        const nhan = m.model && m.model.loai_auc === "holdout_auc" ? "AUC trên nhóm giữ lại" : "AUC khớp";
        const loc = m.model && m.model.loc_du_lieu;
        host.innerHTML = `<div class="panel">
          <h3 class="panel-title">Deep Knowledge Tracing</h3>
          ${m.model ? `<p>Mô hình hiện tại: huấn luyện ${esc(m.model.trained_at)} · ${m.model.n_answers} câu · ${m.model.n_users} người · ${nhan} ${m.model.fit_auc.toFixed(3)}</p>`
            : "<p>Chưa có mô hình.</p>"}
          ${m.model && m.model.note ? `<p class="hint">${esc(m.model.note)}</p>` : ""}
          ${loc ? `<p class="hint">Lọc chống đầu độc: ${loc.cau_tho} câu thô → ${loc.cau_vao} câu vào huấn luyện ·
             loại ${loc.nguoi_bi_loai} người · trần ${loc.tran_moi_nguoi} câu/người</p>
             ${Object.keys(loc.ly_do_loai || {}).length ? `<ul class="hint" style="margin:4px 0 0 18px">${
               Object.entries(loc.ly_do_loai).map(([u, r]) => `<li>user ${esc(u)}: ${esc(r)}</li>`).join("")}</ul>` : ""}` : ""}
          <p class="hint">Hệ thống có ${m.n_answers} câu trả lời (cần ≥ ${m.min_answers}). Nên huấn luyện lại mỗi tuần.</p>
          <button class="btn btn-primary" onclick="trainML(this)">🔁 Huấn luyện lại</button>
          <div id="mlStatus" class="status-line"></div></div>`;
      } else if (adminCurrent === "agent") {
        const [runs, lessons] = await Promise.all([api("/admin/agent/runs"), api("/admin/agent/lessons")]);
        const pass = runs.length ? Math.round(100 * runs.filter((r) => !r.violations.length).length / runs.length) : 0;
        host.innerHTML = `<div class="stat-row">
            <div class="stat"><b>${runs.length}</b><span>lần chạy agent</span></div>
            <div class="stat good"><b>${pass}%</b><span>kế hoạch không vi phạm</span></div>
            <div class="stat"><b>${lessons.filter((l) => l.active).length}</b><span>bài học đang áp dụng</span></div>
          </div>
          <div class="panel"><h3 class="panel-title">Nhật ký chạy</h3><div class="table-scroll"><table class="data-table">
            <thead><tr><th>Lúc</th><th>Người dùng</th><th>Chế độ</th><th>Tool</th><th>Giây</th><th>Phản biện</th><th>Vi phạm</th></tr></thead><tbody>
            ${runs.map((r) => `<tr><td>${dstr(r.at)}</td><td>${esc(tenDep(r.user))}</td><td>${esc(r.mode)}</td><td>${r.tools}</td>
              <td>${r.seconds}</td><td>${r.critic ?? "—"}</td><td>${r.violations.length}</td></tr>`).join("")}
            </tbody></table></div></div>
          <div class="panel"><h3 class="panel-title">Bài học agent tự rút ra</h3>
            ${lessons.length ? lessons.map((l) => `<div class="mini-item" style="align-items:flex-start">
              <span>${l.active ? "✅" : "⏸️"} <b>${esc(l.lesson)}</b><br><span class="hint">${esc(l.evidence)}</span></span>
              <span class="r"><button class="btn btn-ghost btn-sm" onclick="toggleLesson(${l.id})">${l.active ? "Tắt" : "Bật"}</button></span></div>`).join("")
              : '<div class="empty-note">Chưa có bài học nào.</div>'}
            <button class="btn btn-primary" style="margin-top:12px" onclick="runReflect(this)">🪞 Chạy agent phản tư</button>
            <div id="reflectStatus" class="status-line"></div></div>`;
      } else if (adminCurrent === "feedback") {
        const fs = await api("/admin/feedback");
        host.innerHTML = `<div class="panel">${fs.length ? fs.map((f) => `<div class="mini-item" style="align-items:flex-start">
            <span><b>${esc(tenDep(f.name || f.user)) || "Ẩn danh"}</b> ${f.subject ? `· ${esc(f.subject)}` : ""}<br>
              <span class="hint">${esc(f.content)}</span></span>
            <span class="r">${dstr(f.at)}</span></div>`).join("") : '<div class="empty-note">Chưa có góp ý nào.</div>'}</div>`;
      }
    } catch (e) { host.innerHTML = `<div class="empty-note">${esc(e.message)}</div>`; }
  }

  window.setRole = async function (id, role) {
    try { await api(`/admin/users/${id}/role`, { method: "PATCH", body: { role } }); toast("Đã đổi vai trò"); }
    catch (e) { toast(e.message, "err"); }
  };
  window.resetUserPw = async function (id) {
    if (!confirm("Xoá mật khẩu của người dùng này? Họ sẽ đặt mật khẩu mới ở lần đăng nhập tới.")) return;
    try { const r = await api(`/admin/users/${id}/reset-password`, { method: "POST" }); toast(r.message); }
    catch (e) { toast(e.message, "err"); }
  };
  window.trainML = async function (btn) {
    btn.disabled = true; setStatus("mlStatus", "Đang huấn luyện…");
    try { const m = await api("/admin/ml/train", { method: "POST" }); setStatus("mlStatus", `Xong · AUC khớp ${m.fit_auc.toFixed(3)}`, "ok"); }
    catch (e) { setStatus("mlStatus", e.message, "err"); }
    btn.disabled = false;
  };
  window.toggleLesson = async function (id) {
    try { await api(`/admin/agent/lessons/${id}`, { method: "PATCH" }); renderAdmin(); }
    catch (e) { toast(e.message, "err"); }
  };
  window.runReflect = async function (btn) {
    btn.disabled = true; setStatus("reflectStatus", "Agent đang nhìn lại các kế hoạch cũ…");
    try { const r = await api("/admin/agent/reflect", { method: "POST", body: {} }); setStatus("reflectStatus", `Rút được ${r.lessons.length} bài học mới`, "ok"); renderAdmin(); }
    catch (e) { setStatus("reflectStatus", e.message, "err"); }
    btn.disabled = false;
  };

  /* ------------------------------------------------------------------ chuyển view */
  const origSwitchTab = window.switchTab;
  window.switchTab = function (viewId, btn) {
    if (typeof origSwitchTab === "function") origSwitchTab(viewId, btn);
    const needAuth = ["tai-lieu", "chat", "quizz", "phan-tich", "diem-so", "lo-trinh", "gia-su", "cham-bai", "lop-hoc", "quan-tri"];
    if (needAuth.includes(viewId) && !state.user) { requireLogin(); return; }
    loadSubjects().then(() => {
      switch (viewId) {
        case "home": renderHomeStats(); break;
        case "tai-lieu": renderLibrary(); break;
        case "chat": loadChatHistory(); break;
        case "quizz": renderQuizTopics(); renderQuizHistory(); renderMistakes(); break;
        case "phan-tich": if (!state.analytics) loadAnalytics(); break;
        case "diem-so": renderScores(); break;
        case "lo-trinh": loadPlan(); break;
        case "gia-su": paintTutorSuggest(); break;
        case "lop-hoc": renderClasses(); break;
        case "quan-tri": renderAdmin(); break;
        default: break;
      }
    });
  };

  // môn học -> mở chat đúng môn
  const origOpenChat = window.openChatForSubject;
  window.openChatForSubject = function (name, ...rest) {
    const s = state.subjects.find((x) => x.name.toLowerCase().includes(String(name).toLowerCase().split(" ")[0]));
    window.__chatSubjectId = s ? s.id : null;
    const oMon = $("chatSubject");
    if (oMon) oMon.value = s ? String(s.id) : "";
    const badge = $("chatSubjectBadge");
    if (badge) badge.textContent = `Môn: ${s ? s.name : name}`;
    if (typeof origOpenChat === "function") return origOpenChat(name, ...rest);
    switchTab("chat", null);
  };

  /* ------------------------------------------------------------------ khởi động */
  document.addEventListener("DOMContentLoaded", () => {
    const d = $("scDate"); if (d && !d.value) d.value = new Date().toISOString().slice(0, 10);
    const lf = $("formLogin"); if (lf) lf.onsubmit = window.handleLoginSubmit;
    const rf = $("formRegister"); if (rf) rf.onsubmit = window.handleRegisterSubmit;
    document.querySelectorAll(".wtf-card-form form, form.wtf-form").forEach((f) => { f.onsubmit = window.handleWtfSubmit; });
    boot();
  });
  // cho lop jobs.js dung lai (gia su / lo trinh chay nen)
  Object.assign(window, { state, toast, mdToHtml, paintPlan, TOOL_VI, tenDep });

  if (document.readyState !== "loading") {
    const d = $("scDate"); if (d && !d.value) d.value = new Date().toISOString().slice(0, 10);
    boot();
  }
})();
