# 品牌分析仪表板

React + FastAPI 的品牌分析仪表板，前端聚焦沉浸式可视化体验，后端提供品牌分析与仪表板数据接口。

## 目录结构

- `web/`：React 18 + Vite + Tailwind CSS 前端应用
- `api/`：FastAPI 服务，提供分析与仪表板数据接口
- `docker-compose.dev.yml` / `docker-compose.prod.yml`：本地开发与生产部署
- `agents_chat/`：变更记录
- `tasks.md`：任务清单
- `AGENTS.md`：仓库规范

## 技术栈概览

### 前端
- React 18 + Vite 5
- Tailwind CSS 4 + tailwindcss-animate
- Ant Design 5 + @ant-design/icons
- Radix UI + shadcn/ui 组件组合
- Lucide React 图标

### 后端
- FastAPI + Uvicorn
- Pydantic v2
- SQLAlchemy 2 + PyMySQL

## 快速开始

### 前端（web）

```bash
cd web
npm install
npm run dev      # http://localhost:3000
npm run build    # 构建产物位于 web/dist
npm run preview
```

### 后端（api）

```bash
python -m venv .venv
# Windows 使用 .venv\Scripts\activate
# macOS/Linux 使用 source .venv/bin/activate
pip install -r api/requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档：
- Swagger：http://localhost:8000/api/v1/docs
- ReDoc：http://localhost:8000/api/v1/redoc

### 代码检查

```bash
ruff check api
```

## 环境变量

### 前端（web/.env.local）

```bash
VITE_API_TARGET=http://localhost:8000
VITE_USE_MOCK=true
VITE_DEFAULT_TENANT_KEY=tn_1b02b3ef4fbd
VITE_DEFAULT_JOB_ID=job_20260127_223236_989cc4db
VITE_DEFAULT_BRAND=哈基桃电竞
```

### 后端（api/.env 或系统环境变量）

```bash
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=devpassword
DB_NAME=geo
DB_CHARSET=utf8mb4
```

## Docker 与 Compose

### Docker Compose（推荐）

- 开发模式（前端热更新 + 后端服务）：
  ```bash
  docker compose -f docker-compose.dev.yml up --build
  ```
  - 前端：http://localhost:3000
  - 后端：http://localhost:8000
- 生产模式（前端 Nginx 托管构建产物）：
  ```bash
  docker compose -f docker-compose.prod.yml up --build
  ```
  - 前端生产版：http://localhost:8080
  - 后端接口：http://localhost:8091

### 单独构建镜像

- 后端：`api/Dockerfile.dev`、`api/Dockerfile.prod`
- 前端：`web/Dockerfile.dev`、`web/Dockerfile.prod`

## 文档索引

- [api/README.md](./api/README.md)
- [api/docs/DASHBOARD_API_README.md](./api/docs/DASHBOARD_API_README.md)
- [api/docs/METRICS_ALGORITHMS.md](./api/docs/METRICS_ALGORITHMS.md)

## 开发规范

- Git Hooks：提交前执行 `ruff check api` 与 `npm --prefix web run lint/test --if-present`
- 提交信息：Conventional Commits
- 变更记录：新增 `agents_chat/YYYYMMDD-HHMMSS-*.md`（中文）
- 路径别名：`@` 指向 `web/src`，`@/components`、`@/lib` 等见 `web/vite.config.js`
