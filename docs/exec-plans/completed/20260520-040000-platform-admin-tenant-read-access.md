# 平台管理员全租户只读看板实施计划

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

平台管理员应能查看所有 active 租户 dashboard 数据，用于运营、交付和排障；但平台管理员不应被批量加入 `user_tenants`，也不应自动获得租户内写权限。本计划实现 dashboard 读接口的专用平台只读旁路，并在平台租户列表增加不依赖默认 job 的租户级入口。

## Progress

- [x] Phase 0: 文档设计 — 新增产品规格、设计文档、API 参考、active ExecPlan 和 TASKS（2026-05-20）
- [x] Phase 1: 后端测试先行 — 平台管理员无 membership 访问 dashboard 200，普通用户仍 403，写接口仍 403（2026-05-20）
- [x] Phase 2: 后端依赖实现 — 新增 dashboard 只读租户上下文依赖并接入 dashboard 路由组（2026-05-20）
- [x] Phase 3: 前端入口 — 平台租户列表增加租户级入口，dashboard 不要求路由租户在 `user.tenants`（2026-05-20）
- [x] Phase 4: 验证与文档收尾 — 后端、前端、文档门禁通过，归档 ExecPlan 并删除 TASKS（2026-05-20）
- [x] 2026-05-21 修订：移除前端默认 tenant/job/brand 依赖，平台租户入口改为 `/tasks/<tenantKey>/status`。

## Surprises & Discoveries

- 2026-05-20：当前 QuickCEP 可访问只是因为本地补了 `user_tenants` viewer membership；这不是平台管理员全租户可见的最终模型。
- 2026-05-20：Dashboard 路由组统一挂在 `router = APIRouter(dependencies=[Depends(get_current_tenant)])`，适合以路由组依赖替换实现只读旁路。
- 2026-05-20：写接口仍走 `require_current_tenant(required_role="admin")`，平台管理员无 membership 的 `query-jobs/load` 测试保持 403。
- 2026-05-20：前端已有 dashboard 数据请求从路由参数构造 `tenant_key`，平台只读场景不需要把所有租户塞进登录态。

## Decision Log

| Decision | Rationale | Date/Author |
|---|---|---|
| 平台管理员采用 dashboard 只读旁路 | 满足平台排障需要，同时不污染客户租户成员关系 | 2026-05-20 / agent |
| 不放开租户写接口 | 平台看数据和代客户操作是两种权限，需要分开设计和审计 | 2026-05-20 / agent |
| 不把所有租户放进登录响应 | 登录态中的 `tenants` 表达真实 membership；平台可访问租户由平台后台列表承载 | 2026-05-20 / agent |
| 平台租户列表不拼默认 dashboard job | 多租户系统不应依赖 web `.env` 中的 demo tenant/job/brand；先进入任务状态页，由真实任务驱动 dashboard | 2026-05-21 / agent |

## Context and Orientation

相关文件：

| 类型 | 文件 |
|---|---|
| 新增 | `docs/product-specs/20260520-040000-platform-admin-tenant-read-access.md` |
| 新增 | `docs/design-docs/20260520-040000-platform-admin-tenant-read-access.md` |
| 新增 | `docs/references/20260520-040000-platform-admin-tenant-read-access-reference.md` |
| 新增 | `api/tests/test_platform_admin_dashboard_access.py` |
| 修改 | `api/v1/dependencies/auth.py` |
| 修改 | `api/v1/repositories/tenants.py` |
| 修改 | `api/v1/routes/dashboard.py` |
| 修改 | `web/src/components/platform/PlatformTenantsPage.jsx` |
| 修改 | `web/src/components/DashboardLayout.jsx` |

当前行为：

1. Dashboard API 必须通过 `get_current_tenant`。
2. `get_current_tenant` 要求 `user_tenants` membership。
3. `platform_admin` 只用于 `/platform/*` 和平台级管理接口。

目标行为：

1. Dashboard API 使用新的只读依赖。
2. 普通用户仍要求 membership。
3. 平台管理员无 membership 时可读取 active 租户 dashboard。
4. 写接口依赖不变。

## Plan of Work

### Phase 1: 后端测试先行

1. 新增 `api/tests/test_platform_admin_dashboard_access.py`。
2. 构建内存 SQLite schema：`users`、`tenants`、`user_tenants`。
3. 使用 FastAPI TestClient 挂载 dashboard 路由和一个 fake dashboard service。
4. 写失败测试：
   - 平台管理员无 membership 访问 `/api/v1/dashboard/available-dates` 返回 200。
   - 普通用户无 membership 访问同接口返回 403。
   - 平台管理员访问 inactive 租户返回 403。
   - 普通成员仍可访问所属租户返回 200。
5. 扩展 `api/tests/test_tenant_context_routes.py` 或新增测试证明 `/api/v1/query-jobs/load` 未被平台只读旁路放开。

验证：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_admin_dashboard_access.py api/tests/test_tenant_context_routes.py -q
```

### Phase 2: 后端依赖实现

1. 在 `api/v1/repositories/tenants.py` 新增 `get_tenant_summary_by_key(db, tenant_key)`，返回 `tenant_key`、`tenant_name`、`status`。
2. 在 `api/v1/dependencies/auth.py` 新增 `get_current_tenant_for_dashboard_read`。
3. 普通 membership 优先；无 membership 时检查 `get_platform_roles_for_email(current_user.email)`。
4. 只允许 active 租户返回只读上下文。
5. 将 `api/v1/routes/dashboard.py` 路由组依赖替换为 `Depends(get_current_tenant_for_dashboard_read)`。

验证：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_admin_dashboard_access.py -q
uv run --project api ruff check api
```

### Phase 3: 前端入口

1. 在平台租户列表行操作中增加租户级入口按钮。
2. 跳转路径使用 `buildViewPath('task-status', { tenantKey })`。
3. 确认平台 API adapter 仍 `skipTenantHeader: true`。
4. 如 DashboardLayout 对未知 route tenant 有展示问题，补最小 UI：当 active route tenant 不在 `tenants` 中时，展示 `tenantKey` 文本，不强制选择。
5. 增加前端测试覆盖跳转 URL 或抽取 presentation helper 测试。

验证：

```powershell
npm --prefix web test -- --test-reporter=spec
npm --prefix web run build
```

### Phase 4: 验证与文档收尾

1. 更新本 ExecPlan 的 Progress、Surprises、Outcomes。
2. 更新产品规格、设计、参考文档状态。
3. 运行后端全量测试、ruff、前端测试、前端 build、文档 ERROR/WARN 校验。
4. 归档 ExecPlan 到 completed，更新 completed index，删除 `TASKS.md`。

验证：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q
uv run --project api ruff check api
npm --prefix web test -- --test-reporter=spec
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
python scripts/validate_agents_docs.py --level WARN
```

## Validation and Acceptance

- 平台管理员可以查看所有 active 租户 dashboard 数据。
- 普通用户不能查看未加入 membership 的租户 dashboard。
- 平台管理员不能因此获得租户内写权限。
- 平台租户详情页提供看板入口。
- 所有文档和测试门禁通过。

## Outcomes & Retrospective

已完成：

- 新增 `api/tests/test_platform_admin_dashboard_access.py`，覆盖平台管理员无 membership 读取 active 租户 dashboard、普通用户仍 403、inactive 租户 403、租户成员仍可读、平台管理员不获得 `query-jobs/load` 写权限。
- 新增 `api/v1/repositories/tenants.py::get_tenant_summary_by_key`。
- 新增 `api/v1/dependencies/auth.py::get_current_tenant_for_dashboard_read`，普通 membership 优先；无 membership 时只允许 `platform_admin` 读取 active 租户 dashboard。
- `api/v1/routes/dashboard.py` 路由组改用 dashboard 只读依赖，并保留 `dashboard.get_current_tenant` 覆盖点兼容既有测试。
- `web/src/components/platform/PlatformTenantsPage.jsx` 新增 active 租户“任务状态”入口，inactive/suspended 租户按钮禁用。
- `web/src/components/platform/tenantPresentation.js` 新增 `buildTenantTaskStatusPath` 并补测试。
- 2026-05-21 修订：`web/.env` 删除 `VITE_DEFAULT_TENANT_KEY`、`VITE_DEFAULT_JOB_ID`、`VITE_DEFAULT_BRAND`；`web/src/config.js` 不再暴露对应默认业务参数。

验证记录：

- RED：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_admin_dashboard_access.py api/tests/test_tenant_context_routes.py -q`：1 failed，平台管理员无 membership 读取 dashboard 仍 403。
- GREEN：同一命令后续 10 passed。
- `uv run --project api ruff check api`：All checks passed。
- `npm --prefix web test -- --test-reporter=spec`：45 passed。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：76 passed，存在既有 Pydantic/SQLite 警告。
- `npm --prefix web run build`：通过。
- `npm --prefix web run lint`：0 errors，9 warnings（既有 warnings）。
- `python scripts/validate_agents_docs.py --level ERROR`：0 errors，0 warnings。
- `python scripts/validate_agents_docs.py --level WARN`：0 errors，0 warnings。
- 本地真实 SQLite 验证：平台管理员 token 访问 `tn_1b02b3ef4fbd` 与 `tn_6e1f78442bae` 的 `available-dates` 均返回 200。
