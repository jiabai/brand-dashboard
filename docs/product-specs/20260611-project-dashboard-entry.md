# 项目详情页进入看板入口

> 状态：已实现，2026-06-11
>
> 本文档定义租户用户（含租户管理员）从项目详情页选择某次采集 job 进入 legacy 分析看板的产品流程、边界和验收标准。它补齐当前缺失的「项目工作台 → 看板」导航入口：看板数据权限本已具备，但项目工作台没有任何指向看板的可见入口。

## 1. 背景

legacy 分析看板（首页/趋势/分平台/信源/情感）按 `tenant_key + job_id` 寻址。租户用户登录后进入项目工作台（项目列表 / 项目详情 / 数据质量），但这些页面没有指向看板的入口；看板路由仅能直接拼 URL 访问。后端授权本已允许租户成员（任意角色）读取本租户看板（`dashboard` 路由由 `get_current_tenant` 守卫，仅要求 active 成员 + active 租户），因此本阶段只补前端入口与所需的 job 选择能力，不改授权模型。

平台管理员侧已有「Job 感知看板入口」（`buildTenantDashboardPath`，用 `latestJob.jobId + brand` 进 legacy 首页看板）；本阶段为租户用户在项目详情页提供等价但「由用户选择 job」的入口。

## 2. 目标

1. 项目详情页提供「进入看板」入口，与现有「数据质量」按钮并列。
2. 点击后打开右侧 Sheet，列出该项目的采集 job 记录供用户选择（用户明确选择，不自动选最新）。
3. 选择某条 job 记录后，跳转到 legacy 首页看板 `/dashboard/{tenantKey}/{jobId}`，并携带该记录的 `brand` 作为 `?brand=` 参数。
4. job 列表按 `tenant_key + project_id` 过滤，仅展示当前项目、当前租户的 job；默认不含已删除 job。
5. 项目无 job 时展示空状态文案，不报错。

## 3. 非目标

1. 不在项目列表页卡片提供入口（仅项目详情页）。
2. 不实现「自动进入最新 job」——用户明确选择。
3. 不修改 legacy 看板页面本身，也不改看板数据接口。
4. 不在本入口内做多 job 对比或聚合。
5. 不改变看板及 job 列表接口的授权模型（沿用 `get_current_tenant`）。
6. 不新增 job↔project 的数据结构（复用既有 `llm_query_jobs.project_id`）。
7. 落地仅到首页看板；趋势/分平台/信源/情感由用户进入后自行切换，不在本入口范围。

## 4. 用户流程

### 4.1 正常进入看板

1. 租户用户在 `/projects/{tenantKey}/{projectId}` 打开项目详情。
2. 点击「进入看板」，打开右侧 Sheet，加载该项目的 job 列表。
3. Sheet 每行展示：品牌、采集状态徽章、数据生效时间区间。
4. 用户点击某行 → 跳转 `/dashboard/{tenantKey}/{jobId}?brand={brand}`，进入首页看板，看到该 job、该品牌的数据。
5. 用户在看板内可继续切换趋势/分平台等 legacy 页。

### 4.2 项目暂无 job

1. 用户点击「进入看板」。
2. 接口返回空列表（项目为草稿或尚未采集）。
3. Sheet 内展示「该项目还没有采集任务，暂无看板数据」空状态，不报错、不跳转。

### 4.3 平台管理员只读视角

1. 平台管理员以只读客户视角（`isPlatformReadonlyTenantAccess` 为真）查看租户项目详情时，该入口的行为与现有只读边界保持一致，不破坏只读约定（不引入基于平台身份的越权写操作）。

## 5. API 行为

### 5.1 `GET /api/v1/query-jobs/status` 增加可选 `project_id`

- 现状：该接口按 `tenant_key` 返回租户全部 job 记录，授权为 `get_current_tenant`，每条返回 `job_id / project_id / brand / query_status / effective_from / effective_to` 等。
- 变更：新增可选查询参数 `project_id`；提供时在仓储层按 `tenant_key + project_id` 过滤；不提供时行为不变（向后兼容）。
- 授权不变：`get_current_tenant`（active 成员 + active 租户，任意角色；admin 必然通过）。数据按 `tenant_key` 隔离，跨租户不可见。
- `include_deleted` 默认 `false`，沿用现状。

### 5.2 看板数据接口

- 不改动。看板路由继续由 `get_current_tenant` 守卫，租户成员可读本租户看板，数据按 `tenant_key` 过滤。

## 6. 页面行为

### 6.1 项目详情页（ProjectDetailPage）

- 在现有动作区（「数据质量」按钮一带）新增「进入看板」按钮。
- 点击打开右侧 Sheet：
  - 加载中显示加载态；加载失败显示错误信息（复用现有 client 错误展示）。
  - 成功且有 job：列出 job 记录行，每行含品牌、`getQueryJobStatusMeta` 状态徽章、生效时间区间；点击行跳转到首页看板并携带 `brand`。
  - 成功且无 job：显示空状态文案，不提供跳转。
- 跳转路径复用 `buildViewPath('home', { tenantKey, jobId })`，`brand` 以查询参数附加（与平台侧 `buildTenantDashboardPath` 一致）。

### 6.2 前端 API 适配器

- query-jobs 状态适配器支持透传 `project_id`，供 Sheet 按项目拉取 job 列表。

## 7. 安全要求

1. job 列表与看板数据均经 `get_current_tenant`：必须是该租户 active 成员、租户 active；跨租户请求被拒。
2. 入口面向租户用户；不得借此引入基于平台身份的越权写操作，平台只读视角维持既有边界。
3. 前端注入的 `tenant_key`/`project_id` 仅用于导航与请求参数，后端仍以服务端授权与租户过滤为准（不以前端参数作为授权依据）。
4. 不在响应或日志输出敏感凭据；本功能不涉及密码、token 或邮件。

## 8. 验收标准

- 租户管理员在项目详情页可见「进入看板」按钮，点击列出该项目的 job 记录。
- 选择某条 job 后跳转到 `/dashboard/{tenantKey}/{jobId}?brand={brand}`，看板展示对应 job、品牌数据。
- `GET /api/v1/query-jobs/status?project_id=` 仅返回该项目的 job；不传 `project_id` 时行为与改动前一致。
- 跨租户调用（非该租户成员）被 `get_current_tenant` 拒绝。
- 项目无 job 时展示空状态文案，不报错、不跳转。
- 平台只读视角下不破坏既有只读边界。
- 后端 `project_id` 过滤与前端入口、Sheet、导航、空状态有自动化测试覆盖。
- `ruff check api`、后端 pytest、前端测试、`npm --prefix web run build`、`python scripts/validate_agents_docs.py --level ERROR` 全部通过。
