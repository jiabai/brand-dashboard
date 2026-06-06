# 平台管理员全租户只读看板规格

> 状态：已实现，2026-05-21 修订
>
> 本文档定义平台管理员查看所有租户业务看板数据的产品边界。技术设计见 `docs/design-docs/20260520-040000-platform-admin-tenant-read-access.md`，实现计划见 `docs/exec-plans/active/20260520-040000-platform-admin-tenant-read-access.md`。

## 1. 背景

平台运营、交付和支持人员需要在客户反馈“看板无数据、指标异常、任务状态不对”等问题时，快速进入目标租户看板核对数据。当前实现中，平台管理员只拥有 `/platform/*` 平台后台权限；租户工作台仍要求 `user_tenants` membership。因此平台管理员默认只能访问自己被显式加入的租户。

这会导致平台管理员可以看到租户列表，却不能直接打开租户 dashboard 排障。对 B2B SaaS 平台运营不够顺手。

## 2. 目标

1. 平台管理员可以只读访问任意 active 租户的 dashboard 数据。
2. 平台管理员不需要被写入每个租户的 `user_tenants`。
3. 租户成员权限模型保持不变：普通用户仍必须通过 `user_tenants` 才能访问租户数据。
4. 写操作不随只读权限自动放开，任务加载、成员管理、租户内配置仍需要租户管理员或单独的平台代操作设计。
5. 平台后台租户列表提供目标租户入口，不依赖前端 demo 默认 `jobId` 或 `brand`；存在 `latestJob` 时可直达对应 dashboard，缺少最近任务时进入任务状态页再选择具体任务。

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
| 查看所属租户 dashboard | 是 | 是 | 是 | 是 |
| 加载查询任务 | 否，本阶段不放开 | 是 | 否 | 否 |
| 管理租户成员 | 否，本阶段不放开 | 后续 | 否 | 否 |
| 执行器拉取/上报任务 | 否 | 否 | 否 | 否 |

## 5. 用户流程

### 5.1 从平台后台进入目标租户

1. 平台管理员登录 `/platform/tenants`。
2. 在租户列表中找到目标 active 租户。
3. 如果该租户存在 `latestJob.jobId`，点击“看板”直达 `/dashboard/<tenantKey>/<latestJob.jobId>?brand=<latestJob.brand>`。
4. 如果该租户暂无最近任务，点击“任务状态”跳转到 `/tasks/<tenantKey>/status`，由用户选择具体任务进入 dashboard。
5. 进入 dashboard 后，API 请求携带当前 access token 和目标 `tenant_key`。
6. 后端识别当前用户为 `platform_admin`，确认目标租户 active，并授予只读租户上下文。

### 5.2 直接访问租户 URL

平台管理员直接打开 `/dashboard/<tenantKey>/<jobId>` 时，也应可读取目标租户 dashboard 数据；普通用户仍按原 membership 规则校验。

## 6. API 行为

Dashboard 只读接口使用新的授权依赖：

- 普通用户：必须存在 active `user_tenants` membership。
- 平台管理员：无需 membership，但目标租户必须 active。
- 租户不存在或停用：403 或 404 按现有错误策略处理，不返回业务数据。

本阶段只覆盖 `/api/v1/dashboard/*`。以下接口不纳入平台只读旁路：

- `/api/v1/query-jobs/load`
- `/api/v1/conversation/load`
- `/api/v1/executors/*`
- 后续任何会写业务数据、改变租户配置或改变成员关系的接口

## 7. 前端行为

1. `/platform/tenants` 租户列表保留“任务状态”操作；当平台 API 返回 `latestJob` 时，额外提供使用真实 `tenantKey + jobId + brand` 的“看板”入口。
2. 平台管理员进入 dashboard 时，不要求目标租户出现在登录响应的 `user.tenants` 中。
3. API client 继续从 URL/query/body 提取目标 `tenant_key` 并注入 `X-Tenant-Key`。
4. Dashboard 顶部租户选择器仍只展示用户真实 membership；平台只读浏览时可显示当前路由租户名或 `tenant_key`，不必把所有租户塞进登录态。
5. 前端不再使用 `VITE_DEFAULT_TENANT_KEY`、`VITE_DEFAULT_JOB_ID`、`VITE_DEFAULT_BRAND` 作为 dashboard 兜底；租户和任务来自路由/会话，平台租户列表进入 dashboard 时品牌必须来自 `latestJob.brand`。

## 8. 验收标准

- 平台管理员访问未加入 membership 的 active 租户 dashboard 返回 200。
- 非平台管理员访问未加入 membership 的租户 dashboard 仍返回 403。
- 平台管理员访问停用租户 dashboard 返回 403。
- 平台管理员访问 `query-jobs/load` 等写接口仍返回 403，除非同时是该租户 admin。
- `/platform/tenants` 可跳转到目标租户任务状态页，且不需要默认 job id。
- 文档、后端测试、前端测试和构建通过。
