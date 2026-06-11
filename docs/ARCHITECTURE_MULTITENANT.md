# 多租户认证与数据隔离架构补充

> 状态：多租户认证、租户隔离与平台运营后台 MVP 已落地，2026-06-09 修订
>
> 本文档补充 `docs/ARCHITECTURE.md`，聚焦多租户认证、租户上下文、授权边界、机器身份和数据隔离执行机制。产品流程见 `docs/product-specs/20260519-000000-multi-tenant-registration-flow.md`，API 契约见 `docs/references/20260519-000000-tenant-account-api-reference.md`。

## 1. 当前状态

### 1.1 已具备能力

| 能力 | 文件 | 状态 |
|---|---|---|
| 租户创建 | `api/v1/repositories/auth.py::create_tenant_with_admin` | 已实现 |
| 管理员激活 | `api/v1/repositories/auth.py::activate_admin_account` | 已实现 |
| 员工注册 | `api/v1/repositories/auth.py::register_employee` | 已实现 |
| 邀请码验证 | `api/v1/repositories/auth.py::verify_invite_code` | 已实现 |
| 用户登录 | `api/v1/repositories/auth.py::authenticate_user` | 已实现 |
| 密码哈希 | `api/v1/utils/security.py::hash_password` | 已实现，PBKDF2-SHA256 |
| 自定义 token | `api/v1/utils/security.py::sign_token` | 已实现，`payload.signature` |
| 执行器 fetch/report 认证 | `api/v1/routes/query_jobs.py::verify_executor` | 已实现，`executor_id` + `X-Executor-Key` |
| 多租户基础表 | `api/database/schema_auth.sql` | 已实现 |
| 标准 JWT access token | `api/v1/utils/jwt_utils.py` | 已实现，兼容旧 access token 验证 |
| 用户/租户认证依赖 | `api/v1/dependencies/auth.py` | 已实现 |
| 平台管理员鉴权 | `require_platform_admin` | 已实现，MVP 使用 `PLATFORM_ADMIN_EMAILS` |
| 首个平台管理员 bootstrap | `api/scripts/bootstrap_platform_admin.py` | 已实现，本地/部署 CLI，不暴露 HTTP API |
| 租户访问授权 | `api/scripts/grant_tenant_access.py` | 已实现，本地/部署 CLI，为已有用户显式写入 `user_tenants` |
| 平台管理员全租户项目与看板只读 | `get_current_tenant_for_read` / `get_current_tenant_for_dashboard_read` | 已实现，仅用于明确的 GET 读接口 |
| 前端登录态 | `web/src/auth/*`、`web/src/components/LoginView.jsx` | 已实现 |

### 1.2 已修复的安全缺口

| 缺口 | 影响 | 风险 |
|---|---|---|
| 平台管理接口无平台管理员鉴权 | 任意调用者可创建租户、创建/禁用执行器 | 已修复 |
| Dashboard、任务状态、任务加载等用户接口无用户认证 | 业务数据可被未登录访问 | 已修复 |
| 租户上下文依赖客户端传 `tenant_key` | 恶意用户可尝试横向访问其他租户 | 已修复 |
| Access token 使用自定义 HMAC 格式 | 标准库不可验证，缺少 `sub/iat/exp` 语义 | 已修复 |
| 登录响应未返回租户角色 | 前端无法稳定展示租户内权限 | 已修复 |
| 执行器写入未绑定任务上下文 | 执行器可能向非授权租户/job 写入结果 | 已修复 |

后续增强项：登录/激活/邀请码验证限流与审计、平台管理员表、移除旧 access token 兼容逻辑、Auth Pydantic 模型收敛到共享 schemas。

### 1.3 新增平台运营后台边界

当前系统已经新增独立 Platform Console，`AccountManagement` 不再承载正式租户创建表单，也不承载登录前的管理员首次激活流程：

- Web 路由以 `/platform` 开头，不携带 `tenantKey`。
- API 使用 `/api/v1/platform/*`，只依赖 `Authorization` 和 `platform_admin`。
- 不使用 `get_current_tenant`，不发送 `X-Tenant-Key`。
- MVP 页面聚焦租户列表和租户创建；执行器管理后续接入同一后台。
- 租户管理员首次激活使用公开 `/activate?token=...` 入口；登录后的 `/accounts/:tenantKey` 加入团队页只保留员工注册和邀请码核验，不承载租户创建、成员管理或登录辅助表单。

## 2. 目标架构

### 2.1 身份分区

系统存在两类身份，不能混用：

| 身份类型 | 凭据 | 适用接口 | 授权来源 |
|---|---|---|---|
| 用户身份 | `Authorization: Bearer <access_token>` | 登录后的平台管理和租户用户接口 | `users`、`user_tenants`、平台管理员白名单或平台管理员表 |
| 执行器身份 | `executor_id` + `X-Executor-Key` | 任务拉取、任务上报、对话结果写入 | `executors` 与任务绑定关系 |

用户身份分为两个 Web 权限域：

| Web 权限域 | 路由 | API | 租户上下文 |
|---|---|---|---|
| Platform Console | `/platform/*` | `/api/v1/platform/*`、平台级 `/api/v1/executors/*` | 不需要 `tenantKey`，不得发送 `X-Tenant-Key` |
| Tenant Workspace | `/dashboard/:tenantKey/*`、`/tasks/:tenantKey/*`、`/accounts/:tenantKey` | `/api/v1/dashboard/*`、租户级 `/api/v1/query-jobs/*` | 必须发送并校验当前租户 |

### 2.2 用户请求链路

```text
Browser
  Authorization: Bearer <JWT>
  X-Tenant-Key: tn_xxx
        |
        v
FastAPI route
        |
        +-- Depends(get_current_user)
        |     - 解析标准 JWT
        |     - 校验 type=access、exp、用户状态
        |
        +-- Depends(get_current_tenant)
              - 从 X-Tenant-Key 读取目标租户
              - 过渡期允许 query/body tenant_key，但必须与 X-Tenant-Key 一致
              - 校验租户 active
              - 校验 user_tenants 关系 active
              - 校验角色满足 required_role
        |
        v
Service / Repository
  只使用 CurrentTenantContext.tenant_key 查询业务数据
```

关键原则：

- Access token 只证明用户身份，不直接授权某个租户。
- 当前租户必须显式选择，并由服务端校验成员关系。
- 前端 URL 中的 `tenantKey` 只用于路由和用户体验，不是安全来源。
- Repository 层继续强制所有业务查询携带 `tenant_key`。

### 2.3 执行器请求链路

```text
Executor
  query: executor_id
  header: X-Executor-Key
        |
        v
Depends(verify_executor)
  - 校验执行器存在、active、API Key 匹配
        |
        +-- fetch/report
        |     - 通过 executor_id 限制可拉取/上报的任务
        |
        +-- conversation/load
              - 校验 request.tenant_key + request.job_id 属于该 executor_id
              - 写入对话和引用
```

执行器接口不使用用户 JWT。执行器不拥有平台或租户管理权限，只能处理分配给自己的任务。

### 2.4 平台运营后台请求链路

```text
Platform operator browser
  Authorization: Bearer <JWT>
        |
        v
React /platform route
        |
        +-- AuthProvider
        |     - 恢复 access token
        |     - GET /api/v1/auth/me 获取 platformRoles
        |
        +-- PlatformRoute
              - 未登录跳转 /login
              - 平台管理员直登默认进入 /platform/tenants
              - 非 platform_admin 显示 403
        |
        v
FastAPI /api/v1/platform/*
        |
        +-- Depends(require_platform_admin)
              - 解析用户
              - 校验 platform_admin
        |
        v
Platform repository
  查询租户元数据，不查询租户业务数据
```

关键原则：

- Platform Console 是平台元数据后台，不是租户工作台的一个子页面。
- 平台请求不带 `tenant_key`，避免把平台权限和租户成员权限混在一起。
- 平台后台可以管理租户生命周期，并通过项目与 dashboard 只读旁路查看 active 租户业务数据。
- 平台后台进入租户工作台时先到 `/platform/tenants/<tenantKey>`，再以 `/projects/<tenantKey>` 作为主入口；旧 dashboard 和任务状态只作为排障入口。
- Dashboard 展示粒度为 `tenant_key + job_id`，平台管理员查看租户看板时必须使用该租户实际拥有的 `job_id`，不能使用全局默认 `job_id`（不同租户的 `job_id` 不互通，使用错误 `job_id` 会导致查询结果为空）。
- 平台租户列表必须展示 job 摘要；`/api/v1/platform/tenants` 的 `latestJob` 只来自同一 `tenant_key` 下未删除的 `llm_query_jobs`，前端“最新任务看板”排障入口必须使用 `tenantKey + latestJob.jobId + latestJob.brand`，不能让 dashboard 从品牌指标排名中自动选择目标品牌。
- 平台管理员查看 dashboard 不写入 `user_tenants`；平台域身份和客户租户成员身份保持分离。
- 平台管理员只读旁路不能满足租户内写接口的 `tenant_admin` 要求。

## 3. 授权模型

### 3.1 角色映射

| 产品角色 | 数据库存储 | 说明 |
|---|---|---|
| `platform_admin` | MVP：`PLATFORM_ADMIN_EMAILS` 白名单；长期：`platform_admins` 表 | 平台级权限 |
| `tenant_admin` | `user_tenants.role = admin` | 租户内管理权限 |
| `tenant_member` | `user_tenants.role = member` | 租户内读权限 |
| `tenant_viewer` | `user_tenants.role = viewer` | 预留只读权限 |

### 3.2 权限谓词

后端依赖层提供以下谓词：

| 谓词 | 说明 | 典型用途 |
|---|---|---|
| `get_current_user` | 解析并校验 access token | 所有登录后接口 |
| `require_platform_admin` | 用户 email 在平台管理员白名单或平台管理员表中 | 创建租户、管理执行器 |
| `get_current_tenant(required_role=None)` | 校验用户属于目标租户 | 租户成员读接口 |
| `get_current_tenant_for_read` | 用户属于目标租户，或平台管理员只读访问 active 租户 | 明确列入的 GET 读接口 |
| `get_current_tenant_for_dashboard_read` | `get_current_tenant_for_read` 的 dashboard 兼容包装 | Dashboard 只读接口 |
| `get_current_tenant(required_role="admin")` | 校验用户为租户管理员 | 加载查询任务、成员管理 |
| `verify_executor` | 校验执行器 API Key | 任务拉取/上报 |
| `verify_executor_job_scope` | 校验执行器、租户、job 的绑定 | 对话写入、结果写入 |

### 3.3 导入租户访问授权

历史数据或人工导入租户可能先拥有 `tenants` 和业务表数据，但没有对应用户 membership。对于非平台管理员用户，仍应使用本地/部署 CLI 显式授予访问：

```powershell
uv run --project api python api/scripts/grant_tenant_access.py --email <user@example.com> --tenant-key <tn_xxx> --role viewer
```

该 CLI 只写入 `user_tenants`，不创建用户、不修改平台管理员白名单。平台管理员读取项目工作台或 dashboard 则走专用只读依赖，不需要 CLI membership。

### 3.4 平台管理员项目与 dashboard 只读访问

平台管理员属于平台域身份。为支持运营和交付排障，项目 GET 和 dashboard 读接口允许 `platform_admin` 查看任意 active 租户业务数据，但该能力不进入 `user_tenants`，也不能满足租户写接口的 admin 要求。

设计约束：

- 只适用于明确列入的 GET：`/api/v1/dashboard/*`、`GET /api/v1/projects`、`GET /api/v1/projects/{project_id}`、`GET /api/v1/projects/{project_id}/data-quality`、`GET /api/v1/projects/{project_id}/reports`、`GET /api/v1/projects/{project_id}/alerts`。
- 目标租户必须 active。
- Repository 层继续按目标 `tenant_key` 查询，不允许跨租户聚合泄露。
- Dashboard 查询粒度为 `tenant_key + job_id`：平台管理员传入的 `job_id` 必须属于目标租户，否则查询结果为空；平台管理员应通过任务状态接口先获取该租户的有效 `job_id`，再构建 dashboard 访问路径。
- 登录响应 `user.tenants` 仍只返回真实 membership，不返回所有租户。

## 4. ADR

### ADR-001：Access Token 只承载用户身份

**决策**：Access Token 中只放 `sub=user_id`、`type=access`、`iat`、`exp`，不把 `tenant_key` 作为授权依据。

**理由**：

- 一个用户可属于多个租户，token 内写死租户会阻碍租户切换。
- 用户被移出租户后，服务端查 `user_tenants` 可以立即生效。
- URL 和 API header 可以表达当前租户，但必须由服务端校验。

### ADR-002：Access Token 迁移为标准 JWT

**决策**：访问令牌迁移到标准 JWT，使用 `PyJWT` 和 `HS256`，复用 `AUTH_SECRET`。激活令牌可在本阶段继续使用现有自定义 HMAC 格式。

**迁移策略**：

1. 新登录签发标准 JWT。
2. `verify_access_token` 在 7 天宽限期内兼容旧 access token。
3. 宽限期结束后移除旧 access token 兼容逻辑。
4. 激活 token 保持自定义 HMAC，避免把一次性流程与登录态迁移混在一起。

目标 payload：

```json
{
  "sub": "123",
  "type": "access",
  "iat": 1779235200,
  "exp": 1779278400
}
```

### ADR-003：当前租户通过 `X-Tenant-Key` 传入

**决策**：用户态 API 使用 `X-Tenant-Key` header 表达当前租户；过渡期允许 query/body 中继续出现 `tenant_key`，但必须与已校验上下文一致。

**理由**：

- 前端已经使用路径参数承载 `tenantKey`，API Adapter 可以统一映射为 header。
- 相比把租户放进 token，header 更适合用户主动切换租户。
- 相比继续散落 query/body，统一 header 更利于依赖层抽象和审计。

### ADR-004：共享数据库 + 应用层强制隔离

**决策**：继续使用共享数据库、共享 schema，通过应用层和 Repository 层强制 `tenant_key` 隔离。

**理由**：

- 当前 MySQL schema 已围绕 `tenant_key` 建立外键和索引。
- 业务表已有 `tenant_key` 字段。
- 现阶段没有引入独立 schema 或数据库的运维必要性。

强制机制：

- 所有业务 Repository 方法保留 `tenant_key` 参数。
- Route 层不直接从用户输入把 `tenant_key` 传给 Repository，必须通过 `CurrentTenantContext`。
- 测试覆盖跨租户拒绝和缺少租户上下文拒绝。

### ADR-005：平台管理员采用短期白名单、长期表结构

**决策**：MVP 阶段使用 `PLATFORM_ADMIN_EMAILS` 白名单保护平台路由；后续迁移到 `platform_admins` 表。

**理由**：

- 当前 schema 没有平台管理员表，白名单可快速关闭严重安全缺口。
- 平台管理员属于平台域，不应混入任意租户的 `user_tenants`。
- 长期表结构可支持审计、禁用、分级平台权限。

**Bootstrap**：

- 首个平台管理员通过 `api/scripts/bootstrap_platform_admin.py` 创建或激活 `users` 记录。
- CLI 可显式使用 `--write-env` 将邮箱加入 `api/.env` 的 `PLATFORM_ADMIN_EMAILS`。
- CLI 不写入、不打印明文密码；密码只经过 `hash_password` 后入库。
- 已停用或封禁账号不能被 CLI 自动恢复，必须人工审查。

### ADR-006：平台运营后台独立于租户工作台

**决策**：新增 `/platform/*` 作为平台运营后台路由前缀，不复用 `/:tenantKey` 租户工作台壳层承载正式平台运营能力。

**理由**：

- 平台运营人员是平台域身份，不一定属于任何客户租户。
- 租户工作台的路由、菜单和 API 都围绕当前租户设计，继续混放平台操作会让 `tenantKey` 语义变得不可靠。
- 独立后台可以清晰表达平台权限、租户元数据、审计和后续执行器管理。

**取舍**：

- MVP 会增加一套路由壳层和少量 API Adapter，但可以复用现有 AuthProvider、shadcn/ui 和平台管理员依赖。
- `AccountManagement` 中已有的租户创建表单可迁移复用字段和校验，但正式入口应转移到 Platform Console。

## 5. 目标组件

### 5.1 Token 工具

目标文件：`api/v1/utils/jwt_utils.py`

职责：

- `create_access_token(user_id: int, secret: str) -> str`
- `verify_access_token(token: str, secret: str) -> dict`
- 过渡期兼容旧 access token。
- 不处理激活 token；激活 token 继续由 `security.py` 负责。

### 5.2 认证依赖

目标文件：`api/v1/dependencies/auth.py`

职责：

- 定义 `CurrentUser` 和 `CurrentTenantContext`。
- 从 `Authorization` 解析用户。
- 从 `X-Tenant-Key` 解析当前租户。
- 查询用户状态、租户状态、成员关系和角色。
- 提供 `require_platform_admin` 与 `get_current_tenant(required_role)`。

### 5.3 前端认证入口

当前文件范围：

- `web/src/api/client.js`
- `web/src/api/auth.js`
- `web/src/components/AccountManagement.jsx`
- `web/src/config/routes.js`
- 新增登录、激活、注册相关组件或页面。

职责：

- 保存和读取 access token。
- 在 API Adapter 中自动注入 `Authorization`。
- 根据当前路由或选中租户注入 `X-Tenant-Key`。
- 未登录时跳转登录页。
- `/activate?token=...` 是租户管理员首次激活的公开入口；`AccountManagement` 不承载管理员首次激活表单。
- 不通过 `VITE_DEFAULT_TENANT_KEY`、`VITE_DEFAULT_JOB_ID` 或 `VITE_DEFAULT_BRAND` 提供业务默认值；租户来自登录态/路由，任务来自任务路径，品牌来自 URL 或 dashboard 数据。

### 5.4 平台运营后台组件

目标文件范围：

- `web/src/api/platform.js`
- `web/src/components/platform/PlatformLayout.jsx`
- `web/src/components/platform/PlatformRoute.jsx`
- `web/src/components/platform/PlatformTenantsPage.jsx`
- `web/src/components/platform/CreateTenantPanel.jsx`

职责：

- `/platform/*` 使用独立壳层，不依赖 `useDashboardParams`。
- Platform API Adapter 自动携带 `Authorization`，显式跳过 `X-Tenant-Key`。
- 租户列表支持搜索、状态筛选、计划筛选和分页。
- 创建租户成功后展示一次性激活链接、登录地址和邀请码。

## 6. 路由改造策略

| 路由组 | 当前实现 | 后续 |
|---|---|---|
| `/api/v1/public/auth/login` | 公开，返回标准 JWT 和租户角色列表 | 登录失败 HTTP 状态可进一步统一为 401 |
| `/api/v1/public/auth/activate` | 公开，使用激活 token | 保持公开，强化错误与密码校验 |
| `/api/v1/public/users/register` | 公开，使用邀请码 | 保持公开，强化账号状态和枚举防护 |
| `/api/v1/platform/tenants` `POST` | `require_platform_admin` | 平台管理员表和审计 |
| `/api/v1/platform/tenants` `GET` | `require_platform_admin`，不使用租户上下文，返回租户元数据和 job 摘要 | 平台管理员表和审计 |
| `/api/v1/executors/*` | 创建/列表/禁用需要 `require_platform_admin`；register 保留 IP 白名单 | 平台管理员表和审计 |
| `/api/v1/dashboard/*` | `get_current_tenant_for_dashboard_read`，query `tenant_key` 过渡兼容 | 继续只读，允许平台管理员查看 active 租户 |
| `/api/v1/projects` GET、`/api/v1/projects/{project_id}` GET、项目质量/报告/告警 GET | `get_current_tenant_for_read` | 平台管理员可只读 active 租户；写接口仍要求租户 admin |
| `/api/v1/query-jobs/status` | `get_current_tenant` | 兼容期后可减少 query 依赖 |
| `/api/v1/query-jobs/load` | `get_current_tenant(required_role="admin")`，body tenant_key 必须一致 | 增加更细粒度任务权限 |
| `/api/v1/query-jobs/fetch` | 执行器认证 | 保持执行器认证，并继续按 executor_id 限制任务 |
| `/api/v1/conversation/load` | 执行器认证，并验证 job scope | 结果写入审计 |

## 7. 验证策略

### 后端测试

- `api/tests/test_auth.py`：登录返回标准 JWT；旧 access token 兼容；非平台管理员不能创建租户。
- 新增 `api/tests/test_auth_dependencies.py`：缺 token 401、无租户 header 400/403、跨租户 403、角色不足 403。
- 新增或扩展 query jobs/conversation 测试：执行器不能向非绑定租户/job 写入。
- `pytest api/tests/` 通过。
- `ruff check api` 通过。

### 前端验证

- API client 单元测试覆盖 Authorization 和 `X-Tenant-Key` 注入。
- 登录页、激活页、注册页表单校验可用。
- 未登录访问受保护页面跳转登录。
- 已登录用户切换租户后请求 header 变化。
- `npm --prefix web run build` 通过。

### 文档验证

- `python scripts/validate_agents_docs.py --level ERROR`
- `python scripts/validate_agents_docs.py --level WARN`
