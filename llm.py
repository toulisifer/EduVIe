"""Lớp mỏng bọc Gemini: embedding, sinh text (thường / streaming), sinh JSON theo schema.

Free tier giới hạn request/ngày THEO TỪNG MODEL và THEO TỪNG PROJECT (API key), nên:
- Mỗi tác vụ có danh sách model dự phòng; hết quota (429/ngày) hoặc quá tải (503) -> model kế tiếp.
- Có thể khai báo nhiều key (GEMINI_API_KEYS=key1,key2) -> hết quota mọi model ở key này thì sang key kia.
"""
import json
import os
import time
from pathlib import Path
from typing import Iterator

from google import genai
from google.genai import errors, types

from app.config import DATA_DIR, EMBED_DIM, EMBED_MODEL, GEMINI_API_KEY

# Thứ tự ưu tiên. Sửa/bổ sung nếu Google đổi tên model (xem: client().models.list()).
CHAT_MODELS = ["gemini-3.5-flash", "gemini-3.7-flash", "gemini-3-flash-preview",
               "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
OCR_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest",
              "gemini-3.5-flash", "gemini-3.7-flash", "gemini-3-flash-preview"]

API_KEYS = [k.strip() for k in os.getenv("GEMINI_API_KEYS", GEMINI_API_KEY).split(",") if k.strip()]
_clients: dict[int, genai.Client] = {}
_EXH_FILE = DATA_DIR / "quota_exhausted.json"   # chia sẻ giữa các process


def _load_exhausted() -> set[tuple[int, str]]:
    """Đọc danh sách (key, model) đã hết quota NGÀY HÔM NAY (giờ Pacific, lúc Google reset)."""
    try:
        d = json.loads(_EXH_FILE.read_text())
        if d.get("day") == _pacific_day():
            return {(int(k), m) for k, m in d["items"]}
    except Exception:  # noqa: BLE001
        pass
    return set()


def _pacific_day() -> str:
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) - timedelta(hours=7)).strftime("%Y-%m-%d")


def _mark_exhausted(ki: int, model: str):
    _exhausted.add((ki, model))
    try:
        _EXH_FILE.parent.mkdir(parents=True, exist_ok=True)
        _EXH_FILE.write_text(json.dumps({"day": _pacific_day(), "items": sorted(_exhausted)}))
    except Exception:  # noqa: BLE001
        pass


_exhausted: set[tuple[int, str]] = _load_exhausted()   # (key_idx, model) đã hết quota ngày
_last_call = 0.0
MIN_INTERVAL = 4.0                           # giây giữa 2 request để không vượt RPM free tier


def client(idx: int = 0) -> genai.Client:
    if not API_KEYS:
        raise RuntimeError("Chưa có GEMINI_API_KEY (hoặc GEMINI_API_KEYS) trong file .env")
    if idx not in _clients:
        _clients[idx] = genai.Client(api_key=API_KEYS[idx])
    return _clients[idx]


def _is_daily_quota(e: errors.APIError) -> bool:
    return e.code == 429 and "PerDay" in str(e)


def _throttle():
    global _last_call
    wait = MIN_INTERVAL - (time.time() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.time()


def _iter_candidates(models: list[str]):
    for ki in range(len(API_KEYS)):
        for m in models:
            if (ki, m) not in _exhausted:
                yield ki, m


class HetGio(RuntimeError):
    """Đã dùng hết thời gian cho phép mà chưa gọi được model nào."""


def call_with_fallback(models: list[str], contents, config: types.GenerateContentConfig,
                       han_chot: float | None = None):
    """Gọi generate_content, tự đổi model / key khi hết quota hoặc quá tải. Trả về response.

    `han_chot`: mốc time.monotonic() không được vượt quá. Hết giờ thì ném HetGio.

    Vì sao cần hạn chót: có 4 key × 5 model = 20 tổ hợp, mỗi tổ hợp thử 3 lần với các
    quãng chờ 15s, 30s, 45s. Gặp ngày quota căng thì vòng này ngủ tới 20 × 90 = 1800
    giây. Đo thật: một lần sinh đề 60 câu mất 2419 giây — người học ngồi chờ 40 phút
    mà không biết chuyện gì đang xảy ra. Thà trả về ít câu hơn và nói rõ, còn hơn treo.
    """
    last_err = None
    for ki, model in _iter_candidates(models):
        for attempt in range(3):
            if han_chot is not None and time.monotonic() >= han_chot:
                raise HetGio(f"Hết thời gian chờ AI. Lỗi cuối: {last_err}")
            _throttle()
            try:
                return client(ki).models.generate_content(model=model, contents=contents, config=config)
            except errors.APIError as e:
                last_err = e
                if _is_daily_quota(e) or e.code == 404:
                    _mark_exhausted(ki, model)     # hết quota ngày / model không tồn tại -> bỏ qua luôn
                    break
                if e.code in (429, 500, 503):      # quota phút hoặc server quá tải -> chờ rồi thử lại
                    cho = 15 * (attempt + 1)
                    if han_chot is not None:
                        con = han_chot - time.monotonic()
                        if con <= 0:
                            raise HetGio(f"Hết thời gian chờ AI. Lỗi cuối: {e}") from e
                        cho = min(cho, con)        # đừng ngủ quá hạn chót
                    time.sleep(cho)
                    continue
                raise
    raise RuntimeError(f"Tất cả model/key đều hết quota hoặc lỗi. Lỗi cuối: {last_err}")


def stream_with_fallback(models: list[str], contents, config: types.GenerateContentConfig) -> Iterator[str]:
    """Như call_with_fallback nhưng trả về từng đoạn text (streaming). Chỉ đổi model nếu lỗi xảy ra trước chunk đầu."""
    last_err = None
    for ki, model in _iter_candidates(models):
        _throttle()
        try:
            stream = client(ki).models.generate_content_stream(model=model, contents=contents, config=config)
            started = False
            for chunk in stream:
                if chunk.text:
                    started = True
                    yield chunk.text
            return
        except errors.APIError as e:
            last_err = e
            if started:
                raise
            if _is_daily_quota(e) or e.code == 404:
                _mark_exhausted(ki, model)
            elif e.code in (429, 500, 503):
                time.sleep(15)
            else:
                raise
    raise RuntimeError(f"Tất cả model/key đều hết quota hoặc lỗi. Lỗi cuối: {last_err}")


def embed(texts: list[str], task: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
    """task: RETRIEVAL_DOCUMENT khi index, RETRIEVAL_QUERY khi tìm kiếm."""
    out = []
    batch = 20  # lô nhỏ để không vượt token/phút của free tier
    for i in range(0, len(texts), batch):
        done = False
        for ki in range(len(API_KEYS)):
            for attempt in range(4):
                try:
                    res = client(ki).models.embed_content(
                        model=EMBED_MODEL, contents=texts[i:i + batch],
                        config=types.EmbedContentConfig(task_type=task, output_dimensionality=EMBED_DIM))
                    out.extend(e.values for e in res.embeddings)
                    done = True
                    break
                except errors.APIError as e:
                    if _is_daily_quota(e):
                        break                      # sang key khác
                    if e.code in (429, 500, 503) and attempt < 3:
                        time.sleep(20 * (attempt + 1))
                        continue
                    raise
            if done:
                break
        if not done:
            raise RuntimeError("Hết quota embedding ở mọi key")
        if i + batch < len(texts):
            time.sleep(2)
    return out


def generate(prompt, system: str = "", temperature: float = 0.3) -> str:
    res = call_with_fallback(CHAT_MODELS, prompt,
                             types.GenerateContentConfig(system_instruction=system or None, temperature=temperature))
    return res.text or ""


def generate_stream(prompt, system: str = "", temperature: float = 0.3) -> Iterator[str]:
    return stream_with_fallback(CHAT_MODELS, prompt,
                                types.GenerateContentConfig(system_instruction=system or None, temperature=temperature))


def generate_json(prompt, schema: dict, system: str = "", temperature: float = 0.5,
                  han_chot: float | None = None):
    res = call_with_fallback(CHAT_MODELS, prompt, types.GenerateContentConfig(
        system_instruction=system or None, temperature=temperature,
        response_mime_type="application/json", response_schema=schema), han_chot=han_chot)
    from app.sua_latex import sua
    # Mô hình viết LaTeX bằng một dấu gạch chéo, mà "\f", "\t", "\r" lại là escape hợp
    # lệ của JSON — json.loads nuốt mất tên lệnh, "\frac" thành U+000C + "rac".
    # Đây là chỗ duy nhất mọi JSON do AI sinh ra đi qua, nên vá ở đây là vá được hết.
    return sua(json.loads(res.text))
