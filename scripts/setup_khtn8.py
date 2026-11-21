"""Tạo môn Khoa học tự nhiên 8 (KNTT) — 8 chương, chủ đề là tên từng bài trong mục lục.

Ở lớp 8 môn này thay cho Vật lí + Hoá học + Sinh học.
  python -m scripts.setup_khtn8
"""
from sqlalchemy import func

from app import db

TEN = "Khoa học tự nhiên 8"

CHUONG = [
    ("Mở đầu", [
        "Sử dụng một số hoá chất, thiết bị cơ bản trong phòng thí nghiệm"]),
    ("Chương I. Phản ứng hoá học", [
        "Phản ứng hoá học", "Mol và tỉ khối chất khí", "Dung dịch và nồng độ",
        "Định luật bảo toàn khối lượng và phương trình hoá học",
        "Tính theo phương trình hoá học", "Tốc độ phản ứng và chất xúc tác"]),
    ("Chương II. Một số hợp chất thông dụng", [
        "Acid", "Base và thang pH", "Oxide", "Muối", "Phân bón hoá học"]),
    ("Chương III. Khối lượng riêng và áp suất", [
        "Khối lượng riêng", "Thực hành xác định khối lượng riêng",
        "Áp suất trên một bề mặt", "Áp suất chất lỏng và áp suất khí quyển",
        "Lực đẩy Archimedes"]),
    ("Chương IV. Tác dụng làm quay của lực", [
        "Tác dụng làm quay của lực và moment lực", "Đòn bẩy và ứng dụng"]),
    ("Chương V. Điện", [
        "Hiện tượng nhiễm điện do cọ xát", "Dòng điện và nguồn điện",
        "Mạch điện đơn giản", "Tác dụng của dòng điện",
        "Cường độ dòng điện và hiệu điện thế",
        "Thực hành đo cường độ dòng điện và hiệu điện thế"]),
    ("Chương VI. Nhiệt", [
        "Năng lượng nhiệt và nội năng", "Thực hành đo năng lượng nhiệt bằng joulemeter",
        "Sự truyền nhiệt", "Sự nở vì nhiệt"]),
    ("Chương VII. Sinh học cơ thể người", [
        "Khái quát về cơ thể người", "Hệ vận động ở người",
        "Dinh dưỡng và tiêu hoá ở người", "Máu và hệ tuần hoàn của cơ thể người",
        "Hệ hô hấp ở người", "Hệ bài tiết ở người",
        "Điều hoà môi trường trong của cơ thể người",
        "Hệ thần kinh và các giác quan ở người", "Hệ nội tiết ở người",
        "Da và điều hoà thân nhiệt ở người", "Sinh sản ở người"]),
    ("Chương VIII. Sinh vật và môi trường", [
        "Môi trường và các nhân tố sinh thái", "Quần thể sinh vật",
        "Quần xã sinh vật", "Hệ sinh thái", "Sinh quyển",
        "Cân bằng tự nhiên", "Bảo vệ môi trường"]),
]


def main():
    db.init_db()
    with db.SessionLocal() as s:
        sub = s.query(db.Subject).filter(func.lower(db.Subject.name) == TEN.lower()).first()
        if not sub:
            sub = db.Subject(name=TEN)
            s.add(sub); s.flush()
            print("+ môn", TEN)
        have = {c.name: c for c in sub.chapters}
        for i, (cname, bai) in enumerate(CHUONG):
            ch = have.get(cname)
            if not ch:
                ch = db.Chapter(subject_id=sub.id, name=cname, order=i)
                s.add(ch); s.flush()
                print(f"  + {cname}")
            known = {t.name for t in ch.topics}
            for t in bai:
                if t not in known:
                    s.add(db.Topic(chapter_id=ch.id, name=t))
        s.commit()
        sid = sub.id

    with db.SessionLocal() as s:
        sub = s.get(db.Subject, sid)
        print(f"= {TEN}: {len(sub.chapters)} chương, {sum(len(c.topics) for c in sub.chapters)} chủ đề")

    # ghi lai danh muc ra data/topics.json de dung lai duoc CSDL tu dau
    from api.extra import _export_topics_json
    _export_topics_json()
    print("da cap nhat data/topics.json")


if __name__ == "__main__":
    main()
