# 品牌分析仪表板

React + FastAPI 组成的品牌分析仪表板。前端提供沉浸式的可视化体验，后端提供品牌分析与仪表板数据接口。

## 仓库结构

- `web/`：React 18 + Vite + Tailwind 前端应用，所有 UI/样式与前端依赖都在此目录。
- `api/`：FastAPI 服务，提供品牌分析、配置和仪表板数据接口。
- `Dockerfile`：后端容器配置（uvicorn 运行 `api.main:app`）。
- 其他：`agents_chat/` 记录、`tasks.md` 任务清单、`AGENTS.md` 仓库规范。

## 核心特性（前端）

- 📊 实时数据展示：品牌提及率、模型使用率等关键指标。
- ⏱️ 时间筛选：支持昨天、近7天、近30天。
- 📈 可视化图表：环形进度、进度条等多种展示方式。
- 🎨 现代化设计：渐变与毛玻璃效果，动态网格背景。
- 📱 响应式布局与错误处理：涵盖加载、空状态与错误边界。
- 🌟 丰富微交互：Gooey 粘性导航、Spotlight 卡片等动效。

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
python -m venv .venv && source .venv/bin/activate  # Windows 使用 .venv\\Scripts\\activate
pip install -r api/requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
# API 文档: http://localhost:8000/api/docs
```

开发检查（推荐在提交前执行）：

```bash
pip install -r api/requirements-dev.txt
ruff check api
```

### Docker（后端）

```bash
docker build -t brand-analysis-api .
docker run -p 8000:8000 brand-analysis-api
```

### Docker Compose

- 开发模式（前端开发服，支持热更新）：
  ```bash
  docker compose -f docker-compose.dev.yml up --build
  # 前端: http://localhost:3000
  # 后端: http://localhost:8000
  ```
- 生产模式（前端使用 Nginx 托管构建产物）：
  ```bash
  docker compose -f docker-compose.prod.yml up --build
  ```
  - 前端生产版：`http://localhost:8080`
  - 后端接口：`http://localhost:8091`

> 说明：本项目默认连接局域网内的 MySQL 数据库。
> - `api` 通过环境变量 `DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME` 进行配置。
> - **配置方式**：请在 `docker-compose.dev.yml` 或 `docker-compose.prod.yml` 中将 `DB_HOST` 修改为局域网内数据库服务器的实际 IP 地址（例如 `192.168.1.x`）。
> - 确保该远程数据库已开启远程访问权限，并允许来自本机的连接。

## 开发与规范

- Git Hooks：`husky` 会检查 `agents_chat/` 记录，并调用 `ruff check api` 和 `npm --prefix web run lint/test --if-present`。
- 提交信息：使用 Conventional Commits；代码改动需同时更新一条新的 `agents_chat/YYYYMMDD-HHMMSS-*.md`（中文）。
- 路径别名：前端使用 `@` 指向 `web/src`，`@/components`、`@/lib` 等在 `web/vite.config.js` 中定义。

## 组件与样式索引（web/src）

- 主要组件：`components/BrandMentionRate.jsx`、`components/ModelMentionRates.jsx`、`components/ReferencesTable.jsx`、`components/Sidebar.jsx` 等。
- UI 基础：`components/ui/`；工具方法：`lib/cn.js`、`utils/index.js`。
- 样式文件：`styles/*.css`、`index.css`（全局变量）、`App.css`。

更多部署细节请参考 `DEPLOYMENT.md`。后端接口与数据模型说明见 `api/README.md` 与 `api/DASHBOARD_API_README.md`。
