"""Chặn gõ dồn: giới hạn số lần gọi một endpoint trong một khoảng thời gian.

Vì sao cần: /auth/login và /auth/register không có giới hạn nào, nên thử mật khẩu
được vô hạn — mà mật khẩu tối thiểu chỉ 4 ký tự — và tạo tài khoản hàng loạt được,
đó là cửa vào để bơm dữ liệu huấn luyện DKT.

(/auth/reset-password đã có sẵn cơ chế riêng: sai 5 lần thì khoá 15 phút, lưu trong
bảng users — xem app/db.py:reset_password_with_code. Ở đây không đụng vào.)

Đếm trong bộ nhớ tiến trình: đủ cho một máy chủ. Chạy nhiều tiến trình thì mỗi tiến
trình đếm riêng, tức là giới hạn thật lỏng gấp số tiến trình — chấp nhận được, vì đây
là lớp chặn thứ hai chứ không phải lớp duy nhất.
"""
from __future__ import annotations

import threading
import time

from fastapi import HTTPException, Request, status

_KHOA = threading.Lock()
_DAU_VET: dict[str, list[float]] = {}
_LAN_DON = [0.0]
CHU_KY_DON = 300          # dọn dấu vết cũ mỗi 5 phút


def _don(bay_gio: float) -> None:
    if bay_gio - _LAN_DON[0] < CHU_KY_DON:
        return
    _LAN_DON[0] = bay_gio
    for k in [k for k, v in _DAU_VET.items() if not v or bay_gio - v[-1] > 3600]:
        _DAU_VET.pop(k, None)


def dia_chi(req: Request) -> str:
    """IP người gọi. Sau proxy/tunnel thì lấy chặng đầu của X-Forwarded-For."""
    xff = req.headers.get("x-forwarded-for", "")
    if xff:
        return xff.split(",")[0].strip()
    return req.client.host if req.client else "?"


def chan(khoa: str, so_lan: int, trong_giay: int, thong_bao: str) -> None:
    """Cho phép tối đa `so_lan` lượt trong `trong_giay` giây. Quá thì ném 429."""
    bay_gio = time.time()
    with _KHOA:
        _don(bay_gio)
        moc = _DAU_VET.setdefault(khoa, [])
        moc[:] = [t for t in moc if bay_gio - t < trong_giay]
        if len(moc) >= so_lan:
            cho = int(trong_giay - (bay_gio - moc[0])) + 1
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                                f"{thong_bao} Thử lại sau {cho} giây.")
        moc.append(bay_gio)


def xoa_dau_vet(khoa_bat_dau: str = "") -> None:
    """Xoá bộ đếm — dùng trong kiểm thử, hoặc sau khi đăng nhập đúng."""
    with _KHOA:
        for k in [k for k in _DAU_VET if k.startswith(khoa_bat_dau)]:
            _DAU_VET.pop(k, None)
