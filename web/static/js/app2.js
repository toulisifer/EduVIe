/* ===========================================================================
   VuongEdu — lớp hoàn thiện: nối "Môn học" với dữ liệu thật, lọc RAG theo môn,
   dọn phần Hỏi bài, và đưa số liệu trang chủ xuống dưới hero.
   Nạp sau app.js.
   =========================================================================== */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ---------------------------------------------------------------- 1. MÔN HỌC
     UI gốc liệt kê 13 môn × 12 lớp (dữ liệu tĩnh). Hệ thống chỉ có tài liệu cho
     một số môn — đánh dấu rõ môn nào đã có sách, môn nào chưa, và mở đúng môn khi bấm. */
  let ready = [];        // [{id, name, grade, chapters, n_docs, n_topics, learned, weak, mastery}]
  let docsBySubject = {};

  /** Rút số lớp từ tên môn trong CSDL: "Toán 12" -> 12; không có số -> null (dùng cho mọi lớp). */
  function gradeOf(name) {
    const m = String(name).match(/\b(1[0-2]|[1-9])\b\s*$/);
    return m ? Number(m[1]) : null;
  }

  let loadedFor = null;     // token đã dùng để nạp dữ liệu; đổi tài khoản thì nạp lại

  /** Nạp lại khi: chưa có dữ liệu, hoặc đăng nhập/đăng xuất làm token đổi. */
  async function ensureData(force) {
    const t = (() => { try { return localStorage.getItem("vuongedu_token") || ""; } catch { return ""; } })();
    if (!force && ready.length && loadedFor === t) return;
    await loadReadySubjects();
    loadedFor = t;
  }

  async function loadReadySubjects() {
    try {
      const [subs, docs, mastery] = await Promise.all([
        fetch("/subjects").then((r) => r.json()),
        fetch("/documents", { headers: authHeader() }).then((r) => (r.ok ? r.json() : [])),
        fetch("/analytics/mastery", { headers: authHeader() }).then((r) => (r.ok ? r.json() : [])),
      ]);
      docsBySubject = {};
      docs.forEach((d) => { docsBySubject[d.subject_id] = (docsBySubject[d.subject_id] || 0) + 1; });
      const stat = {};
      mastery.forEach((m) => {
        const k = m.subject_id;
        const st = (stat[k] ||= { n_topics: 0, learned: 0, weak: 0, sum: 0 });
        st.n_topics += 1;
        if (m.n > 0) { st.learned += 1; st.sum += (m.mastery || 0); }
        if (m.level === "Yếu") st.weak += 1;
      });
      ready = subs.map((s) => {
        const st = stat[s.id] || { n_topics: (s.chapters || []).reduce((a, c) => a + c.topics.length, 0), learned: 0, weak: 0, sum: 0 };
        return { ...s, grade: gradeOf(s.name), n_docs: docsBySubject[s.id] || 0,
                 n_topics: st.n_topics, learned: st.learned, weak: st.weak,
                 mastery: st.learned ? Math.round(st.sum / st.learned) : null };
      });
    } catch { ready = []; }
  }

  function authHeader() {
    try { const t = localStorage.getItem("vuongedu_token"); return t ? { Authorization: "Bearer " + t } : {}; }
    catch { return {}; }
  }

  /** Ghép tên môn trong UI ("Vật lí") với môn thật trong CSDL ("Vật lí 12") — PHẢI đúng lớp.
      Môn trong CSDL không ghi lớp thì coi là dùng chung cho mọi lớp. */
  /** Chuẩn hoá tên môn để so khớp giữa danh sách tĩnh của giao diện và tên trong CSDL. */
  const norm = (s) => String(s).toLowerCase().replace(/\s+/g, " ").trim()
    // bỏ số lớp trước, rồi mới bỏ đuôi " học" — để "Hoá học 12" và "Hoá Học" cùng thành "hoá"
    .replace(/\s*\b(1[0-2]|[1-9])\b\s*$/, "")
    .replace(/^hóa/, "hoá")
    .replace(/\s*học$/, "")
    .replace(/^ngữ\s+/, "")
    .trim();

  /** Từ lớp 6 đến lớp 9, Vật lí – Hoá học – Sinh học nằm chung trong sách Khoa học tự nhiên. */
  const GOP_KHTN = ["vật lí", "vật lý", "hoá", "sinh"];

  function matchSubject(uiName, grade) {
    const n = norm(uiName);
    const cungLop = (s) => s.grade === null || Number(s.grade) === Number(grade);
    const hit = ready.find((s) => cungLop(s) && norm(s.name) === n);
    if (hit) return hit;
    if (grade <= 9 && GOP_KHTN.includes(n)) {
      return ready.find((s) => cungLop(s) && norm(s.name) === "khoa học tự nhiên");
    }
    return undefined;
  }

  /** Lớp 6–9 học chung sách Khoa học tự nhiên, nên gộp ba thẻ Vật lí – Hoá – Sinh thành một. */
  function gopKhtn(lobby, grade) {
    const cards = [...lobby.querySelectorAll(".subject-card")];
    const ba = cards.filter((c) => {
      const t = (c.querySelector(".sub-name") || {}).textContent || "";
      return GOP_KHTN.includes(norm(t));
    });
    if (grade > 9 || ba.length < 2) return;

    const the = ba[0];                        // giữ thẻ đầu, bỏ các thẻ còn lại
    ba.slice(1).forEach((c) => c.remove());
    the.querySelector(".sub-icon").textContent = "🔬";
    the.querySelector(".sub-name").textContent = "Khoa học tự nhiên";
    const desc = the.querySelector(".sub-desc");
    if (desc) desc.textContent = "Vật lí · Hoá học · Sinh học";
  }

  // bọc renderLobbySubjects của ui.js: thêm huy hiệu "đã có sách" / "chưa có tài liệu"
  const origRender = window.renderLobbySubjects;
  async function decorateLobby() {
    const lobby = $("lobbySubjects"); if (!lobby) return;
    await ensureData();                       // đảm bảo có dữ liệu mới nhất theo tài khoản hiện tại
    const grade = Number(localStorage.getItem("eduvie_selected_grade") || 12);
    gopKhtn(lobby, grade);
    [...lobby.querySelectorAll(".subject-card")].forEach((card) => {
      const nameEl = card.querySelector(".sub-name"); if (!nameEl) return;
      const hit = matchSubject(nameEl.textContent, grade);
      let badge = card.querySelector(".sub-state");
      if (!badge) {
        badge = document.createElement("div");
        badge.className = "sub-state";
        card.appendChild(badge);
      }
      if (hit && hit.n_docs) {
        const pct = hit.n_topics ? Math.round(100 * hit.learned / hit.n_topics) : 0;
        const color = hit.mastery === null ? "var(--card-border)"
          : hit.mastery < 50 ? "#d9534f" : hit.mastery < 75 ? "#f0ad4e" : "#5cb85c";
        badge.innerHTML = `
          <div class="sub-badges">
            <span class="lvl lvl-good">📚 ${hit.n_docs} tài liệu</span>
            ${hit.weak ? `<span class="lvl lvl-weak">🔴 ${hit.weak} chủ đề yếu</span>` : ""}
          </div>
          <div class="sub-progress" title="Đã học ${hit.learned}/${hit.n_topics} chủ đề">
            <span class="sp-bar"><span class="sp-fill" style="width:${pct}%;background:${color}"></span></span>
            <span class="sp-text">${hit.learned}/${hit.n_topics} chủ đề${hit.mastery !== null ? ` · TB ${hit.mastery}%` : ""}</span>
          </div>`;
        card.dataset.subjectId = hit.id;
        card.classList.remove("subject-empty");
      } else {
        badge.innerHTML = '<span class="lvl lvl-na">chưa có tài liệu</span>';
        card.classList.add("subject-empty");
        delete card.dataset.subjectId;
      }
      card.onclick = () => openSubject(nameEl.textContent, grade, hit);
    });
  }

  function openSubject(uiName, grade, hit) {
    window.__chatSubjectId = hit ? hit.id : null;
    const badge = $("chatSubjectBadge");
    if (badge) badge.textContent = hit ? `Môn: ${hit.name} · trả lời theo sách` : `Môn: ${uiName} lớp ${grade} · kiến thức chung`;
    window.switchTab("chat", document.querySelector('button[onclick*="\'chat\'"]'));
    setTimeout(() => {                       // đồng bộ ô chọn môn trong khung chat
      ensureChatSubjectPicker();
      const sel = $("chatSubjectPick");
      if (sel) sel.value = hit ? String(hit.id) : "";
    }, 160);
    const inp = $("userInput");
    if (inp) {
      inp.value = hit
        ? `Tóm tắt kiến thức trọng tâm môn ${hit.name} và cho em biết nên bắt đầu từ chương nào.`
        : `Hướng dẫn em kiến thức trọng tâm môn ${uiName} lớp ${grade}.`;
      inp.focus();
    }
    if (!hit) {
      const box = $("chatBox");
      if (box && !box.querySelector(".no-doc-note")) {
        const d = document.createElement("div");
        d.className = "bubble assistant no-doc-note";
        d.innerHTML = `Môn <b>${esc(uiName)}</b> chưa có tài liệu trong thư viện nên mình sẽ trả lời bằng kiến thức chung (không trích dẫn được trang sách). ` +
          `Quản trị viên có thể nạp sách ở mục <b>Tài liệu</b>.`;
        box.appendChild(d);
      }
    }
  }

  // gọi lại trang trí mỗi khi danh sách môn được vẽ lại
  window.renderLobbySubjects = function (...args) {
    if (typeof origRender === "function") origRender.apply(null, args);
    setTimeout(decorateLobby, 30);
  };
  const origSelectGrade = window.selectGrade;
  if (typeof origSelectGrade === "function") {
    window.selectGrade = function (...args) { origSelectGrade.apply(null, args); setTimeout(decorateLobby, 40); };
  }

  /* ---------------------------------------------------------------- 2. HỎI AI theo môn */
  function ensureChatSubjectPicker() {
    const header = document.querySelector("#view-chat .chat-header");
    if (!header || $("chatSubjectPick")) return;
    const sel = document.createElement("select");
    sel.id = "chatSubjectPick";
    sel.className = "ctl";
    sel.style.cssText = "width:auto;padding:5px 10px;font-size:.82rem";
    sel.innerHTML = '<option value="">Tất cả môn</option>' +
      ready.map((s) => `<option value="${s.id}">${esc(s.name)}</option>`).join("");
    sel.onchange = () => {
      window.__chatSubjectId = sel.value ? +sel.value : null;
      const b = $("chatSubjectBadge");
      if (b) b.textContent = sel.value ? `Môn: ${sel.selectedOptions[0].text}` : "Môn: tất cả";
    };
    const badge = $("chatSubjectBadge");
    if (badge) badge.replaceWith(sel.cloneNode(false)); // giữ chỗ
    header.appendChild(sel);
    if (badge) { badge.style.display = "none"; header.appendChild(badge); }
    if (window.__chatSubjectId) sel.value = String(window.__chatSubjectId);
  }

  /* ---------------------------------------------------------------- 3. HỎI BÀI: dọn lời văn cũ */
  function fixFeedbackCopy() {
    const sec = $("view-hoi-bai"); if (!sec || sec.dataset.fixed) return;
    sec.innerHTML = sec.innerHTML
      .replace(/Phiếu giải đáp thắc mắc từ Trung Tâm VuongEdu[^<]*/g, "Góp ý & thắc mắc")
      .replace(/CSRF Token Protected \(Bảo mật WTForms\)/g, "Nội dung được lưu vào hệ thống")
      .replace(/VuongEdu đang soạn thư &amp; gửi\.\.\./g, "Đang gửi…")
      .replace(/gửi trực tiếp đến hộp thư[^<.]*/gi, "gửi tới quản trị viên")
      .replace(/thư giải đáp/gi, "phản hồi");
    const hint = document.createElement("p");
    hint.className = "hint";
    hint.textContent = "Góp ý được lưu vào hệ thống; quản trị viên xem ở mục Quản trị → Góp ý.";
    const card = sec.querySelector(".wtf-card-form") || sec.firstElementChild;
    if (card) card.prepend(hint);
    // nối lại sự kiện submit sau khi thay HTML
    sec.querySelectorAll("form").forEach((f) => { f.onsubmit = window.handleWtfSubmit; });
    sec.dataset.fixed = "1";
  }

  /* ---------------------------------------------------------------- 4. TRANG CHỦ: số liệu xuống dưới hero */
  function relocateHomeStats() {
    const stats = $("homeQuickStats"), todo = $("homeTodo");
    const home = $("view-home"); if (!home) return;
    let slot = $("homeDataSlot");
    if (!slot) {
      slot = document.createElement("div");
      slot.id = "homeDataSlot";
      slot.className = "snap-slide home-data-slide";
      const hero = $("heroSnapSection");
      if (hero && hero.parentElement) hero.parentElement.insertBefore(slot, hero.nextSibling);
      else home.appendChild(slot);
    }
    if (stats && stats.parentElement !== slot) slot.appendChild(stats);
    if (todo && todo.parentElement !== slot) slot.appendChild(todo);
  }

  /* ---------------------------------------------------------------- gắn vào vòng đời */
  const origSwitch = window.switchTab;
  window.switchTab = function (viewId, btn) {
    if (typeof origSwitch === "function") origSwitch(viewId, btn);
    setTimeout(() => {
      if (viewId === "mon-tu-chon") decorateLobby();
      if (viewId === "chat") ensureChatSubjectPicker();
      if (viewId === "hoi-bai") fixFeedbackCopy();
      if (viewId === "home") relocateHomeStats();
    }, 120);
  };

  /* ---------------------------------------------------------------- 5. Điện thoại: thu gọn sidebar */
  function mobileSidebar() {
    const narrow = window.matchMedia("(max-width: 820px)").matches;
    let userChoice = null;
    try { userChoice = localStorage.getItem("eduvie_sidebar_closed"); } catch { /* bỏ qua */ }
    if (narrow && userChoice === null) document.body.classList.add("sidebar-closed");
    // trên màn hẹp, chọn xong một mục thì đóng sidebar lại cho đỡ che nội dung
    if (narrow) {
      document.querySelectorAll(".nav-item").forEach((b) => {
        if (b.dataset.autoclose) return;
        b.dataset.autoclose = "1";
        b.addEventListener("click", () => {
          if (window.matchMedia("(max-width: 820px)").matches) document.body.classList.add("sidebar-closed");
        });
      });
    }
  }
  window.addEventListener("resize", () => { if (window.matchMedia("(max-width: 820px)").matches) mobileSidebar(); });

  async function init() {
    mobileSidebar();
    await ensureData(true);
    decorateLobby();
    setTimeout(relocateHomeStats, 900);
    // đăng nhập / đăng xuất ở tab khác hoặc trong phiên này -> nạp lại dữ liệu môn học
    window.addEventListener("storage", (e) => { if (e.key === "vuongedu_token") ensureData(true).then(decorateLobby); });
  // cho lớp quản trị gọi sau khi thêm/xoá môn
  window.vuongeduReloadSubjects = () => ensureData(true).then(decorateLobby);
    let lastTok = null;
    setInterval(() => {
      let t = null; try { t = localStorage.getItem("vuongedu_token"); } catch { /* bỏ qua */ }
      if (t !== lastTok) { lastTok = t; ensureData(true).then(decorateLobby); }
    }, 2000);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
  // khi đăng nhập xong, dashboard mới vẽ -> dời lại số liệu
  setTimeout(relocateHomeStats, 2500);
})();
