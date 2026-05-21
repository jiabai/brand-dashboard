#!/usr/bin/env bash

PORT=8000

# 1. 查找占用指定端口的进程 PID
PID=$(lsof -ti :$PORT 2>/dev/null || fuser $PORT/tcp 2>/dev/null | awk '{print $1}')

if [ -z "$PID" ]; then
    echo -e "\033[33mNo process found on port $PORT (already stopped)\033[0m"
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

echo -e "\033[32mStopped successfully\033[0m"