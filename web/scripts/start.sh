#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WEB_ROOT="$PROJECT_ROOT/web"

# 1. 安装依赖
echo -e "\033[36mInstalling dependencies...\033[0m"
npm --prefix "$WEB_ROOT" install --silent

# 2. 切换到 web 目录并启动
cd "$WEB_ROOT"
echo -e "\033[32mStarting Web dev server (non-container mode)...\033[0m"
echo -e "\033[33m  URL: http://localhost:3000\033[0m"
echo -e "\033[33m  API: http://localhost:8000\033[0m"
echo -e "\033[37m  Press Ctrl+C to stop\033[0m"
echo ""

npm run dev