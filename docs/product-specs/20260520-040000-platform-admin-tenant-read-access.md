# 平台管理员全租户项目与看板只读规格

> 状态：已实现，2026-05-21 修订，2026-06-09 修订
>
> 本文档定义平台管理员查看所有 active 租户项目工作台与业务看板数据的产品边界。技术设计见 `docs/design-docs/20260520-040000-platform-admin-tenant-read-access.md`。

## 1. 背景

平台运营、交付和支持人员需要在客户反馈“看板无数据、指标异常、任务状态不对”等问题时，快速进入目标租户看板核对数据。当前实现中，平台管理员只拥有 `/platform/*` 平台后台权限；租户工作台仍要求 `user_tenants` membership。因此平台管理员默认只能访问自己被显式加入的租户。

这会导致平台管理员可以看到租户列表，却不能直接打开租户 dashboard 排障。对 B2B SaaS 平台运营不够顺手。

## 2. 目标

1. 平台管理员可以只读访问任意 active 租户的项目工作台和 dashboard 数据。
2. 平台管理员不需要被写入每个租户的 `user_tenants`。
3. 租户成员权限模型保持不变：普通用户仍必须通过 `user_tenants` 才能访问租户数据。
4. 写操作不随只读权限自动放开，任务加载、成员管理、租户内配置仍需要租户管理员；平台管理员不作为租户管理员代理创建、编辑、归档或删除租户项目。
5. 平台后台租户列表只提供目标租户详情入口，不依赖前端 demo 默认 `jobId` 或 `brand`；租户详情页以“进入项目工作台”为主入口，旧 dashboard 和任务状态放入排障入口。

## 3. 非目标

1. 不实现平台管理员对租户工作台的写权限。
2. 不把平台管理员批量加入所有租户。
3. 不在本阶段新增平台管理员表或审计表；继续沿用 `PLATFORM_ADMIN_EMAILS` MVP。
4. 不改变业务查询的 `tenant_key` 强制过滤。
5. 不改变执行器认证和任务绑定边界。

## 4. 权限矩阵

| 能力 | platform_admin | tenant_admin | tenant_member | tenant_viewer |
|---|---:|---:|---:|---:|
| 查看平台租户列表 | 是 | 否 | 否 | 否 |
| 创建租户 | 是 | 否 | 否 | 否 |
| 查看任意 active 租户 dashboard | 是，只读 | 否，仅所属租户 | 否，仅所属租户 | 否，仅所属租户 |
| 查看任意 active 租户项目工作台 GET | 是，只读 | 否，仅所属租户 | 否，仅所属租户 | 否，仅所属租户 |
| 查看所属租户 dashboard | 是 | 是 | 是 | 是 |
| 加载查询任务 | 否，本阶段不放开 | 是 | 否 | 否 |
| 管理租户成员 | 否，本阶段不放开 | 后续 | 否 | 否 |
| 执行器拉取/上报任务 | 否 | 否 | 否 | 否 |

## 5. 用户流程

### 5.1 从平台后台进入目标租户

1. 平台管理员登录 `/platform/tenants`。
2. 在租户列表中找到目标 active 租户。
3. 点击“详情”进入 `/platform/tenants/<tenantKey>`。
4. 点击“进入项目工作台”进入 `/projects/<tenantKey>`。
5. 在项目列表或租户详情项目行中打开具体项目 `/projects/<tenantKey>/<projectId>`。
6. 需要排查数据完整性时进入 `/projects/<tenantKey>/<projectId>/quality`。
7. 只有排查旧任务或兼容看板时，才在详情页“排障入口”点击“最新任务看板”或“任务状态”。
8. 进入项目页或 dashboard 后，API 请求携带当前 access token 和目标 `tenant_key`。
9. 后端识别当前用户为 `platform_admin`，确认目标租户 active，并授予只读租户上下文。

### 5.2 直接访问租户 URL

平台管理员直接打开 `/projects/<tenantKey>`、`/projects/<tenantKey>/<projectId>`、`/projects/<tenantKey>/<projectId>/quality` 或 `/dashboard/<tenantKey>/<jobId>` 时，也应可读取目标 active 租户的只读数据；普通用户仍按原 membership 规则校验。

## 6. API 行为

Dashboard 和项目 GET 只读接口使用新的授权依赖：

- 普通用户：必须存在 active `user_tenants` membership。
- 平台管理员：无需 membership，但目标租户必须 active。
- 租户不存在或停用：403 或 404 按现有错误策略处理，不返回业务数据。

本阶段覆盖：

- `GET /api/v1/dashboard/*`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{project_id}`
- `GET /api/v1/projects/{project_id}/data-quality`
- `GET /api/v1/projects/{project_id}/reports`
- `GET /api/v1/projects/{project_id}/alerts`

以下接口不纳入平台只读旁路：

- `/api/v1/query-jobs/load`
- `POST /api/v1/projects`
- `POST /api/v1/projects/{project_id}/brands`
- `POST /api/v1/projects/{project_id}/prompt-sets`
- `POST /api/v1/projects/{project_id}/reports`
- `/api/v1/conversation/load`
- `/api/v1/executors/*`
- 后续任何会写业务数据、改变租户配置或改变成员关系的接口

## 7. 前端行为

1. `/platform/tenants` 租户列表只保留“详情”操作。
2. `/platform/tenants/:tenantKey` 顶部主按钮“进入项目工作台”跳 `/projects/:tenantKey`。
3. `/platform/tenants/:tenantKey` 项目行提供“打开项目”和“数据质量”，分别跳 `/projects/:tenantKey/:projectId` 和 `/projects/:tenantKey/:projectId/quality`。
4. 平台管理员进入 `/projects/:tenantKey` 后，项目工作台顶部提供“返回租户详情”，跳回 `/platform/tenants/:tenantKey`。
5. 当平台 API 返回 `latestJob` 时，由 `/platform/tenants/:tenantKey` 详情页的“排障入口”提供使用真实 `tenantKey + jobId + brand` 的“最新任务看板”入口。
6. 平台管理员进入项目工作台或 dashboard 时，不要求目标租户出现在登录响应的 `user.tenants` 中。
7. API client 继续从 URL/query/body 提取目标 `tenant_key` 并注入 `X-Tenant-Key`。
8. Dashboard 顶部租户选择器仍只展示用户真实 membership；平台只读浏览时必须显示当前登录账号，并显示当前路由租户名或 `tenant_key`，不必把所有租户塞进登录态。
9. 平台管理员进入租户项目工作台时始终按平台客户视角处理；即使该账号历史上拥有目标租户 membership，也不展示“加入团队”等租户侧入口。
10. 平台只读进入数据质量页时不展示“重新分析”等写操作按钮。
11. 平台只读进入项目列表、项目详情或数据质量页时，应显示“平台只读视角”提示，说明当前页面只用于查看、排障和体验客户视角。
11. 前端不再使用 `VITE_DEFAULT_TENANT_KEY`、`VITE_DEFAULT_JOB_ID`、`VITE_DEFAULT_BRAND` 作为 dashboard 兜底；租户和任务来自路由/会话，平台租户列表进入 dashboard 时品牌必须来自 `latestJob.brand`。

## 8. 验收标准

- 平台管理员访问未加入 membership 的 active 租户 dashboard 返回 200。
- 平台管理员访问未加入 membership 的 active 租户项目列表、项目详情和数据质量返回 200。
- 非平台管理员访问未加入 membership 的租户 dashboard 仍返回 403。
- 平台管理员访问停用租户 dashboard 返回 403。
- 平台管理员访问 `query-jobs/load` 等写接口仍返回 403，除非同时是该租户 admin。
- `/platform/tenants` 只跳租户详情；租户详情可跳项目工作台、项目详情、数据质量、最新任务看板和任务状态，且不需要默认 job id。
- 平台管理员以只读旁路进入项目列表、项目详情和数据质量页时，页面提示其不能创建、编辑、归档或删除客户项目。
- 文档、后端测试、前端测试和构建通过。
