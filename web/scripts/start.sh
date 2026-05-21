#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WEB_ROOT="$PROJECT_ROOT/web"
PID_FILE="$SCRIPT_DIR/web.pid"
LOG_FILE="$SCRIPT_DIR/web.log"

# 检查是否已经在运行
if [ -s "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo -e "\033[33mWeb dev server is already running (PID: $(cat "$PID_FILE"))\033[0m"
    exit 0
fi

# 1. 安装依赖
echo -e "\033[36mInstalling dependencies...\033[0m"
npm --prefix "$WEB_ROOT" install --silent

# 2. 切换到 web 目录并以守护进程模式启动
cd "$WEB_ROOT"
echo -e "\033[32mStarting Web dev server as daemon...\033[0m"
echo -e "\033[33m  URL: http://localhost:3000\033[0m"
echo -e "\033[33m  API: http://localhost:8000\033[0m"
echo -e "\033[33m  Log: $LOG_FILE\033[0m"
echo ""

nohup npm run dev > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

echo -e "\033[32mStarted successfully (PID: $(cat "$PID_FILE"))\033[0m"