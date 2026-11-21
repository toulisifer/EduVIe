"""AGENT TỐI GIẢN để học — 1 file, không phụ thuộc phần còn lại của dự án (chỉ mượn API key trong .env).

Chạy:   python -m learn.agent_mini
Thử:    "mấy giờ rồi?"  |  "ghi nhớ: tôi thích học buổi tối"  |  "tôi thích học lúc nào?"  |  "12 * 37 bằng bao nhiêu?"
Rồi thử bỏ 1 tool, đổi SYSTEM, thêm tool mới -> xem hành vi đổi ra sao.
"""
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
KEYS = [k for k in os.getenv("GEMINI_API_KEYS", os.getenv("GEMINI_API_KEY", "")).split(",") if k]
MODEL = "gemini-3.5-flash-lite"


CLIENTS = [genai.Client(api_key=k) for k in KEYS]   # một client cho mỗi key, tạo một lần


def ask_llm(contents, config):
    """Gọi Gemini; key nào hết quota (429) thì thử key kế tiếp."""
    last = None
    for c in CLIENTS:
        try:
            return c.models.generate_content(model=MODEL, contents=contents, config=config)
        except genai.errors.APIError as e:
            last = e
            if e.code != 429:
                raise
    raise RuntimeError(f"Hết quota ở mọi key: {last}")
MEMORY_FILE = Path(__file__).with_name("memory.json")

# ============ 1. VAI TRÒ & LUẬT (system prompt) ============
SYSTEM = """Bạn là trợ lý cá nhân. Luật:
- Cần thông tin thật (giờ, ghi nhớ, tính toán) thì DÙNG TOOL, không đoán.
- Khi người dùng nói điều gì về bản thân họ, hãy gọi remember để lưu lại.
- Trả lời ngắn gọn bằng tiếng Việt."""


# ============ 2. TAY CHÂN (tool = hàm Python + docstring rõ ràng) ============
def get_current_time() -> str:
    """Trả về ngày giờ hiện tại. Dùng khi người dùng hỏi giờ, ngày, hôm nay thứ mấy."""
    return datetime.now().strftime("%H:%M, %A %d/%m/%Y")


def calculate(expression: str) -> str:
    """Tính một biểu thức số học, ví dụ '12*37' hoặc '2**10 + 5'. Dùng cho mọi phép tính, đừng tự nhẩm.

    Args:
        expression: biểu thức Python hợp lệ chỉ gồm số và + - * / ** ( ).
    """
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "Biểu thức không hợp lệ"
    return str(eval(expression))  # chỉ an toàn vì đã lọc ký tự ở trên


def remember(fact: str) -> str:
    """Lưu một sự thật về người dùng vào bộ nhớ dài hạn (sở thích, thói quen, mục tiêu...).

    Args:
        fact: câu ngắn mô tả điều cần nhớ, ví dụ 'thích học buổi tối'.
    """
    mem = json.loads(MEMORY_FILE.read_text()) if MEMORY_FILE.exists() else []
    mem.append({"fact": fact, "at": datetime.now().isoformat(timespec="minutes")})
    MEMORY_FILE.write_text(json.dumps(mem, ensure_ascii=False, indent=1))
    return f"Đã nhớ: {fact}"


def recall() -> list:
    """Đọc toàn bộ những điều đã nhớ về người dùng. Dùng khi câu hỏi liên quan đến bản thân người dùng."""
    return json.loads(MEMORY_FILE.read_text()) if MEMORY_FILE.exists() else []


TOOLS = [get_current_time, calculate, remember, recall]
FN = {f.__name__: f for f in TOOLS}


# ============ 3. VÒNG LẶP AGENT ============
def run(user_text: str, history: list) -> str:
    history.append(types.Content(role="user", parts=[types.Part.from_text(text=user_text)]))
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM, tools=TOOLS, temperature=0.3,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),  # ta tự điều khiển để thấy từng bước
    )
    for step in range(6):                                  # tối đa 6 vòng
        res = ask_llm(history, config)
        cand = res.candidates[0]
        calls = [p.function_call for p in cand.content.parts if p.function_call]
        if not calls:                                      # LLM trả lời bằng văn bản -> xong
            history.append(cand.content)
            return res.text
        history.append(cand.content)                       # ghi lại "LLM muốn gọi tool"
        results = []
        for fc in calls:
            out = FN[fc.name](**dict(fc.args or {}))       # CODE CỦA TA chạy tool thật
            print(f"   🔧 {fc.name}({dict(fc.args or {})}) -> {str(out)[:80]}")
            results.append(types.Part.from_function_response(name=fc.name, response={"result": out}))
        history.append(types.Content(role="user", parts=results))   # đưa kết quả lại cho LLM, lặp tiếp
    return "(dừng vì quá số bước)"


if __name__ == "__main__":
    print("Agent mini. Gõ 'thoát' để dừng.\n")
    history = []
    while True:
        q = input("Bạn: ").strip()
        if q.lower() in ("thoát", "exit", "quit"):
            break
        print("Agent:", run(q, history), "\n")
