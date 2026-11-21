/* ===========================================================================
   VuongEdu — Quản trị › Ngân hàng câu hỏi.
   Kho câu hỏi dùng chung: xem, lọc theo môn và độ khó, tìm theo nội dung,
   xem tỉ lệ học sinh làm đúng từng câu, và biết chủ đề nào còn thiếu câu.
   Nạp sau app3.js.
   =========================================================================== */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const token = () => { try { return localStorage.getItem("vuongedu_token") || ""; } catch { return ""; } };

  async function api(duong) {
    const r = await fetch(duong, { headers: { Authorization: "Bearer " + token() } });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || `Lỗi ${r.status}`);
    return r.json();
  }

  const DO_KHO = { easy: "Dễ", medium: "TB", hard: "Khó" };
  const loc = { subject_id: "", difficulty: "", q: "", offset: 0 };
  let mon = [];

  /** Màu theo tỉ lệ đúng: quá thấp = câu khó hoặc có vấn đề, quá cao = câu quá dễ. */
  function mauTiLe(p) {
    if (p === null || p === undefined) return "var(--text-muted)";
    return p < 35 ? "#d9534f" : p > 85 ? "#f0ad4e" : "#5cb85c";
  }

  async function ve() {
    const host = $("adminBody");
    if (!host) return;
    host.innerHTML = '<div class="skeleton">Đang tải ngân hàng…</div>';
    try {
      if (!mon.length) mon = await fetch("/subjects").then((r) => r.json());
      const tham = new URLSearchParams({ limit: 50, offset: loc.offset });
      if (loc.subject_id) tham.set("subject_id", loc.subject_id);
      if (loc.difficulty) tham.set("difficulty", loc.difficulty);
      if (loc.q) tham.set("q", loc.q);
      const [tk, ds] = await Promise.all([api("/admin/bank/stats"), api(`/admin/bank?${tham}`)]);

      const phu = tk.tong_chu_de ? Math.round(100 * tk.chu_de_co_cau / tk.tong_chu_de) : 0;
      host.innerHTML = `
        <div class="stat-row">
          <div class="stat"><b>${tk.tong}</b><span>câu trong kho</span></div>
          <div class="stat"><b>${tk.chu_de_co_cau}/${tk.tong_chu_de}</b><span>chủ đề đã có câu (${phu}%)</span></div>
          <div class="stat"><b>${tk.luot_dua_vao_de}</b><span>lượt đưa vào đề</span></div>
          <div class="stat"><b>${tk.luot_tra_loi}</b><span>lượt trả lời</span></div>
          <div class="stat ${tk.ti_le_dung_chung !== null && tk.ti_le_dung_chung < 40 ? "warn" : "good"}">
            <b>${tk.ti_le_dung_chung === null ? "—" : tk.ti_le_dung_chung + "%"}</b><span>tỉ lệ làm đúng</span></div>
          <div class="stat ${tk.bi_bao_sai ? "warn" : ""}"><b>${tk.bi_bao_sai}</b><span>câu bị báo sai</span></div>
        </div>

        <div class="panel">
          <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:12px">
            <select class="ctl" id="bkMon" style="max-width:190px">
              <option value="">— Tất cả môn —</option>
              ${mon.map((m) => `<option value="${m.id}" ${String(m.id) === loc.subject_id ? "selected" : ""}>${esc(m.name)}</option>`).join("")}
            </select>
            <select class="ctl" id="bkKho" style="max-width:150px">
              <option value="">— Mọi độ khó —</option>
              ${["easy", "medium", "hard"].map((d) => `<option value="${d}" ${d === loc.difficulty ? "selected" : ""}>${DO_KHO[d]}</option>`).join("")}
            </select>
            <input class="ctl" id="bkTim" placeholder="Tìm trong nội dung câu hỏi…" value="${esc(loc.q)}" style="flex:1;min-width:200px">
            <button class="btn btn-ghost btn-sm" id="bkThieu">Chủ đề còn thiếu câu</button>
          </div>

          <p class="hint" style="margin-bottom:10px">
            Tìm thấy <b>${ds.total}</b> câu. Phần trăm là tỉ lệ học sinh trả lời đúng —
            dưới 35% là câu khó hoặc có vấn đề, trên 85% là câu quá dễ.
          </p>

          <div class="table-scroll"><table class="data-table">
            <thead><tr><th>#</th><th>Chủ đề</th><th>Độ khó</th><th>Câu hỏi</th>
              <th>Đã dùng</th><th>Làm đúng</th><th></th></tr></thead>
            <tbody>
              ${ds.items.map((c) => `
                <tr${c.flagged ? ' style="opacity:.55"' : ""}>
                  <td>${c.id}</td>
                  <td><b>${esc(c.topic)}</b><br><span class="hint">${esc(c.subject)} · ${esc(c.chapter)}</span></td>
                  <td>${DO_KHO[c.difficulty] || c.difficulty}</td>
                  <td style="max-width:420px">
                    ${c.flagged ? '<span class="lvl lvl-weak">🚩 bị báo sai</span> ' : ""}
                    ${!c.verified ? '<span class="lvl lvl-na">chưa kiểm chéo</span> ' : ""}
                    ${esc(c.content).slice(0, 200)}${c.content.length > 200 ? "…" : ""}
                    <br><span class="hint">Đáp án: ${esc(c.options[c.correct] || "")}</span>
                  </td>
                  <td>${c.times_used}</td>
                  <td style="color:${mauTiLe(c.ti_le_dung)}">
                    ${c.ti_le_dung === null ? "—" : c.ti_le_dung + "%"}
                    ${c.times_answered ? `<br><span class="hint">${c.times_answered} lượt</span>` : ""}</td>
                  <td><button class="btn btn-ghost btn-sm" data-xoa="${c.id}">Xoá</button></td>
                </tr>`).join("") || '<tr><td colspan="7">Không có câu nào khớp bộ lọc.</td></tr>'}
            </tbody></table></div>

          <div style="display:flex;gap:8px;margin-top:12px;align-items:center">
            <button class="btn btn-ghost btn-sm" id="bkTruoc" ${loc.offset ? "" : "disabled"}>← Trước</button>
            <span class="hint">${loc.offset + 1}–${Math.min(loc.offset + 50, ds.total)} / ${ds.total}</span>
            <button class="btn btn-ghost btn-sm" id="bkSau" ${loc.offset + 50 >= ds.total ? "disabled" : ""}>Sau →</button>
          </div>
        </div>`;

      gan();
    } catch (e) {
      host.innerHTML = `<div class="empty-note">${esc(e.message)}</div>`;
    }
  }

  function gan() {
    const host = $("adminBody");
    $("bkMon").onchange = (e) => { loc.subject_id = e.target.value; loc.offset = 0; ve(); };
    $("bkKho").onchange = (e) => { loc.difficulty = e.target.value; loc.offset = 0; ve(); };
    $("bkTim").onkeydown = (e) => {
      if (e.key === "Enter") { loc.q = e.target.value.trim(); loc.offset = 0; ve(); }
    };
    $("bkTruoc").onclick = () => { loc.offset = Math.max(0, loc.offset - 50); ve(); };
    $("bkSau").onclick = () => { loc.offset += 50; ve(); };
    $("bkThieu").onclick = veThieu;

    host.querySelectorAll("[data-xoa]").forEach((b) => {
      b.onclick = async () => {
        if (!confirm("Xoá câu này khỏi ngân hàng? Những đề đã dùng nó vẫn giữ nguyên.")) return;
        await fetch(`/admin/bank/${b.dataset.xoa}`, {
          method: "DELETE", headers: { Authorization: "Bearer " + token() },
        });
        ve();
      };
    });
  }

  async function veThieu() {
    const host = $("adminBody");
    host.innerHTML = '<div class="skeleton">Đang tính…</div>';
    try {
      const ds = await api("/admin/bank/coverage" + (loc.subject_id ? `?subject_id=${loc.subject_id}` : ""));
      const trong = ds.filter((x) => x.n === 0);
      host.innerHTML = `
        <div class="panel">
          <h3 class="panel-title">Chủ đề còn thiếu câu</h3>
          <p class="hint">${trong.length}/${ds.length} chủ đề chưa có câu nào.
            Mỗi lần học sinh luyện đề ở chủ đề đó, câu mới sinh ra sẽ được nạp vào kho.</p>
          <div class="table-scroll"><table class="data-table">
            <thead><tr><th>Môn</th><th>Chương</th><th>Chủ đề</th><th>Số câu</th></tr></thead>
            <tbody>${ds.slice(0, 120).map((x) => `
              <tr${x.n === 0 ? ' style="color:var(--danger,#d9534f)"' : ""}>
                <td>${esc(x.subject)}</td><td>${esc(x.chapter)}</td>
                <td>${esc(x.topic)}</td><td>${x.n}</td></tr>`).join("")}
            </tbody></table></div>
          <button class="btn btn-ghost btn-sm" style="margin-top:12px" id="bkQuayLai">← Quay lại danh sách câu hỏi</button>
        </div>`;
      $("bkQuayLai").onclick = ve;
    } catch (e) {
      host.innerHTML = `<div class="empty-note">${esc(e.message)}</div>`;
    }
  }

  /* ----------------------------------------- cắm thêm một tab vào trang Quản trị */
  const truoc = window.adminTab;
  window.adminTab = function (name, btn) {
    if (name !== "bank") { truoc.apply(null, arguments); return; }
    document.querySelectorAll("#adminTabs .tab-btn").forEach((b) => b.classList.remove("active"));
    if (btn) btn.classList.add("active");
    loc.offset = 0;
    ve();
  };
})();
