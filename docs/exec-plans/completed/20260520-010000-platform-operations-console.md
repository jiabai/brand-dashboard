# 平台运营后台实施计划

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

本计划把平台运营人员的租户创建能力从租户工作台中拆出来，形成独立 `/platform` Web 后台。完成后，平台运营人员可以登录后进入平台运营后台，查看租户列表，搜索/筛选客户企业，创建新租户并获取激活链接和邀请码。平台后台不依赖 `tenantKey`，不发送 `X-Tenant-Key`，所有平台 API 都由 `platform_admin` 鉴权。

## Progress

- [x] Phase 0: 文档基线 — 新增平台运营后台产品规格、API/前端契约，更新多租户架构、安全和索引（2026-05-20）
- [x] Phase 1: 后端平台租户列表 API — `GET /api/v1/platform/tenants`（2026-05-20）
- [x] Phase 2: 前端平台 API 与权限路由 — platform API adapter、PlatformRoute、403 状态（2026-05-20）
- [x] Phase 3: 平台租户管理页面 — `/platform/tenants` 列表、筛选、分页、创建租户、创建结果面板（2026-05-20）
- [x] Phase 4: 收敛旧账户管理入口 — 租户工作台不再作为正式平台运营入口（2026-05-20）
- [x] Phase 5: 全量验证与文档收尾（2026-05-20）

## Surprises & Discoveries

- 2026-05-20：当前后端只有 `POST /api/v1/platform/tenants`，没有平台租户列表接口。平台运营后台要可用，必须新增 `GET /api/v1/platform/tenants`。
- 2026-05-20：当前 `AccountManagement` 位于租户工作台路由 `/accounts/:tenantKey`，虽然已经按 `platformRoles` 控制创建按钮，但仍不是正式平台运营后台。
- 2026-05-20：平台 API 不应复用租户 API 的 `X-Tenant-Key` 注入逻辑，前端 API client 需要支持显式跳过租户 header。

## Decision Log

| Decision | Rationale | Date/Author |
|---|---|---|
| `/platform/*` 独立于租户工作台 | 平台运营人员不一定属于任何客户租户；平台权限不能依赖 `tenantKey` | 2026-05-20 / agent |
| MVP 先做租户列表和创建租户 | 这是平台运营开通客户的最小闭环；执行器管理可后续扩展 | 2026-05-20 / agent |
| 平台 API 不发送 `X-Tenant-Key` | 避免平台权限和租户成员权限混淆 | 2026-05-20 / agent |
| 租户创建成功结果只在本次展示 activation token | activation token 属于敏感一次性流程，不通过列表接口长期暴露 | 2026-05-20 / agent |

## Context and Orientation

### 当前代码状态

| 区域 | 状态 |
|---|---|
| `api/v1/routes/auth.py` | 已有 `POST /platform/tenants`，无 `GET /platform/tenants` |
| `api/v1/repositories/auth.py` | 已有 `create_tenant_with_admin` |
| `api/v1/repositories/tenants.py` | 只有租户存在性、用户租户成员关系、用户租户摘要查询 |
| `api/v1/dependencies/auth.py` | 已有 `require_platform_admin` |
| `web/src/auth/AuthContext.jsx` | 已提供 `platformRoles`、登录态恢复、退出 |
| `web/src/api/client.js` | 自动注入 token 和租户 header，但还没有平台 API 跳过租户 header 的显式契约 |
| `web/src/components/AccountManagement.jsx` | 租户工作台内的账户管理页，包含租户开通表单雏形 |
| `web/src/App.jsx` | 已有 `/login`、`/activate`、`/register` 和租户工作台路由，尚无 `/platform` |

### 受影响文件

| 类型 | 文件 |
|---|---|
| 新增 | `api/tests/test_platform_tenants.py` |
| 新增 | `web/src/api/platform.js` |
| 新增 | `web/src/api/__tests__/platform.test.js` |
| 新增 | `web/src/components/platform/PlatformRoute.jsx` |
| 新增 | `web/src/components/platform/PlatformLayout.jsx` |
| 新增 | `web/src/components/platform/PlatformTenantsPage.jsx` |
| 新增 | `web/src/components/platform/CreateTenantPanel.jsx` |
| 修改 | `api/v1/routes/auth.py` 或新增平台 routes 模块 |
| 修改 | `api/v1/repositories/tenants.py` |
| 修改 | `web/src/api/client.js` |
| 修改 | `web/src/api/index.js` |
| 修改 | `web/src/App.jsx` |
| 修改 | `web/src/components/AccountManagement.jsx` |
| 修改 | `docs/ARCHITECTURE_MULTITENANT.md`、`docs/SECURITY.md`、平台规格和 reference |

## Plan of Work

### Phase 1: 后端平台租户列表 API

目标：新增平台侧租户列表接口，供 `/platform/tenants` 使用。

步骤：

1. 在 `api/tests/test_platform_tenants.py` 先写失败测试：
   - 缺 token 调用 `GET /api/v1/platform/tenants` 返回 401。
   - 非平台管理员返回 403。
   - 平台管理员返回分页列表。
   - `q`、`status`、`planType` 筛选生效。
   - 响应不包含 password hash、activation token、executor API Key。
2. 在 `api/v1/repositories/tenants.py` 新增 `list_platform_tenant_summaries(db, filters)`。
3. 在 `api/v1/routes/auth.py` 或新的 `api/v1/routes/platform.py` 新增 `GET /platform/tenants`。
4. 用 Pydantic 或 FastAPI Query 校验 `page >= 1`、`1 <= pageSize <= 100`、状态和计划枚举。
5. 运行后端目标测试和 ruff。

验证：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_tenants.py -q
uv run --project api ruff check api
```

预期：新增平台租户列表测试通过，ruff 无错误。

### Phase 2: 前端平台 API 与权限路由

目标：让前端具备平台 API 调用和平台权限 guard。

步骤：

1. 在 `web/src/api/__tests__/platform.test.js` 写失败测试：
   - `fetchPlatformTenants` 序列化 query。
   - 平台 API 带 `Authorization`。
   - 平台 API 不带 `X-Tenant-Key`。
2. 修改 `web/src/api/client.js`，支持 `skipTenantHeader: true` 或 `tenantKey: null` 的显式语义。
3. 新增 `web/src/api/platform.js`，提供 `fetchPlatformTenants` 和 `createPlatformTenant`。
4. 更新 `web/src/api/index.js` 导出平台 API。
5. 新增 `PlatformRoute`，未登录跳转 `/login`，非平台管理员显示 403。

验证：

```powershell
npm --prefix web test -- --test-reporter=spec
npm --prefix web run build
```

预期：前端测试通过，构建通过。

### Phase 3: 平台租户管理页面

目标：完成 `/platform/tenants` 可用页面。

步骤：

1. 新增 `PlatformLayout`，包含平台后台头部、导航、当前用户邮箱和退出按钮。
2. 新增 `PlatformTenantsPage`，读取 URL query 中的 `q/status/planType/page`。
3. 首屏调用 `fetchPlatformTenants`，展示租户表格、加载态、空态和错误态。
4. 新增 `CreateTenantPanel`，复用当前租户开通字段，提交 `createPlatformTenant`。
5. 创建成功后刷新列表，并展示 activationUrl、loginUrl、inviteCode 的结果面板。
6. 在 `web/src/App.jsx` 加入 `/platform` 和 `/platform/tenants` 路由。

验证：

```powershell
npm --prefix web test -- --test-reporter=spec
npm --prefix web run build
```

手动/浏览器验证：

- 未登录访问 `/platform/tenants` 跳转 `/login`。
- 模拟平台管理员登录后可看到平台租户页面。
- 创建租户按钮只在平台后台出现。

### Phase 4: 收敛旧账户管理入口

目标：避免正式平台运营入口长期停留在租户工作台。

步骤：

1. 修改 `AccountManagement`：移除或降级“租户开通”正式入口，显示跳转 `/platform/tenants` 的提示。
2. 保留管理员激活、员工注册、邀请码核验等租户注册相关能力。
3. 确认租户工作台菜单仍适合租户用户，不暴露平台运营导航。
4. 更新文档中的当前实现状态。

验证：

```powershell
npm --prefix web test -- --test-reporter=spec
npm --prefix web run build
```

预期：租户工作台不再是创建租户的正式入口，平台后台成为唯一正式入口。

### Phase 5: 全量验证与文档收尾

目标：完成硬门禁并准备归档。

步骤：

1. 运行后端全量测试和 ruff。
2. 运行前端测试和构建。
3. 使用浏览器检查 `/platform/tenants` 桌面和移动布局。
4. 更新本 ExecPlan 的 Progress、Surprises、Outcomes 和验证记录。
5. 更新 `docs/product-specs/20260520-010000-platform-operations-console.md`、reference、architecture/security 中的实现状态。
6. 全部完成后移动本 ExecPlan 到 `docs/exec-plans/completed/`，更新 completed index，并删除 `TASKS.md`。

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

1. 未登录访问 `/platform/tenants` 跳转 `/login`。
2. 非平台管理员访问 `/platform/tenants` 显示 403。
3. 平台管理员可以访问 `/platform/tenants`。
4. `GET /api/v1/platform/tenants` 支持搜索、状态筛选、计划筛选和分页。
5. 租户列表不返回敏感字段。
6. 平台管理员可以创建租户并看到 activationUrl、loginUrl、inviteCode。
7. 平台 API 请求携带 `Authorization`，不携带 `X-Tenant-Key`。
8. 租户工作台不再作为正式创建租户入口。

## Outcomes & Retrospective

已完成 Phase 1 后端平台租户列表 API：

- 新增 `api/tests/test_platform_tenants.py`，覆盖缺 token、非平台管理员、平台管理员列表、搜索/状态/计划筛选和敏感字段排除。
- `api/v1/repositories/tenants.py` 新增 `list_platform_tenant_summaries`，按租户元数据、管理员邮箱、成员数量聚合列表。
- `api/v1/routes/auth.py` 新增 `GET /api/v1/platform/tenants`，使用 `require_platform_admin`，支持 `q/status/planType/page/pageSize`。

验证记录：

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_tenants.py -q`：5 passed，存在既有 Pydantic/SQLite 警告。
- `uv run --project api ruff check api`：All checks passed。

已完成 Phase 2 前端平台 API 与权限路由：

- 新增 `web/src/api/platform.js`，提供 `fetchPlatformTenants` 与 `createPlatformTenant`。
- `web/src/api/client.js` 支持 `skipTenantHeader: true`，平台 API 保留 `Authorization`，不注入 `X-Tenant-Key`。
- 新增 `web/src/auth/platformAccess.js` 和 `web/src/components/platform/PlatformRoute.jsx`，提供登录态恢复、未登录跳转和非平台管理员 403 状态。

验证记录：

- `npm --prefix web test -- --test-reporter=spec`：40 passed。
- `npm --prefix web run build`：通过。

已完成 Phase 3/4 平台页面与旧入口收敛：

- 新增 `PlatformLayout`、`PlatformTenantsPage`、`CreateTenantPanel`，接入 `/platform` 和 `/platform/tenants`。
- 租户列表支持 URL query 恢复、关键词搜索、状态/计划筛选、分页、加载态、空态和错误态。
- 创建租户使用平台 API，成功后刷新列表并展示 `activationUrl`、`loginUrl`、`inviteCode`。
- `AccountManagement` 不再承载正式租户创建表单，平台管理员仅看到跳转 `/platform/tenants` 的入口。

验证记录：

- `npm --prefix web test -- --test-reporter=spec`：44 passed。
- `npm --prefix web run build`：通过。
- `npm --prefix web run lint`：0 errors，9 warnings（既有 warnings）。

已完成 Phase 5 全量验证与文档收尾：

- 更新平台运营后台产品规格、API/前端契约和多租户架构实现状态。
- Playwright 验证 `/platform/tenants` 未登录跳转、非平台管理员 403、平台管理员桌面/移动租户列表渲染、创建租户抽屉渲染。
- Playwright 验证平台租户 API 请求携带 `Authorization`，不携带 `X-Tenant-Key`。
- 修复 shadcn/Radix `Button` 与 `Sheet` 组合的 ref 警告，避免浏览器控制台出现 UI 组件告警。

最终验证记录：

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：52 passed，存在既有 Pydantic/SQLite 警告。
- `uv run --project api ruff check api`：All checks passed。
- `npm --prefix web test -- --test-reporter=spec`：44 passed。
- `npm --prefix web run build`：通过。
- `npm --prefix web run lint`：0 errors，9 warnings（既有 warnings）。
- `python scripts/validate_agents_docs.py --level ERROR`：0 errors，0 warnings。
- `python scripts/validate_agents_docs.py --level WARN`：0 errors，0 warnings。
- Playwright：guest redirect ok；forbidden state ok；desktop platform page ok；mobile platform page ok。
