# 平台运营后台产品规格

> 状态：MVP 已落地，2026-06-09 更新
>
> 本文档定义 Brand Dashboard 平台运营人员使用的独立 Web 后台。它补充 `docs/product-specs/20260519-000000-multi-tenant-registration-flow.md`：多租户注册和登录能力已经具备，但平台运营入口必须从租户工作台中拆出，形成独立权限域和清晰的信息架构。技术设计见 `docs/ARCHITECTURE_MULTITENANT.md`，API/前端契约见 `docs/references/20260520-010000-platform-operations-console-reference.md`。

## 1. 背景

变更前系统已经具备平台管理员鉴权和 `POST /api/v1/platform/tenants` 创建租户接口；前端也曾在租户工作台的 `AccountManagement` 页面中提供“租户开通”表单。这个入口适合作为早期管理工具，但不适合作为正式 to B SaaS 的平台运营后台，原因是：

1. 平台运营人员不是某个客户租户的成员视角，不应先进入 `/:tenantKey` 租户工作台才能创建租户。
2. 平台级操作和租户级操作共享一个页面，会让权限、导航和审计边界变模糊。
3. 平台运营需要租户列表、创建结果追踪、激活链接/邀请码查看等运营能力，当前租户工作台页面没有独立承载这些工作流。

## 2. 目标与非目标

### 2.1 目标

1. 新增独立平台运营后台入口，路径以 `/platform` 开头，不依赖租户路由参数。
2. 平台运营人员登录后可查看租户列表，搜索客户企业，筛选租户状态和计划类型。
3. 平台运营人员可创建企业租户和首个租户管理员。
4. 创建成功后页面明确展示 `tenantKey`、管理员邮箱、激活链接和邀请码，并支持复制。
5. 非平台管理员不能进入平台运营后台，也不能看到平台级创建租户按钮。
6. 平台运营后台所有 API 使用 `Authorization: Bearer <access_token>` 和 `platform_admin` 鉴权，不使用 `X-Tenant-Key`。

### 2.2 非目标

1. 不在本阶段实现完整 CRM、合同审批、计费、发票或销售线索管理。
2. 不实现平台管理员自助邀请和权限分级；仍沿用 `PLATFORM_ADMIN_EMAILS` 白名单。
3. 不实现租户写操作或完整“代入租户”功能；平台侧只读排障入口通过独立权限边界承载。
4. 不实现租户成员管理；成员管理属于后续租户管理员后台能力。
5. 不重构现有租户 Dashboard 的信息架构，只新增平台运营后台边界。

## 3. 角色与权限

| 角色 | 能否访问 `/platform` | 能力 | 拒绝策略 |
|---|---:|---|---|
| `platform_admin` | 是 | 查看租户列表、创建租户、查看创建结果 | N/A |
| `tenant_admin` | 否 | 只能进入所属租户工作台 | 显示 403 页面，引导返回租户工作台 |
| `tenant_member` | 否 | 只能进入所属租户工作台 | 显示 403 页面，引导返回租户工作台 |
| 未登录用户 | 否 | 无 | 跳转 `/login` |

平台运营后台不需要当前租户上下文；它的授权来源是 `platformRoles`，短期由 `PLATFORM_ADMIN_EMAILS` 派生，长期迁移到平台管理员表。

## 4. 信息架构

### 4.1 路由

| 路由 | 页面 | 权限 | 说明 |
|---|---|---|---|
| `/platform` | 重定向 | `platform_admin` | 重定向到 `/platform/tenants` |
| `/platform/tenants` | 租户管理 | `platform_admin` | MVP 主页面：租户列表 + 创建租户 |
| `/platform/tenants/:tenantKey` | 租户详情 | `platform_admin` | 查看租户元数据、项目摘要、项目工作台主入口和排障入口 |
| `/platform/executors` | 执行器健康 | `platform_admin` | 查看执行器健康、队列和失败任务 |

### 4.2 页面结构

`/platform/tenants` 第一版采用工作台式布局：

1. 顶部：产品标识、当前平台用户邮箱、退出按钮。
2. 左侧导航：租户管理为唯一启用项；执行器管理可作为后续占位。
3. 主区上方：租户搜索框、状态筛选、计划筛选、创建租户按钮。
4. 主区表格：租户名称、`tenantKey`、状态、计划、用户上限、合同到期日、创建时间。
5. 创建租户抽屉或页面内表单：复用现有租户创建字段，但不放在租户工作台里。
6. 创建结果面板：展示激活链接、邀请码和登录地址；刷新页面后不保证仍可查看一次性 activation token。

`/platform/tenants/:tenantKey` 作为租户运营中转页：

1. 顶部：租户名称、`tenantKey`、返回列表、进入项目工作台、刷新。
2. 摘要：租户状态、成员数、项目数、任务数。
3. 排障入口：最新任务看板、任务状态、最近 Job 摘要。
4. 客户资料：管理员、计划、合同、行业和创建时间。
5. 项目概览：项目名称、状态、行业、品类和更新时间摘要；每行提供“打开项目”和“数据质量”。该区域是租户详情摘要，不承担完整项目工作台语义。

## 5. 核心流程

### 5.1 平台运营人员进入后台

1. 用户访问 `/platform`。
2. 未登录时跳转 `/login`，登录后返回 `/platform/tenants`。
3. 平台管理员直接从 `/login` 登录且没有原始来源页时，默认进入 `/platform/tenants`。
4. 已登录但不是 `platform_admin` 时显示 403。
5. `platform_admin` 调用 `GET /api/v1/platform/tenants` 加载租户列表。

验收标准：

- 未登录访问不会发起平台 API 请求。
- 非平台管理员看不到租户列表和创建按钮。
- 平台后台不需要 `tenantKey` 路由参数，也不发送 `X-Tenant-Key`。

### 5.2 查看租户列表

1. 页面默认请求第一页租户列表，按创建时间倒序。
2. 平台运营人员可按关键词搜索企业名称、`tenantKey`、管理员邮箱。
3. 平台运营人员可按租户状态和计划类型筛选。
4. 空结果展示清晰空状态，不暴露 SQL 或内部错误。

验收标准：

- 列表接口必须只返回平台运营所需元数据，不返回密码、token、执行器 API Key 或租户业务数据。
- 搜索和筛选在 URL query 中保留，刷新后状态可恢复。
- API 错误时页面展示可理解错误，并允许重试。

### 5.3 创建租户

1. 平台运营人员点击“创建租户”。
2. 页面提交企业名称、行业、管理员姓名、管理员邮箱等必填字段；可选填写计划、计费周期、用户上限、合同日期、子域名。
3. 后端复用 `POST /api/v1/platform/tenants` 创建租户。
4. 成功后刷新租户列表，并显示创建结果面板。

验收标准：

- 必填字段前端受控校验，后端 Pydantic 再校验。
- 创建中按钮进入 loading 状态，避免重复提交。
- 创建成功后必须展示激活链接和邀请码，并提醒激活链接只在本次结果中展示。
- 创建失败时保留表单输入，展示后端错误消息。

### 5.4 查看租户详情并排障

1. 平台运营人员在 `/platform/tenants` 搜索目标租户。
2. 点击“详情”进入 `/platform/tenants/<tenantKey>`。
3. 先确认租户状态、管理员状态、合同和项目摘要。
4. 需要进入主业务工作流时，点击“进入项目工作台”进入 `/projects/<tenantKey>`。
5. 已经知道目标项目时，在项目行点击“打开项目”进入 `/projects/<tenantKey>/<projectId>?from=platform-tenant-detail`。
6. 需要看采集失败、过期分析和指标覆盖时，在项目行点击“数据质量”进入 `/projects/<tenantKey>/<projectId>/quality?from=platform-tenant-detail`。
7. 只有排查旧任务或兼容看板时，才在“排障入口”点击“最新任务看板”或“任务状态”。

验收标准：

- 详情页请求平台 API，不发送 `X-Tenant-Key`。
- 非平台管理员不能访问详情 API。
- 项目摘要只读展示，不提供项目创建、编辑或成员管理操作。
- 从项目概览直达项目详情时，详情页返回“项目概览”；从项目工作台进入项目详情时，详情页返回“项目工作台”。
- 平台管理员进入 `/projects/*` 后可只读访问 active 租户项目 GET；写接口仍要求租户 admin membership。

## 6. API 分区

平台运营后台使用平台 API 分区：

| API | 用途 | 鉴权 | 租户上下文 |
|---|---|---|---|
| `GET /api/v1/platform/tenants` | 平台侧租户列表 | `platform_admin` | 不需要 `X-Tenant-Key` |
| `GET /api/v1/platform/tenants/{tenant_key}` | 平台侧租户详情和项目摘要 | `platform_admin` | 不需要 `X-Tenant-Key` |
| `POST /api/v1/platform/tenants` | 创建租户 | `platform_admin` | 不需要 `X-Tenant-Key` |
| `GET /api/v1/auth/me` | 恢复登录态和平台角色 | 登录用户 | 不需要 `X-Tenant-Key` |
| `GET /api/v1/projects` | 项目工作台列表 | 租户成员或平台只读 active 租户 | 需要目标 `X-Tenant-Key` |
| `GET /api/v1/projects/{project_id}` | 项目详情 | 租户成员或平台只读 active 租户 | 需要目标 `X-Tenant-Key` |
| `GET /api/v1/projects/{project_id}/data-quality` | 项目数据质量 | 租户成员或平台只读 active 租户 | 需要目标 `X-Tenant-Key` |
| `GET /api/v1/projects/{project_id}/reports` | 项目报告列表 | 租户成员或平台只读 active 租户 | 需要目标 `X-Tenant-Key` |
| `GET /api/v1/projects/{project_id}/alerts` | 项目告警 | 租户成员或平台只读 active 租户 | 需要目标 `X-Tenant-Key` |

`GET /api/v1/platform/tenants` 是本次新增目标接口；`POST /api/v1/platform/tenants` 已存在但需要由新平台页面调用。

## 7. 安全要求

1. `/platform/*` 页面必须由前端 `PlatformRoute` 或等价 guard 保护。
2. 后端平台 API 必须使用 `require_platform_admin`，不能依赖前端隐藏按钮。
3. 平台 API 不接受 `tenant_key` 作为授权依据，不使用 `get_current_tenant`。
4. 平台租户列表只能返回租户和首个管理员的运营元数据，不返回 activation token 历史、password hash、API Key 或业务数据。
5. 创建租户、查看租户列表、权限拒绝必须进入审计计划；当前阶段至少保留 request id 和操作者上下文。
6. `PLATFORM_ADMIN_EMAILS` 是 MVP 机制；生产增强应迁移到可审计的平台管理员表。

## 8. 当前实现状态

已具备：

- 登录态、`platformRoles` 返回、受保护路由基础能力。
- `POST /api/v1/platform/tenants` 后端接口和平台管理员鉴权。
- `GET /api/v1/platform/tenants` 列表接口、仓储查询和敏感字段排除测试。
- `web/src/api/platform.js` 平台 API Adapter，显式跳过 `X-Tenant-Key`。
- 独立 `/platform` 前端路由、平台后台壳层、平台权限 guard 和 403 状态。
- `/platform/tenants` 租户管理页面，支持搜索、状态/计划筛选、分页、创建租户和创建结果面板。
- `/platform/tenants/:tenantKey` 租户详情页，支持查看客户资料、项目概览、项目工作台入口、项目详情入口、数据质量入口和排障入口。
- 平台管理员直接登录后的默认落点为 `/platform/tenants`；从受保护页面跳转到登录页时仍返回原页面。
- 平台租户列表只保留“详情”主入口；最新任务看板和任务状态入口统一放在 `/platform/tenants/:tenantKey` 的“排障入口”区。
- 项目工作台是平台管理员查看客户业务现状的主入口：`/projects/:tenantKey`、`/projects/:tenantKey/:projectId`、`/projects/:tenantKey/:projectId/quality`。
- 租户工作台中的 `AccountManagement` 已降级租户创建入口，只为平台管理员展示跳转 `/platform/tenants`。

后续增强：

- 平台管理员表和审计后台。
- 邀请码管理、执行器写操作管理页。
- 登录/创建租户/查看列表的限流与完整审计记录。

## 9. 验收清单

- 未登录访问 `/platform/tenants` 跳转 `/login`。
- 非 `platform_admin` 访问 `/platform/tenants` 显示 403。
- `platform_admin` 可以看到租户列表。
- 租户列表可搜索、筛选、分页。
- `platform_admin` 可以创建租户并看到激活链接、登录地址和邀请码。
- 创建租户后列表刷新，新租户可见。
- `platform_admin` 可以从租户列表进入 `/platform/tenants/:tenantKey` 查看租户详情和项目摘要。
- `platform_admin` 可以从租户详情进入 `/projects/:tenantKey` 项目工作台。
- `platform_admin` 可以从租户详情项目行进入项目详情和数据质量页。
- `platform_admin` 无 membership 时只读项目 GET，访问 inactive 租户或项目写接口仍被拒绝。
- 平台后台 API 请求携带 `Authorization`，不携带 `X-Tenant-Key`。
- `AccountManagement` 不再作为正式平台运营入口；租户工作台只保留租户侧员工注册、邀请码核验和登录辅助能力，管理员首次激活仅通过公开 `/activate` 流程完成。
- `npm --prefix web test`、`npm --prefix web run build`、`uv run --project api --extra dev pytest api/tests/ -q`、`python scripts/validate_agents_docs.py --level ERROR` 通过。
