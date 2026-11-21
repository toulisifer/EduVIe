"""Thêm môn mới vào taxonomy (bỏ qua môn đã có). Chạy: python -m scripts.add_subjects"""
import json

from app.config import TOPICS_FILE
from app.db import Chapter, SessionLocal, Subject, Topic, init_db

NEW_SUBJECTS = {
    "Vật lí 12": [
        ("Chương 1: Vật lí nhiệt", [
            "Cấu trúc của chất và sự chuyển thể", "Nội năng và định luật I nhiệt động lực học",
            "Nhiệt độ và thang nhiệt độ", "Nhiệt dung riêng", "Nhiệt nóng chảy riêng", "Nhiệt hoá hơi riêng"]),
        ("Chương 2: Khí lí tưởng", [
            "Mô hình động học phân tử chất khí", "Định luật Boyle", "Định luật Charles",
            "Phương trình trạng thái khí lí tưởng", "Áp suất và động năng phân tử"]),
        ("Chương 3: Từ trường", [
            "Từ trường và cảm ứng từ", "Lực từ tác dụng lên dây dẫn", "Từ thông và cảm ứng điện từ",
            "Máy phát điện xoay chiều", "Ứng dụng của hiện tượng cảm ứng điện từ"]),
        ("Chương 4: Vật lí hạt nhân và phóng xạ", [
            "Cấu trúc hạt nhân", "Phản ứng hạt nhân và năng lượng liên kết",
            "Hiện tượng phóng xạ", "Công nghiệp hạt nhân"]),
    ],
    "Hoá học 12": [
        ("Chương 1: Ester – Lipid", ["Ester và lipid", "Xà phòng và chất giặt rửa"]),
        ("Chương 2: Carbohydrate", ["Glucose và fructose", "Saccharose và maltose", "Tinh bột và cellulose"]),
        ("Chương 3: Hợp chất chứa nitrogen", ["Amine", "Amino acid và peptide", "Protein và enzyme"]),
        ("Chương 4: Polymer", ["Đại cương về polymer", "Vật liệu polymer"]),
        ("Chương 5: Pin điện và điện phân", ["Thế điện cực và nguồn điện hoá học", "Điện phân"]),
        ("Chương 6: Đại cương về kim loại", [
            "Cấu tạo và tính chất vật lí của kim loại", "Tính chất hoá học của kim loại",
            "Sự ăn mòn kim loại", "Tách kim loại và tái chế"]),
        ("Chương 7: Nguyên tố nhóm IA và IIA", ["Nguyên tố nhóm IA", "Nguyên tố nhóm IIA"]),
        ("Chương 8: Kim loại chuyển tiếp và phức chất", [
            "Sơ lược về kim loại chuyển tiếp dãy thứ nhất", "Sơ lược về phức chất", "Liên kết và cấu tạo phức chất"]),
    ],
}


def main():
    init_db()
    with SessionLocal() as s:
        for name, chapters in NEW_SUBJECTS.items():
            if s.query(Subject).filter_by(name=name).first():
                print(f"bỏ qua (đã có): {name}")
                continue
            subj = Subject(name=name)
            s.add(subj)
            for i, (ch_name, topics) in enumerate(chapters):
                ch = Chapter(name=ch_name, order=i, subject=subj)
                s.add(ch)
                for t in topics:
                    s.add(Topic(name=t, chapter=ch))
            print(f"thêm: {name} — {len(chapters)} chương, {sum(len(t) for _, t in chapters)} chủ đề")
        s.commit()
        # đồng bộ topics.json
        data = [{"name": sub.name, "chapters": [{"name": c.name, "topics": [t.name for t in c.topics]}
                                                for c in sub.chapters]} for sub in s.query(Subject).all()]
        TOPICS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
