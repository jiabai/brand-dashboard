# Brand Analysis Dashboard

品牌分析仪表板 —— 多租户品牌数据可视化平台，提供品牌提及率、情感分析、趋势洞察、来源分析等一站式品牌监测能力。

## 功能特性

- **品牌提及率分析**：按平台、关键词维度统计品牌提及率，支持 Top 3 品牌对比
- **情感分析**：正面/中性/负面情感分布可视化
- **趋势分析**：品牌提及趋势随时间变化的折线图与热力图
- **来源分析**：域名级引用来源统计，支持词云与排名展示
- **平台详情**：按平台（抖音、B站、小红书等）拆分品牌声量份额
- **多租户架构**：租户级数据隔离，支持邀请码注册与角色权限管理
- **查询任务管理**：异步查询任务创建、状态追踪与结果查看
- **响应式布局**：适配桌面端与移动端，支持暗色模式扩展

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | React + Vite | 18 + 5 |
| UI 组件库 | Ant Design | 5.x |
| 样式方案 | Tailwind CSS | 4.x |
| 图表引擎 | @ant-design/charts (G2) | 5.x |
| 后端框架 | FastAPI + Uvicorn | 0.110+ |
| 数据校验 | Pydantic | v2 |
| ORM | SQLAlchemy | 2.x |
| 数据库 | MySQL | 8.x |
| 容器化 | Docker + Compose | — |

## 项目结构

```
brand-dashboard/
├── web/                          # 前端 React 应用
│   ├── src/
│   │   ├── components/           # 功能组件（仪表板、分析、账户管理等）
│   │   │   └── ui/               # 可复用 UI 原语（Button, Card, Progress, Table）
│   │   ├── lib/                  # 共享工具（cn.js 样式合并）
│   │   ├── utils/                # 业务工具（域名引用、来源分析、趋势图表配置）
│   │   ├── styles/               # 组件级自定义 CSS
│   │   ├── App.jsx               # 根布局（路由 + 全局状态）
│   │   └── config.js             # 环境变量配置入口
│   └── mock/                     # 本地 Mock 数据
├── api/                          # 后端 FastAPI 服务
│   ├── v1/
│   │   ├── routes/               # 路由层（dashboard, auth, analysis, brand_strategy 等）
│   │   ├── models/               # Pydantic 数据模型
│   │   ├── repositories/         # 数据访问层（SQL 查询封装）
│   │   ├── services/             # 业务逻辑层（LLM 客户端等）
│   │   └── utils/                # 工具层（安全、LLM 适配器、日期处理）
│   ├── database/                 # SQL Schema 定义
│   └── tests/                    # 后端测试
├── docs/                         # 项目文档（架构、设计、安全、产品规格等）
├── scripts/                      # 工具脚本（文档验证）
├── docker-compose.dev.yml        # 开发环境编排
└── docker-compose.prod.yml       # 生产环境编排
```

## 前置要求

- **Node.js** >= 18（推荐 20 LTS）
- **Python** >= 3.10
- **MySQL** >= 8.0
- **Docker**（可选，用于容器化部署）

## 快速开始

### 1. 克隆仓库

```bash
git clone <repo-url>
cd brand-dashboard
```

### 2. 启动后端

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r api/requirements.txt
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档自动生成：
- Swagger UI：http://localhost:8000/api/v1/docs
- ReDoc：http://localhost:8000/api/v1/redoc

### 3. 启动前端

```bash
cd web
npm install
npm run dev
```

浏览器访问 http://localhost:3000

### 4. 验证

```bash
# 后端健康检查
curl http://localhost:8000/api/v1/health

# 前端构建验证
npm --prefix web run build
```

## 环境变量

### 前端 (`web/.env.local`)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VITE_API_TARGET` | 后端 API 地址 | `http://localhost:8000` |
| `VITE_USE_MOCK` | 是否启用 Mock 数据 | `true` |
| `VITE_DEFAULT_TENANT_KEY` | 默认租户标识 | `tn_1b02b3ef4fbd` |
| `VITE_DEFAULT_JOB_ID` | 默认查询任务 ID | `job_20260127_223236_989cc4db` |
| `VITE_DEFAULT_BRAND` | 默认品牌名称 | `哈基桃电竞` |

### 后端 (`api/.env` 或系统环境变量)

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_HOST` | 数据库主机 | `127.0.0.1` |
| `DB_PORT` | 数据库端口 | `3306` |
| `DB_USER` | 数据库用户 | `root` |
| `DB_PASSWORD` | 数据库密码 | — |
| `DB_NAME` | 数据库名称 | `geo` |
| `DB_CHARSET` | 数据库字符集 | `utf8mb4` |

## API 概览

所有接口挂载在 `/api/v1/` 前缀下：

| 路由组 | 路径 | 说明 |
|--------|------|------|
| Dashboard | `/api/v1/dashboard/*` | 仪表板核心数据（品牌提及率、引用统计、平台指标） |
| Auth | `/api/v1/auth/*` | 多租户认证（注册、登录、邀请码验证） |
| Analysis | `/api/v1/analysis/*` | 品牌分析（情感、趋势、来源） |
| Brand Strategy | `/api/v1/brand_strategy/*` | 品牌策略数据 |
| Query Jobs | `/api/v1/query-jobs/*` | 异步查询任务管理 |
| Executors | `/api/v1/executors/*` | 查询执行器管理 |
| Conversation | `/api/v1/conversation/*` | LLM 对话接口 |
| Config | `/api/v1/config/*` | 系统配置 |

详细 API 文档见 [api/docs/DASHBOARD_API_README.md](./api/docs/DASHBOARD_API_README.md)

## Docker 部署

### 开发模式（热更新）

```bash
docker compose -f docker-compose.dev.yml up --build
```

| 服务 | 地址 |
|------|------|
| 前端 (Vite HMR) | http://localhost:8443 |
| 后端 (Uvicorn) | http://localhost:8000 |

### 生产模式（Nginx 静态托管）

```bash
docker compose -f docker-compose.prod.yml up --build
```

| 服务 | 地址 |
|------|------|
| 前端 (Nginx) | http://localhost:8080 |
| 后端 (Uvicorn) | http://localhost:8091 |

## 测试

```bash
# 后端测试
pytest api/tests/

# 前端测试
npm --prefix web test

# 后端代码风格检查
ruff check api

# 文档结构验证
python scripts/validate_agents_docs.py --level ERROR
```

## 文档索引

| 文档 | 说明 |
|------|------|
| [AGENTS.md](./AGENTS.md) | AI 协作规则与常用命令 |
| [WORKFLOW.md](./WORKFLOW.md) | 开发工作流（Spec → Plan → 实现 → 验证） |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 系统架构与模块地图 |
| [docs/DESIGN.md](./docs/DESIGN.md) | UI/API/数据模型设计规范 |
| [docs/SECURITY.md](./docs/SECURITY.md) | 安全规范（认证、授权、数据隔离） |
| [docs/EXECUTION_GATES.md](./docs/EXECUTION_GATES.md) | 任务完成门禁与验证清单 |
| [api/README.md](./api/README.md) | 后端详细说明 |
| [api/docs/DASHBOARD_API_README.md](./api/docs/DASHBOARD_API_README.md) | 仪表板 API 文档 |
| [api/docs/METRICS_ALGORITHMS.md](./api/docs/METRICS_ALGORITHMS.md) | 指标算法说明 |
| [web/README.md](./web/README.md) | 前端详细说明 |

## 开发规范

- **提交信息**：遵循 [Conventional Commits](https://www.conventionalcommits.org/)
- **代码风格**：后端 `ruff`，前端 ESLint（通过 Vite）
- **Git Hooks**：提交前自动执行 `ruff check api` 与前端 lint
- **变更记录**：根据变更类型在 `docs/` 对应子目录新增记录（中文）
- **路径别名**：`@` 映射到 `web/src`，支持 `@/components`、`@/lib` 等导入

## 架构原则

- **前后端分离**：`web/` 通过 REST API 获取数据，不直接访问数据库
- **多租户隔离**：所有业务查询强制带 `tenant_key`，数据层保证租户隔离
- **分层依赖**：Routes → Services → Repositories → Models，禁止反向依赖
- **API 版本化**：所有路由挂载 `/api/v1/`，便于后续版本演进
- **组件懒加载**：前端功能组件使用 `React.lazy()` 按需加载