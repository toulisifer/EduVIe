/* ===========================================================================
   VuongEdu — Quản trị › Môn học: thêm / xoá môn, chương, chủ đề.
   Cần cái này để mở lớp mới (ví dụ lớp 8) trước khi tải sách lên.
   Nạp sau app2.js.
   =========================================================================== */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function token() { try { return localStorage.getItem("vuongedu_token") || ""; } catch { return ""; } }

  async function call(path, method = "GET", body) {
    const r = await fetch(path, {
      method,
      headers: { Authorization: "Bearer " + token(), ...(body ? { "Content-Type": "application/json" } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.detail || `Lỗi ${r.status}`);
    return d;
  }

  /* -------------------------------------------------------------- vẽ cây môn học */
  let tree = [];
  let openSubject = null;   // id môn đang mở

  async function render() {
    const host = $("adminBody");
    if (!host) return;
    host.innerHTML = '<div class="skeleton">Đang tải…</div>';
    try {
      tree = await call("/admin/taxonomy");
    } catch (e) {
      host.innerHTML = `<div class="empty-note">${esc(e.message)}</div>`;
      return;
    }
    // gom theo lớp để dễ nhìn: tên môn kết thúc bằng số lớp
    const gradeOf = (n) => { const m = String(n).match(/\b(1[0-2]|[1-9])\b\s*$/); return m ? Number(m[1]) : null; };

    host.innerHTML = `
      <div class="panel">
        <h3 class="panel-title">➕ Thêm môn học mới</h3>
        <p class="hint">Đặt tên kèm số lớp ở cuối để hệ thống tự xếp vào đúng lớp: <b>Toán 8</b>, <b>Vật lí 8</b>, <b>Ngữ văn 8</b>…
          Sau khi có môn, vào tab <b>Tài liệu</b> ở trang Tài liệu để tải sách lên.</p>
        <div class="form-row" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <input class="ctl" id="txNewSubject" placeholder="Tên môn, ví dụ: Toán 8" style="max-width:280px">
          <button class="btn btn-primary" id="txAddSubject">Thêm môn</button>
        </div>
        <div id="txMsg" class="status-line"></div>
      </div>

      <div class="panel">
        <h3 class="panel-title">📗 Môn học hiện có (${tree.length})</h3>
        ${tree.length ? tree.map((s) => {
          const g = gradeOf(s.name);
          const nTopics = s.chapters.reduce((a, c) => a + c.topics.length, 0);
          const open = openSubject === s.id;
          return `<div class="tx-subject" style="border:1px solid var(--border);border-radius:10px;margin-bottom:10px;overflow:hidden">
            <div class="mini-item" style="margin:0;padding:10px 12px;cursor:pointer" data-tx-open="${s.id}">
              <span><b>${open ? "▾" : "▸"} ${esc(s.name)}</b>
                <span class="hint"> · ${g ? "lớp " + g : "không rõ lớp"} · ${s.chapters.length} chương · ${nTopics} chủ đề · ${s.n_docs} tài liệu</span></span>
              <span class="r"><button class="btn btn-ghost btn-sm" data-tx-delsub="${s.id}">Xoá môn</button></span>
            </div>
            ${open ? `<div style="padding:0 12px 12px">
              ${s.chapters.map((c) => `<div style="border-top:1px dashed var(--border);padding:10px 0">
                <div class="mini-item" style="margin:0;padding:0">
                  <span><b>${esc(c.name)}</b> <span class="hint">· ${c.topics.length} chủ đề · ${c.n_docs} tài liệu</span></span>
                  <span class="r"><button class="btn btn-ghost btn-sm" data-tx-delchap="${c.id}">Xoá chương</button></span>
                </div>
                <div style="display:flex;gap:6px;flex-wrap:wrap;margin:8px 0">
                  ${c.topics.length ? c.topics.map((t) => `<span class="chip" style="display:inline-flex;align-items:center;gap:4px">
                    ${esc(t.name)}${t.n_answers ? ` <span class="hint">(${t.n_answers})</span>`
                      : ` <button class="btn-x" data-tx-deltop="${t.id}" title="Xoá chủ đề" style="background:none;border:0;cursor:pointer;color:var(--text-muted)">×</button>`}
                    </span>`).join("") : '<span class="hint">Chưa có chủ đề nào.</span>'}
                </div>
                <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:flex-start">
                  <textarea class="ctl" data-tx-topics="${c.id}" rows="2" placeholder="Mỗi dòng một chủ đề, ví dụ:&#10;Hằng đẳng thức đáng nhớ&#10;Phân tích đa thức thành nhân tử" style="flex:1;min-width:240px"></textarea>
                  <button class="btn btn-ghost btn-sm" data-tx-addtopics="${c.id}">Thêm chủ đề</button>
                </div>
              </div>`).join("")}
              <div style="border-top:1px dashed var(--border);padding-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
                <input class="ctl" data-tx-chapname="${s.id}" placeholder="Tên chương mới, ví dụ: Chương 1: Đa thức" style="flex:1;min-width:240px">
                <button class="btn btn-ghost btn-sm" data-tx-addchap="${s.id}">Thêm chương</button>
              </div>
            </div>` : ""}
          </div>`;
        }).join("") : '<div class="empty-note">Chưa có môn nào.</div>'}
      </div>`;

    bind();
  }

  function msg(text, ok) {
    const m = $("txMsg");
    if (m) m.innerHTML = `<span style="color:${ok ? "var(--good, #16a34a)" : "var(--danger, #dc2626)"}">${esc(text)}</span>`;
  }

  async function guarded(fn) {
    try { await fn(); await afterChange(); }
    catch (e) { msg(e.message, false); }
  }

  async function afterChange() {
    await render();
    if (typeof window.vuongeduReloadSubjects === "function") window.vuongeduReloadSubjects();
  }

  function bind() {
    const host = $("adminBody");
    if (!host) return;

    const add = $("txAddSubject");
    if (add) add.onclick = () => guarded(async () => {
      const name = ($("txNewSubject").value || "").trim();
      if (!name) throw new Error("Hãy nhập tên môn");
      await call("/admin/subjects", "POST", { name });
    });

    host.querySelectorAll("[data-tx-open]").forEach((el) => {
      el.onclick = (ev) => {
        if (ev.target.closest("button")) return;      // nút xoá nằm trong hàng này
        const id = Number(el.dataset.txOpen);
        openSubject = openSubject === id ? null : id;
        render();
      };
    });

    host.querySelectorAll("[data-tx-delsub]").forEach((el) => {
      el.onclick = () => {
        const id = Number(el.dataset.txDelsub);
        const s = tree.find((x) => x.id === id);
        if (!confirm(`Xoá môn "${s ? s.name : id}" cùng toàn bộ chương và chủ đề của nó?`)) return;
        guarded(() => call(`/admin/subjects/${id}`, "DELETE"));
      };
    });

    host.querySelectorAll("[data-tx-addchap]").forEach((el) => {
      el.onclick = () => guarded(async () => {
        const sid = Number(el.dataset.txAddchap);
        const inp = host.querySelector(`[data-tx-chapname="${sid}"]`);
        const name = (inp.value || "").trim();
        if (!name) throw new Error("Hãy nhập tên chương");
        await call("/admin/chapters", "POST", { subject_id: sid, name });
      });
    });

    host.querySelectorAll("[data-tx-delchap]").forEach((el) => {
      el.onclick = () => {
        if (!confirm("Xoá chương này cùng các chủ đề trong đó?")) return;
        guarded(() => call(`/admin/chapters/${Number(el.dataset.txDelchap)}`, "DELETE"));
      };
    });

    host.querySelectorAll("[data-tx-addtopics]").forEach((el) => {
      el.onclick = () => guarded(async () => {
        const cid = Number(el.dataset.txAddtopics);
        const ta = host.querySelector(`[data-tx-topics="${cid}"]`);
        const names = (ta.value || "").split("\n").map((x) => x.trim()).filter(Boolean);
        if (!names.length) throw new Error("Hãy nhập ít nhất một chủ đề");
        const r = await call("/admin/topics", "POST", { chapter_id: cid, names });
        if (!r.added.length) throw new Error("Các chủ đề này đã có sẵn");
      });
    });

    host.querySelectorAll("[data-tx-deltop]").forEach((el) => {
      el.onclick = () => guarded(() => call(`/admin/topics/${Number(el.dataset.txDeltop)}`, "DELETE"));
    });
  }

  /* ------------------------------------------- cắm thêm một tab vào trang Quản trị */
  const origAdminTab = window.adminTab;
  window.adminTab = function (name, btn) {
    if (name !== "taxonomy") { origAdminTab.apply(null, arguments); return; }
    document.querySelectorAll("#adminTabs .tab-btn").forEach((b) => b.classList.remove("active"));
    if (btn) btn.classList.add("active");
    render();
  };
})();
