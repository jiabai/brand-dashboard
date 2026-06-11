# 项目看板入口改用 collection_jobs 作为采集任务来源

> 状态：已实现，2026-06-11
>
> 本文档修订 `docs/product-specs/20260611-project-dashboard-entry.md` 的**数据来源决策**：把项目详情页「进入看板」Sheet 的采集任务来源，从 legacy 的 `llm_query_jobs`（每条查询提示词一行）改为重构后领域模型的 `collection_jobs`（一次采集任务一行）。其余产品意图（项目详情页入口、用户选采集任务、落地 legacy 首页看板）不变。

## 1. 背景

原实现用 `GET /api/v1/query-jobs/status?project_id=` 从 `llm_query_jobs` 取采集任务。但 `llm_query_jobs` 是**查询定义表（每条提示词一行）**：一个采集任务有多条 query 时，Sheet 会列出多条「品牌/状态/时间区间完全相同」的行（实测某项目 1 个采集任务显示为 12 行重复项），用户无法有意义地选择，且每行 React key 相同。

`collection_jobs` 是重构后领域模型里的「采集任务」实体：**一次采集任务一行**，带 job 级 `status`（pending/running/succeeded/failed/expired/cancelled）、采集时间窗 `window_start/window_end`、任务计数、`project_id`，并通过 `source_job_id` 关联到 legacy `job_id`（看板的寻址键，数据在 `qa_brand_state`/`qa_reference`/`llm_conversations` 中按该 job_id 存储）。已验证库内 `collection_jobs.source_job_id` 100% 能对应到 `llm_query_jobs.job_id`。

## 2. 目标

1. 项目详情页「进入看板」Sheet 的采集任务来源改为 `collection_jobs`，**一次采集任务一行**。
2. 新增 `GET /api/v1/projects/{project_id}/collection-jobs`：按 `tenant_key + project_id` 列出该项目的采集任务，仅含 `source_job_id` 非空者（能进 legacy 看板的）。
3. 选择某采集任务 → 跳转 `/dashboard/{tenantKey}/{source_job_id}?brand={targetBrand}`，进入 legacy 首页看板。
4. 看板品牌参数取项目**目标品牌**（`project_brands.role='target'` 第一条）；无目标品牌则省略 `brand`。
5. Sheet 每行展示：采集任务状态（job 级 status）、采集时间窗、成功/期望任务数。
6. 项目无可进看板的采集任务时展示空状态，不报错。

## 3. 非目标

1. 不修改 legacy 看板页面及其数据接口；不把看板迁移到新采集模型寻址。
2. 不展示 `source_job_id` 为空的采集任务（纯新模型新建、尚无 legacy 看板的任务）。
3. 不做多采集任务对比或聚合。
4. 不回滚上一阶段给 `GET /api/v1/query-jobs/status` 增加的 `project_id` 过滤参数与前端适配器 `projectId` 入参（向后兼容、无害，保留）。
5. 不改 `collection_jobs` 表结构（复用既有 `source_job_id`、`project_brands.role`）。
6. 落地仅首页看板；其余 legacy 页由用户进入后自行切换。
7. 不改授权模型。

## 4. 用户流程

### 4.1 正常进入看板

1. 租户用户在 `/projects/{tenantKey}/{projectId}` 打开项目详情，点击「进入看板」。
2. Sheet 加载该项目的采集任务列表（按时间窗倒序，最近在前）。
3. 每行展示采集任务状态徽章、采集时间窗、成功/期望任务数。
4. 用户点击某行 → 跳转 `/dashboard/{tenantKey}/{source_job_id}?brand={targetBrand}`，进入首页看板。

### 4.2 项目无可进看板的采集任务

1. 用户点击「进入看板」。
2. 接口返回空列表（项目尚无采集任务，或现有采集任务 `source_job_id` 均为空）。
3. Sheet 展示「该项目还没有采集任务，暂无看板数据」空状态，不报错、不跳转。

## 5. API 行为

### 5.1 新增 `GET /api/v1/projects/{project_id}/collection-jobs`

- 权限：`get_current_tenant_for_read`（与项目列表/详情读接口一致；active 成员或平台只读旁路）。数据按 `tenant_key` 隔离。
- 行为：`SELECT ... FROM collection_jobs WHERE tenant_key = :tenant_key AND project_id = :project_id AND source_job_id IS NOT NULL ORDER BY window_start DESC, id DESC`。
- 响应 `data`：
  - `targetBrand`：项目目标品牌名（`project_brands` 中 `role='target'`、`status='active'` 的第一条 `brand_name`）；无则为 `null`。
  - `collectionJobs[]`：每项含 `collectionJobId`、`sourceJobId`、`status`、`windowStart`、`windowEnd`、`expectedTaskCount`、`succeededTaskCount`、`failedTaskCount`。
- 不返回 legacy 查询定义细节；不暴露 `source_job_id` 为空的采集任务。

### 5.2 看板数据接口

- 不改动。看板继续由 legacy `job_id`（= `collection_jobs.source_job_id`）寻址，`get_current_tenant` 守卫，数据按 `tenant_key` 过滤。

## 6. 页面行为

### 6.1 项目详情页 Sheet（ProjectDetailPage）

- 「进入看板」按钮不变；点击打开 Sheet。
- Sheet 数据源由 `fetchQueryJobStatus` 改为 `fetchProjectCollectionJobs(projectId)`。
- 每行：采集任务状态徽章（`getCollectionJobStatusMeta` 映射 pending/running/succeeded/failed/expired/cancelled → 中文 + variant）、采集时间窗（`windowStart ~ windowEnd`，无 end 显示「进行中」）、成功/期望任务数（如 `12/12`）。
- 点击行 → `buildProjectDashboardPath({ tenantKey, jobId: sourceJobId, brand: targetBrand })` 导航。
- 加载中/失败/空状态：沿用现有交互与空状态文案。

### 6.2 死代码清理

- 上一阶段的 `normalizeProjectJobRecords`（仅旧 Sheet 使用）改源后成为死代码，连同其单测一并删除。
- `buildProjectDashboardPath` 继续复用，不改。

## 7. 安全要求

1. 新接口经 `get_current_tenant_for_read`：必须是该租户 active 成员或平台只读管理员；跨租户请求被拒。
2. 数据按 `tenant_key` 过滤；`project_id` 仅作过滤条件，授权以服务端为准。
3. 不在响应或日志输出敏感凭据；本功能不涉及密码、token 或邮件。
4. 看板与其数据接口的授权不变。

## 8. 验收标准

- 项目详情页「进入看板」Sheet 对「1 采集任务 × N 查询」的项目只显示 **1 行**（不再是 N 行重复项）。
- 选择某采集任务后跳转 `/dashboard/{tenantKey}/{source_job_id}?brand={targetBrand}`，看板展示对应数据。
- `GET /api/v1/projects/{project_id}/collection-jobs` 仅返回该项目、该租户、`source_job_id` 非空的采集任务；按时间窗倒序。
- 目标品牌正确解析（`project_brands.role='target'`）；无目标品牌时 `brand` 省略。
- 跨租户/非成员调用被拒绝。
- 无可进看板的采集任务时展示空状态，不报错。
- `normalizeProjectJobRecords` 及其单测已删除，前端无残留引用。
- 后端新接口（过滤、隔离、品牌解析）与前端适配器、归一化、状态映射、详情页契约有自动化测试覆盖。
- `ruff check api`、后端 pytest、前端测试、`npm --prefix web run build`、`python scripts/validate_agents_docs.py --level ERROR` 全部通过。
