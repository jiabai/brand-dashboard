#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
PYPROJECT_PATH="$PROJECT_ROOT/api/pyproject.toml"

# 1. 激活项目级虚拟环境（如果存在）
if [ -d "$VENV_PATH" ]; then
    source "$VENV_PATH/bin/activate"
    echo -e "\033[36mActivated project virtual environment: $VENV_PATH\033[0m"
else
    echo -e "\033[33mUsing current Python environment (no project .venv found)\033[0m"
fi

# 2. 安装依赖
if [ -f "$PYPROJECT_PATH" ]; then
    echo -e "\033[36mInstalling dependencies from pyproject.toml using uv...\033[0m"
    uv pip install -e "$PROJECT_ROOT/api" --quiet
fi

# 3. 切换到项目根目录并启动
cd "$PROJECT_ROOT"
echo -e "\033[32mStarting API server (non-container mode)...\033[0m"
echo -e "\033[33m  Dialect: sqlite (from api/.env)\033[0m"
echo -e "\033[33m  Swagger: http://localhost:8000/api/v1/docs\033[0m"
echo -e "\033[37m  Press Ctrl+C to stop\033[0m"
echo ""

uvicorn api.main:app --reload --host 0.0.0.0 --port 8000