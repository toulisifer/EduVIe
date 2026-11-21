
    // DỮ LIỆU ĐẦY ĐỦ 13 MÔN - CHỮ KÝ CHUẨN CÁC NHÀ BÁC HỌC & HÌNH ẢNH THẨM MỸ CAO CẤP
    const subjectData = [
        {
            name: "Toán học", icon: "📐",
            scientist: "Galileo Galilei",
            signature: "/static/signatures/galileo_galilei.svg",
            title: "Cha đẻ của thiên văn học quan sát & vật lý hiện đại",
            image: "/static/images/subjects/toan_galileo.jpg",
            quote: "Vũ trụ được viết bằng ngôn ngữ Toán học, và các ký tự của nó là các hình tam giác, hình tròn và các hình hình học khác."
        },
        {
            name: "Vật lí", icon: "⚡",
            scientist: "Albert Einstein",
            signature: "/static/signatures/albert_einstein.svg",
            title: "Nhà vật lý lý thuyết vĩ đại nhất thế kỷ 20",
            image: "/static/images/subjects/vat_li_einstein.png",
            quote: "Điều đẹp đẽ nhất mà chúng ta có thể trải nghiệm là sự bí ẩn. Đó là nguồn gốc của mọi nghệ thuật và khoa học chân chính."
        },
        {
            name: "Hoá Học", icon: "🧪",
            scientist: "Marie Curie",
            signature: "/static/signatures/marie_curie.svg",
            title: "Nhà bác học đạt 2 giải Nobel hai lĩnh vực khác nhau",
            image: "/static/images/subjects/hoa_hoc_curie.png",
            portrait: "/static/images/portraits/curie.jpg",
            quote: "Trong cuộc sống không có gì đáng sợ, chỉ có những điều cần được thấu hiểu. Bây giờ là lúc cần hiểu nhiều hơn để bớt sợ hãi hơn."
        },
        {
            name: "Sinh Học", icon: "🧬",
            scientist: "Charles Darwin",
            signature: "/static/signatures/charles_darwin.svg",
            title: "Tác giả Thuyết Tiến Hóa vĩ đại của sinh giới",
            image: "/static/images/subjects/sinh_hoc_darwin.png",
            portrait: "/static/images/portraits/darwin.jpg",
            quote: "Không phải loài mạnh nhất hay thông minh nhất sẽ sống sót, mà là loài có khả năng thích nghi tốt nhất với sự thay đổi."
        },
        {
            name: "Ngữ Văn", icon: "✍️",
            scientist: "Lev Tolstoy",
            signature: "/static/signatures/lev_tolstoy.svg",
            title: "Đại văn hào kinh điển của văn học thế giới",
            image: "/static/images/subjects/ngu_van_tolstoy.png",
            portrait: "/static/images/portraits/tolstoy.jpg",
            quote: "Văn học đích thực là chiếc gương phản chiếu tâm hồn con người và hướng con người đến sự hoàn thiện đạo đức."
        },
        {
            name: "Tin Học", icon: "💻",
            scientist: "Alan Turing",
            signature: "/static/signatures/alan_turing.svg",
            title: "Cha đẻ của khoa học máy tính và Trí tuệ nhân tạo",
            image: "/static/images/subjects/tin_hoc_turing.png",
            portrait: "/static/images/portraits/turing.jpg",
            quote: "Chúng ta chỉ có thể nhìn thấy một quãng ngắn phía trước, nhưng ở đó có vô số điều cần phải được hoàn thành."
        },
        {
            name: "Tiếng Anh", icon: "🌐",
            scientist: "William Shakespeare",
            signature: "/static/signatures/william_shakespeare.svg",
            title: "Nhà soạn kịch và thi hào vĩ đại nhất văn học Anh",
            image: "/static/images/subjects/tieng_anh_shakespeare.jpg",
            portrait: "/static/images/portraits/shakespeare.jpg",
            quote: "Biết thêm một ngôn ngữ là mở ra một chân trời mới để kết nối linh hồn của toàn nhân loại."
        },
        {
            name: "Lịch sử", icon: "📜",
            scientist: "Herodotus",
            signature: "/static/signatures/herodotus.svg",
            title: "Người được mệnh danh là 'Người cha của môn Lịch sử'",
            image: "/static/images/subjects/lich_su_herodotus.jpg",
            portrait: "/static/images/portraits/herodotus.jpg",
            quote: "Lịch sử là nhân chứng của thời gian, ánh sáng của chân lý, sự sống của ký ức và người thầy của cuộc đời."
        },
        {
            name: "Địa lí", icon: "🗺️",
            scientist: "Alexander von Humboldt",
            signature: "/static/signatures/alexander_von_humboldt.svg",
            title: "Nhà tự nhiên học đặt nền móng địa lý sinh thái hiện đại",
            image: "/static/images/subjects/dia_li_humboldt.jpg",
            portrait: "/static/images/portraits/humboldt.jpg",
            quote: "Chuyến du hành đích thực của sự khám phá không phải là tìm kiếm những vùng đất mới, mà là nhìn với đôi mắt mới."
        },
        {
            name: "Giáo Dục Công Dân", icon: "⚖️",
            scientist: "Socrates",
            signature: "/static/signatures/socrates.svg",
            title: "Nhà triết học Hy Lạp cổ đại đặt nền móng cho luân lý",
            image: "/static/images/subjects/gdcd_socrates.png",
            portrait: "/static/images/portraits/socrates.jpg",
            quote: "Một cuộc đời không được suy xét kỹ lưỡng là một cuộc đời không đáng sống. Đạo đức là cội nguồn tự do chân chính."
        },
        {
            name: "Công Nghệ", icon: "⚙️",
            scientist: "Nikola Tesla",
            signature: "/static/signatures/nikola_tesla.svg",
            title: "Nhà phát minh thiên tài định hình kỷ nguyên điện năng",
            image: "/static/images/subjects/cong_nghe_tesla.jpg",
            portrait: "/static/images/portraits/tesla.jpg",
            quote: "Hiện tại là của họ; tương lai, nơi tôi thực sự cống hiến mọi công trình, sẽ thuộc về tôi."
        },
        {
            name: "Giáo dục thể chất", icon: "🏃",
            scientist: "Hippocrates",
            signature: "/static/signatures/hippocrates.svg",
            title: "Y tổ với triết lý rèn luyện thân thể để trường thọ",
            image: "/static/images/subjects/gdtc_hippocrates.png",
            portrait: "/static/images/portraits/hippocrates.jpg",
            quote: "Vận động là cội nguồn của sự sống. Thể thao nuôi dưỡng sự bền bỉ của ý chí và tinh thần."
        },
        {
            name: "Quốc phòng - An ninh", icon: "🛡️",
            scientist: "Hồ Chí Minh",
            signature: "/static/signatures/ho_chi_minh.svg",
            title: "Vị lãnh tụ vĩ đại đặt nền móng thế trận quốc phòng toàn dân",
            image: "/static/images/subjects/qp_an_ho_chi_minh.png",
            portrait: "/static/images/portraits/ho_chi_minh.jpg",
            quote: "Các Vua Hùng đã có công dựng nước, Bác cháu ta phải cùng nhau giữ lấy nước."
        }
    ];

    // RENDER SHOWCASE 1 MÔN / 1 HÀNG SO LE VỚI KHUNG CHÈN ANIMATION
    const showcaseContainer = document.getElementById("homeShowcaseList");
    if (showcaseContainer) {
        showcaseContainer.innerHTML = "";
        subjectData.forEach((item, index) => {
            const row = document.createElement("div");
            row.className = "showcase-row";
            row.setAttribute("data-row-index", index);

            // 1. Tạo Card Môn Học
            const card = document.createElement("div");
            card.className = "showcase-card";
            card.onclick = () => openChatForSubject(item.name);

            // Tối ưu LCP & băng thông: 2 thẻ đầu tiên ưu tiên cao, các thẻ sau lazy load & giải mã bất đồng bộ
            const isPriority = index < 2;
            const imgAttrs = isPriority 
                ? 'loading="eager" fetchpriority="high" decoding="async"' 
                : 'loading="lazy" fetchpriority="low" decoding="async"';

            card.innerHTML = `
                <img class="sc-bg-img" src="${item.image}" alt="${item.scientist}" ${imgAttrs} referrerpolicy="no-referrer">
                <div class="sc-overlay"></div>
                <div class="sc-content">
                    <!-- THỨ TỰ 1: CHỮ KÝ CHUẨN CỦA NHÀ BÁC HỌC -->
                    <div class="sc-signature-row">
                        <div class="sc-sig-box">
                            <img class="sc-signature-img" src="${item.signature}" alt="Chữ ký ${item.scientist}" loading="lazy">
                        </div>
                        <div class="sc-scientist-badge">
                            <span class="sc-scientist-name">${item.scientist}</span>
                            <span class="sc-scientist-sub">Danh nhân khoa học</span>
                        </div>
                    </div>

                    <!-- THỨ TỰ 2: CÂU QUOTES CỦA ÔNG -->
                    <div class="sc-quote-area">
                        <p class="sc-quote-headline">“${item.quote}”</p>
                        <div class="sc-marquee-container">
                            <div class="sc-marquee-track">
                                <span class="sc-marquee-item">“${item.quote}”</span>
                                <span class="sc-marquee-sep">✦</span>
                                <span class="sc-marquee-item">${item.scientist}</span>
                                <span class="sc-marquee-sep">✦</span>
                                <span class="sc-marquee-item">“${item.quote}”</span>
                                <span class="sc-marquee-sep">✦</span>
                                <span class="sc-marquee-item">${item.scientist}</span>
                                <span class="sc-marquee-sep">✦</span>
                            </div>
                        </div>
                    </div>

                    <!-- THỨ TỰ 3: TÊN MÔN HỌC & NÚT HÀNH ĐỘNG -->
                    <div class="sc-subject-footer">
                        <div class="sc-subject-title">
                            <span class="sc-subject-icon">${item.icon}</span>
                            <span>${item.name}</span>
                        </div>
                        <button class="sc-nike-btn" onclick="event.stopPropagation(); openChatForSubject('${item.name}')">
                            <span>Khám phá ngay</span>
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                        </button>
                    </div>
                </div>
            `;

            // 2. Tạo Khung Chứa Animation (Slot 0 dành riêng cho Galileo Galilei Toán Học)
            const slot = document.createElement("div");
            slot.id = `animationSlot-${index}`;
            slot.setAttribute("data-subject", item.name);

            if (index === 0) {
                slot.className = "showcase-animation-slot galileo-math-slot";
                slot.onclick = () => openChatForSubject("Toán học");
                slot.innerHTML = `
                    <div class="galileo-stage">
                        <div class="galileo-portrait-layer">
                            <img class="galileo-img-base" src="/static/images/subjects/galileo_portrait.png?v=4" alt="Galileo Galilei" loading="eager" fetchpriority="high">
                            <img class="galileo-img-closed" id="galileoImgClosed" src="/static/images/subjects/galileo_seamless_closed.png?v=4" alt="Galileo Blinking" loading="eager" fetchpriority="high">
                        </div>
                        <div class="galileo-ambient-light"></div>
                        <canvas id="galileoMathCanvas" class="galileo-math-canvas"></canvas>
                    </div>
                `;
            } else if (index === 1) {
                slot.className = "showcase-animation-slot einstein-physics-slot";
                slot.onclick = () => openChatForSubject("Vật lí");
                slot.innerHTML = `
                    <div class="einstein-stage" id="einsteinStage">
                        <div class="einstein-portrait-layer" id="einsteinPortraitLayer">
                            <img class="einstein-img-base" src="/static/images/subjects/einstein_center.png?v=2" alt="Albert Einstein" loading="eager" fetchpriority="high">
                            <img class="einstein-img-look einstein-look-left" id="einsteinImgLookLeft" src="/static/images/subjects/einstein_look_left.png?v=2" alt="Einstein Looking Left" loading="eager" fetchpriority="high">
                            <img class="einstein-img-look einstein-look-right" id="einsteinImgLookRight" src="/static/images/subjects/einstein_look_right.png?v=2" alt="Einstein Looking Right" loading="eager" fetchpriority="high">
                            <img class="einstein-img-closed" id="einsteinImgClosed" src="/static/images/subjects/einstein_closed.png?v=2" alt="Einstein Blinking" loading="eager" fetchpriority="high">
                        </div>
                        <div class="einstein-ambient-light"></div>
                        <canvas id="einsteinPhysicsCanvas" class="einstein-physics-canvas"></canvas>
                    </div>
                `;
            } else {
                // Các môn còn lại: chân dung nhà bác học. Có video thì phát video,
                // không thì dùng ảnh với chuyển động Ken Burns chậm.
                slot.className = "showcase-animation-slot portrait-slot";
                slot.onclick = () => openChatForSubject(item.name);
                // Ảnh riêng cho khung này (item.portrait) để không trùng ảnh của thẻ môn học bên cạnh.
                const anh = item.portrait || item.image;
                const media = item.video
                    ? `<video class="portrait-media" src="${item.video}" autoplay muted loop playsinline
                              preload="metadata" poster="${anh}"></video>`
                    : `<img class="portrait-media" src="${anh}" alt="${item.scientist}" loading="lazy" decoding="async">`;
                slot.innerHTML = `
                    <div class="portrait-stage">
                        ${media}
                        <div class="portrait-veil"></div>
                        <div class="portrait-badge">${item.icon} ${item.name}</div>
                        <div class="portrait-quote">“${item.quote}”</div>
                        <div class="portrait-caption">
                            <div class="portrait-name">${item.scientist}</div>
                            <div class="portrait-role">${item.title}</div>
                            <img class="portrait-signature" src="${item.signature}" alt="Chữ ký ${item.scientist}" loading="lazy">
                        </div>
                    </div>
                `;
            }

            // 3. Xếp SO LE (Zig-zag) và gán hiệu ứng AOS đối xứng
            // index chẵn (0, 2, 4...): Môn học bên TRÁI, Animation bên PHẢI
            // index lẻ (1, 3, 5...): Animation bên TRÁI, Môn học bên PHẢI
            if (index % 2 === 0) {
                card.setAttribute("data-aos", "fade-right");
                slot.setAttribute("data-aos", "fade-left");
                row.appendChild(card);
                row.appendChild(slot);
            } else {
                slot.setAttribute("data-aos", "fade-right");
                card.setAttribute("data-aos", "fade-left");
                row.appendChild(slot);
                row.appendChild(card);
            }

            showcaseContainer.appendChild(row);
        });
    }

    // Tiện ích hỗ trợ người dùng chèn animation vào slot bất kỳ
    window.getAnimationSlot = function(identifier) {
        if (typeof identifier === 'number') {
            return document.getElementById(`animationSlot-${identifier}`);
        }
        return document.querySelector(`.showcase-animation-slot[data-subject="${identifier}"]`);
    };

    // ==========================================
    // AOS (ANIMATE ON SCROLL) ENGINE
    // Chuẩn https://michalsnik.github.io/aos/
    // Lướt xuống hiện lên - lướt qua mất đi (2 chiều)
    // ==========================================
    function initAOS() {
        const viewport = document.querySelector(".main-viewport");
        if (!viewport) return;

        if (window._aosObserver) {
            window._aosObserver.disconnect();
        }

        window._aosObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("aos-animate");
                } else {
                    // Khi lướt qua khỏi tầm nhìn thì tự động mất đi
                    entry.target.classList.remove("aos-animate");
                }
            });
        }, {
            root: viewport,
            rootMargin: "0px 0px -40px 0px",
            threshold: 0.12
        });

        document.querySelectorAll("[data-aos]").forEach(el => window._aosObserver.observe(el));
    }

    initAOS();

    // =========================================================
    // 1. GALILEO BLINKING ENGINE (NHẮM MỞ MẮT TỰ NHIÊN NHƯ NGƯỜI THẬT)
    // =========================================================
    let galileoBlinkTimer = null;

    function initGalileoBlinking() {
        const closedImg = document.getElementById("galileoImgClosed");
        if (!closedImg) return;

        function doBlink() {
            closedImg.classList.add("blink-closed");
            setTimeout(() => {
                closedImg.classList.remove("blink-closed");
                // 28% cơ hội nhấp nháy mắt kép (double blink) tự nhiên
                if (Math.random() < 0.28) {
                    setTimeout(() => {
                        closedImg.classList.add("blink-closed");
                        setTimeout(() => {
                            closedImg.classList.remove("blink-closed");
                        }, 65);
                    }, 160);
                }
            }, 110);
        }

        function scheduleNextBlink() {
            if (galileoBlinkTimer) clearTimeout(galileoBlinkTimer);
            const delay = 2400 + Math.random() * 2800; // ngẫu nhiên 2.4s - 5.2s
            galileoBlinkTimer = setTimeout(() => {
                doBlink();
                scheduleNextBlink();
            }, delay);
        }

        scheduleNextBlink();
    }

    // =========================================================
    // 2. GALILEO MATH 3D CANVAS (CÁC PHƯƠNG TRÌNH TOÁN HỌC BAY LÊN TỰ DO & KHÔNG DÍNH MẶT)
    // =========================================================
    function initGalileoMathCanvas() {
        const canvas = document.getElementById("galileoMathCanvas");
        const container = document.getElementById("animationSlot-0");
        if (!canvas || !container) return;

        const ctx = canvas.getContext("2d");
        let animationFrameId = null;
        let isVisible = true;
        let currentW = 560;
        let currentH = 540;

        function resize() {
            const rect = container.getBoundingClientRect();
            currentW = rect.width || 560;
            currentH = rect.height || 540;
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            canvas.width = currentW * dpr;
            canvas.height = currentH * dpr;
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.scale(dpr, dpr);
        }
        resize();
        window.addEventListener("resize", resize);

        // Danh sách 16 phương trình toán học & vật lý kinh điển liên quan Galileo & Newton & Euler
        const equationsList = [
            "v = g · t",
            "s = ½ g t²",
            "T = 2π√(l/g)",
            "e^(iπ) + 1 = 0",
            "∑ 1/n² = π²/6",
            "x = (-b ± √Δ) / 2a",
            "∫ f(x) dx",
            "∇ × E = -∂B/∂t",
            "a² + b² = c²",
            "lim (sin x)/x = 1",
            "F = m · a",
            "Δs ∝ Δ(t²)",
            "F = G(m₁m₂)/r²",
            "Φ = (1 + √5) / 2",
            "sin²θ + cos²θ = 1",
            "E = m · c²"
        ];

        const rectInit = container.getBoundingClientRect();
        const initW = rectInit.width || 560;
        const initH = rectInit.height || 540;
        const faceRx = 142; // bán kính an toàn vùng mặt (trục ngang)
        const faceRy = 152; // bán kính an toàn vùng mặt (trục dọc)

        // Hàm phân bổ ban đầu cho phương trình ở hai bên mạn sườn
        function createFormula(text, index, total, W, H) {
            const isLeft = index % 2 === 0;
            const cx = W / 2;
            let x;
            if (isLeft) {
                x = 24 + Math.random() * Math.max(30, (cx - faceRx - 44));
            } else {
                x = (cx + faceRx + 24) + Math.random() * Math.max(30, (W - (cx + faceRx + 48)));
            }
            // Khởi tạo rải đều từ dưới lên trên để khi mở trang đã có các công thức bay lượn
            const y = 30 + (index / total) * (H + 30) + Math.random() * 20;
            const vy = 0.72 + (index % 4) * 0.16 + Math.random() * 0.22;
            const scale = 0.88 + (index % 3) * 0.14;
            return {
                text,
                x,
                y,
                vy,
                scale,
                baseAlpha: 0.88 + Math.random() * 0.12,
                wobble: Math.random() * Math.PI * 2,
                wobbleSpeed: 0.014 + Math.random() * 0.012,
                wobbleAmp: 0.38 + Math.random() * 0.32,
                isLeft,
                currentAlpha: 0
            };
        }

        const formulas = equationsList.map((text, i) =>
            createFormula(text, i, equationsList.length, initW, initH)
        );

        // 45 hạt bụi tinh tú / ánh sao vũ trụ bay lên nhẹ nhàng
        const stars = [];
        for (let i = 0; i < 45; i++) {
            stars.push({
                x: Math.random() * initW,
                y: Math.random() * initH,
                vy: 0.35 + Math.random() * 0.65,
                size: 1 + Math.random() * 1.8,
                alpha: 0.25 + Math.random() * 0.65,
                wobble: Math.random() * Math.PI * 2,
                wobbleSpeed: 0.02 + Math.random() * 0.025
            });
        }

        // Tương tác chuột & Hiệu ứng Parallax 3D
        let mouse = { x: -1000, y: -1000, targetX: 0, targetY: 0, currentX: 0, currentY: 0 };

        container.addEventListener("mousemove", (e) => {
            const rect = container.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;
            mouse.targetX = (mouse.x / rect.width - 0.5) * 20;
            mouse.targetY = (mouse.y / rect.height - 0.5) * 15;

            // Nghiêng thẻ 3D sống động
            const rotY = (mouse.x / rect.width - 0.5) * 6;
            const rotX = -(mouse.y / rect.height - 0.5) * 6;
            container.style.transform = `perspective(1000px) rotateY(${rotY}deg) rotateX(${rotX}deg) translateY(-4px) scale(1.01)`;
        });

        container.addEventListener("mouseleave", () => {
            mouse.x = -1000;
            mouse.y = -1000;
            mouse.targetX = 0;
            mouse.targetY = 0;
            container.style.transform = "";
        });

        // Vòng lặp Render 60 FPS
        function render(timestamp) {
            if (!isVisible) {
                animationFrameId = null;
                return;
            }
            const W = currentW;
            const H = currentH;

            ctx.clearRect(0, 0, W, H);

            // Tọa độ tâm quanh đầu Galileo (38% chiều cao)
            mouse.currentX += (mouse.targetX - mouse.currentX) * 0.08;
            mouse.currentY += (mouse.targetY - mouse.currentY) * 0.08;
            const cx = W / 2 + mouse.currentX;
            const cy = H * 0.38 + mouse.currentY;

            // 1. Vẽ các hạt bụi ánh sáng vàng ấm bay lượn lên trên (tinh giản để giữ trọn vẹn 60 FPS)
            stars.forEach(s => {
                s.y -= s.vy;
                s.wobble += s.wobbleSpeed;
                s.x += Math.sin(s.wobble) * 0.28;

                // Tái sinh hạt bụi khi bay lên đỉnh
                if (s.y < -10) {
                    s.y = H + 10 + Math.random() * 20;
                    s.x = Math.random() * W;
                }

                // Giảm mật độ bụi ngay giữa mặt
                const dxFace = s.x - cx;
                const dyFace = s.y - cy;
                const distFaceNorm = Math.sqrt((dxFace / faceRx) * (dxFace / faceRx) + (dyFace / faceRy) * (dyFace / faceRy));
                let starFaceFade = 1;
                if (distFaceNorm < 0.9) {
                    starFaceFade = Math.max(0, (distFaceNorm - 0.5) / 0.4);
                }

                const starAlpha = s.alpha * starFaceFade * Math.min(1, Math.max(0, s.y / (H * 0.3)));
                if (starAlpha > 0.05) {
                    ctx.beginPath();
                    ctx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
                    ctx.fillStyle = `rgba(255, 225, 150, ${starAlpha})`;
                    ctx.fill();
                }
            });

            // 2. Cập nhật quỹ đạo bay lên và vùng cấm dính mặt của Galileo
            formulas.forEach(f => {
                // Bay lên trên (vy)
                f.y -= f.vy;
                f.wobble += f.wobbleSpeed;
                f.x += Math.sin(f.wobble) * f.wobbleAmp;

                // Tương tác đẩy nhẹ từ con trỏ chuột
                if (mouse.x > 0) {
                    const mdx = f.x - mouse.x;
                    const mdy = f.y - mouse.y;
                    const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
                    if (mDist < 85 && mDist > 0) {
                        const mForce = (85 - mDist) / 85;
                        f.x += (mdx / mDist) * mForce * 8;
                        f.y += (mdy / mDist) * mForce * 5;
                    }
                }

                // VÙNG TRÁNH MẶT GALILEO (ĐỘNG LỰC HỌC TỰ NHIÊN - KHÔNG BAO GIỜ DÍNH MẶT)
                const dx = f.x - cx;
                const dy = f.y - cy;
                const normDist = Math.sqrt(Math.pow(dx / faceRx, 2) + Math.pow(dy / faceRy, 2));

                // Nếu tiến vào gần elip khuôn mặt, tạo lực đẩy dạt sang 2 bên
                if (normDist < 1.25) {
                    const repulse = (1.25 - normDist) / 1.25;
                    if (dx >= 0) {
                        f.x += repulse * 3.6;
                    } else {
                        f.x -= repulse * 3.6;
                    }
                }

                // Độ trong suốt tránh mặt tuyệt đối (Face Exclusion Mask)
                let faceAlpha = 1;
                if (normDist < 1.15) {
                    // Càng vào sát mặt thì mờ dần và triệt tiêu hoàn toàn về 0
                    faceAlpha = Math.max(0, (normDist - 0.78) / 0.37);
                }

                // Hiệu ứng bay lên dần rõ, lên đỉnh mờ dần rồi biến mất (Fade in & Fade out)
                let altitudeFade = 1;
                if (f.y > H - 75) {
                    // Mới xuất hiện từ dưới đáy: hiện dần
                    altitudeFade = Math.max(0, (H - f.y) / 75);
                } else if (f.y < H * 0.38) {
                    // Bay lên nửa trên: mờ dần và biến mất hẳn khi lên tới đỉnh
                    altitudeFade = Math.max(0, (f.y - 15) / (H * 0.38 - 15));
                }

                f.currentAlpha = f.baseAlpha * faceAlpha * altitudeFade;

                // Tái sinh phương trình khi đã bay lên hết đỉnh hoặc đã biến mất hoàn toàn
                if (f.y <= 15 || (f.currentAlpha <= 0.01 && f.y < H * 0.32)) {
                    f.y = H + 25 + Math.random() * 50;
                    const spawnLeft = Math.random() > 0.5;
                    f.isLeft = spawnLeft;
                    if (spawnLeft) {
                        f.x = 24 + Math.random() * Math.max(30, (cx - faceRx - 44));
                    } else {
                        f.x = (cx + faceRx + 24) + Math.random() * Math.max(30, (W - (cx + faceRx + 48)));
                    }
                    f.vy = 0.72 + Math.random() * 0.65;
                    f.wobble = Math.random() * Math.PI * 2;
                }
            });

            // 3. Vẽ các phương trình phát sáng vàng ánh kim (Golden Amber Glow)
            formulas.forEach(f => {
                if (f.currentAlpha <= 0.02) return;

                const alpha = Math.max(0, Math.min(1, f.currentAlpha));
                const scale = f.scale;

                ctx.save();
                ctx.font = `600 ${Math.round(13.5 * scale)}px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, serif`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";

                const metrics = ctx.measureText(f.text);
                const textWidth = metrics.width;
                const textHeight = 18 * scale;

                // Nền kính mờ amber bảo vệ chữ sắc nét trên nền tranh tối
                ctx.fillStyle = `rgba(18, 9, 4, ${alpha * 0.65})`;
                ctx.strokeStyle = `rgba(212, 163, 115, ${alpha * 0.4})`;
                ctx.lineWidth = 1;

                const padX = 10 * scale;
                const padY = 5 * scale;
                ctx.beginPath();
                if (ctx.roundRect) {
                    ctx.roundRect(
                        f.x - textWidth / 2 - padX,
                        f.y - textHeight / 2 - padY,
                        textWidth + padX * 2,
                        textHeight + padY * 2,
                        7 * scale
                    );
                } else {
                    ctx.rect(
                        f.x - textWidth / 2 - padX,
                        f.y - textHeight / 2 - padY,
                        textWidth + padX * 2,
                        textHeight + padY * 2
                    );
                }
                ctx.fill();
                ctx.stroke();

                // Chữ phát sáng vàng ánh kim (tự động tắt bóng mờ Gaussian khi đang cuộn trang để bảo đảm 50-60 FPS)
                if (!isSnapScrolling) {
                    ctx.shadowColor = `rgba(255, 215, 110, ${alpha * 0.85})`;
                    ctx.shadowBlur = Math.round(8 * scale);
                } else {
                    ctx.shadowBlur = 0;
                }
                ctx.fillStyle = `rgba(255, 242, 210, ${alpha})`;
                ctx.fillText(f.text, f.x, f.y);

                ctx.restore();
            });

            animationFrameId = requestAnimationFrame(render);
        }

        animationFrameId = requestAnimationFrame(render);

        // Tự động tạm dừng Canvas khi không nằm trong khung nhìn để tiết kiệm 100% pin & GPU
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                isVisible = entry.isIntersecting;
                if (isVisible && !animationFrameId) {
                    animationFrameId = requestAnimationFrame(render);
                }
            });
        }, { root: document.querySelector(".main-viewport"), threshold: 0.08 });
        observer.observe(container);
    }

    // =========================================================
    // 2B. EINSTEIN LOOKING AROUND & BLINKING ENGINE
    // =========================================================
    function initEinsteinLookingAround() {
        const lookLeft = document.getElementById("einsteinImgLookLeft");
        const lookRight = document.getElementById("einsteinImgLookRight");
        const closed = document.getElementById("einsteinImgClosed");
        const stage = document.getElementById("einsteinStage");

        if (!lookLeft || !lookRight || !closed) return;

        let gazeState = 'center';
        let gazeTimeout = null;
        let isUserHovering = false;
        let hoverResetTimer = null;

        function setGaze(direction) {
            gazeState = direction;
            if (direction === 'left') {
                lookLeft.style.opacity = '1';
                lookRight.style.opacity = '0';
            } else if (direction === 'right') {
                lookLeft.style.opacity = '0';
                lookRight.style.opacity = '1';
            } else {
                lookLeft.style.opacity = '0';
                lookRight.style.opacity = '0';
            }
        }

        function scheduleNextGaze() {
            if (isUserHovering) return;

            const candidates = ['left', 'right', 'center', 'center'].filter(c => c !== gazeState);
            const chosen = candidates[Math.floor(Math.random() * candidates.length)] || 'center';
            setGaze(chosen);

            const duration = 2000 + Math.random() * 2200;
            gazeTimeout = setTimeout(scheduleNextGaze, duration);
        }

        function doBlink() {
            closed.classList.add("blink-closed");
            setTimeout(() => {
                closed.classList.remove("blink-closed");
                if (Math.random() < 0.28) {
                    setTimeout(() => {
                        closed.classList.add("blink-closed");
                        setTimeout(() => closed.classList.remove("blink-closed"), 85);
                    }, 130);
                }
            }, 110);
        }

        function scheduleNextBlink() {
            const delay = 2600 + Math.random() * 2800;
            setTimeout(() => {
                doBlink();
                scheduleNextBlink();
            }, delay);
        }

        if (stage) {
            stage.addEventListener("mousemove", (e) => {
                isUserHovering = true;
                clearTimeout(hoverResetTimer);
                clearTimeout(gazeTimeout);

                const rect = stage.getBoundingClientRect();
                const relX = (e.clientX - rect.left) / rect.width;

                if (relX < 0.42) {
                    setGaze('left');
                } else if (relX > 0.58) {
                    setGaze('right');
                } else {
                    setGaze('center');
                }

                hoverResetTimer = setTimeout(() => {
                    isUserHovering = false;
                    scheduleNextGaze();
                }, 2200);
            });

            stage.addEventListener("mouseleave", () => {
                hoverResetTimer = setTimeout(() => {
                    isUserHovering = false;
                    scheduleNextGaze();
                }, 1000);
            });
        }

        scheduleNextGaze();
        scheduleNextBlink();
    }

    // =========================================================
    // 2C. EINSTEIN PHYSICS 3D CANVAS (CÁC PHƯƠNG TRÌNH VẬT LÝ VÀ HẠT LƯỢNG TỬ VŨ TRỤ)
    // =========================================================
    function initEinsteinPhysicsCanvas() {
        const canvas = document.getElementById("einsteinPhysicsCanvas");
        const container = document.getElementById("animationSlot-1");
        if (!canvas || !container) return;

        const ctx = canvas.getContext("2d");
        let animationFrameId = null;
        let isVisible = true;
        let currentW = 560;
        let currentH = 540;

        function resize() {
            const rect = container.getBoundingClientRect();
            currentW = rect.width || 560;
            currentH = rect.height || 540;
            const dpr = Math.min(window.devicePixelRatio || 1, 2);
            canvas.width = currentW * dpr;
            canvas.height = currentH * dpr;
            ctx.setTransform(1, 0, 0, 1, 0, 0);
            ctx.scale(dpr, dpr);
        }
        resize();
        window.addEventListener("resize", resize);

        const equationsList = [
            "E = m · c²",
            "F = dp / dt",
            "λ = h / p",
            "R_μν - ½Rg_μν = κT_μν",
            "Δx · Δp ≥ ℏ / 2",
            "γ = 1 / √(1 - v²/c²)",
            "E = h · ν",
            "c = 299,792,458 m/s",
            "ds² = -c²dt² + dx² + dy² + dz²",
            "p = γ · m · v",
            "S = k · ln(Ω)",
            "L = T - V",
            "∇ · B = 0",
            "G = 6.674 × 10⁻¹¹",
            "ħ = 1.054 × 10⁻³⁴",
            "e^(-iHt/ℏ)"
        ];

        const rectInit = container.getBoundingClientRect();
        const initW = rectInit.width || 560;
        const initH = rectInit.height || 540;
        const faceRx = 145;
        const faceRy = 152;

        function createFormula(text, index, total, W, H) {
            const isLeft = index % 2 === 0;
            const cx = W / 2;
            let x;
            if (isLeft) {
                x = 24 + Math.random() * Math.max(30, (cx - faceRx - 44));
            } else {
                x = (cx + faceRx + 24) + Math.random() * Math.max(30, (W - (cx + faceRx + 48)));
            }
            const y = 30 + (index / total) * (H + 30) + Math.random() * 20;
            const vy = 0.70 + (index % 4) * 0.16 + Math.random() * 0.22;
            const scale = 0.88 + (index % 3) * 0.14;
            return {
                text,
                x,
                y,
                vy,
                scale,
                baseAlpha: 0.90 + Math.random() * 0.10,
                wobble: Math.random() * Math.PI * 2,
                wobbleSpeed: 0.013 + Math.random() * 0.012,
                wobbleAmp: 0.36 + Math.random() * 0.32,
                isLeft,
                currentAlpha: 0
            };
        }

        const formulas = equationsList.map((text, i) =>
            createFormula(text, i, equationsList.length, initW, initH)
        );

        const particles = [];
        for (let i = 0; i < 48; i++) {
            particles.push({
                x: Math.random() * initW,
                y: Math.random() * initH,
                vy: 0.32 + Math.random() * 0.65,
                size: 0.9 + Math.random() * 1.8,
                alpha: 0.25 + Math.random() * 0.65,
                wobble: Math.random() * Math.PI * 2,
                wobbleSpeed: 0.02 + Math.random() * 0.025,
                isCyan: Math.random() < 0.4
            });
        }

        let mouse = { x: -1000, y: -1000, targetX: 0, targetY: 0, currentX: 0, currentY: 0 };

        container.addEventListener("mousemove", (e) => {
            const rect = container.getBoundingClientRect();
            mouse.x = e.clientX - rect.left;
            mouse.y = e.clientY - rect.top;
            mouse.targetX = (mouse.x / rect.width - 0.5) * 20;
            mouse.targetY = (mouse.y / rect.height - 0.5) * 15;

            const rotY = (mouse.x / rect.width - 0.5) * 6;
            const rotX = -(mouse.y / rect.height - 0.5) * 6;
            container.style.transform = `perspective(1000px) rotateY(${rotY}deg) rotateX(${rotX}deg) translateY(-4px) scale(1.01)`;
        });

        container.addEventListener("mouseleave", () => {
            mouse.x = -1000;
            mouse.y = -1000;
            mouse.targetX = 0;
            mouse.targetY = 0;
            container.style.transform = "";
        });

        function render() {
            if (!isVisible) {
                animationFrameId = null;
                return;
            }
            const W = currentW;
            const H = currentH;

            ctx.clearRect(0, 0, W, H);

            mouse.currentX += (mouse.targetX - mouse.currentX) * 0.08;
            mouse.currentY += (mouse.targetY - mouse.currentY) * 0.08;
            const cx = W / 2 + mouse.currentX;
            const cy = H * 0.38 + mouse.currentY;

            particles.forEach(p => {
                p.y -= p.vy;
                p.wobble += p.wobbleSpeed;
                p.x += Math.sin(p.wobble) * 0.28;

                if (p.y < -10) {
                    p.y = H + 10 + Math.random() * 20;
                    p.x = Math.random() * W;
                }

                const dxFace = p.x - cx;
                const dyFace = p.y - cy;
                const distFaceNorm = Math.sqrt((dxFace / faceRx) * (dxFace / faceRx) + (dyFace / faceRy) * (dyFace / faceRy));
                let particleFaceFade = 1;
                if (distFaceNorm < 0.9) {
                    particleFaceFade = Math.max(0, (distFaceNorm - 0.5) / 0.4);
                }

                const pAlpha = p.alpha * particleFaceFade * Math.min(1, Math.max(0, p.y / (H * 0.3)));
                if (pAlpha > 0.05) {
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                    ctx.fillStyle = p.isCyan ? `rgba(56, 189, 248, ${pAlpha})` : `rgba(255, 255, 255, ${pAlpha})`;
                    ctx.fill();
                }
            });

            formulas.forEach(f => {
                f.y -= f.vy;
                f.wobble += f.wobbleSpeed;
                f.x += Math.sin(f.wobble) * f.wobbleAmp;

                if (mouse.x > 0) {
                    const mdx = f.x - mouse.x;
                    const mdy = f.y - mouse.y;
                    const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
                    if (mDist < 85 && mDist > 0) {
                        const mForce = (85 - mDist) / 85;
                        f.x += (mdx / mDist) * mForce * 8;
                        f.y += (mdy / mDist) * mForce * 5;
                    }
                }

                const dx = f.x - cx;
                const dy = f.y - cy;
                const normDist = Math.sqrt(Math.pow(dx / faceRx, 2) + Math.pow(dy / faceRy, 2));

                if (normDist < 1.25) {
                    const repulse = (1.25 - normDist) / 1.25;
                    if (dx >= 0) {
                        f.x += repulse * 3.6;
                    } else {
                        f.x -= repulse * 3.6;
                    }
                }

                let faceAlpha = 1;
                if (normDist < 1.15) {
                    faceAlpha = Math.max(0, (normDist - 0.78) / 0.37);
                }

                let edgeFade = 1;
                if (f.y < H * 0.2) {
                    edgeFade = Math.max(0, f.y / (H * 0.2));
                } else if (f.y > H * 0.85) {
                    edgeFade = Math.max(0, (H - f.y) / (H * 0.15));
                }

                f.currentAlpha = f.baseAlpha * edgeFade * faceAlpha;

                if (f.y < -35) {
                    f.y = H + 30 + Math.random() * 40;
                    if (f.isLeft) {
                        f.x = 24 + Math.random() * Math.max(30, (cx - faceRx - 44));
                    } else {
                        f.x = (cx + faceRx + 24) + Math.random() * Math.max(30, (W - (cx + faceRx + 48)));
                    }
                }

                if (f.currentAlpha > 0.03) {
                    ctx.save();
                    const fontSize = Math.round(14 * f.scale);
                    ctx.font = `italic 600 ${fontSize}px "SF Pro Display", -apple-system, "Segoe UI", sans-serif`;
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";

                    ctx.shadowColor = "rgba(255, 255, 255, 0.45)";
                    ctx.shadowBlur = 8;
                    ctx.fillStyle = `rgba(240, 246, 255, ${f.currentAlpha * 0.95})`;

                    ctx.fillText(f.text, f.x, f.y);
                    ctx.restore();
                }
            });

            animationFrameId = requestAnimationFrame(render);
        }

        const animObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    if (!isVisible) {
                        isVisible = true;
                        if (!animationFrameId) render();
                    }
                } else {
                    isVisible = false;
                }
            });
        }, { root: document.querySelector(".main-viewport"), threshold: 0.08 });
        animObserver.observe(container);

        render();
    }

    // =========================================================
    // 3. FULLPAGE SECTION SCROLL SNAPPING & DOT NAVIGATION
    // LƯỚT CHUỘT THEO TỪNG TRANG RỜI VÀ ĐIỀU HƯỚNG DẠNG CHẤM
    // =========================================================
    let currentSnapIndex = 0;
    let isSnapScrolling = false;
    let snapCooldownTimer = null;
    let wheelAccumulator = 0;
    let wheelCooldownTimer = null;

    function getSnapSections() {
        const hero = document.getElementById("heroSnapSection");
        const rows = Array.from(document.querySelectorAll("#homeShowcaseList .showcase-row"));
        const all = [];
        if (hero) all.push(hero);
        all.push(...rows);
        return all;
    }

    window.scrollToSnapIndex = function(index, smooth = true) {
        const sections = getSnapSections();
        if (sections.length === 0) return;

        if (index < 0) index = 0;
        if (index >= sections.length) index = sections.length - 1;

        currentSnapIndex = index;
        const target = sections[index];
        if (!target) return;

        const viewport = document.querySelector('.main-viewport');
        if (!viewport) return;

        isSnapScrolling = true;

        // Vô hiệu hóa tạm thời scroll-snap để triệt tiêu hoàn toàn xung đột vật lý giữa CSS Snap và JS Smooth Scroll
        viewport.style.scrollSnapType = 'none';

        let targetScrollTop = 0;
        if (index === 0) {
            targetScrollTop = 0;
        } else {
            const viewRect = viewport.getBoundingClientRect();
            const targetRect = target.getBoundingClientRect();
            const targetCenterRel = (targetRect.top - viewRect.top) + targetRect.height / 2;
            const viewCenter = viewRect.height / 2;
            const delta = targetCenterRel - viewCenter;
            targetScrollTop = Math.max(0, Math.round(viewport.scrollTop + delta));
        }

        viewport.scrollTo({
            top: targetScrollTop,
            behavior: smooth ? 'smooth' : 'auto'
        });

        updateDotNav(index);

        // ĐỔI MÀU NỀN:
        // Index 1: Toán học (Galileo) -> màu nâu đậm Baroque
        // Index 2: Vật lí (Einstein) -> MÀU ĐEN TUYỆT ĐỐI (PITCH BLACK)
        if (index === 1) {
            document.body.classList.add("theme-galileo-active");
            document.body.classList.remove("theme-einstein-active");
        } else if (index === 2) {
            document.body.classList.remove("theme-galileo-active");
            document.body.classList.add("theme-einstein-active");
        } else {
            document.body.classList.remove("theme-galileo-active");
            document.body.classList.remove("theme-einstein-active");
        }

        clearTimeout(snapCooldownTimer);
        snapCooldownTimer = setTimeout(() => {
            viewport.style.scrollSnapType = 'y mandatory';
            isSnapScrolling = false;
        }, 550);
    };

    function updateDotNav(index) {
        const items = document.querySelectorAll(".dot-nav-item");
        items.forEach((item, idx) => {
            if (idx === index) {
                item.classList.add("active");
            } else {
                item.classList.remove("active");
            }
        });
    }

    function renderDotNav() {
        const nav = document.getElementById("fullpageDotNav");
        if (!nav) return;
        nav.innerHTML = "";

        // Chấm 0: Chào mừng VuongEdu
        const heroDot = document.createElement("div");
        heroDot.className = "dot-nav-item active";
        heroDot.setAttribute("data-index", "0");
        heroDot.onclick = () => window.scrollToSnapIndex(0);
        heroDot.innerHTML = `
            <span class="dot-label">✨ Chào Mừng VuongEdu</span>
            <span class="dot-indicator"></span>
        `;
        nav.appendChild(heroDot);

        // Các chấm cho 13 môn học
        subjectData.forEach((sub, idx) => {
            const pageIdx = idx + 1;
            const dot = document.createElement("div");
            dot.className = "dot-nav-item";
            dot.setAttribute("data-index", pageIdx);
            dot.onclick = () => window.scrollToSnapIndex(pageIdx);
            dot.innerHTML = `
                <span class="dot-label">${sub.icon} ${sub.name} • ${sub.scientist}</span>
                <span class="dot-indicator"></span>
            `;
            nav.appendChild(dot);
        });
    }

    function initFullpageScrollAndDots() {
        const viewport = document.querySelector('.main-viewport');
        if (!viewport) return;

        renderDotNav();

        // 1. BẮT SỰ KIỆN CUỘN CHUỘT (WHEEL): LƯỚT 1 PHẦN LÀ QUA ĐÚNG 1 TRANG
        viewport.addEventListener('wheel', (e) => {
            const homeView = document.getElementById("view-home");
            if (!homeView || !homeView.classList.contains("active")) return;

            // Bỏ qua nếu người dùng đang cuộn trong khung chat hoặc form
            if (e.target.closest('#chatMessages') || e.target.closest('#sidebarPromptList') || e.target.closest('.wtf-card-form') || e.target.closest('textarea')) {
                return;
            }

            e.preventDefault();

            if (isSnapScrolling) return;

            wheelAccumulator += e.deltaY;
            clearTimeout(wheelCooldownTimer);
            wheelCooldownTimer = setTimeout(() => {
                wheelAccumulator = 0;
            }, 180);

            // Ngưỡng phát hiện cuộn chuột
            if (Math.abs(wheelAccumulator) >= 25) {
                const sections = getSnapSections();
                if (wheelAccumulator > 0) {
                    if (currentSnapIndex < sections.length - 1) {
                        window.scrollToSnapIndex(currentSnapIndex + 1);
                    }
                } else {
                    if (currentSnapIndex > 0) {
                        window.scrollToSnapIndex(currentSnapIndex - 1);
                    }
                }
                wheelAccumulator = 0;
            }
        }, { passive: false });

        // 2. PHÍM MŨI TÊN & PHÍM SPACE ĐIỀU HƯỚNG TRANG
        window.addEventListener('keydown', (e) => {
            const homeView = document.getElementById("view-home");
            if (!homeView || !homeView.classList.contains("active")) return;

            if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) {
                return;
            }

            const sections = getSnapSections();
            if (e.key === 'ArrowDown' || e.key === 'PageDown' || (e.key === ' ' && !e.shiftKey)) {
                e.preventDefault();
                if (currentSnapIndex < sections.length - 1) {
                    window.scrollToSnapIndex(currentSnapIndex + 1);
                }
            } else if (e.key === 'ArrowUp' || e.key === 'PageUp' || (e.key === ' ' && e.shiftKey)) {
                e.preventDefault();
                if (currentSnapIndex > 0) {
                    window.scrollToSnapIndex(currentSnapIndex - 1);
                }
            } else if (e.key === 'Home') {
                e.preventDefault();
                window.scrollToSnapIndex(0);
            } else if (e.key === 'End') {
                e.preventDefault();
                window.scrollToSnapIndex(sections.length - 1);
            }
        });

        // 3. VUỐT MÀN HÌNH TRÊN THIẾT BỊ DI ĐỘNG / CẢM ỨNG
        let touchStartY = 0;
        viewport.addEventListener('touchstart', (e) => {
            if (e.touches && e.touches.length > 0) {
                touchStartY = e.touches[0].clientY;
            }
        }, { passive: true });

        viewport.addEventListener('touchend', (e) => {
            const homeView = document.getElementById("view-home");
            if (!homeView || !homeView.classList.contains("active")) return;

            if (e.changedTouches && e.changedTouches.length > 0) {
                const touchEndY = e.changedTouches[0].clientY;
                const diff = touchStartY - touchEndY;
                const sections = getSnapSections();
                if (Math.abs(diff) >= 40 && !isSnapScrolling) {
                    if (diff > 0 && currentSnapIndex < sections.length - 1) {
                        window.scrollToSnapIndex(currentSnapIndex + 1);
                    } else if (diff < 0 && currentSnapIndex > 0) {
                        window.scrollToSnapIndex(currentSnapIndex - 1);
                    }
                }
            }
        }, { passive: true });

        // 4. THEO DÕI VỊ TRÍ TRUNG TÂM (INTERSECTION OBSERVER) ĐỂ ĐỒNG BỘ CHẤM & MÀU NỀN NẾU KÉO THANH CUỘN
        const snapObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
                    const sections = getSnapSections();
                    const idx = sections.indexOf(entry.target);
                    if (idx !== -1 && !isSnapScrolling) {
                        currentSnapIndex = idx;
                        updateDotNav(idx);
                        if (idx === 1) {
                            document.body.classList.add("theme-galileo-active");
                            document.body.classList.remove("theme-einstein-active");
                        } else if (idx === 2) {
                            document.body.classList.remove("theme-galileo-active");
                            document.body.classList.add("theme-einstein-active");
                        } else {
                            document.body.classList.remove("theme-galileo-active");
                            document.body.classList.remove("theme-einstein-active");
                        }
                    }
                }
            });
        }, {
            root: viewport,
            threshold: [0.5]
        });

        getSnapSections().forEach(sec => snapObserver.observe(sec));
    }

    // Kích hoạt toàn bộ hệ thống động lực học Galileo, Einstein & Điều hướng trang
    initGalileoBlinking();
    initGalileoMathCanvas();
    initEinsteinLookingAround();
    initEinsteinPhysicsCanvas();
    initFullpageScrollAndDots();


    // CHỌN KHỐI LỚP (TỪ LỚP 1 TỚI LỚP 12)
    let currentSelectedGrade = parseInt(localStorage.getItem("eduvie_selected_grade")) || 1;

    // Phân bổ môn học tương ứng theo từng khối lớp
    const gradeSubjectMap = {
        1: [
            "Toán",
            "Tiếng Việt",
            "Tiếng Anh"
        ],
        2: [
            "Toán",
            "Tiếng Việt",
            "Tiếng Anh",
            "Tự Nhiên Và Xã Hội",
            "Hoạt Động Trải Nghiệm"
        ],
        3: [
            "Toán",
            "Tiếng Việt",
            "Tiếng Anh",
            "Đạo Đức",
            "Công Nghệ",
            "Tin Học",
            "Hoạt Động Trải Nghiệm"
        ],
        4: [
            "Toán",
            "Tiếng Việt",
            "Tiếng Anh",
            "Đạo Đức",
            "Lịch Sử",
            "Địa Lí",
            "Tin Học",
            "Công Nghệ",
            "Hoạt Động Trải Nghiệm"
        ],
        5: [
            "Toán",
            "Tiếng Việt",
            "Tiếng Anh",
            "Đạo Đức",
            "Lịch Sử",
            "Địa Lí",
            "Tin Học",
            "Công Nghệ",
            "Hoạt Động Trải Nghiệm"
        ]
    };

    const specialSubjectDefinitions = {
        "toán": {
            name: "Toán",
            icon: "📐",
            scientist: "Galileo Galilei",
            image: "/static/images/subjects/toan_galileo.jpg"
        },
        "tiếng việt": {
            name: "Tiếng Việt",
            icon: "✍️",
            scientist: "Lev Tolstoy",
            image: "/static/images/subjects/ngu_van_tolstoy.png"
        },
        "tự nhiên và xã hội": {
            name: "Tự Nhiên Và Xã Hội",
            icon: "🌿",
            scientist: "Charles Darwin",
            image: "/static/images/subjects/sinh_hoc_darwin.png"
        },
        "hoạt động trải nghiệm": {
            name: "Hoạt Động Trải Nghiệm",
            icon: "🎒",
            scientist: "Kỹ năng sống & Hoạt động thực tế",
            image: "/static/images/subjects/gdtc_hippocrates.png"
        },
        "đạo đức": {
            name: "Đạo Đức",
            icon: "🌱",
            scientist: "Socrates",
            image: "/static/images/subjects/gdcd_socrates.png"
        },
        "lịch sử": {
            name: "Lịch Sử",
            icon: "📜",
            scientist: "Herodotus",
            image: "/static/images/subjects/lich_su_herodotus.jpg"
        },
        "địa lí": {
            name: "Địa Lí",
            icon: "🗺️",
            scientist: "Alexander von Humboldt",
            image: "/static/images/subjects/dia_li_humboldt.jpg"
        },
        "công nghệ": {
            name: "Công Nghệ",
            icon: "⚙️",
            scientist: "Nikola Tesla",
            image: "/static/images/subjects/cong_nghe_tesla.jpg"
        },
        "tin học": {
            name: "Tin Học",
            icon: "💻",
            scientist: "Alan Turing",
            image: "/static/images/subjects/tin_hoc_turing.png"
        },
        "tiếng anh": {
            name: "Tiếng Anh",
            icon: "🌐",
            scientist: "William Shakespeare",
            image: "/static/images/subjects/tieng_anh_shakespeare.jpg"
        }
    };

    function getSubjectInfo(name) {
        const key = name.trim().toLowerCase();
        if (specialSubjectDefinitions[key]) {
            return specialSubjectDefinitions[key];
        }
        return subjectData.find(s => s.name.toLowerCase() === key) || {
            name: name,
            icon: "📚",
            scientist: "VuongEdu"
        };
    }

    // Render danh sách môn học theo khối lớp đang chọn
    function renderLobbySubjects(gradeNum) {
        const lobby = document.getElementById("lobbySubjects");
        if (!lobby) return;
        lobby.innerHTML = "";

        const subjects = gradeSubjectMap[gradeNum]
            ? gradeSubjectMap[gradeNum].map(getSubjectInfo)
            : subjectData;

        subjects.forEach(s => {
            const card = document.createElement("div");
            card.className = "subject-card";
            card.innerHTML = `
                <div class="sub-icon">${s.icon}</div>
                <div class="sub-name">${s.name}</div>
                <div class="sub-desc">${s.scientist}</div>
            `;
            card.onclick = () => openChatForSubject(s.name);
            lobby.appendChild(card);
        });
    }

    function initGradeSelection() {
        const boxes = document.querySelectorAll(".grade-box");
        boxes.forEach((box, idx) => {
            const gNum = idx + 1;
            if (gNum === currentSelectedGrade) {
                box.classList.add("active");
            } else {
                box.classList.remove("active");
            }
        });
        renderLobbySubjects(currentSelectedGrade);
    }

    function selectGrade(gradeNum, btnElement) {
        currentSelectedGrade = gradeNum;
        localStorage.setItem("eduvie_selected_grade", gradeNum);
        document.querySelectorAll(".grade-box").forEach(b => b.classList.remove("active"));
        if (btnElement) {
            btnElement.classList.add("active");
        }
        renderLobbySubjects(gradeNum);
    }

    initGradeSelection();

    function openChatForSubject(subjName) {
        const chatNavBtn = document.querySelector('button[onclick*="\'chat\'"]');
        switchTab('chat', chatNavBtn);
        document.getElementById("chatSubjectBadge").innerText = `Môn: ${subjName} - Lớp ${currentSelectedGrade}`;
        document.getElementById("userInput").value = `Hướng dẫn cho em tài liệu ôn tập và kiến thức trọng tâm môn ${subjName} lớp ${currentSelectedGrade}`;
        document.getElementById("userInput").focus();
    }

    function switchTab(viewId, btnElement) {
        document.querySelectorAll(".view-section").forEach(sec => sec.classList.remove("active"));
        document.querySelectorAll(".nav-item").forEach(btn => btn.classList.remove("active"));
        
        document.getElementById(`view-${viewId}`).classList.add("active");
        if (btnElement) btnElement.classList.add("active");

        const dotNav = document.getElementById("fullpageDotNav");
        if (dotNav) {
            dotNav.style.display = (viewId === 'home') ? 'flex' : 'none';
        }

        const viewport = document.querySelector(".main-viewport");
        if (viewport) {
            viewport.scrollTop = 0;
            viewport.style.scrollSnapType = (viewId === 'home') ? 'y mandatory' : 'none';
        }

        if (viewId !== 'home') {
            document.body.classList.remove("theme-galileo-active");
            document.body.classList.remove("theme-einstein-active");
            currentSnapIndex = 0;
        } else {
            if (typeof updateDotNav === 'function') {
                updateDotNav(0);
            }
        }

        if (typeof window.checkGlobeVisibility === 'function') {
            window.checkGlobeVisibility();
        }

        if (viewId === 'home' && typeof window.resizeGlobe3D === 'function') {
            setTimeout(window.resizeGlobe3D, 50);
        }

        if (typeof initAOS === 'function') {
            setTimeout(initAOS, 60);
        }
    }

    /* Tự động chuyển đến tab Hỏi Bài (Flask-WTF) khi người dùng vừa gửi form hoặc có lỗi validate */
    /* khối Flask-WTF cũ đã bỏ: form nay gọi REST API */

    function handleWtfSubmit() {
        const btn = document.querySelector(".wtf-btn-primary");
        if (btn) {
            btn.value = "⏳ VuongEdu đang soạn thư & gửi...";
            btn.style.opacity = "0.75";
            btn.style.pointerEvents = "none";
        }
    }

    function toggleSidebarSlide(e) {
        if (e) e.stopPropagation();
        const body = document.body;
        body.classList.toggle("sidebar-closed");
        const isClosed = body.classList.contains("sidebar-closed");

        try {
            localStorage.setItem("eduvie_sidebar_closed", isClosed ? "true" : "false");
        } catch (err) {}

        if (typeof window.resizeGlobe3D === 'function') {
            setTimeout(window.resizeGlobe3D, 360);
        }
    }

    // Khôi phục trạng thái đóng/mở sidebar từ bộ nhớ trình duyệt
    try {
        if (localStorage.getItem("eduvie_sidebar_closed") === "true") {
            document.body.classList.add("sidebar-closed");
        }
    } catch (e) {}



    // Theme Toggle
    const html = document.documentElement;
    function applyTheme(theme) {
        const logoImg = document.getElementById("appBrandLogo");
        const favIcon = document.getElementById("appFavicon");
        const appleIcon = document.getElementById("appAppleIcon");

        if (theme === "dark") {
            html.setAttribute("data-theme", "dark");
            document.getElementById("tIcon").innerText = "🌙";
            document.getElementById("tLabel").innerText = "Chế độ Tối";
            localStorage.setItem("claugpt_theme", "dark");
            if (logoImg) logoImg.src = "/static/images/logo-dark-v2.png";
            if (favIcon) favIcon.href = "/static/images/favicon-tab-dark.png?v=4";
            if (appleIcon) appleIcon.href = "/static/images/favicon-tab-dark.png?v=4";
        } else {
            html.setAttribute("data-theme", "light");
            document.getElementById("tIcon").innerText = "☀️";
            document.getElementById("tLabel").innerText = "Chế độ Sáng";
            localStorage.setItem("claugpt_theme", "light");
            if (logoImg) logoImg.src = "/static/images/logo-light.png";
            if (favIcon) favIcon.href = "/static/images/favicon-tab-light.png?v=4";
            if (appleIcon) appleIcon.href = "/static/images/favicon-tab-light.png?v=4";
        }
        if (typeof window.updateGlobeTheme === 'function') {
            window.updateGlobeTheme(theme);
        }
    }
    function toggleTheme() {
        applyTheme(html.getAttribute("data-theme") === "dark" ? "light" : "dark");
    }
    applyTheme(localStorage.getItem("claugpt_theme") || "light");

    // Bảng điểm 13 môn
    const defaultScores = [
        [8, 8.5, 7.5, 8, 8.5], [7, 7.5, 7, 7.5, 8], [9, 8.5, 8, 8.5, 9],
        [6.5, 7, 6.5, 7, 7], [7, 7.5, 8, 7.5, 8], [8, 8.5, 8, 8, 8.5],
        [8.5, 9, 8.5, 9, 9], [8, 8.5, 8, 8.5, 8], [9, 9.5, 9, 9.5, 10],
        [8.5, 9, 8.5, 9, 9.5], [8, 8, 8.5, 8, 8.5], [9, 9, 9, 9, 9], [8.5, 8.5, 9, 9, 9]
    ];

    const tbody = document.getElementById("gradeBody");
    subjectData.forEach((sub, idx) => {
        const row = document.createElement("tr");
        const def = defaultScores[idx] || [8, 8, 8, 8, 8];
        row.innerHTML = `
            <td class="sub-name">${sub.name}</td>
            <td><input type="number" step="0.1" min="0" max="10" class="score-box" value="${def[0]}" onchange="calcAllGrades()"></td>
            <td><input type="number" step="0.1" min="0" max="10" class="score-box" value="${def[1]}" onchange="calcAllGrades()"></td>
            <td><input type="number" step="0.1" min="0" max="10" class="score-box" value="${def[2]}" onchange="calcAllGrades()"></td>
            <td><input type="number" step="0.1" min="0" max="10" class="score-box" value="${def[3]}" onchange="calcAllGrades()"></td>
            <td><input type="number" step="0.1" min="0" max="10" class="score-box" value="${def[4]}" onchange="calcAllGrades()"></td>
            <td class="score-avg" id="avg-${idx}">0.0</td>
        `;
        tbody.appendChild(row);
    });

    let gradeSummaryText = "";

    function calcAllGrades() {
        const rows = tbody.querySelectorAll("tr");
        let sumAvg = 0;
        let count = 0;
        let minScore = 999;
        let minSubject = "";
        let details = [];

        rows.forEach((row, i) => {
            const inputs = row.querySelectorAll("input");
            const d15_1 = parseFloat(inputs[0].value) || 0;
            const d15_2 = parseFloat(inputs[1].value) || 0;
            const dtt = parseFloat(inputs[2].value) || 0;
            const dgk = parseFloat(inputs[3].value) || 0;
            const dck = parseFloat(inputs[4].value) || 0;

            const avg = Math.round(((d15_1 + d15_2 + dtt + dgk * 2 + dck * 3) / 8) * 10) / 10;
            const avgCell = document.getElementById(`avg-${i}`);
            avgCell.innerText = avg.toFixed(1);
            avgCell.classList.remove("score-low");

            sumAvg += avg;
            count++;
            details.push(`${subjectData[i].name}: ${avg.toFixed(1)}`);

            if (avg < minScore) {
                minScore = avg;
                minSubject = subjectData[i].name;
            }
        });

        rows.forEach((row, i) => {
            const avgCell = document.getElementById(`avg-${i}`);
            if (parseFloat(avgCell.innerText) === minScore) {
                avgCell.classList.add("score-low");
            }
        });

        const overall = parseFloat((sumAvg / count).toFixed(2));
        document.getElementById("finalAvg").innerText = overall.toFixed(2);

        let rank = "Yếu";
        if (overall >= 9.0) rank = "Xuất sắc";
        else if (overall >= 8.0) rank = "Giỏi";
        else if (overall >= 7.0) rank = "Khá";
        else if (overall >= 5.0) rank = "Trung Bình";

        document.getElementById("academicRank").innerText = rank;
        document.getElementById("lowestSubjectNotice").innerText = `⚠️ Cần lưu ý: ${minSubject} (${minScore.toFixed(1)})`;

        gradeSummaryText = `Bảng điểm trung bình:\n${details.join(", ")}\nĐTB: ${overall.toFixed(2)} | Học lực: ${rank}. Môn thấp nhất: ${minSubject} (${minScore.toFixed(1)}).`;
    }

    calcAllGrades();

    // Logic Chat
    const chatHistory = [];

    async function sendMessage() {
        const input = document.getElementById("userInput");
        const btn = document.getElementById("sendBtn");
        const text = input.value.trim();
        if (!text) return;

        appendMessage("user", text);
        input.value = "";
        input.disabled = true;
        btn.disabled = true;

        showThinkingIndicator();

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    history: chatHistory,
                    grades_summary: gradeSummaryText
                })
            });

            const data = await res.json();
            removeThinkingIndicator();

            if (res.ok) {
                appendTypewriterMessage(data.reply, () => {
                    input.disabled = false;
                    btn.disabled = false;
                    input.focus();
                });
                chatHistory.push({ role: "user", content: text });
                chatHistory.push({ role: "model", content: data.reply });
                return;
            } else {
                appendMessage("assistant", "Lỗi: " + (data.detail || "Không thể tải phản hồi"));
            }
        } catch (e) {
            removeThinkingIndicator();
            appendMessage("assistant", "Mất kết nối với máy chủ.");
        } finally {
            input.disabled = false;
            btn.disabled = false;
            input.focus();
        }
    }

    function showThinkingIndicator() {
        removeThinkingIndicator();
        const chatBox = document.getElementById("chatBox");
        const div = document.createElement("div");
        div.id = "thinkingIndicator";
        div.className = "bubble assistant thinking";
        div.innerHTML = `
            <span>✨ VuongEdu đang suy nghĩ</span>
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
        `;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function removeThinkingIndicator() {
        const el = document.getElementById("thinkingIndicator");
        if (el) el.remove();
    }

    function appendTypewriterMessage(text, onComplete) {
        const chatBox = document.getElementById("chatBox");
        const div = document.createElement("div");
        div.className = "bubble assistant";
        chatBox.appendChild(div);

        const cleaned = cleanFormatting(text);
        let i = 0;
        const step = Math.max(1, Math.floor(cleaned.length / 140));
        const delay = 14;

        function streamText() {
            if (i < cleaned.length) {
                i += step;
                div.innerText = cleaned.slice(0, Math.min(i, cleaned.length));
                chatBox.scrollTop = chatBox.scrollHeight;
                setTimeout(streamText, delay);
            } else {
                div.innerText = cleaned;
                chatBox.scrollTop = chatBox.scrollHeight;
                if (onComplete) onComplete();
            }
        }
        streamText();
    }

    function cleanFormatting(text) {
        if (!text) return "";
        let cleaned = text.replace(/(\d)\s*\*\s*(\d)/g, "$1 × $2");
        cleaned = cleaned.replace(/^(\s*)\*\s+/gm, "$1- ");
        cleaned = cleaned.replace(/^#{1,6}\s*/gm, "");
        cleaned = cleaned.replace(/[*#]/g, "");
        return cleaned.trim();
    }

    function appendMessage(role, text) {
        const chatBox = document.getElementById("chatBox");
        const div = document.createElement("div");
        div.className = `bubble ${role}`;
        div.innerText = role === "assistant" ? cleanFormatting(text) : text;
        chatBox.appendChild(div);
        chatBox.scrollTop = chatBox.scrollHeight;
    }


    // ==========================================
    // CÂU HỎI GỢI Ý RANDOM THEO MÔN HỌC (F5 ĐỔI MỚI)
    // ==========================================
    const subjectSuggestionsPool = [
        {
            subject: "Toán học",
            icon: "📐",
            questions: [
                "Phương pháp giải nhanh phương trình bậc 2 và định lý Vi-ét?",
                "Ý nghĩa hình học của đạo hàm và cách tìm cực trị hàm số?",
                "Cách tính thể tích khối chóp và khối lăng trụ dễ nhớ nhất?",
                "Mẹo ghi nhớ các công thức lượng giác cơ bản nhanh chóng?"
            ]
        },
        {
            subject: "Vật lí",
            icon: "⚡",
            questions: [
                "Tại sao bầu trời lại có màu xanh vào ban ngày?",
                "Sự khác biệt giữa dòng điện xoay chiều AC và một chiều DC?",
                "Định luật bảo toàn cơ năng áp dụng cho con lắc như thế nào?",
                "Bản chất của hiện tượng cảm ứng điện từ Faraday là gì?"
            ]
        },
        {
            subject: "Hóa học",
            icon: "🧪",
            questions: [
                "Phương pháp thăng bằng electron để cân bằng phản ứng oxi hóa - khử?",
                "Làm thế nào để nhận biết các chất hữu cơ bằng thuốc thử đặc trưng?",
                "Bản chất của liên kết hiđro và tác động đến nhiệt độ sôi?",
                "Đặc điểm cấu tạo và tính chất hóa học của hiđrocacbon no?"
            ]
        },
        {
            subject: "Sinh học",
            icon: "🧬",
            questions: [
                "Cơ chế nhân đôi ADN và nguyên tắc bán bảo tồn diễn ra thế nào?",
                "Quy luật phân li độc lập của Menđen có ý nghĩa gì trong chọn giống?",
                "Quá trình quang hợp ở thực vật gồm những pha nào?",
                "Sự khác biệt cơ bản giữa đột biến gen và đột biến NST?"
            ]
        },
        {
            subject: "Ngữ văn",
            icon: "📖",
            questions: [
                "Cách viết mở bài gián tiếp lôi cuốn cho bài văn nghị luận?",
                "Cấu trúc 5 bước viết đoạn văn nghị luận xã hội 200 chữ?",
                "Phân tích vẻ đẹp người lính trong bài thơ Tây Tiến của Quang Dũng?",
                "Nghệ thuật xây dựng tình huống éo le trong tác phẩm Vợ nhặt?"
            ]
        },
        {
            subject: "Lịch sử",
            icon: "📜",
            questions: [
                "Ý nghĩa lịch sử và nguyên nhân thắng lợi Cách mạng Tháng Tám 1945?",
                "Chiến dịch Điện Biên Phủ: Ý nghĩa phương châm Đánh chắc tiến chắc?",
                "Bối cảnh ra đời và tác động của xu thế toàn cầu hóa?",
                "Nguyên nhân sâu xa dẫn đến Chiến tranh thế giới thứ hai (1939 - 1945)?"
            ]
        },
        {
            subject: "Địa lí",
            icon: "🌍",
            questions: [
                "Khí hậu nhiệt đới ẩm gió mùa tác động gì đến nông nghiệp Việt Nam?",
                "Vì sao vùng Đông Nam Bộ có nền kinh tế phát triển năng động nhất?",
                "Hiện tượng El Niño và La Niña hình thành như thế nào?",
                "Đặc điểm địa hình đồi núi ảnh hưởng gì đến phân bố dân cư nước ta?"
            ]
        },
        {
            subject: "Tiếng Anh",
            icon: "🇬🇧",
            questions: [
                "Cách phân biệt thì Hiện tại hoàn thành và Quá khứ đơn dễ hiểu?",
                "Mẹo phân biệt và chia câu điều kiện loại 1, 2, 3 chuẩn xác?",
                "Quy tắc phát âm đuôi -ed và -s/es chuẩn bản xứ?",
                "Những cụm Phrasal Verbs thường gặp nhất trong đề thi THPT?"
            ]
        },
        {
            subject: "Tin học",
            icon: "💻",
            questions: [
                "So sánh thuật toán tìm kiếm tuần tự và tìm kiếm nhị phân?",
                "Khái niệm mảng một chiều trong lập trình và cách duyệt mảng?",
                "Nguyên lý hoạt động của mô hình client-server và giao thức HTTP?",
                "Khóa chính (Primary Key) trong cơ sở dữ liệu quan hệ có vai trò gì?"
            ]
        },
        {
            subject: "GD Công Dân",
            icon: "⚖️",
            questions: [
                "Quyền bình đẳng của công dân trước pháp luật được thể hiện thế nào?",
                "Phân biệt 4 hình thức thực hiện pháp luật trong đời sống?",
                "Quyền được bảo đảm an toàn và bí mật thư tín của công dân?",
                "Trách nhiệm của thanh niên trong việc xây dựng và bảo vệ Tổ quốc?"
            ]
        },
        {
            subject: "Công nghệ",
            icon: "⚙️",
            questions: [
                "Nguyên lý hoạt động 4 kỳ của động cơ đốt trong (nạp, nén, nổ, xả)?",
                "Cách vẽ và đọc bản vẽ kỹ thuật hình chiếu vuông góc đơn giản?",
                "Quy trình thiết kế mạch điều khiển bật tắt đèn tự động bằng cảm biến?",
                "Ứng dụng của công nghệ tự động hóa trong nông nghiệp hiện đại?"
            ]
        },
        {
            subject: "GD Thể Chất",
            icon: "🏃",
            questions: [
                "Kỹ thuật khởi động bài bản để phòng ngừa chấn thương khi chạy?",
                "Cách duy trì nhịp thở đều đặn và giữ sức khi chạy cự ly dài?",
                "Phương pháp sơ cứu tức thời khi bị chuột rút hoặc bong gân?",
                "Chế độ dinh dưỡng khoa học giúp hồi phục cơ bắp nhanh sau luyện tập?"
            ]
        },
        {
            subject: "QP-AN",
            icon: "🛡️",
            questions: [
                "Cấu tạo cơ bản và nguyên lý hoạt động của súng tiểu liên AK?",
                "Kỹ thuật băng bó vết thương và cố định xương gãy bằng nẹp?",
                "Ý nghĩa nghệ thuật quân sự 'Lấy yếu chống mạnh, lấy ít địch nhiều'?",
                "Trách nhiệm của học sinh trong việc bảo vệ chủ quyền biển đảo?"
            ]
        }
    ];

    // Chọn ngẫu nhiên 3 câu hỏi từ 3 môn học khác nhau
    function getRandomSuggestions(count = 3) {
        const pool = [...subjectSuggestionsPool].sort(() => 0.5 - Math.random());
        const chosen = pool.slice(0, count);
        return chosen.map(sub => {
            const q = sub.questions[Math.floor(Math.random() * sub.questions.length)];
            return {
                subject: sub.subject,
                icon: sub.icon,
                question: q
            };
        });
    }

    // Hiển thị 3 câu hỏi gợi ý vào sidebar
    function refreshSuggestedPrompts() {
        const container = document.getElementById("sidebarPromptList");
        if (!container) return;
        container.innerHTML = "";
        const prompts = getRandomSuggestions(3);
        prompts.forEach((p, index) => {
            const item = document.createElement("div");
            item.className = "prompt-item";
            item.title = `Câu hỏi gợi ý ${index + 1}: Bấm để hỏi ngay với Trợ lý AI VuongEdu`;
            item.innerHTML = `
                <div class="prompt-item-header">
                    <span class="prompt-badge">${p.icon} ${p.subject}</span>
                    <span class="prompt-arrow">↗</span>
                </div>
                <div class="prompt-text">${p.question}</div>
            `;
            item.addEventListener("click", () => {
                askSuggestedQuestion(p.question, p.subject);
            });
            container.appendChild(item);
        });
    }

    // Xử lý khi học sinh click vào câu hỏi gợi ý
    function askSuggestedQuestion(questionText, subjectName) {
        const chatNavBtn = document.querySelector("button[onclick*=\"'chat'\"]");
        switchTab("chat", chatNavBtn);

        const badge = document.getElementById("chatSubjectBadge");
        if (badge && subjectName) {
            badge.innerText = `Môn: ${subjectName}`;
        }

        const input = document.getElementById("userInput");
        if (input) {
            input.value = questionText;
            sendMessage();
        }
    }

    // Khởi tạo ngay khi tải trang (F5)
    refreshSuggestedPrompts();

    // =========================================================
    // HỆ THỐNG ĐĂNG NHẬP & ĐĂNG KÝ TÀI KHOẢN (AUTH SYSTEM)
    // =========================================================
    let currentUser = null;

    // Quản lý Modal Đăng Nhập & Đăng Ký
    function openAuthModal(mode = 'login') {
        const overlay = document.getElementById("authModalOverlay");
        if (!overlay) return;
        switchAuthMode(mode);
        overlay.style.display = "flex";
        document.body.style.overflow = "hidden";
        setTimeout(() => {
            if (mode === 'register') {
                const regInput = document.getElementById("regUsername");
                if (regInput) regInput.focus();
            } else {
                const loginInput = document.getElementById("loginUsername");
                if (loginInput) loginInput.focus();
            }
        }, 80);
    }

    function closeAuthModal() {
        const overlay = document.getElementById("authModalOverlay");
        if (overlay) {
            overlay.style.display = "none";
        }
        document.body.style.overflow = "";
    }

    function handleModalOverlayClick(e) {
        if (e.target && e.target.id === "authModalOverlay") {
            closeAuthModal();
        }
    }

    // Quản lý Dropdown khi click vào tên tài khoản ở góc trên bên phải
    function toggleUserDropdown(e) {
        if (e) e.stopPropagation();
        const pill = document.getElementById("topUserPill");
        if (pill) {
            pill.classList.toggle("dropdown-open");
        }
    }

    function goToStatsFromDropdown(e) {
        if (e) e.stopPropagation();
        const pill = document.getElementById("topUserPill");
        if (pill) pill.classList.remove("dropdown-open");
        const navBtn = document.querySelector("button[onclick*=\"'diem-so'\"]");
        switchTab('diem-so', navBtn);
    }

    function logoutFromDropdown(e) {
        if (e) e.stopPropagation();
        const pill = document.getElementById("topUserPill");
        if (pill) pill.classList.remove("dropdown-open");
        handleLogout();
    }

    // Đóng dropdown khi click ra ngoài hoặc bấm ESC
    window.addEventListener('click', function(e) {
        const pill = document.getElementById("topUserPill");
        if (pill && !pill.contains(e.target)) {
            pill.classList.remove("dropdown-open");
        }
    });

    window.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAuthModal();
            const pill = document.getElementById("topUserPill");
            if (pill) pill.classList.remove("dropdown-open");
        }
    });

    // Chuyển đổi qua lại giữa Đăng Nhập và Đăng Ký
    function switchAuthMode(mode) {
        const loginSec = document.getElementById("authLoginSection");
        const regSec = document.getElementById("authRegisterSection");
        const alertBox = document.getElementById("modalAuthAlertBox") || document.getElementById("authAlertBox");

        if (!loginSec || !regSec) return;

        if (mode === 'register') {
            loginSec.style.display = "none";
            regSec.style.display = "block";
            if (alertBox && !alertBox.classList.contains("auth-alert-success")) {
                alertBox.style.display = "none";
            }
            const regInput = document.getElementById("regUsername");
            if (regInput) regInput.focus();
        } else {
            regSec.style.display = "none";
            loginSec.style.display = "block";
            if (alertBox && !alertBox.classList.contains("auth-alert-success")) {
                alertBox.style.display = "none";
            }
            const loginInput = document.getElementById("loginUsername");
            if (loginInput) loginInput.focus();
        }
    }

    // Hiển thị thông báo phản hồi (Alert Banner)
    function showAuthAlert(message, type = "info") {
        const alertBox = document.getElementById("modalAuthAlertBox") || document.getElementById("authAlertBox");
        if (!alertBox) return;

        alertBox.className = `auth-alert-banner auth-alert-${type}`;
        let icon = "💡";
        if (type === "success") icon = "✨";
        if (type === "error") icon = "⚠️";

        alertBox.innerHTML = `<span>${icon}</span> <div>${message}</div>`;
        alertBox.style.display = "flex";
    }

    // Ẩn/Hiện mật khẩu
    function togglePasswordVisibility(inputId, btn) {
        const input = document.getElementById(inputId);
        if (!input) return;
        if (input.type === "password") {
            input.type = "text";
            if (btn) btn.innerText = "🙈";
        } else {
            input.type = "password";
            if (btn) btn.innerText = "👁️";
        }
    }

    // Xử lý khi bấm Tạo Tài Khoản (Đăng Ký)
    async function handleRegisterSubmit(e) {
        e.preventDefault();
        const username = document.getElementById("regUsername")?.value.trim() || "";
        const password = document.getElementById("regPassword")?.value || "";
        const confirmPassword = document.getElementById("regConfirmPassword")?.value || "";

        if (!username) {
            showAuthAlert("Vui lòng nhập Tên tài khoản.", "error");
            return;
        }
        if (!password) {
            showAuthAlert("Vui lòng nhập Mật khẩu.", "error");
            return;
        }
        if (!confirmPassword) {
            showAuthAlert("Vui lòng nhập Mật khẩu xác nhận.", "error");
            return;
        }
        if (password !== confirmPassword) {
            showAuthAlert("Mật khẩu xác nhận không trùng khớp với Mật khẩu!", "error");
            return;
        }
        if (password.length < 4) {
            showAuthAlert("Mật khẩu cần có tối thiểu 4 ký tự.", "error");
            return;
        }

        const btn = document.getElementById("btnRegisterSubmit");
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span>Đang tạo tài khoản...</span> <span>⏳</span>`;
        }

        try {
            const res = await fetch("/api/auth/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    username: username,
                    password: password,
                    confirm_password: confirmPassword
                })
            });
            const data = await res.json();

            if (data.success) {
                // 1. Thông báo Tạo tài khoản thành công
                showAuthAlert("Tạo tài khoản thành công!", "success");

                // 2. Xóa mật khẩu cũ trong form đăng ký
                const regPass = document.getElementById("regPassword");
                const regConf = document.getElementById("regConfirmPassword");
                if (regPass) regPass.value = "";
                if (regConf) regConf.value = "";

                // 3. Tự động nhảy về phần Đăng Nhập sau tích tắc
                setTimeout(() => {
                    switchAuthMode('login');

                    // Điền sẵn tên vào ô đăng nhập
                    const loginUser = document.getElementById("loginUsername");
                    if (loginUser) {
                        loginUser.value = username;
                    }
                    const loginPass = document.getElementById("loginPassword");
                    if (loginPass) {
                        loginPass.value = "";
                        loginPass.focus();
                    }

                    // Tiếp tục hiển thị thông báo thành công ở trang Đăng nhập
                    showAuthAlert("Tạo tài khoản thành công! Hãy nhập mật khẩu của bạn để Tiếp Tục.", "success");
                }, 600);
            } else {
                showAuthAlert(data.error || "Không thể tạo tài khoản, vui lòng thử lại.", "error");
            }
        } catch (err) {
            showAuthAlert("Lỗi kết nối máy chủ: " + err.message, "error");
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = `<span>Tạo Tài Khoản</span> <span class="btn-arrow">✨</span>`;
            }
        }
    }

    // Xử lý khi bấm Tiếp Tục (Đăng Nhập)
    async function handleLoginSubmit(e) {
        e.preventDefault();
        const username = document.getElementById("loginUsername")?.value.trim() || "";
        const password = document.getElementById("loginPassword")?.value || "";

        if (!username || !password) {
            showAuthAlert("Vui lòng nhập đầy đủ Tên và Mật khẩu.", "error");
            return;
        }

        const btn = document.getElementById("btnLoginSubmit");
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = `<span>Đang xác thực...</span> <span>⏳</span>`;
        }

        try {
            const res = await fetch("/api/auth/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            });
            const data = await res.json();

            if (data.success) {
                currentUser = data.user;
                localStorage.setItem("eduvie_user", JSON.stringify(data.user));
                updateAuthUI(data.user);
                showAuthAlert(`Đăng nhập thành công! Chào mừng ${window.tenDep ? window.tenDep(data.user.username) : data.user.username} đến với VuongEdu 🎉`, "success");

                // Tự động đóng Modal sau khi đăng nhập thành công
                setTimeout(() => {
                    closeAuthModal();
                }, 700);
            } else {
                showAuthAlert(data.error || "Tên tài khoản hoặc mật khẩu không chính xác.", "error");
            }
        } catch (err) {
            showAuthAlert("Lỗi kết nối máy chủ: " + err.message, "error");
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = `<span>Tiếp Tục</span> <span class="btn-arrow">→</span>`;
            }
        }
    }

    // Xử lý Đăng Xuất
    async function handleLogout() {
        try {
            await fetch("/api/auth/logout", { method: "POST" });
        } catch (err) {
            console.error(err);
        }
        currentUser = null;
        localStorage.removeItem("eduvie_user");
        updateAuthUI(null);
        showAuthAlert("Bạn đã đăng xuất tài khoản thành công.", "info");
    }

    // Cập nhật giao diện theo trạng thái đăng nhập
    function updateAuthUI(user) {
        const topLoginBtn = document.getElementById("topLoginBtn");
        const topUserPill = document.getElementById("topUserPill");
        const topUserName = document.getElementById("topUserName");
        const dropdownUserTitle = document.getElementById("dropdownUserTitle");
        const sidebarUserWidget = document.getElementById("sidebarUserWidget");
        const sidebarUserName = document.getElementById("sidebarUserName");
        const welcomeUserName = document.getElementById("welcomeUserName");

        if (user && user.username) {
            if (topLoginBtn) topLoginBtn.style.display = "none";
            if (topUserPill) topUserPill.style.display = "inline-flex";
            if (topUserName) topUserName.innerText = (window.tenDep ? window.tenDep(user.username) : user.username);
            if (dropdownUserTitle) dropdownUserTitle.innerText = (window.tenDep ? window.tenDep(user.username) : user.username);
            if (welcomeUserName) welcomeUserName.innerText = (window.tenDep ? window.tenDep(user.username) : user.username);
            if (sidebarUserWidget) {
                sidebarUserWidget.style.display = "flex";
                if (sidebarUserName) sidebarUserName.innerText = (window.tenDep ? window.tenDep(user.username) : user.username);
            }
        } else {
            if (topLoginBtn) topLoginBtn.style.display = "inline-flex";
            if (topUserPill) {
                topUserPill.style.display = "none";
                topUserPill.classList.remove("dropdown-open");
            }
            if (welcomeUserName) welcomeUserName.innerText = "Bạn";
            if (sidebarUserWidget) sidebarUserWidget.style.display = "none";
        }
    }

    // Tự động kiểm tra phiên đăng nhập khi mở trang
    async function checkAuthSession() {
        // 1. Kiểm tra localStorage trước để phản hồi tức thì
        const cached = localStorage.getItem("eduvie_user");
        if (cached) {
            try {
                currentUser = JSON.parse(cached);
                updateAuthUI(currentUser);
            } catch (e) {
                localStorage.removeItem("eduvie_user");
            }
        }

        // 2. Việc xác thực thật do app.js lo bằng JWT (/me). Bản mẫu gọi /api/auth/me —
        //    endpoint đó không tồn tại nên chỉ tạo lỗi 404 trong console, đã bỏ.
        if (!cached) updateAuthUI(null);
    }

    checkAuthSession();



(function() {
    const container = document.getElementById('globe3d-canvas-container');
    if (!container || typeof THREE === 'undefined') return;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const width = container.clientWidth || 320;
    const height = container.clientHeight || 320;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 4.6;

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const globeGroup = new THREE.Group();
    scene.add(globeGroup);

    // 2. Lưới cầu đa diện Wireframe Icosahedron
    const sphereGeo = new THREE.IcosahedronGeometry(1.45, 2);
    const sphereMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        wireframe: true,
        transparent: true,
        opacity: 0.38
    });
    const sphereMesh = new THREE.Mesh(sphereGeo, sphereMat);
    globeGroup.add(sphereMesh);

    // 3. Lõi phát sáng mềm (Inner Glow Core)
    const coreGeo = new THREE.SphereGeometry(1.2, 24, 24);
    const coreMat = new THREE.MeshBasicMaterial({
        color: 0x4f46e5,
        transparent: true,
        opacity: 0.12,
        wireframe: false
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    globeGroup.add(coreMesh);

    // 4. Đám mây hạt tinh vân (Stardust Particle Sphere)
    const particleCount = 700;
    const particleGeo = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
        const u = Math.random();
        const v = Math.random();
        const theta = u * 2.0 * Math.PI;
        const phi = Math.acos(2.0 * v - 1.0);
        const r = 1.45 + (Math.random() - 0.5) * 0.35;

        positions[i] = r * Math.sin(phi) * Math.cos(theta);
        positions[i + 1] = r * Math.sin(phi) * Math.sin(theta);
        positions[i + 2] = r * Math.cos(phi);
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const particleMat = new THREE.PointsMaterial({
        color: 0x00f2fe,
        size: 0.038,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending
    });
    const particleSystem = new THREE.Points(particleGeo, particleMat);
    globeGroup.add(particleSystem);

    // 5. Hai vòng đai quỹ đạo tri thức (Orbit Rings)
    const ringGeo1 = new THREE.TorusGeometry(2.1, 0.012, 16, 120);
    const ringMat1 = new THREE.MeshBasicMaterial({
        color: 0xa855f7,
        transparent: true,
        opacity: 0.55
    });
    const ring1 = new THREE.Mesh(ringGeo1, ringMat1);
    ring1.rotation.x = Math.PI / 2.3;
    ring1.rotation.y = Math.PI / 6;
    globeGroup.add(ring1);

    const ringGeo2 = new THREE.TorusGeometry(2.35, 0.012, 16, 120);
    const ringMat2 = new THREE.MeshBasicMaterial({
        color: 0x0071e3,
        transparent: true,
        opacity: 0.45
    });
    const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
    ring2.rotation.x = -Math.PI / 2.8;
    ring2.rotation.y = -Math.PI / 4.5;
    globeGroup.add(ring2);

    // Điểm sáng vệ tinh xoay trên vòng quỹ đạo
    const satGeo = new THREE.SphereGeometry(0.045, 12, 12);
    const satMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const satellite = new THREE.Mesh(satGeo, satMat);
    satellite.position.set(2.1, 0, 0);
    ring1.add(satellite);

    // 6. Xử lý tương tác kéo xoay chuột & cảm ứng (Drag & Mouse Move)
    let isDragging = false;
    let prevMouse = { x: 0, y: 0 };
    let mouse = { x: 0, y: 0 };
    let target = { x: 0, y: 0 };
    let mouseTicking = false;

    // Chỉ tính toán vị trí chuột khi quả cầu hiển thị và điều tiết bằng requestAnimationFrame
    window.addEventListener('mousemove', (e) => {
        if (!isGlobeVisible) return;
        if (!mouseTicking) {
            mouseTicking = true;
            requestAnimationFrame(() => {
                mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
                mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
                mouseTicking = false;
            });
        }
    }, { passive: true });

    container.addEventListener('mousedown', (e) => {
        isDragging = true;
        prevMouse.x = e.clientX;
        prevMouse.y = e.clientY;
    });

    window.addEventListener('mouseup', () => { isDragging = false; });

    window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const dx = e.clientX - prevMouse.x;
        const dy = e.clientY - prevMouse.y;
        globeGroup.rotation.y += dx * 0.007;
        globeGroup.rotation.x += dy * 0.007;
        prevMouse.x = e.clientX;
        prevMouse.y = e.clientY;
    }, { passive: true });

    // Hỗ trợ cảm ứng trên điện thoại/tablet
    container.addEventListener('touchstart', (e) => {
        if (e.touches.length === 1) {
            isDragging = true;
            prevMouse.x = e.touches[0].clientX;
            prevMouse.y = e.touches[0].clientY;
        }
    }, { passive: true });

    window.addEventListener('touchend', () => { isDragging = false; });

    window.addEventListener('touchmove', (e) => {
        if (!isDragging || e.touches.length !== 1) return;
        const dx = e.touches[0].clientX - prevMouse.x;
        const dy = e.touches[0].clientY - prevMouse.y;
        globeGroup.rotation.y += dx * 0.007;
        globeGroup.rotation.x += dy * 0.007;
        prevMouse.x = e.touches[0].clientX;
        prevMouse.y = e.touches[0].clientY;
    }, { passive: true });

    // 7. Cập nhật kích thước khi resize
    function resizeGlobe() {
        if (!container.clientWidth || !container.clientHeight) return;
        const w = container.clientWidth;
        const h = container.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    }
    window.resizeGlobe3D = resizeGlobe;
    window.addEventListener('resize', resizeGlobe, { passive: true });

    if (window.ResizeObserver) {
        new ResizeObserver(() => resizeGlobe()).observe(container);
    }

    // 8. Animation Loop tối ưu tài nguyên (Tự động pause khi khuất màn hình hoặc đổi tab)
    let angle = 0;
    let isGlobeVisible = true;
    let globeAnimId = null;

    function animate() {
        if (!isGlobeVisible) {
            globeAnimId = null;
            return;
        }
        globeAnimId = requestAnimationFrame(animate);

        // Chuyển động tự động
        sphereMesh.rotation.y += 0.002;
        particleSystem.rotation.y -= 0.0015;
        ring1.rotation.z += 0.004;
        ring2.rotation.z -= 0.003;

        // Xoay nhẹ theo vị trí chuột (Parallax Lerp) khi không giữ chuột kéo
        if (!isDragging) {
            target.x = mouse.y * 0.3;
            target.y = mouse.x * 0.4;
            globeGroup.rotation.x += (target.x - globeGroup.rotation.x) * 0.035;
            globeGroup.rotation.y += (target.y + angle - globeGroup.rotation.y) * 0.035;
            angle += 0.002;
        }

        renderer.render(scene, camera);
    }

    function checkGlobeActive() {
        const homeSection = document.getElementById('view-home');
        const isHome = homeSection && homeSection.classList.contains('active');
        const isVisible = isHome && !document.hidden;

        if (isVisible) {
            if (!isGlobeVisible) {
                isGlobeVisible = true;
                if (!globeAnimId) animate();
            }
        } else {
            isGlobeVisible = false;
        }
    }
    window.checkGlobeVisibility = checkGlobeActive;

    // IntersectionObserver để pause Three.js khi cuộn trang ra khỏi banner
    if ('IntersectionObserver' in window) {
        const globeObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const homeSection = document.getElementById('view-home');
                const isHome = homeSection && homeSection.classList.contains('active');
                if (entry.isIntersecting && isHome && !document.hidden) {
                    if (!isGlobeVisible) {
                        isGlobeVisible = true;
                        if (!globeAnimId) animate();
                    }
                } else {
                    isGlobeVisible = false;
                }
            });
        }, { root: document.querySelector('.main-viewport'), threshold: 0.05 });
        globeObserver.observe(container);
    }

    document.addEventListener('visibilitychange', checkGlobeActive);

    // Cập nhật màu sắc & blending của quả cầu 3D tương thích hoàn hảo chế độ Sáng / Tối
    function updateGlobeTheme(theme) {
        if (!sphereMat) return;
        if (theme === 'light') {
            sphereMat.color.setHex(0x4f46e5);
            sphereMat.opacity = 0.52;
            coreMat.color.setHex(0x6366f1);
            coreMat.opacity = 0.15;
            particleMat.color.setHex(0x4338ca);
            particleMat.blending = THREE.NormalBlending;
            particleMat.opacity = 0.85;
            ringMat1.color.setHex(0x4338ca);
            ringMat1.opacity = 0.55;
            ringMat2.color.setHex(0x818cf8);
            ringMat2.opacity = 0.7;
            satMat.color.setHex(0x4f46e5);
        } else {
            sphereMat.color.setHex(0x38bdf8);
            sphereMat.opacity = 0.38;
            coreMat.color.setHex(0x4f46e5);
            coreMat.opacity = 0.12;
            particleMat.color.setHex(0x00f2fe);
            particleMat.blending = THREE.AdditiveBlending;
            particleMat.opacity = 0.9;
            ringMat1.color.setHex(0xa855f7);
            ringMat1.opacity = 0.55;
            ringMat2.color.setHex(0x0071e3);
            ringMat2.opacity = 0.45;
            satMat.color.setHex(0xffffff);
        }
        particleMat.needsUpdate = true;
    }
    window.updateGlobeTheme = updateGlobeTheme;
    updateGlobeTheme(document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light");

    animate();
})();
