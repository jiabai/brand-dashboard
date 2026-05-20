# B2B SaaS 多租户注册、登录与租户管理规格

> 状态：Phase 1-5 已落地，2026-05-20 修订
>
> 本文档定义 Brand Dashboard 面向 to B 企业客户的多租户注册、登录、租户成员管理与安全边界。它覆盖用户可见流程和产品验收标准；技术实现细节见 `docs/ARCHITECTURE_MULTITENANT.md`，API 契约见 `docs/references/20260519-000000-tenant-account-api-reference.md`。

## 1. 背景与目标

Brand Dashboard 将从单租户/弱鉴权数据看板演进为企业级 SaaS。系统必须支持平台侧为客户企业开通租户、客户管理员激活账号、企业员工通过邀请码加入租户、用户登录后在其有权限的租户内访问数据。

本阶段目标是建立安全可上线的 MVP：

1. 平台操作员可创建企业租户和首个租户管理员。
2. 租户管理员可通过激活链接设置密码并登录。
3. 租户员工可通过邀请码注册并加入企业租户。
4. 登录后所有业务数据访问必须经过服务端认证与租户成员关系校验。
5. 前端保留 `tenantKey` 作为路由和当前租户选择信号，但后端不得信任客户端自报租户。

本阶段非目标：

1. 不实现自助试用租户注册入口；企业租户由平台侧创建。
2. 不实现完整计费、发票、合同审批流。
3. 不实现 SSO/SAML/OIDC；后续企业版可单独立项。
4. 不引入新前端状态管理库。

## 2. 角色与权限

### 2.1 产品角色

| 产品角色 | 说明 | 主要入口 | 数据库映射 |
|---|---|---|---|
| 平台管理员 `platform_admin` | 乙方运营/销售/交付人员，负责开通租户、管理执行器和平台级配置 | `/api/v1/platform/*`、`/api/v1/executors/*` | 短期使用环境变量白名单，长期使用 `platform_admins` 表 |
| 租户管理员 `tenant_admin` | 客户企业负责人，拥有本企业成员、任务和看板管理权限 | 租户内管理页面、任务加载接口 | `user_tenants.role = admin` |
| 租户成员 `tenant_member` | 客户企业普通员工，可访问本企业看板与任务状态 | 仪表板、分析页、任务状态页 | `user_tenants.role = member` |
| 租户只读成员 `tenant_viewer` | 预留角色，仅可查看看板 | 后续企业权限扩展 | `user_tenants.role = viewer` |
| 执行器 `executor` | 机器到机器身份，用于拉取任务、上报结果和写入抓取结果 | `/api/v1/query-jobs/fetch`、`/api/v1/query-jobs/report`、`/api/v1/conversation/load` | `executors.executor_id` + API Key |

### 2.2 权限矩阵

| 能力 | platform_admin | tenant_admin | tenant_member | tenant_viewer | executor |
|---|---:|---:|---:|---:|---:|
| 创建租户 | 是 | 否 | 否 | 否 | 否 |
| 创建/禁用执行器 | 是 | 否 | 否 | 否 | 否 |
| 激活自己的管理员账号 | 否 | 是 | 否 | 否 | 否 |
| 使用邀请码注册 | 否 | 否 | 是 | 可扩展 | 否 |
| 登录并查看所属租户列表 | 是 | 是 | 是 | 是 | 否 |
| 查看本租户仪表板 | 可按平台权限跨租户只读 | 是 | 是 | 是 | 否 |
| 创建或加载查询任务 | 可代操作 | 是 | 否 | 否 | 否 |
| 查看任务状态 | 可跨租户 | 是 | 是 | 是 | 否 |
| 拉取/上报执行任务 | 否 | 否 | 否 | 否 | 是 |
| 写入对话与引用结果 | 否 | 否 | 否 | 否 | 是，且必须与任务绑定 |

## 3. 核心概念

### tenant_key

- 格式：`tn_` + 12 位十六进制字符，例如 `tn_1a2b3c4d5e6f`。
- 用途：租户资源标识、URL 路由参数、业务表隔离字段。
- 约束：一旦生成永久不变；所有业务查询必须带 `tenant_key`；所有受保护 API 必须校验当前身份是否可访问该 `tenant_key`。

### 用户与租户关系

一个用户可以属于多个租户。Access Token 只证明“用户是谁”，不直接证明“当前请求可以访问哪个租户”。当前租户必须由前端路径、`X-Tenant-Key` header 或过渡期 query/body 中显式选择，服务端通过 `user_tenants` 校验成员关系和角色。

### 邀请码

- 格式：6 位大写字母和数字，例如 `ABC123`。
- 默认有效期：30 天。
- 使用限制：可设置最大使用次数；超过次数或过期后不可注册。
- 安全要求：验证邀请码接口可返回租户展示名，但不得泄露租户内部成员、计划、联系人等敏感信息。

### 激活令牌

- 现状格式：自定义 HMAC 签名 token，即 `payload.signature`。
- 用途：租户管理员首次激活账号。
- 有效期：7 天。
- 安全要求：单次使用；激活后用户状态变为 `active`；重复激活返回统一错误。

### 访问令牌

- 目标格式：标准 JWT，即 `header.payload.signature`，算法 `HS256`。
- 用途：用户登录后访问受保护 API。
- 有效期：12 小时。
- Payload 不包含可授权的 `tenant_key`；只包含 `sub`、`type=access`、`iat`、`exp` 等身份和时效信息。

## 4. 用户流程

### 4.1 平台操作员创建企业租户

1. 平台操作员登录平台管理后台。
2. 提交企业名称、行业、管理员姓名、管理员邮箱、计划类型、用户上限、期望子域名等信息。
3. 后端在事务中校验企业名称、管理员邮箱、子域名唯一性。
4. 后端创建 `tenants`、管理员 `users`、`user_tenants(role=admin)` 和默认 `invitation_codes`。
5. 后端生成管理员激活链接和初始邀请码。
6. MVP 阶段返回激活链接，由平台操作员人工发送给客户管理员；后续可接入邮件服务。

验收标准：

- 未登录或非平台管理员调用创建租户接口返回 401/403。
- 重复企业名称、重复子域名、异常邮箱状态会失败并回滚。
- 成功响应不返回管理员临时密码或密码哈希。
- 创建动作记录审计信息，包括操作者、租户、管理员邮箱、请求 ID。

### 4.2 租户管理员激活账号

1. 管理员打开激活链接。
2. 前端提交激活 token、密码、确认密码。
3. 后端验证 token 签名、类型、过期时间和用户状态。
4. 后端写入新密码哈希，将用户置为 `active` 和 `is_verified=true`。
5. 前端引导管理员进入登录页。

验收标准：

- 密码和确认密码不一致时返回 400。
- token 过期、类型错误、签名错误、用户不存在或已激活时返回统一安全错误，不泄露内部状态。
- 密码必须满足最小长度和复杂度策略，服务端 Pydantic 校验和仓储层校验一致。

### 4.3 租户员工通过邀请码注册

1. 员工输入邀请码，前端可先调用验证接口展示企业名称。
2. 员工提交姓名、邮箱、密码、手机号。
3. 后端验证邀请码状态、过期时间、使用次数和目标租户状态。
4. 后端创建新用户或复用已有用户，并新增 `user_tenants(role=member)`。
5. 后端递增邀请码使用次数。
6. 注册成功后用户可登录。

验收标准：

- 邀请码过期、停用、超限时无法注册。
- 已加入该租户的邮箱不能重复注册。
- 复用已有邮箱时必须验证账号状态，避免将停用或暂停账号加入新租户。
- 注册和登录失败错误文案统一，避免邮箱枚举。

### 4.4 用户登录与租户选择

1. 用户提交邮箱和密码。
2. 后端验证用户状态和密码。
3. 后端返回 access token、用户基础信息和可访问租户列表。
4. 前端保存 token，并选择默认租户进入应用。
5. 前端访问业务 API 时携带 `Authorization: Bearer <token>` 和当前租户标识。
6. 后端每次请求都校验 token、用户状态、租户状态、成员关系和角色。

验收标准：

- 登录成功响应包含租户列表和每个租户内角色。
- 登录失败统一返回 401 或业务错误，不区分邮箱不存在和密码错误。
- 用户被停用、租户被停用、成员关系被停用后，后续请求立即返回 403。
- 前端切换租户后，业务请求必须使用新的当前租户标识。

## 5. API 分区

| 分区 | 示例 | 身份机制 | 租户策略 |
|---|---|---|---|
| Public Auth | `/api/v1/public/auth/login`、`/api/v1/public/auth/activate` | 无登录态，依赖密码、激活 token 或邀请码 | 只允许完成注册/登录所需的最小租户信息 |
| Platform | `/api/v1/platform/tenants`、`/api/v1/executors/*` | `Authorization` + `platform_admin` | 可管理多个租户，但必须有审计 |
| Tenant User | `/api/v1/dashboard/*`、`/api/v1/query-jobs/status` | `Authorization` + `X-Tenant-Key` | 服务端强制校验 `user_tenants` |
| Tenant Admin | `/api/v1/query-jobs/load` | `Authorization` + `X-Tenant-Key` + `tenant_admin` | body/query 中的 `tenant_key` 必须与上下文一致 |
| Executor | `/api/v1/query-jobs/fetch`、`/api/v1/query-jobs/report`、`/api/v1/conversation/load` | `executor_id` + `X-Executor-Key` | 必须校验任务、执行器、租户绑定关系 |

## 6. 当前实现状态

已实现：

- `api/v1/routes/auth.py` 提供租户创建、管理员激活、邀请码验证、员工注册、用户登录。
- `api/v1/repositories/auth.py` 实现事务化租户创建；登录 access token 已迁移为标准 JWT，激活 token 保持自定义 HMAC。
- `api/database/schema_auth.sql` 包含 `tenants`、`users`、`user_tenants`、`tenant_configs`、`invitation_codes`。
- `api/v1/routes/query_jobs.py` 的执行器 fetch/report 已有 `X-Executor-Key` 校验。
- `api/v1/dependencies/auth.py` 已提供当前用户、当前租户、租户角色和平台管理员鉴权依赖。
- Dashboard、任务状态、任务加载已接入用户-租户成员校验；任务加载要求租户管理员。
- `conversation/load` 已校验执行器、租户、job 绑定。
- 前端已形成登录态、受保护路由、退出、租户切换，以及 `Authorization` / `X-Tenant-Key` 自动注入。

后续增强：

- 登录、激活、邀请码验证和员工注册仍需接入限流、审计事件和统一错误枚举策略。
- 平台管理员 MVP 仍使用 `PLATFORM_ADMIN_EMAILS` 白名单，后续应迁移到可审计的平台管理员表。
- Auth 请求/响应模型后续可从路由内联模型收敛到 `api/v1/models/schemas.py`。

## 7. 安全与合规要求

1. 所有受保护接口必须有认证依赖；公开接口只限注册登录最小流程。
2. 所有业务查询必须在数据访问层带 `tenant_key`，且该 `tenant_key` 必须来自已校验的租户上下文。
3. Pydantic 模型必须校验邮箱格式、密码长度、邀请码格式、子域名格式、计划类型枚举和日期格式。
4. 认证失败、密码错误、邮箱不存在不得泄露可枚举信息。
5. 密码继续使用 PBKDF2-SHA256 现有格式；如迁移 Argon2 或 bcrypt，需要单独设计兼容策略。
6. Access token 使用 `AUTH_SECRET` 签名，生产环境未配置时应用必须启动失败。
7. 创建租户、登录失败、激活失败、跨租户拒绝、执行器认证失败必须可审计。
8. 生产 CORS 必须限制为实际域名。

## 8. 验收清单

- 平台管理员可以创建租户，非平台管理员不能创建租户。
- 管理员可以激活账号并登录。
- 员工可以通过有效邀请码注册，不能通过无效或过期邀请码注册。
- 登录响应返回标准 JWT、用户信息、租户列表和角色。
- 无 token 请求 Dashboard 返回 401。
- 有 token 但访问不属于自己的 `tenant_key` 返回 403。
- `tenant_admin` 可以加载查询任务，`tenant_member` 不能加载查询任务。
- 执行器只能写入与其任务匹配的租户和 job 数据。
- 前端登录、激活、注册、退出和租户切换流程可用。
- `pytest api/tests/`、`npm --prefix web run build`、`python scripts/validate_agents_docs.py --level ERROR` 通过。
