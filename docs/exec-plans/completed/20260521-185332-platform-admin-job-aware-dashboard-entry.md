# 平台管理员 Job 感知看板入口实施计划

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

平台管理员登录后的平台租户列表需要展示 job 上下文，因为 dashboard 的最小访问单元是 `tenant_key + job_id`，目标品牌则由 URL `brand` 查询参数驱动。本计划让平台租户接口返回每个租户的 job 摘要，并让前端使用真实 job 和目标品牌构造 dashboard 入口，避免使用全局默认 job 或从品牌排名中误选竞品。

## Progress

- [x] Phase 0: 阅读 AGENTS、架构、设计、PRD、多租户补充文档，确认 dashboard 粒度为 `tenant_key + job_id`（2026-05-21）
- [x] Phase 1: 规格与计划落档，创建 TASKS（2026-05-21）
- [x] Phase 2: TDD 红灯，新增后端与前端契约测试（2026-05-21）
- [x] Phase 3: 后端平台租户列表返回 job 摘要（2026-05-21）
- [x] Phase 4: 前端平台租户列表展示 job 信息并提供真实 dashboard 入口（2026-05-21）
- [x] Phase 5: 验证、文档同步、归档 ExecPlan 并删除 TASKS（2026-05-21）

## Surprises & Discoveries

- 2026-05-21：已有文档已经补充 `tenant_key + job_id` 不变量，但平台租户列表实现仍只展示租户维度。
- 2026-05-21：现有平台租户入口跳到 `/tasks/<tenantKey>/status`，避免了默认 job，但登录后的首屏仍没有 job 信息。
- 2026-05-21：`TASKS.md` 在任务进行中会触发文档验证脚本的标准区段错误；完成后删除该文件并重跑文档验证。

## Decision Log

| Decision | Rationale | Date/Author |
|---|---|---|
| 在 `/api/v1/platform/tenants` 返回 job 摘要 | 平台登录首屏本来就是租户列表，附带最近 job 和计数可直接满足 job 感知，不新增额外 round-trip | 2026-05-21 / agent |
| dashboard 入口使用最近 job | 首屏需要一个可用入口；完整 job 列表仍由任务状态页承载 | 2026-05-21 / agent |
| 无 job 时禁用 dashboard 入口 | Dashboard 无 `job_id` 不能正确查询，禁用比拼接占位符更安全 | 2026-05-21 / agent |
| dashboard 入口必须携带 `latestJob.brand` | dashboard 缺少 `brand` 时会按品牌指标列表第一个品牌自动补齐，竞品可能因提及率更高而被误设为目标品牌 | 2026-05-21 / agent |

## Context and Orientation

相关文件：

| 类型 | 文件 |
|---|---|
| 新增 | `docs/product-specs/20260521-185332-platform-admin-job-aware-dashboard-entry.md` |
| 修改 | `api/v1/repositories/tenants.py` |
| 修改 | `api/v1/routes/auth.py` |
| 修改 | `api/tests/test_platform_tenants.py` |
| 修改 | `web/src/components/platform/PlatformTenantsPage.jsx` |
| 修改 | `web/src/components/platform/tenantPresentation.js` |
| 修改 | `web/src/components/platform/__tests__/tenantPresentation.test.js` |

## Plan of Work

### Phase 1: 测试先行

1. 后端测试扩展 `api/tests/test_platform_tenants.py`：
   - fixture 增加 `llm_query_jobs` 表。
   - 插入同租户多个 job 和其他租户 job。
   - 断言 `/api/v1/platform/tenants` 返回 `jobCount`、`latestJob.jobId`、状态与品牌信息。
2. 前端 presentation 测试扩展：
   - `normalizeTenantListResponse` 保留 job 字段。
   - 新增 `buildTenantDashboardPath(tenant)`，断言使用真实 `latestJob.jobId` 和 `latestJob.brand`。
   - 无 job 返回空路径或不可用值。

### Phase 2: 后端实现

1. 在 `list_platform_tenant_summaries` 查询中加入 job 聚合字段。
2. 在 `_platform_tenant_item` 映射为 camelCase 响应：
   - `jobCount`
   - `activeJobCount`
   - `latestJob: { jobId, brand, category, queryStatus, effectiveFrom, effectiveTo, createdAt } | null`
3. 保持平台接口只走 `require_platform_admin`，不发送或依赖 `X-Tenant-Key`。

### Phase 3: 前端实现

1. 平台租户表格新增“任务”列。
2. 任务列展示 job 总数、最近 job id、品牌/品类、状态。
3. 操作列增加“看板”按钮，active 且有 latest job 时启用。
4. “任务状态”入口保留，用于查看完整任务列表。

### Phase 4: 验证与归档

1. 运行相关后端与前端测试。
2. 运行 `ruff check api`、`npm --prefix web run build`、文档结构验证。
3. 更新本计划的 Progress、Outcomes、验证记录。
4. 移动 ExecPlan 到 completed，更新 index，删除 `TASKS.md`。

## Validation and Acceptance

- 平台租户接口返回真实 job 摘要。
- 平台租户列表展示 job 信息。
- 平台管理员 dashboard 入口使用真实 `tenantKey + jobId + brand`。
- 没有 job 的租户不会生成 dashboard 入口。
- 文档和测试门禁通过；如软门禁未运行，记录原因。

## Outcomes & Retrospective

已完成：

- `api/v1/repositories/tenants.py::list_platform_tenant_summaries` 在平台租户列表查询中加入 `jobCount`、`activeJobCount` 和最近未删除 job 字段。
- `api/v1/routes/auth.py::_platform_tenant_item` 将 job 摘要映射为 `latestJob`，并对字符串时间做 ISO 风格归一。
- `web/src/components/platform/PlatformTenantsPage.jsx` 新增“任务”列，展示最近 job id、状态、品牌/品类、job 计数，并新增使用真实 `tenantKey + latestJob.jobId + latestJob.brand` 的“看板”按钮。
- 2026-05-21 反馈修正：平台看板入口原先只带 `tenantKey + jobId`，进入 dashboard 后会由 `brand-metrics` 首项自动补齐 `brand`；当竞品 Freshworks 排在 Quickcep 前面时，Quickcep 租户会误显示 Freshworks。已改为入口 URL 显式带 `latestJob.brand`。
- `web/src/components/platform/tenantPresentation.js` 新增 `buildTenantDashboardPath` 和任务状态展示元数据。
- 新增产品规格 `docs/product-specs/20260521-185332-platform-admin-job-aware-dashboard-entry.md`，并同步 `ARCHITECTURE`、`ARCHITECTURE_MULTITENANT`、`DESIGN`、`PRD`。

验证记录：

- RED：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_tenants.py -q`：2 failed，响应缺少 `jobCount`。
- RED：`npm --prefix web test -- --test-reporter=spec src/components/platform/__tests__/tenantPresentation.test.js`：failed，缺少 `buildTenantDashboardPath` export。
- GREEN：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_tenants.py -q`：6 passed，存在既有 Pydantic/SQLite warnings。
- GREEN：`npm --prefix web test -- --test-reporter=spec src/components/platform/__tests__/tenantPresentation.test.js`：6 passed。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：77 passed，存在既有 Pydantic/SQLite warnings。
- `uv run --project api ruff check api`：All checks passed。
- `npm --prefix web test -- --test-reporter=spec`：50 passed。
- `npm --prefix web run build`：通过。
- 浏览器 sanity check：打开 `http://127.0.0.1:3000/platform/tenants`，未登录按预期跳转 `/login`，标题为“明察 InsightFlow”，console error 数为 0。
- 文档验证：初次运行因进行中的 `TASKS.md` 缺少标准区段失败；任务完成删除 `TASKS.md` 后重跑。
