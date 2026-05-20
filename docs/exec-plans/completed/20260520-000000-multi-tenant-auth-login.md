# 多租户管理与登录功能实施计划

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

本计划把 Brand Dashboard 的多租户注册雏形推进到可作为 B2B SaaS 使用的登录和租户授权闭环。完成后，平台管理员可以安全创建企业租户，租户管理员和成员可以登录并访问自己租户的数据，所有业务接口都由服务端校验用户、租户、角色和执行器边界，不再信任客户端自报 `tenant_key`。

## Progress

- [x] Phase 0: 文档基线 — 审阅并修订产品规格、架构补充、API 参考、安全规范和本 ExecPlan（2026-05-20）
- [x] Phase 1: 后端认证基础层 — 标准 JWT、认证依赖、当前用户接口（2026-05-20）
- [x] Phase 2: 平台管理保护 — 创建租户和执行器管理接口加入平台管理员鉴权（2026-05-20）
- [x] Phase 3: 租户上下文保护 — Dashboard、任务状态、任务加载等用户态接口强制租户成员校验（2026-05-20）
- [x] Phase 4: 执行器边界补强 — conversation load 校验执行器、租户和 job 绑定（2026-05-20）
- [x] Phase 5: 前端登录态 — 登录/激活/注册入口、token 保存、Authorization 和 X-Tenant-Key 注入（2026-05-20）
- [x] Phase 6: 验证、文档收尾与迁移说明（2026-05-20）

## Surprises & Discoveries

- 2026-05-20：现有注册/登录 API 已经可跑通基础流程，但 access token 和 activation token 都使用自定义 HMAC `payload.signature`，API 参考原先把二者都写成 JWT，已修正为“activation 保持现状、access 迁移 JWT”。
- 2026-05-20：一个用户可以属于多个租户，因此不能从 access token 直接推导唯一 `tenant_key`。目标方案改为 token 识别用户，`X-Tenant-Key` 或过渡期 query/body 选择租户，服务端校验成员关系。
- 2026-05-20：执行器接口是机器身份，不应套用户 JWT。`query-jobs/fetch` 和 `report` 已有执行器 key 校验，但 `conversation/load` 还需要校验 `tenant_key + job_id + executor_id` 绑定。
- 2026-05-20：本地 `pytest` 命令不可用，项目后端验证需使用 `uv run --project api --extra dev pytest ...` 并设置 `PYTHONPATH=.`，否则 `api` 包无法从仓库根导入。
- 2026-05-20：Dashboard 路由组加入统一租户依赖后，既有 LOCF/日期测试需要显式 override 租户上下文；这是测试职责分离问题，不是业务回归。
- 2026-05-20：平台管理员 MVP 通过 `PLATFORM_ADMIN_EMAILS` 白名单识别，因此登录响应和 `/auth/me` 也需要返回 `platformRoles`，否则前端无法安全控制“创建租户”入口展示。

## Decision Log

| Decision | Rationale | Date/Author |
|---|---|---|
| Access token 迁移到标准 JWT | 使用标准库验证，减少手写加密代码风险；便于前端识别过期时间 | 2026-05-20 / agent |
| Activation token 本阶段保留自定义 HMAC | 激活是一次性流程，避免和登录态迁移耦合；现有实现已可用 | 2026-05-20 / agent |
| 当前租户使用 `X-Tenant-Key` 表达 | 支持多租户用户切换；后端可集中校验成员关系 | 2026-05-20 / agent |
| 过渡期允许 query/body `tenant_key` | 降低对既有前后端调用的破坏，但必须与服务端租户上下文一致 | 2026-05-20 / agent |
| 平台管理员 MVP 使用 `PLATFORM_ADMIN_EMAILS` | 当前无平台管理员表；白名单能最快关闭平台接口裸奔风险 | 2026-05-20 / agent |
| 执行器继续使用 API Key | 机器身份与用户身份职责不同，执行器只应处理被分配的任务 | 2026-05-20 / agent |
| 后端验证命令使用 uv 项目环境 | 当前 shell 没有全局 pytest，uv 环境可稳定安装 dev 依赖并运行测试 | 2026-05-20 / agent |

## Context and Orientation

### 完成后代码状态

| 区域 | 状态 |
|---|---|
| `api/v1/routes/auth.py` | 已有租户创建、激活、邀请码验证、员工注册、登录；Pydantic 请求模型定义在路由文件内 |
| `api/v1/repositories/auth.py` | 已实现注册/登录仓储逻辑；登录返回标准 JWT、租户角色和平台角色 |
| `api/v1/utils/security.py` | 提供密码哈希、执行器 API Key、通用自定义 token |
| `api/v1/routes/dashboard.py` | 路由组已统一接入 `get_current_tenant` |
| `api/v1/routes/query_jobs.py` | fetch/report 保持执行器认证；status/load 已接入用户租户上下文和角色校验 |
| `api/v1/routes/conversation.py` | load 已校验任务与执行器绑定 |
| `api/v1/routes/executors.py` | 创建、列表、禁用执行器已接入平台管理员保护；register 保持 IP/API Key 注册机制 |
| `web/src/api/client.js` | 自动注入 `Authorization` 和 `X-Tenant-Key` |
| `web/src/auth/*` | 提供登录态存储、恢复、退出和租户选择 |
| `web/src/components/AccountManagement.jsx` | 已有租户开通、激活、注册、登录的管理页，并按平台角色控制租户创建入口 |

### 受影响文件

| 类型 | 文件 |
|---|---|
| 新增 | `api/v1/dependencies/__init__.py` |
| 新增 | `api/v1/dependencies/auth.py` |
| 新增 | `api/v1/utils/jwt_utils.py` |
| 新增 | `api/tests/test_auth_dependencies.py` |
| 新增 | `web/src/auth/AuthContext.jsx` |
| 新增 | `web/src/auth/storage.js` |
| 新增 | `web/src/components/LoginView.jsx` |
| 新增 | `web/src/components/ProtectedRoute.jsx` |
| 修改 | `api/pyproject.toml`、`api/uv.lock` |
| 修改 | `api/v1/routes/auth.py` |
| 修改 | `api/v1/repositories/auth.py` |
| 修改 | `api/v1/routes/dashboard.py` |
| 修改 | `api/v1/routes/query_jobs.py` |
| 修改 | `api/v1/routes/conversation.py` |
| 修改 | `api/v1/routes/executors.py` |
| 修改 | `api/v1/repositories/query_jobs.py` |
| 修改 | `api/v1/repositories/tenants.py` |
| 修改 | `api/v1/models/schemas.py` |
| 修改 | `api/tests/test_auth.py` |
| 修改 | `web/src/api/client.js` |
| 修改 | `web/src/api/auth.js` |
| 修改 | `web/src/App.jsx` |
| 修改 | `web/src/config/routes.js` |
| 修改 | `web/src/components/AccountManagement.jsx` |
| 修改 | `web/src/hooks/useDashboardParams.js` |
| 修改 | `docs/SECURITY.md`、`docs/ARCHITECTURE.md`、`docs/ARCHITECTURE_MULTITENANT.md` |

## Plan of Work

### Phase 1: 后端认证基础层

目标：标准化 access token，建立可复用的认证依赖，新增当前用户接口。

步骤：

1. 在 `api/pyproject.toml` 增加 `pyjwt>=2.10,<3.0`，运行依赖锁定命令更新 `api/uv.lock`。
2. 新建 `api/v1/utils/jwt_utils.py`，实现 `create_access_token`、`verify_access_token`，并在 7 天过渡期兼容旧 access token。
3. 新建 `api/v1/dependencies/auth.py`，定义 `CurrentUser`、`CurrentTenantContext`、`get_current_user`、`get_current_tenant`、`require_platform_admin`。
4. 在 `api/v1/models/schemas.py` 增加认证请求/响应模型，逐步替换 `api/v1/routes/auth.py` 内联模型。
5. 修改 `api/v1/repositories/auth.py::authenticate_user`，登录成功返回标准 JWT、租户角色和租户成员状态。
6. 在 `api/v1/routes/auth.py` 新增 `GET /auth/me`，用于前端刷新后恢复登录态。
7. 扩展 `api/tests/test_auth.py`，覆盖登录 token 格式、租户角色返回、`/auth/me`。
8. 新增 `api/tests/test_auth_dependencies.py`，覆盖缺 token、无效 token、用户停用、租户停用、跨租户访问和角色不足。

验证：

```powershell
pytest api/tests/test_auth.py api/tests/test_auth_dependencies.py
ruff check api
```

预期：认证相关测试通过，ruff 无错误。

### Phase 2: 平台管理保护

目标：关闭平台创建租户和执行器管理接口的裸奔风险。

步骤：

1. 在 `api/v1/dependencies/auth.py` 实现 `require_platform_admin`，读取 `PLATFORM_ADMIN_EMAILS`，匹配当前用户 email。
2. 修改 `api/v1/routes/auth.py::create_tenant`，加入 `Depends(require_platform_admin)`。
3. 修改 `api/v1/routes/executors.py`，创建、列表、禁用执行器接口加入 `Depends(require_platform_admin)`。
4. 保持 `POST /api/v1/executors/register` 使用 IP 白名单注册机制，不加入用户 JWT。
5. 扩展测试：非平台管理员创建租户返回 403，白名单平台管理员创建租户返回 200，非平台管理员不能创建/禁用执行器。

验证：

```powershell
pytest api/tests/test_auth.py
pytest api/tests/test_query_jobs_repository.py
ruff check api
```

预期：平台接口权限测试通过，既有 query jobs 仓储测试不回归。

### Phase 3: 租户上下文保护

目标：所有用户态业务接口从认证依赖获取已校验租户上下文。

步骤：

1. 在 `api/v1/repositories/tenants.py` 增加查询用户租户关系的方法，返回 `tenant_key`、租户状态、成员角色、成员状态。
2. 修改 `api/v1/routes/dashboard.py` 全部端点，使用 `tenant: CurrentTenantContext = Depends(get_current_tenant)`，Repository 调用只使用 `tenant.tenant_key`。
3. 修改 `api/v1/routes/query_jobs.py::list_query_jobs_status`，使用 `get_current_tenant`。
4. 修改 `api/v1/routes/query_jobs.py::load_query_jobs`，使用 `get_current_tenant(required_role="admin")`，并校验 body `tenant_key` 与上下文一致。
5. 梳理 `api/v1/routes/analysis.py`、`api/v1/routes/brand_strategy.py`、`api/v1/routes/config.py` 中涉及租户或业务数据的端点，按相同规则加入认证依赖。
6. 保留 query/body `tenant_key` 过渡兼容，但在依赖层集中校验一致性。
7. 扩展后端测试，覆盖无 token 401、跨租户 403、成员可读、成员不可加载任务、管理员可加载任务。

验证：

```powershell
pytest api/tests/
ruff check api
```

预期：所有后端测试通过；跨租户访问被拒绝。

### Phase 4: 执行器边界补强

目标：执行器只能处理分配给自己的任务，不能向任意租户或 job 写入结果。

步骤：

1. 在 `api/v1/repositories/query_jobs.py` 增加 `executor_has_job_scope(db, executor_id, tenant_key, job_id)`。
2. 在 `api/v1/routes/query_jobs.py` 增加 `verify_executor_job_scope` 或共享 helper。
3. 修改 `api/v1/routes/conversation.py::load_conversations`，在写入前校验 `request.tenant_key + request.job_id + executor_id` 是否存在匹配任务。
4. 为 `conversation/load` 增加测试：正确执行器可写入；错误执行器、错误租户、错误 job 返回 403。

验证：

```powershell
pytest api/tests/test_query_jobs_repository.py
pytest api/tests/
ruff check api
```

预期：执行器边界测试通过，不破坏现有 fetch/report。

### Phase 5: 前端登录态

目标：前端形成真实登录态，所有受保护 API 自动带认证 header。

步骤：

1. 新建 `web/src/auth/storage.js`，封装 access token、当前租户和用户信息的 localStorage 读写。
2. 新建 `web/src/auth/AuthContext.jsx`，提供 `login`、`logout`、`refreshMe`、`selectTenant`、`currentTenantKey`。
3. 修改 `web/src/api/client.js`，支持传入 `authToken`、`tenantKey`，自动注入 `Authorization` 和 `X-Tenant-Key`。
4. 修改 `web/src/api/auth.js`，新增 `getMe`，登录成功后保存 token 和用户信息。
5. 新建 `web/src/components/LoginView.jsx`，使用现有 shadcn/ui 表单风格实现登录。
6. 新建 `web/src/components/ProtectedRoute.jsx`，未登录时跳转 `/login`。
7. 修改 `web/src/App.jsx` 和 `web/src/config/routes.js`，新增 `/login`、`/activate`、`/register` 路由，并保护 DashboardLayout 下的租户页面。
8. 修改 `web/src/hooks/useDashboardParams.js` 或 API Adapter 调用链，确保路由中的 `tenantKey` 被映射为 API header。
9. 收敛 `AccountManagement.jsx`：保留平台/注册调试能力时必须显示权限状态；正式租户创建按钮只对平台管理员可见。
10. 增加前端测试，覆盖 API client header 注入、登录后保存 token、退出后清理 token。

验证：

```powershell
npm --prefix web test
npm --prefix web run build
```

预期：前端测试和构建通过；受保护页面未登录时不能直接访问。

### Phase 6: 验证、文档收尾与迁移说明

目标：完成硬门禁，确保文档与实现一致。

步骤：

1. 运行全量后端测试和 ruff。
2. 运行前端测试和构建。
3. 启动后端与前端，手动验证登录、激活、注册、租户切换、跨租户拒绝。
4. 更新 `docs/SECURITY.md`、`docs/ARCHITECTURE.md`、`docs/ARCHITECTURE_MULTITENANT.md`、API 参考中的“现状差距”。
5. 更新本 ExecPlan 的 Progress、Decision Log、Outcomes & Retrospective、验证记录。
6. 全部完成后将本文件移动到 `docs/exec-plans/completed/`，更新 completed index，并删除根目录 `TASKS.md`。

验证：

```powershell
pytest api/tests/
ruff check api
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
python scripts/validate_agents_docs.py --level WARN
```

预期：硬门禁通过；如 WARN 仍存在，需在 Outcomes 中解释残余风险。

## Validation and Acceptance

### API 验收

1. 未认证调用 `/api/v1/dashboard/*` 返回 401。
2. 已认证用户访问不属于自己的 `tenant_key` 返回 403。
3. `tenant_member` 可查看 Dashboard 和任务状态。
4. `tenant_member` 调用任务加载返回 403。
5. `tenant_admin` 可加载本租户查询任务。
6. 非平台管理员调用 `/api/v1/platform/tenants` 返回 403。
7. 平台管理员可创建租户。
8. 执行器只能拉取、上报和写入分配给自己的任务。

### 前端验收

1. `/login` 可登录并进入默认租户页面。
2. 刷新页面后 `GET /api/v1/auth/me` 可恢复登录态。
3. 退出后本地 token 被清理，受保护页面跳转登录。
4. 切换租户后 API 请求携带新的 `X-Tenant-Key`。
5. 跨租户 403 时前端显示可理解错误，不泄露其他租户信息。

## Outcomes & Retrospective

已完成 Phase 1 后端认证基础层：

- 新增 `api/v1/utils/jwt_utils.py`，登录 access token 迁移为标准 JWT，并兼容旧 access token 验证。
- 新增 `api/v1/dependencies/auth.py`，提供 `get_current_user`、`get_current_tenant`、`require_current_tenant`、`require_platform_admin`。
- 新增 `GET /api/v1/auth/me`。
- 登录响应新增 `tokenType`、`expiresIn`、租户角色和成员状态。

验证记录：

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_auth.py api/tests/test_auth_dependencies.py -q`：13 passed，存在既有 Pydantic/SQLite 警告。
- `uv run --project api ruff check api`：All checks passed。

残余风险：

- Phase 1 尚未把 auth 请求/响应模型完全迁移到 `api/v1/models/schemas.py`，后续 Phase 可结合路由改造继续收敛。

已完成 Phase 2 平台管理保护：

- `POST /api/v1/platform/tenants` 加入 `require_platform_admin`。
- `POST /api/v1/executors/`、`GET /api/v1/executors/`、`DELETE /api/v1/executors/{executor_id}` 加入 `require_platform_admin`。
- `POST /api/v1/executors/register` 保持执行器 IP 白名单注册机制，不混用用户 JWT。

验证记录：

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_auth.py api/tests/test_platform_admin_auth.py api/tests/test_query_jobs_repository.py -q`：14 passed，存在既有 Pydantic 警告。
- `uv run --project api ruff check api`：All checks passed。

已完成 Phase 3 租户上下文保护：

- Dashboard 路由组加入统一 `get_current_tenant` 依赖，现有 query `tenant_key` 进入依赖层校验后继续兼容。
- `GET /api/v1/query-jobs/status` 改为使用已校验的 `CurrentTenantContext.tenant_key`。
- `POST /api/v1/query-jobs/load` 改为要求租户管理员角色，并校验 body `tenant_key` 与上下文一致。

验证记录：

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_auth.py api/tests/test_auth_dependencies.py api/tests/test_platform_admin_auth.py api/tests/test_tenant_context_routes.py api/tests/test_query_jobs_repository.py -q`：23 passed，存在既有 Pydantic/SQLite 警告。
- `uv run --project api ruff check api`：All checks passed。

残余风险：

- Phase 3 先覆盖 Dashboard 路由组和 Query Jobs 用户态接口；`analysis.py`、`brand_strategy.py`、`config.py` 未发现直接租户数据访问，但后续全量审计仍需复核。

已完成 Phase 4 执行器边界补强：

- `api/v1/repositories/query_jobs.py` 新增 `executor_has_job_scope`，按 `executor_id + tenant_key + job_id` 校验未删除任务绑定。
- `api/v1/routes/query_jobs.py` 提供 `verify_executor_job_scope`，供执行器写入类接口复用。
- `api/v1/routes/conversation.py::load_conversations` 在写入前校验执行器任务范围，未绑定返回 403。
- `api/tests/test_conversation_executor_scope.py` 覆盖错误执行器拒绝与正确执行器可写入。
- `api/tests/test_dashboard_locf.py` 增加统一 dashboard 测试 client，显式 override 已认证租户上下文，避免业务测试混入登录夹具。

验证记录：

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_conversation_executor_scope.py api/tests/test_query_jobs_repository.py -q`：3 passed，存在既有 SQLite 警告。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：47 passed，存在既有 Pydantic/SQLite 警告。
- `uv run --project api ruff check api`：All checks passed。

已完成 Phase 5 前端登录态：

- 新增 `web/src/auth/storage.js`，封装本地会话读写、默认租户选择和当前租户更新。
- 新增 `web/src/auth/AuthContext.jsx`，提供登录、退出、刷新 `/auth/me`、租户选择和当前用户状态。
- `web/src/api/client.js` 自动注入 `Authorization` 和 `X-Tenant-Key`，租户优先级为显式参数、body、URL query、当前会话。
- 新增 `web/src/components/LoginView.jsx`，提供登录、管理员激活和员工注册入口。
- 新增 `web/src/components/ProtectedRoute.jsx`，未登录访问业务路由时跳转 `/login`。
- `DashboardLayout` 增加租户选择和退出入口；`AccountManagement` 按 `platformRoles` 控制平台租户创建按钮。
- 登录响应和 `/auth/me` 返回 `platformRoles`，与 `PLATFORM_ADMIN_EMAILS` 保持一致。

验证记录：

- `npm --prefix web test -- --test-reporter=spec`：35 passed。
- `npm --prefix web run build`：构建通过。
- `npm --prefix web run lint`：0 errors，9 warnings，均为既有未使用变量/Hook 依赖警告。
- Playwright 本地检查：`/login` 桌面与移动渲染正常；未登录 dashboard 重定向 `/login`；模拟登录后 dashboard API 请求携带 `Authorization` 与 `X-Tenant-Key`。

已完成 Phase 6 验证与文档收尾：

- 更新产品规格、API 参考、架构补充和安全文档，把“执行前差距”改为当前实现与后续增强。
- 后端全量测试、ruff、前端测试、前端构建、前端 lint 和本地浏览器验证均完成。

最终验证记录：

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：47 passed，存在既有 Pydantic/SQLite 警告。
- `uv run --project api ruff check api`：All checks passed。
- `npm --prefix web test -- --test-reporter=spec`：35 passed。
- `npm --prefix web run build`：构建通过。
- `npm --prefix web run lint`：0 errors，9 warnings（既有警告）。

残余风险：

- 登录、激活、邀请码验证和员工注册尚未接入限流与审计事件。
- 平台管理员仍是环境变量白名单，后续应迁移到平台管理员表。
- 旧 access token 兼容逻辑仍在宽限期内保留，后续需要按迁移计划移除。
