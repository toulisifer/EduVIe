"""Sinh sẵn câu hỏi vào ngân hàng, theo từng chủ đề.

Khác với lúc học sinh bấm "Tạo đề" (sinh tới đâu dùng tới đó), script này nạp
trước một lượng câu vào kho để đề về sau được ghép từ câu có sẵn — nhìn thấy
được, đếm được, kiểm tra được, thay vì mỗi lần lại nhờ AI nghĩ ra câu mới.

Mỗi chủ đề tốn khoảng 2 lượt gọi AI (1 sinh + 1 kiểm tra chéo) cho 5 câu.
Chạy lại nhiều lần được: câu trùng nội dung tự bị bỏ qua.

  python -m scripts.nap_ngan_hang --mon "Toán 8" --moi-chu-de 5
  python -m scripts.nap_ngan_hang --mon "Toán 8" --chuong 1 2      # chỉ vài chương
  python -m scripts.nap_ngan_hang --mon "Toán 8" --thu             # xem kế hoạch, không gọi AI
"""
import argparse
import sys
import time

from app import bank, db
from app.quiz import DIFFICULTY_VI, SCHEMA, SYSTEM, _hop_le, validate_answers
from app.llm import generate_json
from app.rag.chat import retrieve

DO_KHO = ["easy", "medium", "hard"]


def sinh_cho_chu_de(topic, subject_id: int, do_kho: str, n: int, chuong: str) -> list[dict]:
    """Gọi AI sinh n câu cho một chủ đề, đã qua bước kiểm tra chéo.

    Truy hồi bằng "chương + chủ đề" chứ không chỉ tên chủ đề: tên trần như "Đơn thức"
    kéo về cả đoạn sách của chương Phân thức đại số, và AI ra đề theo đoạn đó — câu hỏi
    gắn nhãn Chương I nhưng nội dung lại là Chương VI.
    """
    doan = retrieve(f"{chuong} {topic.name}", user_id=1, subject_id=subject_id, k=3)
    ngu_canh = "\n\n".join(f"[{h['filename']} tr.{h['page']}]\n{h['text']}" for h in doan) \
        or "(không có tài liệu, dùng kiến thức chuẩn của chương trình)"

    prompt = f"""CHỦ ĐỀ CẦN KIỂM TRA:
- topic_id={topic.id}: {topic.path}

TÀI LIỆU THAM KHẢO (có thể lẫn nội dung chương khác):
{ngu_canh}

YÊU CẦU: Tạo đúng {n} câu trắc nghiệm, độ khó {DIFFICULTY_VI[do_kho]}.

BẮT BUỘC: mọi câu phải kiểm tra ĐÚNG chủ đề "{topic.name}" thuộc "{chuong}".
Đoạn tài liệu ở trên có thể chứa nội dung của chương khác — nếu vậy thì bỏ qua,
ra đề theo đúng chủ đề được giao, dựa vào kiến thức chuẩn của chương trình.
Các câu phải khác nhau rõ rệt, không hỏi lặp cùng một ý."""

    items = validate_answers(generate_json(prompt, SCHEMA, system=SYSTEM, temperature=0.8))
    return [it for it in items if _hop_le(it, {topic.id})]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mon", required=True, help='tên môn, ví dụ "Toán 8"')
    ap.add_argument("--moi-chu-de", type=int, default=5, help="số câu mỗi chủ đề (mặc định 5)")
    ap.add_argument("--do-kho", default="medium", choices=DO_KHO)
    ap.add_argument("--chuong", nargs="*", type=int, help="chỉ nạp cho vài chương (1 = chương đầu)")
    ap.add_argument("--bo-qua-du", type=int, default=0,
                    help="bỏ qua chủ đề đã có từ ngần này câu trở lên")
    ap.add_argument("--thu", action="store_true", help="chỉ in kế hoạch, không gọi AI")
    a = ap.parse_args()

    db.init_db()
    with db.SessionLocal() as s:
        mon = s.query(db.Subject).filter(db.Subject.name == a.mon).first()
        if not mon:
            co = [x.name for x in s.query(db.Subject)]
            print(f"Không có môn {a.mon!r}. Hiện có: {co}")
            return 1
        chuong = sorted(mon.chapters, key=lambda c: c.order)
        if a.chuong:
            chuong = [c for i, c in enumerate(chuong, 1) if i in a.chuong]
        ds = [(t.id, t.name, c.name) for c in chuong for t in c.topics]
        sid = mon.id

    co_san = bank.dem_kha_dung([t[0] for t in ds])
    can = [(tid, ten, ch) for tid, ten, ch in ds if co_san.get(tid, 0) < max(a.bo_qua_du, 1)]

    print(f"Môn {a.mon}: {len(chuong)} chương, {len(ds)} chủ đề")
    print(f"Đã có câu: {sum(1 for t in ds if co_san.get(t[0], 0))} chủ đề")
    print(f"Sẽ nạp cho: {len(can)} chủ đề × {a.moi_chu_de} câu "
          f"≈ {len(can) * 2} lượt gọi AI\n")

    if a.thu:
        for tid, ten, ch in can[:20]:
            print(f"   {ch.split(':')[0][:26]:<28} {ten[:40]:<42} đang có {co_san.get(tid, 0)}")
        if len(can) > 20:
            print(f"   … và {len(can) - 20} chủ đề nữa")
        print("\n(chạy không có --thu để nạp thật)")
        return 0

    them = loi = 0
    t0 = time.time()
    for i, (tid, ten, ch) in enumerate(can, 1):
        with db.SessionLocal() as s:
            topic = s.get(db.Topic, tid)
            _ = topic.path
        try:
            items = sinh_cho_chu_de(topic, sid, a.do_kho, a.moi_chu_de, ch)
        except Exception as e:  # noqa: BLE001
            loi += 1
            print(f"  [{i}/{len(can)}] {ten[:44]:<46} LỖI: {type(e).__name__}: {str(e)[:70]}")
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                print("\n  Hết lượt gọi trong ngày — dừng tại đây, mai chạy tiếp.")
                break
            continue

        moi = 0
        for it in items:
            if bank.them_cau(tid, it.get("difficulty", a.do_kho), it["question"],
                             [str(o) for o in it["options"]][:4], it["correct_index"],
                             it.get("explanation", ""), source="ai",
                             verified=not it.get("unverified")):
                moi += 1
        them += moi
        print(f"  [{i}/{len(can)}] {ten[:44]:<46} +{moi} câu")

    phut = (time.time() - t0) / 60
    print(f"\nĐã nạp {them} câu mới trong {phut:.1f} phút. Lỗi: {loi}")
    t = bank.thong_ke()
    print(f"Kho hiện có {t['tong']} câu, phủ {t['chu_de_co_cau']}/{t['tong_chu_de']} chủ đề")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
