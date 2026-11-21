"""Kiểm tra tiên quyết liên lớp: yếu chủ đề lớp 8 thì chủ đề lớp 12 phụ thuộc nó phải bị chặn.

Dữ liệu thử được chèn rồi xoá sạch, không để lại gì trong CSDL.
  python -m scripts.test_prereq_crossgrade
"""
from datetime import datetime

from app import analytics, db
from app.learning import prereq_mastery, prerequisites, recommend_quiz, weak_prereqs

PRE_TOPIC = "Phân thức đại số"      # Toán 8
POST_TOPIC = "Đường tiệm cận"       # Toán 12, cần nền trên

db.init_db()
with db.SessionLocal() as s:
    u = s.query(db.User).filter_by(username="demo").first()
    pre_t = s.query(db.Topic).filter_by(name=PRE_TOPIC).first()
    post_t = s.query(db.Topic).filter_by(name=POST_TOPIC).first()
    assert u and pre_t and post_t, "thiếu user demo hoặc chủ đề"
    uid, pre_id, post_id = u.id, pre_t.id, post_t.id

pre = prerequisites()
print(f"cạnh trong đồ thị: {POST_TOPIC} cần {[pre_id]} -> {pre_id in pre.get(post_id, [])}")

m = prereq_mastery(uid)
print("trước khi chèn:", weak_prereqs(post_id, m, pre) or "không bị chặn")

# chèn 6 câu sai cho chủ đề lớp 8 -> mastery = 0% -> mức Yếu
with db.SessionLocal() as s:
    ids = []
    for _ in range(6):
        a = db.Answer(user_id=uid, topic_id=pre_id, difficulty="medium",
                      is_correct=False, answered_at=datetime.utcnow())
        s.add(a); s.flush(); ids.append(a.id)
    s.commit()

try:
    m2 = prereq_mastery(uid)
    row = m2[m2["topic_id"] == pre_id].iloc[0]
    print(f"sau khi chèn: {PRE_TOPIC} = {row['mastery']}% ({row['level']}, {row['n']} câu)")
    blocked = weak_prereqs(post_id, m2, pre)
    print(f"{POST_TOPIC} bị chặn bởi: {blocked or 'không gì'}")
    assert blocked == [PRE_TOPIC], "cạnh liên lớp KHÔNG hoạt động"

    rec = recommend_quiz(uid, subject_id=1, n_topics=2)
    names = [t[1] for t in rec["topics"]]
    print("đề xuất luyện tiếp (Toán 12):", names)
    assert POST_TOPIC not in names, "vẫn đề xuất chủ đề đang bị chặn"
    print("\nOK: yếu chủ đề lớp 8 thì chủ đề lớp 12 phụ thuộc nó bị loại khỏi đề xuất.")
finally:
    with db.SessionLocal() as s:
        for i in ids:
            a = s.get(db.Answer, i)
            if a:
                s.delete(a)
        s.commit()
    left = analytics.topic_mastery(uid, None)
    left = left[left["topic_id"] == pre_id].iloc[0]
    print(f"đã dọn dữ liệu thử — {PRE_TOPIC} còn {left['n']} câu")
