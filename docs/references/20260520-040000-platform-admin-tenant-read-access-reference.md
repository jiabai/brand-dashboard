# 平台管理员租户看板只读访问参考

> 状态：已实现，2026-05-20 创建
>
> 本文档记录平台管理员全租户只读看板访问的 API 与前端契约。产品规格见 `docs/product-specs/20260520-040000-platform-admin-tenant-read-access.md`。

## 1. 后端契约

### 1.1 Dashboard API

范围：

```text
GET /api/v1/dashboard/*
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

### 3.1 平台租户列表

`/platform/tenants` 每行对 active 租户提供租户级入口：

```text
/tasks/<tenantKey>/status
```

该入口不依赖前端环境变量中的默认 `tenantKey`、`jobId` 或 `brand`。平台管理员先进入目标租户的任务状态页，再选择具体任务进入 dashboard。后续如果平台租户列表 API 返回最近有效任务，可在服务端数据明确时再跳到对应 dashboard。

### 3.2 Dashboard 访问

平台管理员直接进入 `/dashboard/:tenantKey/:jobId` 时：

- 不要求该 `tenantKey` 出现在 `user.tenants`。
- API client 仍应从 query 或 URL 派生 `tenant_key` 并发送 `X-Tenant-Key`。
- 顶部租户选择器可保持只展示真实 membership；平台只读租户不进入该列表。
- Dashboard 不使用 `VITE_DEFAULT_TENANT_KEY`、`VITE_DEFAULT_JOB_ID`、`VITE_DEFAULT_BRAND` 兜底；租户和任务必须来自路由，品牌来自 URL `brand` 参数或由 dashboard 数据首个品牌自动补齐。

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
