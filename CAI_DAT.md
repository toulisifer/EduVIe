# Cài đặt VuongEdu trên máy bạn

Bản này **không kèm cơ sở dữ liệu và sách giáo khoa** — chỉ có mã nguồn. Chạy xong bạn sẽ có một hệ thống trống, tự tạo tài khoản và tự nạp sách của mình vào.

## 1. Cần chuẩn bị

**Python 3.11 trở lên.** Kiểm tra bằng `python3 --version`. Dự án gốc chạy trên Python 3.14, Ubuntu (WSL trên Windows cũng được).

**Một khoá Gemini miễn phí** — bắt buộc, không có thì AI không chạy:

1. Vào https://aistudio.google.com/apikey
2. Đăng nhập Google, bấm **Create API key**
3. Chép chuỗi dài đó ra, lát nữa dán vào `.env`

Khoá miễn phí cho khoảng 20 lượt gọi mỗi ngày cho mỗi mô hình. Muốn nhiều hơn thì tạo thêm khoá ở các project Google khác nhau rồi khai báo cả loạt (xem bước 3).

## 2. Cài thư viện

```bash
cd ai-learning-assistant
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Trên Windows không dùng WSL thì dòng thứ ba là `.venv\Scripts\activate`.

Bước này tải khoảng 500 MB (PyTorch cho phần học máy), mất 5–10 phút.

## 3. Khai báo khoá

```bash
cp .env.example .env
```

Mở `.env` bằng trình soạn thảo bất kỳ, sửa hai dòng:

```
GEMINI_API_KEY=dán_khoá_vừa_lấy_vào_đây
JWT_SECRET=một_chuỗi_ngẫu_nhiên_dài_bạn_tự_nghĩ
```

Có nhiều khoá thì dùng dòng này thay cho dòng đầu, cách nhau dấu phẩy:

```
GEMINI_API_KEYS=khoá1,khoá2,khoá3
```

`JWT_SECRET` là chuỗi dùng để ký phiên đăng nhập — gõ bừa một chuỗi dài là được, nhưng đừng để nguyên giá trị mẫu.

## 4. Chạy

```bash
./start.sh --no-tunnel
```

Mở http://localhost:8000

Lần đầu chạy, hệ thống tự tạo cơ sở dữ liệu `data/app.db` và nạp sẵn danh mục môn → chương → chủ đề từ `data/topics.json` (6 môn, 178 chủ đề).

Bỏ `--no-tunnel` thì có thêm một địa chỉ công khai để người khác vào, nhưng cần cài `cloudflared` trước.

## 5. Tạo tài khoản quản trị

Đăng ký tài khoản đầu tiên qua giao diện web, rồi chạy lệnh này để tự cấp quyền quản trị cho mình:

```bash
.venv/bin/python -c "
from app import db
db.init_db()
with db.SessionLocal() as s:
    u = s.query(db.User).first()
    u.role = 'admin'; s.commit()
    print('đã cấp quyền admin cho:', u.username)
"
```

Có quyền quản trị mới tải sách lên và quản lý môn học được.

## 6. Nạp sách

Chưa có sách thì AI vẫn trả lời được, nhưng bằng kiến thức chung và **không trích dẫn được trang sách** — mất đi điểm mạnh nhất của hệ thống.

**Cách dễ:** vào mục **Tài liệu** trên web, chọn môn và chương, tải PDF lên. Nhớ chọn đúng chương và điền khoảng trang, đừng chọn "Cả môn" với sách dày.

**Cách nhanh hơn cho cả cuốn** — chia theo chương từ dòng lệnh:

```bash
# Bước 1: đọc mục lục để biết chương nằm ở trang nào
.venv/bin/python -m scripts.read_toc data/uploads/sach.pdf 3 4 5

# Bước 2: nạp theo chương (số là trang PDF, thường lệch với số in trên sách)
.venv/bin/python -m scripts.ingest_book --user "tên tài khoản của bạn" \
    --subject "Toán 8" --file data/uploads/sach.pdf \
    --chapters "1:6-29" "2:30-48"
```

PDF bản scan sẽ được OCR bằng AI, khoảng 5–7 giây mỗi trang và tốn 1 lượt gọi mỗi trang. Một cuốn 150 trang ăn hết 150 lượt, nên chia ra vài ngày nếu chỉ có một khoá.

Muốn thêm môn hoặc lớp khác: vào **Quản trị → 📗 Môn học**. Tên môn **phải có số lớp ở cuối** (`Toán 10`, `Vật lí 11`) vì giao diện đọc số đó để xếp vào đúng lớp.

## 7. Kiểm tra chạy đúng

Ba lệnh này không tốn lượt gọi AI nào:

```bash
.venv/bin/python -m scripts.test_authorization   # phân quyền, 14 phép thử
.venv/bin/python -m scripts.test_taxonomy        # quản lý môn học
.venv/bin/python -m scripts.show_auth --map      # bản đồ quyền của 71 endpoint
```

## Lỗi hay gặp

**`ModuleNotFoundError`** — chưa bật môi trường ảo. Chạy lại `source .venv/bin/activate`.

**Lỗi 429 hoặc `RESOURCE_EXHAUSTED`** — hết lượt trong ngày. Khoá miễn phí reset khoảng 14 giờ (giờ Việt Nam). Thêm khoá vào `GEMINI_API_KEYS` để nhân thêm.

**AI trả lời chậm 2–4 phút ở Gia sư AI và Lộ trình** — bình thường. Hai chức năng này gọi AI nhiều lượt liên tiếp. Màn hình hiện từng bước nó đang làm.

**Sửa file trong `web/static/` mà trình duyệt không đổi** — tăng số `?v=N` trong `web/templates/index.html` rồi Ctrl+Shift+R.

**Sửa file trong `app/` hoặc `api/`** — phải khởi động lại: `scripts/restart_web.sh`.

## Cấu trúc để đọc code

| Thư mục | Nội dung |
|---|---|
| `app/` | Phần lõi: `db.py` (20 bảng), `rag/` (tìm kiếm trong sách), `quiz.py`, `agent.py`, `reflection.py` |
| `api/` | REST API: `deps.py` (phân quyền), `main.py`, `extra.py` — 71 endpoint |
| `web/` | Giao diện một trang (HTML + JS thuần, không framework) |
| `scripts/` | Công cụ: nạp sách, kiểm thử, trình diễn code |
| `eval/` | Đo chất lượng: RAG (Hit@5, MRR) và agent |

Swagger xem toàn bộ API: http://localhost:8000/docs

Chi tiết kiến trúc nằm trong `README.md`.
