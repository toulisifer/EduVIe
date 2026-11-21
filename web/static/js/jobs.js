/* ===========================================================================
   VuongEdu — Gia sư AI và Lộ trình (agent / multi-agent) chạy nền.
   Server trả job_id ngay rồi ta hỏi tiến độ mỗi 2 giây, nên:
   - không còn bị Cloudflare cắt ở giây thứ 100 (lỗi 524) khi dùng link public;
   - người dùng thấy agent đang gọi công cụ nào thay vì ngồi chờ 3 phút.
   Nạp sau app.js.
   =========================================================================== */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const token = () => { try { return localStorage.getItem("vuongedu_token") || ""; } catch { return ""; } };

  const TOOL_VI = {
    get_student_overview: "Xem tổng quan học tập", get_topic_mastery: "Lấy mastery từng chủ đề",
    get_recent_mistakes: "Xem các câu làm sai gần đây", get_review_and_prerequisites: "Xem lịch ôn & kiến thức nền",
    search_documents: "Tra cứu sách giáo khoa", save_study_plan: "Lưu kế hoạch",
  };
  const STAGE_VI = { diagnoser: "Chẩn đoán", planner: "Lập kế hoạch", critic: "Phản biện",
                     validator: "Kiểm tra luật", repair: "Tự sửa", save: "Lưu kế hoạch" };

  function stepHtml(s) {
    if (s.stage) return `<div class="tl">🧠 <b>${esc(STAGE_VI[s.stage] || s.stage)}</b> ${esc(s.text || "")}</div>`;
    const name = TOOL_VI[s.tool] || s.tool || "bước";
    return `<div class="tl">🔧 <b>${esc(name)}</b><br><code>${esc(s.tool || "")}(${esc(JSON.stringify(s.args || {}))})</code></div>`;
  }

  /** Hỏi /jobs/{id} tới khi xong. onProgress(steps, giây) gọi sau mỗi lần hỏi. */
  async function follow(jobId, onProgress) {
    for (;;) {
      await new Promise((r) => setTimeout(r, 2000));
      const res = await fetch(`/jobs/${jobId}`, { headers: { Authorization: "Bearer " + token() } });
      if (res.status === 404) throw new Error("Việc này không còn (server đã khởi động lại) — hãy gửi lại yêu cầu");
      if (!res.ok) continue;                       // mạng chập chờn thì hỏi lại
      const j = await res.json();
      onProgress(j.steps || [], j.seconds || 0);
      if (j.status === "done") return j.result;
      if (j.status === "failed") throw new Error(j.error || "Chạy thất bại");
    }
  }

  window.theoDoiJob = follow;      // app.js dùng lại cho việc sinh đề dài

  /* ------------------------------------------------------------------ GIA SƯ AI */
  window.sendTutor = async function () {
    if (!window.state || !window.state.user) { if (window.requireLogin) window.requireLogin(); }
    const input = $("tutorInput");
    const text = (input.value || "").trim();
    if (!text) return;
    input.value = "";
    const box = $("tutorBox");
    const add = (role, html) => {
      const d = document.createElement("div");
      d.className = `bubble ${role}`; d.innerHTML = html;
      box.appendChild(d); box.scrollTop = box.scrollHeight;
      return d;
    };
    add("user", esc(text));
    const think = add("assistant thinking", '<div class="typing-dots"><span></span><span></span><span></span></div>');
    const tools = $("tutorTools");
    tools.innerHTML = '<div class="tl">đang tra cứu…</div>';

    try {
      const r = await fetch("/agent", {
        method: "POST",
        headers: { Authorization: "Bearer " + token(), "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, subject_id: +(($("anSubject") || {}).value) || null }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || `Lỗi ${r.status}`);

      const out = await follow(d.job_id, (steps, giay) => {
        tools.innerHTML = steps.map(stepHtml).join("") +
          `<div class="tl hint">⏳ đã ${giay} giây…</div>`;
      });
      think.remove();
      add("assistant", window.mdToHtml ? window.mdToHtml(out.answer) : esc(out.answer));
      tools.innerHTML = (out.trace || []).map(stepHtml).join("") || '<div class="tl">(không gọi công cụ nào)</div>';
    } catch (e) {
      think.remove();
      add("assistant", `<span style="color:#d9534f">${esc(e.message)}</span>`);
      tools.innerHTML = "";
    }
  };

  /* ------------------------------------------------------------------ LỘ TRÌNH */
  const origCreatePlan = window.createPlan;
  window.createPlan = async function () {
    const mode = (document.querySelector("input[name=planmode]:checked") || {}).value || "quick";
    if (mode === "quick") return origCreatePlan.apply(this, arguments);   // nhanh, giữ nguyên đường cũ

    const status = (msg, kind) => {
      const el = $("plStatus");
      if (el) el.innerHTML = `<span style="color:${kind === "err" ? "var(--danger,#dc2626)" : kind === "ok" ? "var(--good,#16a34a)" : "inherit"}">${msg}</span>`;
    };
    const trace = $("plTrace");
    trace.hidden = false; trace.innerHTML = "";
    status(`Đang chạy chế độ ${mode}…`);

    try {
      const r = await fetch("/plan2", {
        method: "POST",
        headers: { Authorization: "Bearer " + token(), "Content-Type": "application/json" },
        body: JSON.stringify({ subject_id: +$("plSubject").value || null, goal: $("plGoal").value,
                               days: +$("plDays").value, hours_per_day: +$("plHours").value, mode }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || `Lỗi ${r.status}`);

      const out = await follow(d.job_id, (steps, giay) => {
        trace.innerHTML = steps.map(stepHtml).join("") + `<div class="tl hint">⏳ đã ${giay} giây…</div>`;
        status(`Đang chạy chế độ ${mode} — ${giay} giây, ${steps.length} bước. Có thể rời trang, việc vẫn chạy.`);
      });

      status("Xong", "ok");
      trace.innerHTML = (out.trace || []).map(stepHtml).join("") || '<div class="tl">(không có bước nào)</div>';
      if (out.critique && window.toast) {
        window.toast(`Agent phản biện chấm ${out.critique.score}/10` +
          (out.violations && out.violations.length ? ` · còn ${out.violations.length} vi phạm` : " · validator ✅"));
      }
      window.state.plan = out.plan;
      window.paintPlan();
    } catch (e) {
      status(esc(e.message), "err");
    }
  };
})();
