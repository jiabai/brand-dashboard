# 平台运营后台 API 与前端契约

> 状态：MVP 已落地契约，2026-05-20
>
> 本文档定义 `/platform` 平台运营后台的 Web 路由、API 请求响应、权限边界和测试契约。产品规格见 `docs/product-specs/20260520-010000-platform-operations-console.md`，多租户架构见 `docs/ARCHITECTURE_MULTITENANT.md`。

## 1. Web 路由契约

| 路由 | 页面组件 | 权限 | 行为 |
|---|---|---|---|
| `/platform` | `PlatformRedirect` | `platform_admin` | 重定向 `/platform/tenants` |
| `/platform/tenants` | `PlatformTenantsPage` | `platform_admin` | 租户列表、筛选、创建租户 |
| `/platform/tenants/:tenantKey` | `PlatformTenantDetailPage` | `platform_admin` | 后续增强，MVP 可暂不实现 |
| `/platform/executors` | `PlatformExecutorsPage` | `platform_admin` | 后续增强，MVP 可暂不暴露 |

前端权限规则：

1. 未登录用户进入 `/platform/*` 时跳转 `/login`，并保留返回地址。
2. 已登录但 `user.platformRoles` 不包含 `platform_admin` 时显示平台 403 页面。
3. 平台后台请求不应注入 `X-Tenant-Key`；API client 通过 `skipTenantHeader: true` 显式跳过租户 header。
4. 平台管理员直接从 `/login` 登录且没有原始来源页时，默认跳转 `/platform/tenants`。
5. 如果登录前来自某个受保护页面，登录后优先返回该页面。

## 2. API 通用约定

平台运营 API 均使用：

```http
Authorization: Bearer <access_token>
```

不使用：

```http
X-Tenant-Key: <tenant_key>
```

错误响应遵循现有响应外壳：

```json
{
  "status": "error",
  "code": 403,
  "message": "需要平台管理员权限"
}
```

## 3. 租户列表

### `GET /api/v1/platform/tenants`

平台运营后台租户列表。

鉴权：`require_platform_admin`。

Query 参数：

| 字段 | 类型 | 必填 | 默认 | 说明 |
|---|---|---:|---|---|
| `q` | string | 否 | 空 | 搜索租户名称、`tenantKey`、管理员邮箱 |
| `status` | string | 否 | 空 | `active`、`inactive`、`suspended` |
| `planType` | string | 否 | 空 | `trial`、`basic`、`pro`、`enterprise` |
| `page` | int | 否 | 1 | 页码，最小 1 |
| `pageSize` | int | 否 | 20 | 每页数量，范围 1-100 |

请求示例：

```bash
curl "http://localhost:8000/api/v1/platform/tenants?q=alibaba&status=active&page=1&pageSize=20" \
  -H "Authorization: Bearer <platform_access_token>"
```

成功响应：

```json
{
  "status": "success",
  "code": 200,
  "message": "获取租户列表成功",
  "data": {
    "items": [
      {
        "tenantKey": "tn_1a2b3c4d5e6f",
        "tenantName": "阿里巴巴集团",
        "companyLegalName": "阿里巴巴（中国）网络技术有限公司",
        "industry": "互联网/电子商务",
        "status": "active",
        "planType": "enterprise",
        "maxUsers": 200,
        "billingCycle": "yearly",
        "contractStartDate": "2026-05-20",
        "contractEndDate": "2027-05-19",
        "adminEmail": "zhangsan@alibaba.com",
        "adminStatus": "pending_activation",
        "memberCount": 1,
        "createdAt": "2026-05-20T10:15:30Z"
      }
    ],
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "total": 1,
      "totalPages": 1
    }
  }
}
```

字段说明：

| 字段 | 来源 | 说明 |
|---|---|---|
| `tenantKey` | `tenants.tenant_key` | 租户唯一标识 |
| `tenantName` | `tenants.tenant_name` | 企业显示名 |
| `companyLegalName` | `tenants.company_legal_name` | 企业法定名 |
| `industry` | `tenants.industry` | 行业 |
| `status` | `tenants.status` | 租户状态 |
| `planType` | `tenants.plan_type` | 订阅计划 |
| `maxUsers` | `tenants.max_users` | 用户上限 |
| `billingCycle` | `tenants.billing_cycle` | 计费周期 |
| `contractStartDate` | `tenants.contract_start_date` | 合同开始日期 |
| `contractEndDate` | `tenants.contract_end_date` | 合同结束日期 |
| `adminEmail` | `users.email` + `user_tenants.role=admin` | 首个或任一管理员邮箱，优先创建时间最早者 |
| `adminStatus` | `users.status` | 管理员账号状态 |
| `memberCount` | `COUNT(user_tenants)` | active/inactive 成员关系数量总和 |
| `createdAt` | `tenants.created_at` | 租户创建时间 |

安全约束：

- 不返回 password hash。
- 不返回 activation token 历史。
- 不返回邀请码明文列表；邀请码只在创建租户成功结果中展示，后续如需管理邀请码需单独设计。
- 不返回任何租户业务数据、任务数据或执行器 API Key。

错误：

| HTTP | message | 场景 |
|---:|---|---|
| 401 | 未提供有效的认证令牌 | 缺少或无效 token |
| 403 | 需要平台管理员权限 | 非平台管理员 |
| 400 | 请求参数无效 | page/pageSize/status/planType 非法 |

## 4. 创建租户

### `POST /api/v1/platform/tenants`

当前已存在接口，平台运营后台使用该接口创建租户。

请求和响应详见 `docs/references/20260519-000000-tenant-account-api-reference.md#2-创建租户`。

平台运营后台额外前端契约：

1. 必填字段：`tenantName`、`industry`、`adminName`、`adminEmail`。
2. `maxUsers` 为空时不提交；填写时必须为正整数。
3. 合同日期使用 `YYYY-MM-DD`。
4. 成功响应的 `activationUrl`、`loginUrl`、`inviteCode` 必须展示在创建结果面板。
5. 创建成功后重新请求 `GET /api/v1/platform/tenants`。

## 5. API Adapter 契约

已新增 `web/src/api/platform.js`：

| 函数 | 输入 | 输出 |
|---|---|---|
| `fetchPlatformTenants(params, options)` | `{ q, status, planType, page, pageSize }` | `GET /api/v1/platform/tenants` 响应 |
| `createPlatformTenant(payload, options)` | 租户创建 payload | `POST /api/v1/platform/tenants` 响应 |

`createPlatformTenant` 已从 public auth API 分类中移出，由 `platform.js` 承载。

平台 API 调用必须：

- 注入 `Authorization`。
- 显式不注入 `X-Tenant-Key`。
- 保留 `AbortController.signal` 支持。

## 6. 前端状态契约

`PlatformTenantsPage` 建议状态：

| 状态 | 类型 | 说明 |
|---|---|---|
| `filters.q` | string | 搜索关键词 |
| `filters.status` | string | 状态筛选 |
| `filters.planType` | string | 计划筛选 |
| `pagination.page` | number | 当前页 |
| `pagination.pageSize` | number | 每页数量 |
| `tenants` | array | 当前页租户 |
| `isLoading` | boolean | 列表加载中 |
| `createResult` | object/null | 最近一次创建租户结果 |
| `error` | string/null | 列表或创建错误 |

URL query 应保存 `q`、`status`、`planType`、`page`，便于刷新和分享运营筛选状态。

## 7. 测试契约

后端测试：

- `api/tests/test_platform_tenants.py`
  - `GET /platform/tenants` 缺 token 返回 401。
  - 非平台管理员返回 403。
  - 平台管理员可分页获取租户列表。
  - `q/status/planType` 筛选生效。
  - 响应不包含 password hash、activation token、API Key。

前端测试：

- `web/src/api/__tests__/platform.test.js`
  - 平台 API 注入 `Authorization`。
  - 平台 API 不注入 `X-Tenant-Key`。
  - 查询参数序列化正确。
- `web/src/auth/__tests__/platformAccess.test.js`
  - 非平台角色访问 `/platform/tenants` 的访问状态为 `forbidden`。
  - 未登录访问 `/platform/tenants` 的访问状态为 `login`。
- `web/src/auth/__tests__/redirect.test.js`
  - 平台管理员直登默认跳转 `/platform/tenants`。
  - 有原始受保护页面来源时优先返回来源页。
  - 普通租户用户直登继续跳转默认 dashboard。
- `web/src/components/platform/__tests__/tenantPresentation.test.js`
  - 列表响应、筛选参数、状态标签和创建 payload 规范化。

构建验证：

- `npm --prefix web test`
- `npm --prefix web run build`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `uv run --project api ruff check api`
