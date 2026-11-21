# VuongEdu — AI Learning Assistant

Trợ lý học tập cá nhân hoá: hỏi đáp theo sách giáo khoa (RAG có trích dẫn trang) → quiz theo chủ đề →
phân tích điểm yếu → AI lập lộ trình và tự kiểm tra lại kế hoạch của mình.

Kho tài liệu hiện có: **Toán 12, Vật lí 12, Hoá học 12, Toán 8, Tiếng Anh 8** (33 tài liệu, 131 chủ đề).

## Chạy

```bash
cd ~/ai-learning-assistant
./start.sh
```

Mở http://localhost:8000. `start.sh` bật FastAPI (phục vụ luôn giao diện web) và một link public qua Cloudflare.

| Lệnh | Tác dụng |
|---|---|
| `./start.sh` | web + link public |
| `./start.sh --no-tunnel` | chỉ chạy trong máy |
| `./start.sh --streamlit` | chạy kèm giao diện Streamlit cũ ở cổng 8501 |
| `scripts/restart_web.sh` | khởi động lại nhanh mỗi khi sửa file trong `app/` hoặc `api/` |

Lần đầu: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`,
rồi tạo `.env` theo mẫu `.env.example` và dán khoá vào `GEMINI_API_KEYS`.

Tài khoản demo có sẵn dữ liệu 2 tuần: `python -m scripts.seed_demo` → đăng nhập tên `demo`.

## Giao diện

Giao diện web (`web/`) có 13 mục: Trang chủ, Môn học, Tài liệu, Hỏi AI, Luyện đề, Chấm bài, Phân tích,
Điểm số, Lộ trình, Gia sư AI, Lớp học, Hỏi bài, Quản trị.

**Sửa bất cứ file nào trong `web/static/` thì phải tăng số `?v=N` trong `web/templates/index.html`**,
nếu không trình duyệt vẫn dùng bản cũ trong cache. Hiện dùng `v=12`.

Bản Streamlit (`Home.py`, `pages/`) vẫn chạy được, giữ làm bản dự phòng.

## REST API

63 endpoint, JWT. Swagger: http://localhost:8000/docs

Luồng: `POST /auth/login` → `access_token` → header `Authorization: Bearer <token>`.

Tải tài liệu lên chạy **nền**: `POST /documents` trả `202` ngay, xem tiến độ bằng `GET /documents/{id}`.
Làm vậy vì Cloudflare cắt mọi request quá 100 giây, mà OCR một cuốn sách mất hàng chục phút.

## Cấu trúc

```
api/main.py                FastAPI: auth, documents, chat, quiz, scores + phục vụ giao diện web
api/deps.py                JWT, các dependency phân quyền (current_user / teacher_user / admin_user)
api/extra.py               dashboard, learning, analytics, classroom, plan2, admin, quản lý môn học

web/templates/index.html   giao diện một trang
web/static/js/app.js       client API + logic toàn bộ các mục
web/static/js/app2.js      trang Môn học (nối với dữ liệu thật), lọc RAG theo môn
web/static/js/app3.js      Quản trị › Môn học: thêm/xoá môn, chương, chủ đề
web/static/js/upload.js    tải tài liệu + theo dõi tiến độ OCR

app/db.py                  SQLite models (20 bảng) + migrate + seed taxonomy
app/llm.py                 bọc Gemini: đổi model và đổi key khi hết quota, streaming, JSON schema
app/rag/ingest.py          trích text (PyMuPDF) / OCR → chunk → embedding → ChromaDB
app/rag/ocr.py             OCR bằng Gemini vision, cache theo hash file
app/rag/chat.py            hybrid retrieval (vector + BM25, RRF) + mở rộng truy vấn theo nhãn bài
app/quiz.py                sinh quiz (structured output) + kiểm tra chéo đáp án, chấm, lưu theo chủ đề
app/analytics.py           mastery = Σ(w_khó × w_thời_gian × đúng)/Σw; ngưỡng yếu/tốt
app/learning.py            lặp lại ngắt quãng (SM-2), adaptive quiz, đồ thị tiên quyết
app/grader.py              chấm bài tự luận / bài chụp ảnh bằng Gemini vision
app/classroom.py           lớp học, mã lớp, giao đề, heatmap lớp
app/advisor.py             nhận xét + lộ trình nhanh (1 request)
app/agent.py               AI Agent: Gemini function calling, 6 tool
app/multi_agent.py         Chẩn đoán → Lập kế hoạch → Phản biện
app/reflection.py          validator, auto_repair, phản tư (xem mục dưới)
app/ml/kt.py               Deep Knowledge Tracing (LSTM) + baseline

data/topics.json           taxonomy dự phòng, tự ghi lại mỗi khi sửa môn học trên giao diện
data/prerequisites.json    đồ thị kiến thức: chủ đề nào cần nền nào (82 chủ đề, 103 cạnh)
data/ocr_cache/            kết quả OCR theo hash file — nạp lại cùng cuốn sách không tốn quota
```

## Thêm môn / lớp mới

Quản trị → tab **📗 Môn học**. Tên môn phải có **số lớp ở cuối** (`Toán 8`, `Tiếng Anh 8`) vì trang
Môn học đọc số đó để xếp vào đúng lớp. Thêm chương và chủ đề theo mục lục sách, rồi vào Tài liệu tải PDF lên.

Nạp cả cuốn sách từ dòng lệnh thì nhanh hơn (chia theo chương):

```bash
python -m scripts.read_toc data/uploads/sach.pdf 3 4 5    # OCR trang mục lục để biết chương nằm ở đâu
python -m scripts.ingest_book --user "tên admin" --subject "Toán 8" \
    --file data/uploads/sach.pdf --chapters "1:6-29" "2:30-48"
```

Số trang là **trang PDF**, thường lệch so với số in trên sách — `read_toc` giúp xác định. Trang bìa chương
OCR ra rỗng vì toàn hình, đó là dấu hiệu nhận ra ranh giới chương.

## Agent tự đánh giá & tự sửa (bậc 6)

- `app/reflection.py`: `validate_plan` (5 luật, code thuần), `auto_repair` (sửa xác định R1/R2/R3),
  `plan_outcome` (đo hậu quả kế hoạch: % hoàn thành, Δ mastery so với snapshot lúc tạo),
  `reflect` (agent phản tư rút bài học → bảng `agent_lessons`, tự chèn vào prompt lần sau),
  `log_run` (nhật ký chất lượng agent → bảng `agent_runs`).
- Quy trình multi-agent: Chẩn đoán → Lập kế hoạch → Phản biện (LLM) → Validator (code) ép sửa tối đa 2 vòng
  → auto_repair → lưu.
- Đồ thị tiên quyết xét **trên mọi môn**: yếu "Phân thức đại số" (lớp 8) thì "Đường tiệm cận" (lớp 12) bị chặn.
- Đo: `python -m eval.agent_eval`. Xem ở Quản trị → tab Agent.

## Đánh giá

```bash
python -m eval.rag_eval            # Hit@5, MRR (không tốn LLM)
python -m eval.rag_eval --judge    # + faithfulness / correctness bằng LLM (2 request / câu)
python -m eval.agent_eval          # pass rate kế hoạch trước/sau auto_repair
python -m scripts.test_taxonomy            # API quản lý môn học
python -m scripts.test_upload_bg           # tải tài liệu chạy nền
python -m scripts.test_prereq_crossgrade   # tiên quyết liên lớp
```

Kết quả 26/09: RAG Hit@5 96%, MRR 0.88 (28 câu). Agent 12 kế hoạch, pass 17% → 83% sau auto_repair.
DKT trên ASSISTments 2009: AUC 0.825 (hồi quy logistic 0.761, trung bình theo kỹ năng 0.620).

## Ghi chú vận hành

- **Quota free tier tính theo model × project.** `app/llm.py` tự đổi model rồi đổi key khi hết;
  thêm key từ project khác vào `GEMINI_API_KEYS=key1,key2`. Mỗi trang OCR / câu chat / đề quiz = 1 request.
  Embedding có quota riêng — hết thì cả chat lẫn quiz đều kẹt, reset khoảng 14:00 giờ Việt Nam.
- Sửa `app/` hoặc `api/` → chạy `scripts/restart_web.sh`. Sửa `web/static/` → Ctrl+Shift+R và nhớ tăng `?v=N`.
- PDF scan: chỉ OCR khoảng trang của chương đang học, đừng chọn "Cả môn" với sách dày.
- Kho tài liệu dùng chung cho mọi người dùng (SGK nạp một lần).

## Mở trên điện thoại (cùng Wi-Fi)

PowerShell (Admin) trên Windows — IP WSL lấy bằng `wsl hostname -I`, đổi sau mỗi lần khởi động máy:

```powershell
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=<IP_WSL>
New-NetFirewallRule -DisplayName "VuongEdu 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

Điện thoại mở `http://<IP máy tính>:8000` (xem IP bằng `ipconfig`).
Nếu IP WSL đổi: `netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0` rồi thêm lại.

## Link public cho người ở xa

`./start.sh` tự mở sẵn. Chạy tay:

```bash
~/.local/bin/cloudflared tunnel --url http://localhost:8000 --protocol http2
```

Link dạng `https://xxx.trycloudflare.com`, đổi mỗi lần chạy lại. Chrome gắn nhãn "Nguy hiểm" cho tên miền này —
muốn hết cảnh báo thì cần tên miền riêng. Ai có link đều dùng được và đều tốn quota Gemini, chỉ gửi cho người thử nghiệm.
