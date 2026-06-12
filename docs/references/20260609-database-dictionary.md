# 数据库表结构与字段字典

> 日期：2026-06-09
>
> 适用范围：当前 `api/database/schema.sql` 中的 MySQL 主 schema；`api/database/schema_sqlite.sql` 为测试镜像，字段语义应保持一致。
>
> 说明：本文面向人阅读，解释表和字段的业务含义。最终可执行结构以 `api/database/schema.sql`、`api/database/schema_auth.sql`、`api/database/schema_business.sql` 和 `api/database/migrations/` 为准。

## 1. 总览

Brand Dashboard 当前采用共享数据库、共享 schema、多租户字段隔离。所有租户业务数据必须带 `tenant_key`；用户与租户成员关系通过 `tenants`、`users`、`user_tenants` 表表达。

业务主线已经从旧的 `tenant_key + job_id` 批次看板，迁移到以 `monitoring_projects` 为核心的长期品牌监测项目：

```text
tenant
  -> monitoring_projects
  -> project_brands / prompt_sets / prompt_items
  -> collection_jobs / collection_tasks / collection_attempts
  -> analysis_runs
  -> qa_brand_state / qa_reference
  -> alert_rules / alert_events / generated_reports
```

兼容期仍保留旧表：

```text
llm_query_jobs
llm_conversations
llm_conversation_references
qa_brand_state
qa_reference
```

其中 `llm_query_jobs.project_id`、`collection_jobs.source_job_id`、`qa_brand_state.analysis_run_id`、`qa_reference.analysis_run_id` 是新旧模型之间的过渡桥接字段。

## 2. 通用字段约定

| 字段 | 通用含义 |
|------|----------|
| `id` | 数据库内部自增主键，只用于本库内部定位，不作为跨系统业务 ID。 |
| `tenant_key` | 租户隔离键。业务查询必须显式过滤该字段。 |
| `*_id` | 对外或跨表使用的稳定业务 ID，例如 `project_id`、`collection_job_id`、`analysis_run_id`。 |
| `created_at` | 行创建时间。 |
| `updated_at` | 行最近更新时间，MySQL 中通常通过 `ON UPDATE CURRENT_TIMESTAMP` 自动维护。 |
| `status` | 业务状态字段。不同表的枚举不同，具体见各表说明。 |
| JSON 字段 | MySQL 使用 `json` 类型；SQLite 测试 schema 中通常以文本保存等价结构。 |
| 空字符串维度 | `alert_rules`、`alert_events` 中的 `brand_id`、`platform`、`keyword` 使用空字符串表示“全量/不限该维度”。 |

## 3. 认证与租户表

### 3.1 `tenants`

租户主表，表示一个客户组织。所有租户业务数据最终都归属到某个 `tenant_key`。

| 字段 | 说明 |
|------|------|
| `id` | 租户内部自增主键。 |
| `tenant_key` | 租户稳定字符串标识，用于路由、API header、Repository 查询和业务表外键。 |
| `tenant_name` | 租户显示名称。当前要求唯一。 |
| `subdomain` | 租户子域名，可为空，非空时唯一。 |
| `company_legal_name` | 企业法定名称。 |
| `company_type` | 企业类型。 |
| `registration_no` | 企业注册号或统一社会信用代码。 |
| `industry` | 租户所属行业。 |
| `contact_name` | 租户联系人姓名。 |
| `contact_email` | 租户联系人邮箱。 |
| `contact_phone` | 租户联系人电话。 |
| `status` | 租户状态：`active`、`inactive`、`suspended`。 |
| `plan_type` | 订阅计划类型。 |
| `max_users` | 当前计划允许的最大用户数，默认 10。 |
| `billing_cycle` | 计费周期，例如 `monthly`、`yearly`。 |
| `contract_start_date` | 合同开始日期。 |
| `contract_end_date` | 合同结束日期。 |
| `created_by` | 创建该租户的平台操作员 `user_key`。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `tenant_key` 唯一，`tenant_name` 唯一，`subdomain` 非空时唯一。 |
| 索引 | `idx_tenant_key`、`idx_subdomain` 支持租户解析。 |

### 3.2 `users`

用户账号主表，保存登录身份和基础资料。

| 字段 | 说明 |
|------|------|
| `id` | 用户内部自增主键。 |
| `user_key` | 用户全局稳定字符串 ID，例如 UUID/ULID。 |
| `email` | 登录邮箱，唯一。 |
| `password_hash` | 密码哈希。 |
| `first_name` | 名。 |
| `last_name` | 姓。 |
| `phone_number` | 手机号。 |
| `is_verified` | 邮箱或账号是否已验证。 |
| `status` | 用户状态：`pending_activation`、`active`、`inactive`、`suspended`。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `user_key` 唯一，`email` 唯一。 |
| 安全 | API 不应返回 `password_hash`。 |

### 3.3 `user_tenants`

用户与租户的多对多成员关系表。一个用户可属于多个租户，并在不同租户中拥有不同角色。

| 字段 | 说明 |
|------|------|
| `user_id` | 关联 `users.id`。 |
| `tenant_id` | 关联 `tenants.id`。 |
| `role` | 租户内角色，例如 `admin`、`member`、`viewer`。 |
| `status` | 成员关系状态：`active`、`inactive`。 |
| `created_at` | 成员关系创建时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 主键 | `(user_id, tenant_id)`，同一用户在同一租户只保留一条成员关系。 |
| 外键 | `user_id -> users.id`，`tenant_id -> tenants.id`，均级联删除。 |
| 索引 | `idx_tenant_user` 支持按租户列出成员。 |

### 3.4 `tenant_configs`

租户 UI/品牌配置表，目前保存轻量的租户展示配置。

| 字段 | 说明 |
|------|------|
| `tenant_id` | 关联 `tenants.id`，同时作为主键。 |
| `theme_color` | 租户主题色，默认 `#3498db`。 |
| `logo_url` | 租户 Logo 地址。 |
| `custom_domain` | 自定义访问域名。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 外键 | `tenant_id -> tenants.id`，租户删除时级联删除配置。 |

### 3.5 `invitation_codes`

租户邀请码表，用于邀请用户加入租户。

| 字段 | 说明 |
|------|------|
| `id` | 邀请码内部自增主键。 |
| `tenant_id` | 所属租户 `tenants.id`。 |
| `code` | 邀请码文本，当前设计为 6 位，唯一。 |
| `status` | 邀请码状态：`active`、`inactive`、`expired`。 |
| `max_uses` | 最大使用次数，`NULL` 表示无限制。 |
| `usage_count` | 已使用次数。 |
| `expires_at` | 过期时间。 |
| `created_by` | 创建人 `users.id`。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `code` 唯一。 |
| 外键 | `tenant_id -> tenants.id`，租户删除时级联删除邀请码。 |
| 索引 | `tenant_id`、`code`、`status` 支持校验和管理。 |

## 4. 项目配置表

### 4.1 `monitoring_projects`

监测项目主表。它是新架构的核心业务对象，表示租户内一个长期品牌监测项目。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `project_id` | 项目稳定业务 ID，对 API、采集、分析、指标等链路开放。 |
| `name` | 项目名称。 |
| `industry` | 项目所属行业。 |
| `category` | 项目所属品类或赛道。 |
| `status` | 项目状态：`draft`、`active`、`paused`、`archived`。 |
| `created_by` | 创建人 `users.id`。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, project_id)` 是稳定业务键。 |
| 外键 | `tenant_key -> tenants.tenant_key`，租户删除时级联删除项目。 |
| 索引 | `(tenant_key, status)` 支持项目列表状态筛选；`(tenant_key, category)` 支持品类筛选。 |

生命周期：

- 删除项目会级联删除项目品牌、问题集和问题项配置。
- 采集批次、分析运行、分析事实、告警和报告绑定项目，但历史链路不应轻易物理删除。

### 4.2 `project_brands`

项目品牌配置表，保存目标品牌、竞品和仅观察品牌。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `project_id` | 所属监测项目。 |
| `brand_id` | 项目内稳定品牌 ID。 |
| `brand_name` | 品牌标准展示名。 |
| `role` | 品牌角色：`target` 目标品牌，`competitor` 竞品，`watch_only` 仅观察。 |
| `aliases` | 品牌别名 JSON，例如英文名、简称、常见写法。 |
| `status` | 品牌配置状态：`active`、`inactive`。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, project_id, brand_id, role)` 防止同一项目同一品牌角色重复配置。 |
| 外键 | `(tenant_key, project_id) -> monitoring_projects`，项目删除时级联删除品牌配置。 |
| 索引 | `(tenant_key, project_id, role)` 支持按项目角色加载品牌；`(tenant_key, brand_id)` 支持按品牌排查。 |

### 4.3 `prompt_sets`

项目问题集版本表。一个项目可以有多版问题集，用于控制采集问题集合的版本。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `project_id` | 所属监测项目。 |
| `prompt_set_id` | 问题集稳定业务 ID。 |
| `version` | 项目内问题集版本号。 |
| `name` | 问题集名称。 |
| `status` | 问题集状态：`draft`、`active`、`archived`。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, prompt_set_id)` 标识问题集；`(tenant_key, project_id, version)` 保证项目内版本号唯一。 |
| 外键 | `(tenant_key, project_id) -> monitoring_projects`，项目删除时级联删除问题集。 |
| 索引 | `(tenant_key, project_id, status)` 支持项目详情加载当前问题集。 |

### 4.4 `prompt_items`

问题项表，保存某个问题集下的单条消费者问题。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `prompt_set_id` | 所属问题集。 |
| `prompt_item_id` | 问题项稳定业务 ID。 |
| `keyword` | 问题关键词或主题。 |
| `query_content` | 完整提问文本。 |
| `status` | 问题项状态：`active`、`inactive`。 |
| `sort_order` | 展示或采集排序。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, prompt_set_id, prompt_item_id)` 保证同一问题集内问题项幂等。 |
| 外键 | `(tenant_key, prompt_set_id) -> prompt_sets`，问题集删除时级联删除问题项。 |
| 索引 | `(tenant_key, prompt_set_id, status)` 支持加载 active 问题；`(tenant_key, keyword)` 支持关键词筛选。 |

## 5. 原始采集兼容表

### 5.1 `llm_conversations`

旧原始回答主表，保存 AI 平台对某个问题的一次回答原文。兼容期仍作为分析插件的原始输入来源。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `job_id` | 旧任务批次 ID。一个 `job_id` 对应一批问答。 |
| `conversation_id` | 单条对话稳定 ID，通常来自文件名或采集产物。 |
| `platform` | AI 平台，例如 `deepseek`、`doubao`、`qianwen`、`kimi`、`yuanbao`。 |
| `brand` | 采集时关联的目标品牌，可为空。 |
| `category` | 品类。 |
| `keyword` | 生成问题的关键词。 |
| `query_content` | 用户提问内容。 |
| `answer_content` | AI 回答原文。 |
| `generated_date` | 回答生成业务日期。 |
| `extracted_at` | 原始文件生成时间，表示采集产物时间，不应随更新变化。 |
| `created_at` | 入库时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, conversation_id)`。 |
| 外键 | `tenant_key -> tenants.tenant_key`，租户删除时级联删除。 |
| 索引 | `tenant_key + job_id`、`tenant_key + generated_date`、平台、品牌、品类、关键词索引支持 dashboard 兼容查询。 |

### 5.2 `llm_conversation_references`

旧原始引用表，保存回答中出现的引用链接。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `job_id` | 旧任务批次 ID。 |
| `conversation_id` | 所属回答 ID。 |
| `platform` | AI 平台。 |
| `brand` | 采集时关联的目标品牌，可为空。 |
| `category` | 品类。 |
| `keyword` | 问题关键词。 |
| `query_content` | 用户提问内容。 |
| `url` | 引用链接原始 URL。 |
| `domain` | 从 URL 提取的域名。 |
| `cite_index` | 引用在回答中的出现序号，从 1 开始。 |
| `site_name` | 站点名称或页面标题。 |
| `content_type` | 内容类型，例如 `news`、`tech_review`、`gov_report`。 |
| `generated_date` | 回答生成业务日期。 |
| `created_at` | 入库时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, conversation_id, url(191))`，兼容期仍使用 URL 前缀唯一键。 |
| 外键 | `(tenant_key, conversation_id) -> llm_conversations`，回答删除时级联删除引用。 |
| 索引 | 租户批次、日期、平台、品牌、品类、关键词、域名、内容类型。 |

兼容说明：

- 当前未引入 `url_hash`，历史重复和跨作用域碰撞风险记录在领域数据参考文档中。
- 目标模型应迁移为 answer snapshot/reference 模型，并用规范化 URL hash 表达唯一性。

## 6. 执行器与采集生命周期表

### 6.1 `executors`

执行器注册表，保存可领取采集任务的外部 worker 身份。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `executor_id` | 执行器稳定字符串 ID。 |
| `name` | 执行器名称。 |
| `type` | 执行器类型。 |
| `status` | 执行器状态，当前常用值为 `active`。 |
| `ip_address` | 预设执行器 IP，用于注册或身份校验。 |
| `api_key` | 执行器身份密钥。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `executor_id` 唯一。 |
| 下游引用 | `llm_query_jobs.executor_id`、`collection_tasks.lease_owner`、`collection_attempts.executor_id` 可引用该表。 |

### 6.2 `collection_jobs`

采集批次表。一次 collection job 表示某个项目在某个窗口、使用某个问题集发起的一批采集。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `collection_job_id` | 采集批次稳定业务 ID。 |
| `project_id` | 所属监测项目。 |
| `prompt_set_id` | 本批次使用的问题集，可为空。 |
| `source_job_id` | 兼容期桥接字段，指向旧 `llm_query_jobs.job_id`。 |
| `status` | 批次状态：`pending`、`running`、`succeeded`、`failed`、`expired`、`cancelled`。 |
| `window_start` | 采集窗口开始时间。 |
| `window_end` | 采集窗口结束时间。 |
| `expected_task_count` | 预期任务数。 |
| `succeeded_task_count` | 成功任务数。 |
| `failed_task_count` | 失败任务数。 |
| `created_by` | 创建人 `users.id`。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, collection_job_id)`。 |
| 外键 | `(tenant_key, project_id) -> monitoring_projects`；`(tenant_key, prompt_set_id) -> prompt_sets`；`tenant_key -> tenants`。 |
| 索引 | 项目状态、问题集、旧 `source_job_id`。 |

生命周期：

- 删除采集批次会级联删除 `collection_tasks` 和 `collection_attempts`。
- 删除项目不应轻易级联删除历史采集批次，避免破坏分析和审计链路。

### 6.3 `collection_tasks`

采集任务表。它是执行器可领取的最小任务单元。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `collection_task_id` | 采集任务稳定业务 ID。 |
| `collection_job_id` | 所属采集批次。 |
| `project_id` | 所属监测项目。 |
| `prompt_set_id` | 所属问题集。 |
| `prompt_item_id` | 所属问题项。 |
| `platform` | 目标 AI 平台。 |
| `query_content` | 本任务要发送给 AI 平台的完整问题文本。 |
| `run_index` | 同一批次内的运行序号，用于多次重复采集。 |
| `status` | 任务状态：`pending`、`reserved`、`running`、`succeeded`、`failed`、`expired`、`cancelled`。 |
| `lease_owner` | 当前持有租约的执行器 `executor_id`。 |
| `lease_until` | 当前租约过期时间。 |
| `reserved_at` | 被领取时间。 |
| `started_at` | 执行开始时间。 |
| `finished_at` | 执行结束时间。 |
| `attempt_count` | 已尝试次数。 |
| `max_attempts` | 最大尝试次数，默认 3。 |
| `last_error_code` | 最近一次失败错误码。 |
| `last_error_message` | 最近一次失败错误信息。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, collection_task_id)`。 |
| 外键 | 所属批次、项目、问题项均使用带 `tenant_key` 的复合外键；`lease_owner -> executors.executor_id`，执行器删除时置空。 |
| 索引 | `idx_collection_tasks_fetch` 支持领取候选查询；批次状态、项目状态、问题项、租约持有者索引用于排障和队列页。 |

### 6.4 `collection_attempts`

采集执行尝试表。一个任务可以因为失败、超时或重试产生多次 attempt。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `attempt_id` | 执行尝试稳定业务 ID。 |
| `collection_task_id` | 所属采集任务。 |
| `executor_id` | 执行该 attempt 的执行器。 |
| `status` | attempt 状态：`running`、`succeeded`、`failed`、`timeout`、`cancelled`。 |
| `started_at` | 开始时间。 |
| `finished_at` | 结束时间。 |
| `error_code` | 错误码。 |
| `error_message` | 错误信息。 |
| `raw_response_id` | 原始回答或外部采集产物 ID。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, attempt_id)`。 |
| 外键 | `(tenant_key, collection_task_id) -> collection_tasks`，任务删除时级联删除 attempt；`executor_id -> executors.executor_id`，执行器删除时置空。 |
| 索引 | 任务、执行器状态、执行器外键索引支持排障和健康度查询。 |

## 7. 分析与事实指标表

### 7.1 `analysis_runs`

分析运行表，记录一次分析任务的状态、输入范围、插件版本和错误信息。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `analysis_run_id` | 分析运行稳定业务 ID。 |
| `project_id` | 所属监测项目。 |
| `collection_job_id` | 本次分析消费的采集批次。 |
| `status` | 分析状态：`pending`、`running`、`succeeded`、`failed`、`stale`。 |
| `plugin_versions` | 本次使用的分析插件版本 JSON。 |
| `model_config_hash` | 模型与分析配置摘要，用于可复现和新鲜度判断。 |
| `input_watermark` | 输入数据水位，例如采集完成时间或输入版本。 |
| `started_at` | 分析开始时间。 |
| `finished_at` | 分析结束时间。 |
| `stale_at` | 该 run 被判定为过期的时间。 |
| `error_code` | 失败或过期错误码。 |
| `error_message` | 失败或过期原因。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, analysis_run_id)`。 |
| 外键 | `(tenant_key, project_id) -> monitoring_projects`；`(tenant_key, collection_job_id) -> collection_jobs`；`tenant_key -> tenants`。 |
| 索引 | 项目状态、采集批次、状态更新时间支持查询和 retry。 |

### 7.2 事实聚合指标（无独立表）

当前分支不再保留独立指标快照表。`brand_metrics_v1` 指标口径由 `qa_brand_state` 和 `qa_reference` 在 Repository 层聚合：

| 指标 | 来源 | 说明 |
|------|------|------|
| `mention_rate` | `qa_brand_state.is_mentioned` | 提及该品牌的去重回答数 / 该维度去重回答数。 |
| `first_mention_rate` | `qa_brand_state.is_first_mentioned` | 首位提及该品牌的去重回答数 / 该维度去重回答数。 |
| `top3_mention_rate` | `qa_brand_state.is_top3_mentioned` | Top3 提及该品牌的去重回答数 / 该维度去重回答数。 |
| `sentiment_negative_ratio` | `qa_brand_state.sentiment_status` | 负面情绪去重回答数 / 有情绪标签的去重回答数。 |
| `reference_rate` | `qa_reference.conversation_id` | 带引用的去重回答数 / 该维度去重回答数。 |

实现位置：`api/v1/repositories/fact_metrics.py`。报告通过 `generated_reports.metrics_json` 保存生成时结果，告警通过 `alert_events.current_value` / `previous_value` 保存触发时结果。

## 8. 告警与报告表

### 8.1 `alert_rules`

告警规则配置表。规则定义某个项目中需要监控的指标、维度和阈值。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `alert_rule_id` | 告警规则稳定业务 ID。 |
| `project_id` | 所属监测项目。 |
| `name` | 规则显示名称。 |
| `rule_type` | 规则类型，例如 `metric_drop`、`metric_rise`、`metric_change`。 |
| `metric_name` | 被监控的指标名。 |
| `metric_definition_version` | 指标口径版本，默认 `brand_metrics_v1`。 |
| `brand_id` | 品牌维度，空字符串表示不限品牌。 |
| `brand_name` | 创建规则时的品牌显示名。 |
| `platform` | 平台维度，空字符串表示不限平台。 |
| `keyword` | 关键词维度，空字符串表示不限关键词。 |
| `threshold_value` | 触发阈值，表示绝对变化量阈值。 |
| `severity` | 告警级别，例如 `info`、`warning`、`critical`。 |
| `status` | 规则状态，例如 `active`、`disabled`。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, alert_rule_id)`；规则身份唯一键按项目、类型、指标、口径和维度去重。 |
| 外键 | `(tenant_key, project_id) -> monitoring_projects`；`tenant_key -> tenants`。 |
| 索引 | 项目状态、项目指标规则类型索引。 |

### 8.2 `alert_events`

告警事件表。系统评估告警规则后，满足阈值的变化会形成可查询、可去重的事件。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `alert_event_id` | 告警事件稳定业务 ID。 |
| `alert_rule_id` | 触发该事件的规则 ID。 |
| `project_id` | 所属监测项目。 |
| `analysis_run_id` | 当前指标所属分析运行。 |
| `collection_job_id` | 当前指标所属采集批次。 |
| `metric_date` | 当前指标业务日期。 |
| `metric_name` | 被监控的指标名。 |
| `metric_definition_version` | 指标口径版本。 |
| `brand_id` | 品牌维度。 |
| `brand_name` | 品牌显示名。 |
| `platform` | 平台维度。 |
| `keyword` | 关键词维度。 |
| `dimension_hash` | 维度 hash。 |
| `previous_metric_date` | 对比基线的指标日期。 |
| `previous_value` | 对比基线指标值。 |
| `current_value` | 当前指标值。 |
| `delta_value` | 当前值与基线值的绝对差。 |
| `threshold_value` | 触发时使用的阈值。 |
| `severity` | 告警级别。 |
| `event_status` | 事件处理状态：`open`、`acknowledged`、`resolved`。 |
| `title` | 告警标题。 |
| `message` | 告警说明。 |
| `triggered_at` | 触发时间。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, alert_event_id)`；`uk_alert_events_dedupe` 防止同一规则、run、日期和维度重复生成事件。 |
| 外键 | 项目、规则、分析运行均使用带 `tenant_key` 的复合外键。 |
| 索引 | 项目事件状态、分析运行、规则索引支持项目页和报告读取。 |

### 8.3 `generated_reports`

报告结果表。保存一次项目报告生成后的 JSON 快照，后续 PDF/CSV 导出应基于该稳定结果扩展。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `report_id` | 报告稳定业务 ID。 |
| `project_id` | 所属监测项目。 |
| `report_type` | 报告类型，默认 `project_summary`。 |
| `title` | 报告标题。 |
| `timeframe` | 报告时间窗口类型，默认 `custom`。 |
| `start_date` | 报告窗口开始日期。 |
| `end_date` | 报告窗口结束日期。 |
| `status` | 报告状态，默认 `generated`。 |
| `summary_json` | 报告摘要快照 JSON。 |
| `metrics_json` | 核心指标结果 JSON。 |
| `alerts_json` | 告警事件摘要 JSON，可为空。 |
| `generated_by` | 生成报告的用户 `users.id`。 |
| `generated_at` | 报告生成时间。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, report_id)`。 |
| 外键 | `(tenant_key, project_id) -> monitoring_projects`；`tenant_key -> tenants`。 |
| 索引 | 项目生成时间、项目日期窗口索引支持报告列表和历史查询。 |

## 9. Legacy 任务与分析结果表

### 9.1 `llm_query_jobs`

旧查询任务表。兼容期仍用于旧执行器 fetch/report、旧任务状态页和旧 dashboard 入口。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `tenant_key` | 租户隔离键。 |
| `job_id` | 旧作业/批次 ID。 |
| `project_id` | 兼容期桥接字段，指向新监测项目，可为空。 |
| `category` | 品类。 |
| `brand` | 目标品牌，可为空。 |
| `competitor` | 竞品品牌 JSON。 |
| `keyword` | 核心关键词。 |
| `query_content` | 具体问题文本。 |
| `query_status` | 旧任务状态：`0` 未生效，`1` 生效中，`2` 已完成，`3` 已失效。 |
| `executor_id` | 分配或领取该任务的执行器。 |
| `total_runs` | 总执行次数，默认 15。 |
| `executed_runs` | 已发生 attempt 数，包含成功和失败。 |
| `last_executed_date` | 最近一次执行日期，用于跨日重置和每日多次领取控制。 |
| `effective_from` | 生效开始时间。 |
| `effective_to` | 生效结束时间，`NULL` 表示未结束。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |
| `is_deleted` | 软删除标识：`0` 未删除，`1` 已删除。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 外键 | `tenant_key -> tenants.tenant_key`；`executor_id -> executors.executor_id`，执行器删除时置空。 |
| 索引 | 租户批次、项目桥接、品牌、品类、关键词、创建时间、执行器领取、跨日重置。 |

兼容说明：

- `project_id` 不加外键，避免历史任务和项目删除策略互相阻塞。
- 长期目标是由 `collection_jobs`、`collection_tasks`、`collection_attempts` 接管采集生命周期。

### 9.2 `qa_brand_state`

品牌问答事实表，记录每个回答中某个品牌是否被提及、是否首位/Top3、情绪等。当前用于 dashboard、情感分析、报告、告警和数据质量的指标聚合输入。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `job_id` | 旧作业/批次 ID。 |
| `tenant_key` | 租户隔离键。 |
| `analysis_run_id` | 生成该事实的分析运行，可为空以兼容历史事实。 |
| `date` | 事实业务日期。 |
| `conversation_id` | 所属回答 ID。 |
| `brand` | 被判断的品牌名称。 |
| `category` | 品类。 |
| `platform` | AI 平台。 |
| `keyword` | 问题关键词。 |
| `is_mentioned` | 是否提及该品牌：`0` 否，`1` 是。 |
| `is_first_mentioned` | 是否首位提及。 |
| `is_top3_mentioned` | 是否前三提及。 |
| `sentiment_status` | 情感状态，例如 `positive`、`negative`、`neutral`、`unknown`。 |
| `brands_found` | 回答中识别到的全部品牌 JSON。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `uk_tenant_job_conv_brand` 使用 `(tenant_key(191), job_id(191), conversation_id(191), brand)`，支持分析插件重跑 upsert。 |
| 外键 | `tenant_key -> tenants.tenant_key`；`(tenant_key, analysis_run_id) -> analysis_runs`。 |
| 索引 | 日期、品牌、平台、情感、回答 ID、分析运行索引支持 dashboard 和事实指标聚合。 |

兼容说明：

- `analysis_run_id` 可为空，是为了不破坏历史事实行。
- 唯一键使用前缀字段，是为了兼容 MySQL `utf8mb4` 组合索引长度限制。

### 9.3 `qa_reference`

分析后的引用事实表，记录回答引用链接是否为发稿链接及其分类结果。

| 字段 | 说明 |
|------|------|
| `id` | 内部自增主键。 |
| `job_id` | 旧作业/批次 ID。 |
| `tenant_key` | 租户隔离键。 |
| `analysis_run_id` | 生成该事实的分析运行，可为空以兼容历史事实。 |
| `date` | 事实业务日期。 |
| `conversation_id` | 所属回答 ID。 |
| `platform` | AI 平台。 |
| `brand` | 品牌名称，可为空。 |
| `category` | 品类。 |
| `keyword` | 问题关键词。 |
| `query_content` | 用户提问内容。 |
| `url` | 引用链接 URL。 |
| `is_published_link` | 是否为发稿链接：`0` 否，`1` 是。 |
| `domain` | URL 域名。 |
| `content_type` | 内容类型，例如 `news`、`tech_review`、`gov_report`。 |
| `created_at` | 创建时间。 |
| `updated_at` | 更新时间。 |

关键约束：

| 类型 | 说明 |
|------|------|
| 唯一性 | `(tenant_key, conversation_id, url(191))`，兼容期仍使用旧唯一键。 |
| 外键 | `tenant_key -> tenants.tenant_key`；`(tenant_key, analysis_run_id) -> analysis_runs`。 |
| 索引 | 平台、品牌、品类、关键词、域名、内容类型、是否发稿链接、分析运行。 |

兼容说明：

- 当前唯一键无法区分同一回答下不同品牌维度的同 URL 分类事实，目标模型应引入 `url_hash` 和更细粒度业务键。

## 10. 数据初始化与事件

`schema.sql` 还包含一个 MySQL event：

| 名称 | 说明 |
|------|------|
| `ev_reset_query_jobs_daily` | 每日重置已跑满 `total_runs` 且仍在有效期内的旧 `llm_query_jobs.executed_runs`，用于兼容旧执行器按日重复领取任务。 |

该事件不是表结构，但会影响 `llm_query_jobs` 的运行语义。部署环境需要确认 MySQL event scheduler 已开启。

## 11. 表关系速查

| 上游表 | 下游表 | 关系 |
|--------|--------|------|
| `tenants` | 几乎所有业务表 | 通过 `tenant_key` 或 `tenant_id` 隔离租户数据。 |
| `users` | `user_tenants` | 用户加入多个租户。 |
| `tenants` | `user_tenants` | 租户拥有多个成员。 |
| `tenants` | `tenant_configs`、`invitation_codes` | 租户配置和邀请码。 |
| `monitoring_projects` | `project_brands`、`prompt_sets` | 项目下配置品牌和问题集。 |
| `prompt_sets` | `prompt_items` | 问题集下挂问题项。 |
| `monitoring_projects` | `collection_jobs` | 项目生成采集批次。 |
| `collection_jobs` | `collection_tasks` | 批次拆成可领取任务。 |
| `collection_tasks` | `collection_attempts` | 任务产生一次或多次执行尝试。 |
| `collection_jobs` | `analysis_runs` | 成功采集批次进入分析运行。 |
| `analysis_runs` | `qa_brand_state`、`qa_reference` | 成功分析运行写入可追溯事实。 |
| `qa_brand_state`、`qa_reference` | `alert_events` | 告警评估读取事实聚合指标并生成事件。 |
| `alert_rules` | `alert_events` | 规则触发事件。 |
| `monitoring_projects` | `generated_reports` | 项目生成报告结果。 |
| `llm_query_jobs` | `llm_conversations`、`llm_conversation_references` | 旧任务批次产生原始问答和引用。 |
| `analysis_runs` | `qa_brand_state`、`qa_reference` | 兼容期分析事实写入血缘字段。 |

## 12. 维护建议

- 新增或修改表字段时，同步更新 `api/database/schema.sql`、MySQL migration、SQLite 测试 schema 和本文。
- 新增业务表时优先使用 `(tenant_key, stable_business_id)` 作为跨表业务键，避免只依赖自增 `id`。
- 新增查询必须确认 Repository 层显式过滤 `tenant_key`。
- 新增 JSON 字段时，文档中应说明 JSON 结构的最小稳定字段。
- 修改 legacy 表唯一键前，先运行重复数据检查并记录迁移策略。
