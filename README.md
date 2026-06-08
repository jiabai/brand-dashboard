# Brand Dashboard

多租户品牌监测业务系统。当前主流程以“监测项目”为中心，支持项目配置、采集任务、分析运行、指标快照、问答快照、情感分析、告警、报告和数据质量排障。旧 `tenant_key + job_id` dashboard 与任务页面仍保留为兼容入口，便于历史链接访问和排障。

## 功能特性

- **监测项目**：租户以项目为单位管理目标品牌、竞品、问题集和后续监测结果。
- **采集生命周期**：支持 collection task 领取、lease 防重复、attempt start/complete、失败重试和平台健康度查看。
- **分析运行**：分析结果绑定 `analysis_run_id`，支持失败原因记录、stale 标记和 retry。
- **指标快照**：品牌提及率、首位提及率、Top3 提及率、情绪占比和引用率写入 `metric_snapshots` read model。
- **看板与分析**：legacy dashboard 支持品牌提及、趋势、分平台、信源、情感和问答快照读取。
- **告警与报告**：项目级告警规则、告警事件、报告生成和报告列表 read model。
- **数据质量**：项目数据质量页展示失败采集、过期分析、指标覆盖率和重新分析入口。
- **多租户架构**：租户级数据隔离，支持邀请码注册、租户角色、平台管理员后台和执行器机器身份。

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端框架 | React + Vite | 18 + 5 |
| UI 组件库 | shadcn/ui（基于 Radix UI） | - |
| 样式方案 | Tailwind CSS | 4.x |
| 图表引擎 | 原生 SVG/CSS 轻量图表 | - |
| 图标库 | Lucide React | - |
| 后端框架 | FastAPI + Uvicorn | 0.110+ |
| 数据校验 | Pydantic | v2 |
| ORM | SQLAlchemy | 2.x |
| 数据库 | MySQL | 8.x |
| 容器化 | Docker + Compose | - |

## 项目结构

```text
brand-dashboard/
├── web/                          # 前端 React 应用
│   ├── src/
│   │   ├── api/                  # projects, dashboard, queryJobs, analysisRuns, platform, auth adapters
│   │   ├── auth/                 # 登录态、租户上下文、平台角色
│   │   ├── components/           # 项目、dashboard、平台后台、账户和 UI 组件
│   │   ├── config/               # 路由与菜单配置
│   │   ├── hooks/                # URL 参数、时间窗口、主题 hooks
│   │   ├── lib/                  # 共享工具
│   │   ├── styles/               # 自定义 CSS
│   │   └── utils/                # 路由、展示和指标工具
│   └── package.json
├── api/                          # 后端 FastAPI 服务
│   ├── v1/
│   │   ├── routes/               # projects, dashboard, analysis-runs, collection, auth, platform 等
│   │   ├── models/               # Pydantic 数据模型
│   │   ├── repositories/         # SQL 查询封装
│   │   ├── services/             # 项目、分析、指标、报告、数据质量等业务逻辑
│   │   └── utils/                # 安全、LLM 适配器、日期处理
│   ├── database/                 # SQL Schema 与迁移脚本
│   └── tests/                    # 后端测试
├── analysis/                     # 分析插件与离线兼容入口
├── docs/                         # 架构、规格、执行计划、参考和变更记录
├── scripts/                      # 文档验证等工具脚本
├── docker-compose.dev.yml        # 开发环境编排
└── docker-compose.prod.yml       # 生产环境编排
```

## 快速开始

### 1. 克隆仓库

```bash
git clone <repo-url>
cd brand-dashboard
```

### 2. 启动后端

```bash
uv sync --project api --extra dev
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档：

- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

### 3. 启动前端

```bash
npm --prefix web install
npm --prefix web run dev
```

浏览器访问 http://localhost:3000 。租户用户默认进入 `/projects/:tenantKey`，平台管理员默认进入 `/platform/tenants`。

### 4. 验证

```bash
# 后端健康检查
curl http://localhost:8000/api/v1/health

# 后端测试
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests -q

# 后端代码检查
uv run --project api ruff check api

# 前端测试和构建
npm --prefix web test
npm --prefix web run build

# 文档验证
python scripts/validate_agents_docs.py --level ERROR
python scripts/validate_agents_docs.py --level WARN
```

## 环境变量

### 前端

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VITE_API_TARGET` | 后端 API 地址 | `http://localhost:8000` |
| `VITE_USE_MOCK` | 是否启用本地 mock | `false` |
| `VITE_DEFAULT_EXECUTOR_ID` | 旧任务创建页默认执行器 | `exec_bbda021a` |
| `VITE_DEFAULT_INCLUDE_DELETED` | 旧任务状态页是否默认包含删除任务 | `false` |

### 后端

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_HOST` | 数据库主机 | `127.0.0.1` |
| `DB_PORT` | 数据库端口 | `3306` |
| `DB_USER` | 数据库用户 | `root` |
| `DB_PASSWORD` | 数据库密码 | - |
| `DB_NAME` | 数据库名称 | `geo` |
| `DB_CHARSET` | 数据库字符集 | `utf8mb4` |
| `CORS_ORIGINS` | 允许跨域来源，逗号分隔 | `http://localhost:3000,http://localhost:5173` |
| `PLATFORM_ADMIN_EMAILS` | 平台管理员邮箱白名单 | - |

## API 概览

所有接口挂载在 `/api/v1/` 前缀下：

| 路由组 | 路径 | 说明 |
|--------|------|------|
| Projects | `/api/v1/projects/*` | 项目列表、详情、告警、报告、数据质量 |
| Dashboard | `/api/v1/dashboard/*` | legacy dashboard、问答快照、情感分析等读面 |
| Analysis Runs | `/api/v1/analysis-runs/*` | 分析运行查询和 retry |
| Collection Tasks | `/api/v1/collection-tasks/*` | 执行器领取采集任务 |
| Collection Attempts | `/api/v1/collection-attempts/*` | 采集 attempt start/complete |
| Query Jobs | `/api/v1/query-jobs/*` | legacy 查询任务加载、状态和上报 |
| Conversation | `/api/v1/conversation/*` | 原始回答和引用入库 |
| Platform | `/api/v1/platform/*` | 平台租户管理和采集健康度 |
| Executors | `/api/v1/executors/*` | 执行器注册、管理和认证 |
| Auth | `/api/v1/public/auth/*`、`/api/v1/auth/me` | 登录、激活、注册和当前用户 |
| Config | `/api/v1/config/*` | 系统配置 |

详细领域参考见 [docs/references/20260606-brand-monitoring-domain-data-reference.md](./docs/references/20260606-brand-monitoring-domain-data-reference.md)。

## 前端入口

| 路径 | 说明 |
|------|------|
| `/projects/:tenantKey` | 租户默认入口，项目列表 |
| `/projects/:tenantKey/:projectId` | 项目详情 |
| `/projects/:tenantKey/:projectId/quality` | 项目数据质量 |
| `/accounts/:tenantKey` | 租户账户管理 |
| `/platform/tenants` | 平台租户管理 |
| `/platform/executors` | 平台采集健康度 |
| `/dashboard/:tenantKey/:jobId` 等 | legacy dashboard 兼容入口 |
| `/tasks/:tenantKey/new`、`/tasks/:tenantKey/status` | legacy task 兼容入口 |

## Docker 部署

### 开发模式

```bash
docker compose -f docker-compose.dev.yml up --build
```

| 服务 | 地址 |
|------|------|
| 前端 Vite | http://localhost:8443 |
| 后端 Uvicorn | http://localhost:8000 |

### 生产模式

```bash
docker compose -f docker-compose.prod.yml up --build
```

| 服务 | 地址 |
|------|------|
| 前端 Nginx | http://localhost:8080 |
| 后端 Uvicorn | http://localhost:8091 |

## 文档索引

| 文档 | 说明 |
|------|------|
| [AGENTS.md](./AGENTS.md) | AI 协作规则与常用命令 |
| [WORKFLOW.md](./WORKFLOW.md) | 开发工作流 |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 系统架构与模块地图 |
| [docs/ARCHITECTURE_MULTITENANT.md](./docs/ARCHITECTURE_MULTITENANT.md) | 多租户认证与隔离补充 |
| [docs/DESIGN.md](./docs/DESIGN.md) | UI / API / 数据模型设计规范 |
| [docs/SECURITY.md](./docs/SECURITY.md) | 安全规范 |
| [docs/EXECUTION_GATES.md](./docs/EXECUTION_GATES.md) | 完成门禁 |
| [docs/design-docs/](./docs/design-docs/) | 架构决策与设计评审记录 |
| [docs/changelog/](./docs/changelog/) | 功能变更与实现记录 |
| [docs/product-specs/](./docs/product-specs/) | 产品需求规格 |
| [docs/references/](./docs/references/) | API 与领域数据参考 |
| [docs/exec-plans/](./docs/exec-plans/) | 执行计划 |
| [api/README.md](./api/README.md) | 后端说明 |
| [web/README.md](./web/README.md) | 前端说明 |

## 开发规范

- 提交信息遵循 Conventional Commits。
- 后端使用 `ruff` 和 `pytest`。
- 前端使用 Node test、ESLint 和 Vite build。
- 每次提交根据变更类型在 `docs/` 对应目录创建中文记录。
- 涉及业务行为的阶段必须同步 ExecPlan、reference 或 design 文档。

## 架构原则

- 前后端分离：`web/` 通过 REST API 获取数据，不直接访问数据库。
- 项目优先：租户主流程围绕监测项目，而不是一次性 job。
- 多租户隔离：所有业务查询强制带 `tenant_key`，数据层保证租户过滤。
- 分层依赖：Routes -> Services -> Repositories -> Models。
- 指标快照优先：dashboard、报告、告警和数据质量优先消费 `metric_snapshots`。
- Legacy 可访问但不主推：旧 job/task 路由保留兼容，不作为主导航。
