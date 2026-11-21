/* ===========================================================================
   VuongEdu — Tải tài liệu: chạy nền + theo dõi tiến độ.
   Trước đây request bị giữ mở suốt quá trình OCR nên qua Cloudflare tunnel
   đứt ở giây thứ 100 (lỗi 524). Nay server trả lời ngay, trang tự hỏi tiến độ.
   Nạp sau app.js.
   =========================================================================== */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  function token() { try { return localStorage.getItem("vuongedu_token") || ""; } catch { return ""; } }

  function say(html, kind) {
    const el = $("docUploadStatus");
    if (!el) return;
    const color = kind === "err" ? "var(--danger, #dc2626)" : kind === "ok" ? "var(--good, #16a34a)" : "inherit";
    el.innerHTML = `<span style="color:${color}">${html}</span>`;
  }

  /** Hỏi trạng thái mỗi 3 giây cho tới khi xong hoặc hỏng. */
  async function watch(docId, t0) {
    for (;;) {
      await new Promise((r) => setTimeout(r, 3000));
      let d;
      try {
        const r = await fetch(`/documents/${docId}`, { headers: { Authorization: "Bearer " + token() } });
        if (!r.ok) throw new Error("x");
        d = await r.json();
      } catch { continue; }                      // mạng chập chờn thì hỏi lại
      const phut = Math.round((Date.now() - t0) / 60000);
      if (d.status === "ready") {
        say(`✅ Xong: ${d.n_chunks} đoạn đã được index (${phut} phút).`, "ok");
        if (typeof window.vuongeduReloadSubjects === "function") window.vuongeduReloadSubjects();
        const btn = document.querySelector('button[onclick*="tai-lieu"]');
        if (btn) window.switchTab("tai-lieu", btn);   // vẽ lại thư viện
        return;
      }
      if (d.status === "failed") { say(`❌ ${esc(d.error || "Xử lý thất bại")}`, "err"); return; }
      say(`⏳ ${esc(d.progress || "Đang xử lý…")} — đã ${phut} phút. Bạn có thể rời trang, việc vẫn chạy tiếp.`);
    }
  }

  window.uploadDocument = async function () {
    const f = $("docFile") && $("docFile").files[0];
    if (!f) { say("Chưa chọn tệp", "err"); return; }
    if (!$("docSubject").value) { say("Chưa chọn môn", "err"); return; }
    if (!$("docChapter").value && f.size > 20 * 1024 * 1024) {
      if (!confirm('Bạn đang nạp cả cuốn sách vào mục "Cả môn". Việc này OCR hàng trăm trang và rất dễ hết quota Gemini trong ngày.\n\nNên chọn từng chương, hoặc điền khoảng trang. Vẫn tiếp tục?')) return;
    }
    const fd = new FormData();
    fd.append("file", f);
    fd.append("subject_id", $("docSubject").value);
    if ($("docChapter").value) fd.append("chapter_id", $("docChapter").value);
    fd.append("page_from", $("docFrom").value || 1);
    fd.append("page_to", $("docTo").value || 0);

    say(`⬆️ Đang tải tệp lên (${(f.size / 1048576).toFixed(1)} MB)…`);
    try {
      const r = await fetch("/documents", { method: "POST", headers: { Authorization: "Bearer " + token() }, body: fd });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || `Lỗi ${r.status}`);
      say("🚀 Đã nhận tệp, bắt đầu xử lý nền…");
      watch(d.id, Date.now());
    } catch (e) {
      say(`${esc(e.message)} — nếu đang dùng link trycloudflare, hãy thử lại trên http://localhost:8000`, "err");
    }
  };
})();
