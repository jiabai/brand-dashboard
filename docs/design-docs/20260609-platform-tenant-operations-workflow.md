# 平台租户项目工作台中转页设计

> 日期：2026-06-09
>
> 状态：已实现

## 背景

平台管理员登录后默认进入 `/platform/tenants`。此前租户列表同时承担客户发现和排障入口，平台管理员点击“看板”会直接跳到某个租户的 legacy dashboard。这个路径可用，但缺少一层客户运营上下文，也会让旧 `tenant_key + job_id` 看板重新变成主入口。当前产品主线已经收敛到项目工作台，因此平台管理员也应先进入租户详情，再进入项目工作台或具体项目；旧 dashboard 和任务状态只作为排障入口保留。

## 设计目标

1. 平台后台继续保持平台域身份：不依赖当前租户，不发送 `X-Tenant-Key`。
2. 平台管理员从租户列表先进入租户详情，再以 `/projects/:tenantKey` 作为主业务入口。
3. 租户详情展示运营所需摘要：租户状态、管理员、合同、任务、最近 Job 和项目概览。
4. 租户详情的旧 dashboard 和任务状态入口统一降级为“排障入口”，不再承担主路径。
5. 平台管理员可只读进入 active 租户项目工作台，但不获得租户写权限。

## 路由与数据流

```text
/platform/tenants
  -> /platform/tenants/:tenantKey
       -> 进入项目工作台 /projects/:tenantKey
       -> 打开项目 /projects/:tenantKey/:projectId?from=platform-tenant-detail
       -> 数据质量 /projects/:tenantKey/:projectId/quality?from=platform-tenant-detail
       -> 排障入口：最新任务看板 /dashboard/:tenantKey/:jobId
       -> 排障入口：任务状态 /tasks/:tenantKey/status
  -> /platform/executors
```

`/platform/tenants/:tenantKey` 调用 `GET /api/v1/platform/tenants/{tenant_key}`。该接口使用 `require_platform_admin`，返回平台运营视图中的租户元数据和监测项目摘要。进入 `/projects/*` 后，项目 GET API 使用平台只读租户上下文：有真实 membership 的用户按原租户权限读取；无 membership 的 `platform_admin` 只能读取 active 租户。

项目详情页存在两个上游入口，因此返回目标必须由来源决定：

- 从 `/projects/:tenantKey` 项目工作台进入项目详情：不携带来源，详情页返回 `/projects/:tenantKey`。
- 从 `/platform/tenants/:tenantKey` 的“项目概览”进入项目详情或数据质量：携带 `from=platform-tenant-detail`，详情页返回 `/platform/tenants/:tenantKey#project-overview`。
- 数据质量页返回项目详情时保留 `from=platform-tenant-detail`，避免“项目概览 -> 数据质量 -> 项目详情 -> 返回”链路丢失来源。

## 权限边界

| 能力 | 本次行为 |
|------|----------|
| 查看租户详情 | `platform_admin` 可通过平台 API 读取 |
| 查看项目摘要 | `platform_admin` 可通过平台 API 读取摘要 |
| 查看项目工作台 | `platform_admin` 可只读访问 active 租户的项目 GET 接口 |
| 查看 dashboard | 继续沿用既有 dashboard 只读旁路，作为排障入口 |
| 新建/修改项目 | 不放开，仍要求租户 admin membership |
| 管理成员 | 不放开 |
| 写入任务 | 不放开 |

## 决策

| 决策 | 原因 |
|------|------|
| 新增平台详情 API，而不是复用租户项目 API | 平台后台属于平台域，不能为了读取项目摘要而伪造租户 membership。 |
| 租户列表只保留“详情”入口 | 平台后台第一层只负责找到客户，避免同一行同时出现详情、看板、任务状态三种去向。 |
| 详情页主按钮为“进入项目工作台” | 项目工作台是当前主业务入口；旧 dashboard 不再作为平台管理员主路径。 |
| 详情页项目区命名为“项目概览” | 避免与 `/projects/:tenantKey` 的“项目工作台”混淆；详情页只承接摘要和快捷下钻。 |
| 项目行提供“打开项目”和“数据质量” | 平台管理员常见动作是进入具体项目看配置和质量，不应被迫先打开 legacy dashboard。 |
| 项目概览下钻携带来源参数 | 同一个项目详情页同时服务项目工作台和租户详情页，返回目标必须按入口上下文分流。 |
| 旧 dashboard 和任务状态放入“排障入口” | 兼容旧任务和现场排障，但避免主路径语义混乱。 |
| 项目 GET 使用平台只读依赖，写接口保持原样 | 平台管理员能看 active 租户项目现状，但不被写入 membership，也不获得租户 admin 权限。 |

## 验证策略

- 后端：平台管理员可读详情，非平台管理员拒绝，缺失租户 404，项目 GET 对 active 租户只读放行，inactive 租户和写接口拒绝。
- 前端：平台详情 API 不发送 `X-Tenant-Key`，详情路径、项目工作台路径、带来源的项目详情路径和数据质量路径正确编码，响应规范化稳定。
- 构建：前端生产构建通过。
- 文档：`validate_agents_docs.py --level ERROR` 通过。
