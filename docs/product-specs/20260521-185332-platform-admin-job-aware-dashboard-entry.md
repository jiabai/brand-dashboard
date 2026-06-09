# 平台管理员 Job 感知看板入口规格

> 状态：已实现，2026-06-09 修订为排障入口约束
>
> 日期：2026-05-21
>
> 背景文档：`docs/product-specs/PRD.md`、`docs/ARCHITECTURE.md`、`docs/ARCHITECTURE_MULTITENANT.md`、`docs/DESIGN.md`

## 1. 背景

Dashboard 的查询与展示粒度已经收敛为 `tenant_key + job_id`。平台管理员登录后如果只看到租户列表，仍然缺少进入 dashboard 所必需的 job 上下文；使用全局默认 `job_id` 会导致跨租户 job 不匹配，页面空数据或误导排障。

## 2. 目标

1. 平台管理员在 `/platform/tenants` 看到每个租户的 job 摘要。
2. 租户列表必须暴露真实 `job_id`，至少包含最近 job 和 job 总数。
3. 平台管理员从租户详情的“排障入口”进入 dashboard 时，URL 必须使用该租户实际拥有的 `tenantKey + jobId + brand`。
4. 没有 job 的租户仍可在租户详情页进入任务状态页，但 dashboard 入口应禁用或不可显示。
5. 平台 API 仍属于平台权限域，不发送 `X-Tenant-Key`，不放开租户写权限。
6. 当前主业务入口是 `/projects/:tenantKey` 项目工作台；本规格只约束旧 dashboard 排障入口，不再定义平台管理员主路径。

## 3. 非目标

1. 不新增平台管理员的租户写权限。
2. 不把平台管理员写入所有租户的 `user_tenants`。
3. 不在租户列表中展开完整任务明细；完整任务仍由 `/tasks/:tenantKey/status` 承载。
4. 不改变 dashboard 业务查询接口的 `(tenant_key, job_id)` 过滤口径。

## 4. 用户流程

1. 平台管理员登录后进入 `/platform/tenants`。
2. 租户表格展示租户基本信息与任务摘要：job 总数、最近 job id、品牌/品类和状态。
3. 点击“详情”进入 `/platform/tenants/<tenantKey>`。
4. 若最近 job 存在且租户 active，在详情页“排障入口”点击“最新任务看板”进入 `/dashboard/<tenantKey>/<jobId>?brand=<latestJob.brand>`。
5. 若没有 job，详情页展示“暂无任务”，并保留“任务状态”入口用于后续排查或创建任务。

## 5. 验收标准

- `/api/v1/platform/tenants` 返回每个租户的 `jobCount` 和 `latestJob`。
- `latestJob.jobId` 只来自同一 `tenant_key` 的 `llm_query_jobs`。
- 前端表格展示 job 信息，不再只有租户信息。
- 租户列表只保留“详情”入口。
- 详情页“最新任务看板”排障入口使用真实 `tenantKey + latestJob.jobId + latestJob.brand`，避免自动默认到竞品品牌。
- 无 job 或非 active 租户不能点击 dashboard 入口。
- 后端测试、前端测试、构建、文档结构验证通过。
