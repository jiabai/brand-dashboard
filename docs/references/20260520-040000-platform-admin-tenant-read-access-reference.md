# 平台管理员租户项目与看板只读访问参考

> 状态：已实现，2026-05-20 创建，2026-06-09 修订
>
> 本文档记录平台管理员全租户项目工作台与看板只读访问的 API 与前端契约。产品规格见 `docs/product-specs/20260520-040000-platform-admin-tenant-read-access.md`。

## 1. 后端契约

### 1.1 Dashboard 与项目 GET API

范围：

```text
GET /api/v1/dashboard/*
GET /api/v1/projects
GET /api/v1/projects/{project_id}
GET /api/v1/projects/{project_id}/data-quality
GET /api/v1/projects/{project_id}/reports
GET /api/v1/projects/{project_id}/alerts
```

鉴权：

```http
Authorization: Bearer <access_token>
X-Tenant-Key: tn_xxxxxxxxxxxx
```

授权规则：

| 用户状态 | 目标租户 | membership | 平台角色 | 结果 |
|---|---|---|---|---|
| active | active | active | 任意 | 200 |
| active | active | 无 | platform_admin | 200，只读 |
| active | active | 无 | 非 platform_admin | 403 |
| active | inactive | 任意 | platform_admin | 403 |
| inactive/suspended | 任意 | 任意 | 任意 | 403 |

### 1.2 写接口不变

以下接口不使用平台只读旁路：

```text
POST /api/v1/query-jobs/load
POST /api/v1/conversation/load
POST /api/v1/projects
POST /api/v1/projects/{project_id}/brands
POST /api/v1/projects/{project_id}/prompt-sets
POST /api/v1/projects/{project_id}/reports
POST /api/v1/platform/tenants
POST /api/v1/executors/*
```

其中租户内写接口仍需满足租户 admin 或执行器 job scope；平台管理员身份本身不等于租户 admin。

## 2. 后端实现建议

新增依赖名称建议：

```python
def get_current_tenant_for_dashboard_read(...) -> CurrentTenantContext:
    ...
```

项目 GET 路由使用同一类只读语义，实际实现可使用更通用的 `get_current_tenant_for_read`，并让 dashboard 专用名称作为兼容包装。

上下文建议新增字段：

| 字段 | 普通成员 | 平台只读 |
|---|---|---|
| `tenant_key` | 目标租户 | 目标租户 |
| `tenant_name` | 目标租户名 | 目标租户名 |
| `role` | `admin/member/viewer` | `platform_admin_readonly` |
| `product_role` | `tenant_admin/tenant_member/tenant_viewer` | `platform_admin` |
| `access_scope` | `tenant_member` | `platform_readonly` |

如果为了减少改动暂不新增 `access_scope`，也必须用 `role="platform_admin_readonly"` 区分平台只读上下文，并确保它不能满足租户 admin 判断。

## 3. 前端契约

### 3.1 平台租户入口

`/platform/tenants` 每行只保留平台租户详情入口：

```text
/platform/tenants/<tenantKey>
```

当平台租户详情 API 返回 `latestJob.jobId` 时，详情页提供 dashboard 入口：

```text
/dashboard/<tenantKey>/<latestJob.jobId>?brand=<latestJob.brand>
```

详情页还提供租户级任务状态入口：

```text
/tasks/<tenantKey>/status
```

这些入口不依赖前端环境变量中的默认 `tenantKey`、`jobId` 或 `brand`。dashboard 入口必须使用平台租户 API 返回的真实 `latestJob` 与品牌值；缺少最近任务时，平台管理员再从详情页进入目标租户的任务状态页选择具体任务。

当前主业务入口：

```text
/projects/<tenantKey>
/projects/<tenantKey>/<projectId>
/projects/<tenantKey>/<projectId>/quality
```

租户详情页顶部提供“进入项目工作台”，下方项目区标题为“项目概览”，项目行提供“打开项目”和“数据质量”。项目概览直达项目详情或数据质量时携带 `from=platform-tenant-detail`，项目详情页返回 `/platform/tenants/:tenantKey#project-overview`；从项目工作台进入项目详情时不携带来源，默认返回 `/projects/:tenantKey`。进入 `/projects/:tenantKey` 后，页面标题为“项目工作台”。旧 dashboard 入口文案为“最新任务看板”，与“任务状态”一起放入“排障入口”。

### 3.2 Dashboard 访问

平台管理员直接进入 `/projects/:tenantKey`、`/projects/:tenantKey/:projectId`、`/projects/:tenantKey/:projectId/quality` 或 `/dashboard/:tenantKey/:jobId` 时：

- 不要求该 `tenantKey` 出现在 `user.tenants`。
- API client 仍应从 query 或 URL 派生 `tenant_key` 并发送 `X-Tenant-Key`。
- 顶部租户选择器可保持只展示真实 membership；平台只读租户不进入该列表。
- Dashboard 不使用 `VITE_DEFAULT_TENANT_KEY`、`VITE_DEFAULT_JOB_ID`、`VITE_DEFAULT_BRAND` 兜底；租户和任务必须来自路由。平台租户列表进入 dashboard 时必须显式携带 `latestJob.brand`，只有一般直接访问缺少 `brand` 时才可由 dashboard 数据首个品牌自动补齐。

## 4. 测试清单

后端：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_admin_dashboard_access.py -q
```

前端：

```powershell
npm --prefix web test -- --test-reporter=spec
npm --prefix web run build
```

全量：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q
uv run --project api ruff check api
python scripts/validate_agents_docs.py --level ERROR
python scripts/validate_agents_docs.py --level WARN
```
