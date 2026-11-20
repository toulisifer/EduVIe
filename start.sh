#!/usr/bin/env bash
# Khởi động VuongEdu: giao diện web (FastAPI, cổng 8000) + tunnel public.
#   ./start.sh              -> web + link public
#   ./start.sh --streamlit  -> thêm bản Streamlit cũ ở cổng 8501 (dự phòng/quản trị)
#   ./start.sh --no-tunnel  -> chỉ chạy nội bộ, không mở link public
# Dừng tất cả: Ctrl+C
cd "$(dirname "$0")" || exit 1
source .venv/bin/activate

pkill -f "uvicorn api.main" 2>/dev/null
pkill -f "streamlit run Home.py" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 1

echo "▶ Khởi động web VuongEdu (FastAPI)…"
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs_web.txt 2>&1 &

if [[ "$*" == *"--streamlit"* ]]; then
  echo "▶ Khởi động bản Streamlit (dự phòng)…"
  nohup streamlit run Home.py --server.address 0.0.0.0 --server.headless true > logs_streamlit.txt 2>&1 &
fi

PUB=""
if [[ "$*" != *"--no-tunnel"* ]]; then
  echo "▶ Mở tunnel public (Cloudflare)…"
  nohup ~/.local/bin/cloudflared tunnel --url http://localhost:8000 --protocol http2 > logs_tunnel.txt 2>&1 &
  for _ in $(seq 1 30); do
    PUB=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' logs_tunnel.txt 2>/dev/null | head -1)
    [[ -n "$PUB" ]] && break
    sleep 1
  done
fi

WSL_IP=$(hostname -I | awk '{print $1}')
echo
echo "==================== VuongEdu ===================="
echo "  Máy này        : http://localhost:8000"
echo "  Cùng Wi-Fi     : http://<IP-may-tinh>:8000   (cần portproxy cổng 8000, xem README)"
[[ -n "$PUB" ]] && echo "  Người ở xa     : $PUB"
echo "  API docs       : http://localhost:8000/docs"
[[ "$*" == *"--streamlit"* ]] && echo "  Streamlit (cũ) : http://localhost:8501"
echo "  IP WSL hiện tại: $WSL_IP"
echo "=================================================="
echo "  Ctrl+C để dừng tất cả."
echo

trap 'echo; echo "⏹ Dừng…"; pkill -f "uvicorn api.main"; pkill -f "streamlit run Home.py"; pkill -f "cloudflared tunnel"; exit 0' INT TERM
tail -f logs_web.txt
