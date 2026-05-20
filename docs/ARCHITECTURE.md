# Architecture

## 概述

Brand Analysis Dashboard 是一个品牌分析仪表板应用，前端 React 18 + shadcn/ui（基于 Radix UI）+ Tailwind 提供可视化界面，后端 FastAPI + SQLAlchemy + MySQL 提供多租户数据服务。前后端通过 REST API 通信，支持 Docker 部署。

## 模块地图

```
brand-dashboard/
├── web/                          # 前端（React 18 + Vite）
│   ├── src/
│   │   ├── api/                  # 前端 API Adapter（dashboard, queryJobs, auth）
│   │   ├── components/           # 功能组件
│   │   │   └── ui/               # shadcn/ui 可复用 UI 原语（button, card, table, dialog 等）
│   │   ├── config/               # 前端路由等静态配置（routes.js）
│   │   ├── lib/                  # 共享工具（cn.js）
│   │   ├── utils/                # 业务工具（domainCitationQuery, sourceAnalysis, trendChartConfig）
│   │   ├── hooks/                # 路由与页面级 hooks（useDashboardParams, useTimeframeManager）
│   │   ├── styles/               # 组件级 CSS
│   │   ├── App.jsx               # 路由定义与主题入口
│   │   ├── config.js             # 环境变量配置
│   │   └── main.jsx              # 挂载入口
│   └── package.json
├── api/                          # 后端（FastAPI）
│   ├── v1/
│   │   ├── routes/               # 路由层：dashboard, auth, analysis, brand_strategy, config, query_jobs, executors, conversation
│   │   ├── models/schemas.py     # Pydantic 模型
│   │   ├── repositories/         # 数据访问层：database.py, auth.py, query_jobs.py, executors.py, conversation.py, tenants.py
│   │   ├── services/             # 业务逻辑层：llm_client.py
│   │   └── utils/                # 工具层：security, llm_adapters, llm_operator, url_domain_resolver
│   ├── database/                 # SQL Schema（schema.sql, schema_auth.sql, schema_business.sql）
│   ├── main.py                   # FastAPI 应用入口
│   └── pyproject.toml
├── docs/                         # 项目文档
└── scripts/                      # 工具脚本
```

## 关键文件

| 文件 | 职责 |
|------|------|
| `web/src/App.jsx` | 前端主题入口与 React Router 路由定义 |
| `web/src/config/routes.js` | 前端路由、菜单、任务入口的单一配置源 |
| `web/src/api/index.js` | 前端 API Adapter 出口，统一封装 dashboard/query-jobs/auth 请求 |
| `web/src/components/DashboardLayout.jsx` | 仪表板壳层，负责 Header、Sidebar、时间筛选控件和子路由 Outlet |
| `web/src/hooks/useDashboardParams.js` | 统一读取路径参数与查询参数，提供 URL 查询参数更新入口 |
| `web/src/hooks/useTimeframeManager.js` | 仪表板时间范围、可用日期、日期参数同步逻辑 |
| `web/src/config.js` | 环境变量入口，API 地址和默认业务参数 |
| `api/main.py` | FastAPI 应用入口，CORS 配置，路由注册 |
| `api/v1/routes/dashboard.py` | 仪表板核心 API（品牌提及率、引用统计、平台指标） |
| `api/v1/routes/auth.py` | 多租户认证（租户创建、用户注册、邀请码验证） |
| `docs/ARCHITECTURE_MULTITENANT.md` | 多租户认证、租户上下文、平台/执行器权限与数据隔离补充架构 |
| `api/v1/repositories/database.py` | 数据访问层，所有 SQL 查询的入口 |
| `api/v1/repositories/query_jobs.py` | 查询任务数据访问（状态同步、任务拉取、上报计数、批量加载） |
| `api/v1/repositories/executors.py` | 执行器数据访问（创建、注册校验、列表、禁用） |
| `api/v1/repositories/conversation.py` | 对话与引用数据入库访问 |
| `api/v1/repositories/tenants.py` | 租户存在性校验等共享租户查询 |
| `api/v1/models/schemas.py` | Pydantic 模型定义，API 请求/响应的数据契约 |
| `api/database/schema.sql` | 完整数据库 Schema（租户 + 用户 + 业务表） |

## 架构不变量

- 前后端分离：前端只通过 REST API 获取数据，不直接访问数据库
- 多租户隔离：所有业务查询必须带 `tenant_key`，数据层强制租户过滤
- 多租户授权：前端 URL 中的 `tenantKey` 只是当前租户选择信号；后端必须通过认证依赖校验用户、租户状态、成员关系和角色后，才能把 `tenant_key` 传入 Repository
- 身份分区：用户接口使用 `Authorization: Bearer <access_token>`；执行器接口使用 `executor_id` + `X-Executor-Key`，两类身份不能混用
- 分层依赖方向：Routes → Services → Repositories → Models，禁止反向依赖
- API 版本化：所有路由挂载在 `/api/v1/` 前缀下
- 组件懒加载：前端功能组件使用 `React.lazy()` 按需加载
- 前端页面路由：使用 `react-router-dom`，分析类页面路径携带 `tenantKey + jobId`，租户级页面路径只携带 `tenantKey`

## 架构边界

- 前端 `web/` 和后端 `api/` 是独立部署单元，通过 HTTP 通信
- 前端开发服务器（Vite）代理 API 请求到后端
- 数据库只被 `api/v1/repositories/` 访问，路由层不直接写 SQL
- LLM 服务通过 `api/v1/services/llm_client.py` 统一封装
