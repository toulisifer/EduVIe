#!/usr/bin/env bash
cd "$(dirname "$0")/.." || exit 1
pkill -f "uvicorn api.main" 2>/dev/null
sleep 1
setsid nohup .venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs_web.txt 2>&1 < /dev/null &
sleep 9
echo restarted
