# Architecture

## 概述

Brand Dashboard 当前已从单纯的 `tenant_key + job_id` 品牌分析看板，演进为以“监测项目”为主线的多租户品牌监测业务系统。前端使用 React 18 + shadcn/ui + Tailwind，后端使用 FastAPI + SQLAlchemy + MySQL。系统仍保留旧 dashboard 和 query job 路由作为兼容排障入口，但用户主流程已经从 `/projects/:tenantKey` 进入。

核心业务链路：

```text
租户 / 项目
  -> 品牌、竞品、问题集配置
  -> 采集批次、采集任务、执行尝试
  -> 原始回答与引用入库
  -> 分析运行与事实血缘
  -> 事实聚合指标
  -> dashboard、问答快照、情感分析、告警、报告、数据质量
```

## 模块地图

```text
brand-dashboard/
├── web/                          # 前端 React 18 + Vite
│   ├── src/
│   │   ├── api/                  # API Adapter：projects, dashboard, queryJobs, analysisRuns, platform, auth
│   │   ├── auth/                 # 登录态、租户选择、平台角色判断
│   │   ├── components/           # 功能组件
│   │   │   ├── projects/         # 项目列表、详情、数据质量
│   │   │   ├── platform/         # 平台运营后台
│   │   │   └── ui/               # shadcn/ui 可复用 UI 原语
│   │   ├── config/               # 路由、菜单、legacy 入口配置
│   │   ├── hooks/                # URL 参数、时间窗口、主题等 hooks
│   │   ├── lib/                  # 共享工具 cn.js
│   │   ├── utils/                # 路由、指标、筛选和展示工具
│   │   ├── App.jsx               # React Router 路由定义
│   │   └── config.js             # 前端环境变量入口
│   └── package.json
├── api/                          # 后端 FastAPI
│   ├── v1/
│   │   ├── routes/               # projects, dashboard, analysis-runs, collection, query-jobs, auth, platform, executors
│   │   ├── models/schemas.py     # Pydantic 请求/响应契约
│   │   ├── repositories/         # 数据访问层，所有业务查询强制 tenant_key
│   │   ├── services/             # 项目、分析、事实指标、告警、报告、数据质量等业务逻辑
│   │   └── utils/                # 安全、LLM adapter、日期和 URL 工具
│   ├── database/                 # MySQL/SQLite schema 与迁移脚本
│   ├── tests/                    # 后端回归测试
│   └── main.py                   # FastAPI 应用入口
├── analysis/                     # 可复用分析插件和离线分析兼容入口
├── docs/                         # 项目文档、执行计划、变更记录
└── scripts/                      # 文档验证等工具脚本
```

## 关键文件

| 文件 | 职责 |
|------|------|
| `web/src/config/routes.js` | 路由、主菜单、legacy 路由和 App route 生成的单一配置源 |
| `web/src/App.jsx` | 前端路由定义；租户用户默认进入项目列表，平台管理员进入平台后台 |
| `web/src/components/Sidebar.jsx` | 租户工作台侧边栏；当前主入口为“监测项目”和“加入团队”，平台管理员只读客户视角隐藏加入入口 |
| `web/src/components/projects/` | 项目列表、项目详情、项目数据质量页面和展示归一化逻辑 |
| `web/src/api/index.js` | 前端 API Adapter 出口，避免组件中手写 URL |
| `api/main.py` | FastAPI 应用入口、CORS、路由注册和健康检查 |
| `api/v1/routes/projects.py` | 项目列表、详情、告警、报告和数据质量 API |
| `api/v1/routes/collection_tasks.py` | 执行器采集任务领取 API |
| `api/v1/routes/collection_attempts.py` | 采集 attempt start/complete API |
| `api/v1/routes/analysis_runs.py` | 分析运行查询与 retry API |
| `api/v1/routes/dashboard.py` | legacy dashboard 读面，含问答快照和情感分析真实数据接口 |
| `api/v1/repositories/fact_metrics.py` | 基于 `qa_brand_state` / `qa_reference` 聚合 `brand_metrics_v1` 指标口径 |
| `api/v1/services/analysis_runner.py` | 系统级分析运行编排，调用 `analysis/` 插件并写入事实血缘 |
| `api/v1/services/reports.py` | 项目报告生成和报告列表 read model |
| `api/v1/services/data_quality.py` | 项目级失败采集、过期分析和指标覆盖率聚合 |
| `docs/references/20260606-brand-monitoring-domain-data-reference.md` | 本次重构的领域模型、API 和数据生命周期参考 |

## 架构不变量

- 前后端分离：`web/` 只通过 REST API 获取数据，不直接访问数据库。
- 项目优先：租户用户默认进入 `/projects/:tenantKey`；项目承载品牌、竞品、问题集、采集、分析、指标、告警、报告和数据质量。
- Legacy 兼容边界：系统只兼容历史资产，包括历史链接、历史数据、排障读面和兼容期桥接字段；不兼容历史产品形态。`/dashboard/:tenantKey/:jobId`、`/tasks/:tenantKey/status` 等旧 job/task 路由继续可直接访问，但不再暴露为主导航入口；新主流程、新页面和新 API 不再把 `job_id` 作为产品入口。
- 多租户隔离：所有业务查询必须显式携带服务端校验后的 `tenant_key`，Repository 层强制租户过滤。
- 数据生命周期分层：配置层、采集层、原始层、分析事实层、事实聚合指标、洞察交付层各自有明确边界。
- 指标口径：dashboard、报告、告警和数据质量基于 `qa_brand_state` / `qa_reference` 按 `brand_metrics_v1` 实时聚合；报告和告警事件继续持久化生成时结果。
- 分析血缘：分析结果必须绑定 `analysis_run_id`，并能追溯到 `project_id`、`collection_job_id` 和指标口径版本。
- 身份分区：用户接口使用 `Authorization: Bearer <access_token>`；执行器接口使用 `executor_id + X-Executor-Key`；两类身份不能混用。
- 平台运营后台：`/platform/*` 不属于租户工作台，不发送 `X-Tenant-Key`，平台 API 使用 `platform_admin` 鉴权。
- 分层依赖方向：Routes -> Services -> Repositories -> Models，禁止反向依赖和跨层直接访问。
- API 版本化：所有业务 API 挂载在 `/api/v1/` 前缀下。

## 领域模型主线

| 层级 | 代表数据 | 当前落地状态 |
|------|----------|--------------|
| 项目配置 | `monitoring_projects`、`project_brands`、`prompt_sets`、`prompt_items` | 项目列表、详情、品牌和问题集配置 API 已落地 |
| 采集生命周期 | `collection_jobs`、`collection_tasks`、`collection_attempts` | 采集任务领取、attempt start/complete 和平台健康度已落地 |
| 原始数据 | `llm_conversations`、`llm_conversation_references` | 兼容期继续使用旧表，通过 `collection_jobs.source_job_id` 桥接 |
| 分析运行 | `analysis_runs`、`qa_brand_state.analysis_run_id`、`qa_reference.analysis_run_id` | 分析运行状态机、retry 和插件接入已落地 |
| 事实聚合指标 | `qa_brand_state`、`qa_reference`、`api/v1/repositories/fact_metrics.py` | `brand_metrics_v1` 基于成功分析事实聚合 |
| 洞察交付 | `alert_rules`、`alert_events`、`generated_reports`、项目数据质量 API | 告警、报告、数据质量 MVP 已落地 |

## 前端路由策略

| 路由类别 | 路径 | 状态 |
|----------|------|------|
| 项目主流程 | `/projects/:tenantKey`、`/projects/:tenantKey/:projectId`、`/projects/:tenantKey/:projectId/quality` | 主入口 |
| 加入团队 | `/accounts/:tenantKey` | 租户成员入口，保留历史路径 |
| 平台后台 | `/platform/tenants`、`/platform/executors` | 平台管理员入口 |
| legacy dashboard | `/dashboard/:tenantKey/:jobId`、`/trend/:tenantKey/:jobId`、`/platforms/:tenantKey/:jobId`、`/sources/:tenantKey/:jobId`、`/sentiment/:tenantKey/:jobId`、`/snapshots/:tenantKey/:jobId` | 直接访问可用，不在主导航中展示 |
| legacy task | `/tasks/:tenantKey/new`、`/tasks/:tenantKey/status` | 直接访问可用，不在主导航中展示 |

路由配置以 `web/src/config/routes.js` 为单一策略源：`getProductShapeRoutes()` 表示当前产品形态，必须保持项目优先且不依赖 `job_id`；`getLegacyCompatibilityRoutes()` 表示历史兼容资产，只允许作为直接访问和排障入口保留。

## 架构边界

- 前端开发服务器通过 Vite 代理 `/api` 到后端，生产环境由 Nginx 承载静态资源。
- 数据库只允许 `api/v1/repositories/` 访问；路由层不直接写 SQL。
- `analysis/` 插件作为系统分析服务的可调用库接入，后续可独立 worker 化，但当前仍属于模块化单体边界。
- 平台后台只处理平台元数据、租户运营和执行器健康，不直接拥有租户写权限。
