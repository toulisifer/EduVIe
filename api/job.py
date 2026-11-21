"""Việc chạy nền cho các thao tác AI kéo dài (gia sư, lộ trình agent/multi-agent).

Lý do: một lượt gia sư gọi 7 công cụ mất ~190 giây, lộ trình multi-agent còn lâu hơn.
Nếu giữ HTTP request mở suốt thời gian đó thì Cloudflare tunnel cắt ở giây thứ 100 (lỗi 524),
và người dùng cũng không thấy agent đang làm gì. Nay: trả job_id ngay, client hỏi tiến độ.

Trạng thái giữ trong bộ nhớ tiến trình — đủ cho việc ngắn hạn; khởi động lại server thì mất,
client sẽ nhận 404 và báo người dùng gửi lại.
"""
import threading
import time
import traceback
import uuid
from typing import Any, Callable

TTL_SECONDS = 30 * 60      # dọn job đã xong sau 30 phút
_JOBS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()


def _sweep() -> None:
    now = time.time()
    for jid in [k for k, v in _JOBS.items() if v["done_at"] and now - v["done_at"] > TTL_SECONDS]:
        _JOBS.pop(jid, None)


def start(user_id: int, kind: str, fn: Callable[[Callable[[dict], None]], Any]) -> str:
    """Chạy `fn` trong luồng riêng. `fn` nhận một hàm on_step(dict) để báo tiến độ."""
    jid = uuid.uuid4().hex[:12]
    with _LOCK:
        _sweep()
        _JOBS[jid] = {"user_id": user_id, "kind": kind, "status": "running", "steps": [],
                      "result": None, "error": "", "started_at": time.time(), "done_at": None}

    def on_step(step: dict) -> None:
        with _LOCK:
            job = _JOBS.get(jid)
            if job:
                job["steps"].append(step)

    def run() -> None:
        try:
            out = fn(on_step)
            with _LOCK:
                _JOBS[jid].update(status="done", result=out, done_at=time.time())
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            with _LOCK:
                _JOBS[jid].update(status="failed", error=str(e), done_at=time.time())

    threading.Thread(target=run, daemon=True).start()
    return jid


def get(jid: str, user_id: int) -> dict | None:
    """Trạng thái job. Trả None nếu không có hoặc không phải job của người này."""
    with _LOCK:
        job = _JOBS.get(jid)
        if not job or job["user_id"] != user_id:
            return None
        return {"job_id": jid, "kind": job["kind"], "status": job["status"],
                "steps": list(job["steps"]), "result": job["result"], "error": job["error"],
                "seconds": round((job["done_at"] or time.time()) - job["started_at"])}
