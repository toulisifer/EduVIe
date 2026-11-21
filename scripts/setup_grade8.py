"""Tạo môn/chương/chủ đề lớp 8 (Toán 8, Tiếng Anh 8) theo mục lục sách KNTT & Global Success.

Chạy được nhiều lần: đã có thì bỏ qua, không tạo trùng.
  python -m scripts.setup_grade8
"""
from sqlalchemy import func

from app import db

TOAN8 = [
    # (tên chương, [chủ đề])  — tập một, theo mục lục
    ("Chương I. Đa thức", [
        "Đơn thức", "Đa thức", "Phép cộng và phép trừ đa thức",
        "Phép nhân đa thức", "Phép chia đa thức cho đơn thức"]),
    ("Chương II. Hằng đẳng thức đáng nhớ và ứng dụng", [
        "Hiệu hai bình phương", "Bình phương của một tổng hay một hiệu",
        "Lập phương của một tổng, lập phương của một hiệu", "Tổng và hiệu hai lập phương",
        "Phân tích đa thức thành nhân tử"]),
    ("Chương III. Tứ giác", [
        "Tứ giác", "Hình thang cân", "Hình bình hành", "Hình chữ nhật",
        "Hình thoi và hình vuông"]),
    ("Chương IV. Định lí Thalès", [
        "Định lí Thalès trong tam giác", "Đường trung bình của tam giác",
        "Tính chất đường phân giác của tam giác"]),
    ("Chương V. Dữ liệu và biểu đồ", [
        "Thu thập và phân loại dữ liệu", "Biểu diễn dữ liệu bằng bảng, biểu đồ",
        "Phân tích số liệu thống kê dựa vào biểu đồ"]),
    ("Hoạt động thực hành trải nghiệm (tập một)", [
        "Công thức lãi kép", "Tính toán trên đa thức với GeoGebra",
        "Vẽ hình đơn giản với GeoGebra", "Phân tích đặc điểm khí hậu Việt Nam"]),
    # tập hai — chủ đề lấy từ Bảng tra cứu và Bảng giải thích thuật ngữ cuối sách
    ("Chương VI. Phân thức đại số", [
        "Phân thức đại số", "Điều kiện xác định của phân thức", "Rút gọn phân thức",
        "Quy đồng mẫu thức nhiều phân thức", "Phép cộng và phép trừ phân thức",
        "Phép nhân và phép chia phân thức"]),
    ("Chương VII. Phương trình bậc nhất và hàm số bậc nhất", [
        "Phương trình bậc nhất một ẩn", "Giải bài toán bằng cách lập phương trình",
        "Hàm số và mặt phẳng toạ độ", "Đồ thị của hàm số",
        "Hàm số bậc nhất", "Hệ số góc của đường thẳng"]),
    ("Chương VIII. Mở đầu về tính xác suất của biến cố", [
        "Kết quả có thể và kết quả thuận lợi", "Xác suất thực nghiệm của một biến cố",
        "Xác suất của biến cố trong trường hợp cổ điển"]),
    ("Chương IX. Tam giác đồng dạng", [
        "Hai tam giác đồng dạng", "Tỉ số đồng dạng của hai tam giác",
        "Các trường hợp đồng dạng của hai tam giác", "Định lí Pythagore",
        "Định lí Pythagore đảo", "Hình đồng dạng và hình đồng dạng phối cảnh"]),
    ("Chương X. Một số hình khối trong thực tiễn", [
        "Hình chóp tam giác đều", "Hình chóp tứ giác đều",
        "Diện tích xung quanh của hình chóp đều", "Thể tích của hình chóp đều"]),
    ("Hoạt động thực hành trải nghiệm (tập hai)", [
        "Ứng dụng phương trình bậc nhất trong thực tiễn", "Thực hành tính toán với phần mềm"]),
]

ANH8 = [
    # Global Success: 4 chủ điểm, mỗi chủ điểm 3 unit + 1 bài ôn
    ("Our Communities (Unit 1–3)", [
        "Unit 1: Leisure time", "Unit 2: Life in the countryside", "Unit 3: Teenagers", "Review 1"]),
    ("Our Heritage (Unit 4–6)", [
        "Unit 4: Ethnic groups of Viet Nam", "Unit 5: Our customs and traditions",
        "Unit 6: Lifestyles", "Review 2"]),
    ("Our World (Unit 7–9)", [
        "Unit 7: Environmental protection", "Unit 8: Shopping",
        "Unit 9: Natural disasters", "Review 3"]),
    ("Visions of the Future (Unit 10–12)", [
        "Unit 10: Communication in the future", "Unit 11: Science and technology",
        "Unit 12: Life on other planets", "Review 4"]),
]


def ensure(name: str, chapters: list[tuple[str, list[str]]]):
    with db.SessionLocal() as s:
        sub = s.query(db.Subject).filter(func.lower(db.Subject.name) == name.lower()).first()
        if not sub:
            sub = db.Subject(name=name)
            s.add(sub); s.flush()
            print(f"+ môn {name}")
        have = {c.name: c for c in sub.chapters}
        for i, (cname, topics) in enumerate(chapters):
            ch = have.get(cname)
            if not ch:
                ch = db.Chapter(subject_id=sub.id, name=cname, order=i)
                s.add(ch); s.flush()
                print(f"  + {cname}")
            known = {t.name for t in ch.topics}
            for t in topics:
                if t not in known:
                    s.add(db.Topic(chapter_id=ch.id, name=t))
        s.commit()
        n_ch = len(sub.chapters)
        n_tp = sum(len(c.topics) for c in sub.chapters)
        print(f"= {name}: {n_ch} chương, {n_tp} chủ đề")


if __name__ == "__main__":
    db.init_db()
    ensure("Toán 8", TOAN8)
    ensure("Tiếng Anh 8", ANH8)

    # ghi lai danh muc ra data/topics.json de dung lai duoc CSDL tu dau
    from api.extra import _export_topics_json
    _export_topics_json()
    print("da cap nhat data/topics.json")
