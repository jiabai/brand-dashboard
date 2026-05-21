#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=3000
PID_FILE="$SCRIPT_DIR/web.pid"

# 1. 查找占用指定端口的进程 PID
PID=$(lsof -ti :$PORT 2>/dev/null || fuser -n tcp $PORT 2>/dev/null)

# 回退：通过 PID 文件查找
if [ -z "$PID" ] && [ -s "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ! kill -0 "$PID" 2>/dev/null; then
        PID=""
    fi
fi

if [ -z "$PID" ]; then
    echo -e "\033[33mNo process found on port $PORT (already stopped)\033[0m"
    rm -f "$PID_FILE"
    exit 0
fi

# 2. 停止进程
PROCESS_NAME=$(ps -p "$PID" -o comm= 2>/dev/null)
echo -e "\033[36mStopping $PROCESS_NAME (PID: $PID) on port $PORT...\033[0m"
kill "$PID"

# 等待进程退出
sleep 1
if kill -0 "$PID" 2>/dev/null; then
    echo -e "\033[33mProcess did not stop, force killing...\033[0m"
    kill -9 "$PID"
fi

rm -f "$PID_FILE"
echo -e "\033[32mStopped successfully\033[0m"