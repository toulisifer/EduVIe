/* ===========================================================================
   VuongEdu — hiển thị công thức.
   Mô hình trả lời bằng LaTeX ($x^2$, $H_2SO_4$) nhưng trang web trước đây không
   có thư viện nào dựng công thức, nên người học nhìn thấy nguyên ký tự thô.
   Tệp này nạp KaTeX rồi tự dựng lại mỗi khi có nội dung mới chèn vào trang.
   =========================================================================== */
(() => {
  "use strict";

  const CDN = "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9";
  const DELIMS = [
    { left: "$$", right: "$$", display: true },
    { left: "\\[", right: "\\]", display: true },
    { left: "\\(", right: "\\)", display: false },
    { left: "$", right: "$", display: false },
  ];

  function nap(tag, attrs) {
    return new Promise((ok, loi) => {
      const el = Object.assign(document.createElement(tag), attrs);
      el.onload = ok;
      el.onerror = () => loi(new Error("không tải được " + (attrs.src || attrs.href)));
      document.head.appendChild(el);
    });
  }

  /** Dựng công thức trong một phần tử; bỏ qua nếu KaTeX chưa sẵn sàng. */
  function dung(el) {
    if (!el || !window.renderMathInElement) return;
    try {
      window.renderMathInElement(el, {
        delimiters: DELIMS,
        throwOnError: false,          // công thức sai thì giữ nguyên chữ, không làm vỡ trang
        ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code", "option"],
      });
    } catch { /* không để lỗi công thức chặn phần còn lại */ }
  }
  window.renderMath = dung;

  // Theo dõi cả MÀN HÌNH (section.view-section) chứ không liệt kê từng ô nội dung.
  //
  // Trước đây tệp này giữ một danh sách id cứng ("quizBox", "plList"...). Giao diện đổi
  // tên ô thì danh sách thành lỗi thời mà không ai biết: đề trắc nghiệm nằm trong
  // #quizPaper và #clsPaper, hai ô chưa bao giờ có trong danh sách, nên công thức trong
  // đề hiện nguyên chữ $11,2\text{ g}$. Theo dõi theo màn hình thì ô nào thêm sau cũng
  // được phủ, không phải nhớ cập nhật danh sách nữa.
  const VUNG = "main .view-section";

  let obs = null;
  const dang_theo_doi = new Set();

  /** Gom nhiều thay đổi liên tiếp thành một lần dựng. */
  let hang = new Set();
  let hen = null;
  function xepHang(el) {
    hang.add(el);
    clearTimeout(hen);
    hen = setTimeout(() => {
      const ds = [...hang];
      hang = new Set();
      // Tự KaTeX cũng sửa DOM; ngắt theo dõi trong lúc dựng để khỏi tự kích hoạt lại.
      obs.disconnect();
      ds.forEach(dung);
      obs.takeRecords();
      dang_theo_doi.forEach(gan);
    }, 120);
  }

  function gan(el) {
    obs.observe(el, { childList: true, subtree: true });
  }

  function quet() {
    document.querySelectorAll(VUNG).forEach((el) => {
      if (!dang_theo_doi.has(el)) {
        dang_theo_doi.add(el);
        gan(el);
      }
      dung(el);                       // dựng phần đã có sẵn (ví dụ lịch sử chat)
    });
  }

  function theoDoi() {
    obs = new MutationObserver((ds) => {
      for (const d of ds) {
        if (d.addedNodes.length) xepHang(d.target);
      }
    });
    quet();
    // Màn hình nào dựng sau mới gắn được, nên quét lại khi đổi tab.
    const oldSwitch = window.switchTab;
    if (typeof oldSwitch === "function") {
      window.switchTab = function (...args) {
        const r = oldSwitch.apply(this, args);
        setTimeout(quet, 300);
        return r;
      };
    }
  }

  (async () => {
    try {
      await nap("link", { rel: "stylesheet", href: `${CDN}/katex.min.css` });
      await nap("script", { src: `${CDN}/katex.min.js` });
      await nap("script", { src: `${CDN}/contrib/auto-render.min.js` });
    } catch (e) {
      console.warn("KaTeX:", e.message, "— công thức sẽ hiện dạng chữ.");
      return;
    }
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", theoDoi);
    } else {
      theoDoi();
    }
  })();
})();
