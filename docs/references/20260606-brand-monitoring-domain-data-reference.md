# 品牌监测领域模型与数据生命周期参考

> 状态：规划中
> 日期：2026-06-06
> 关联规格：`docs/product-specs/20260606-brand-monitoring-system-refactor.md`
> 关联设计：`docs/design-docs/20260606-brand-monitoring-target-architecture.md`

## 1. 术语表

| 术语 | 定义 |
|------|------|
| Tenant | 客户组织，所有业务数据必须归属某个 `tenant_key`。 |
| Monitoring Project | 租户内一个长期品牌监测项目。 |
| Target Brand | 项目重点监测的目标品牌。 |
| Competitor Brand | 项目中用于对比的竞品品牌。 |
| Prompt Set | 某一版消费者问题集合。 |
| Prompt Item | 单条消费者问题。 |
| Collection Job | 一次采集批次，由项目、问题集版本、平台和时间窗口生成。 |
| Collection Task | 可被执行器领取的最小采集任务。 |
| Collection Attempt | 执行器对某个任务的一次执行尝试。 |
| Answer Snapshot | AI 平台对某个问题的一次回答原文。 |
| Answer Reference | 回答中的引用链接。 |
| Analysis Run | 对一批原始数据执行分析的运行记录。 |
| Brand Mention Fact | 某回答中某品牌的提及、首位、Top3 和情绪事实。 |
| Reference Classification | 某引用链接的内容类型、是否发稿链接和来源质量事实。 |
| Metric Snapshot | 面向 dashboard 和报告的聚合指标快照。 |

## 2. 目标实体参考

### 2.1 MonitoringProject

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `id` | bigint | 内部主键。 |
| `project_id` | varchar | 对外稳定 ID。 |
| `tenant_key` | varchar | 租户隔离字段。 |
| `name` | varchar | 项目名称。 |
| `industry` | varchar | 行业。 |
| `category` | varchar | 品类。 |
| `status` | enum | `draft`、`active`、`paused`、`archived`。 |
| `created_by` | bigint | 创建人。 |
| `created_at` | timestamp | 创建时间。 |
| `updated_at` | timestamp | 更新时间。 |

### 2.2 ProjectBrand

| 字段 | 类型建议 | 说明 |
|------|----------|------|
| `project_id` | varchar | 所属项目。 |
| `brand_id` | varchar | 品牌 ID。 |
| `brand_name` | varchar | 标准品牌名。 |
| `role` | enum | `target`、`competitor`、`watch_only`。 |
| `aliases` | json | 别名、英文名、简称。 |
| `status` | enum | `active`、`inactive`。 |

### 2.3 PromptSet / PromptItem

| 实体 | 关键字段 | 说明 |
|------|----------|------|
| `prompt_sets` | `prompt_set_id`、`project_id`、`version`、`status` | 问题集版本。 |
| `prompt_items` | `prompt_item_id`、`prompt_set_id`、`keyword`、`query_content`、`status` | 单条消费者问题。 |

### 2.3.1 Phase 3.1 schema 落地说明

Phase 3.1 已在 MySQL/SQLite schema 中新增 `monitoring_projects`、`project_brands`、`prompt_sets`、`prompt_items` 四张配置表，并提供 MySQL 迁移脚本：

```bash
mysql -u root -p geo < api/database/migrations/20260607_add_monitoring_project_model.mysql.sql
```

落地规则：

| 范围 | 规则 |
|------|------|
| 租户隔离 | 四张表均保留 `tenant_key`；跨表关系使用带 `tenant_key` 的复合外键。 |
| 项目唯一性 | `monitoring_projects` 使用 `(tenant_key, project_id)` 作为稳定业务键。 |
| 品牌配置 | `project_brands` 使用 `(tenant_key, project_id, brand_id, role)` 约束同一项目中的品牌角色配置。 |
| 问题集版本 | `prompt_sets` 使用 `(tenant_key, prompt_set_id)` 标识问题集，并用 `(tenant_key, project_id, version)` 约束项目内版本号。 |
| 问题项 | `prompt_items` 使用 `(tenant_key, prompt_set_id, prompt_item_id)` 保证同一问题集内问题项幂等。 |
| 生命周期 | 删除 `monitoring_projects` 时级联删除项目品牌、问题集和问题项配置；既有采集明细和分析事实暂不级联，等待 Phase 4/5 引入 collection/analysis 生命周期后再绑定。 |

### 2.4 CollectionJob / CollectionTask / CollectionAttempt

| 实体 | 关键字段 | 说明 |
|------|----------|------|
| `collection_jobs` | `collection_job_id`、`project_id`、`prompt_set_id`、`status`、`window_start`、`window_end` | 一次采集批次。 |
| `collection_tasks` | `collection_task_id`、`collection_job_id`、`platform`、`prompt_item_id`、`status`、`lease_until` | 可领取任务。 |
| `collection_attempts` | `attempt_id`、`collection_task_id`、`executor_id`、`status`、`started_at`、`finished_at`、`error_message` | 单次执行尝试。 |

### 2.4.1 Phase 4.1 schema 落地说明

Phase 4.1 已在 MySQL/SQLite schema 中新增 `collection_jobs`、`collection_tasks`、`collection_attempts` 三张采集生命周期表，并提供 MySQL 迁移脚本：

```bash
mysql -u root -p geo < api/database/migrations/20260607_add_collection_lifecycle_model.mysql.sql
```

落地规则：

| 范围 | 规则 |
|------|------|
| 租户隔离 | 三张表均保留 `tenant_key`；跨表关系使用带 `tenant_key` 的复合唯一键和复合外键，避免跨租户任务或 attempt 误挂接。 |
| 采集批次 | `collection_jobs` 使用 `(tenant_key, collection_job_id)` 作为稳定业务键，并通过 `(tenant_key, project_id)` 绑定监测项目。`source_job_id` 仅用于兼容期追溯旧 `llm_query_jobs.job_id`。 |
| 任务领取 | `collection_tasks` 保留 `status`、`lease_owner`、`lease_until`、`reserved_at`、`started_at`、`finished_at`，并用 `idx_collection_tasks_fetch (tenant_key, status, lease_until, id)` 支持 Phase 4.2 的领取查询。 |
| 重试与失败 | `collection_tasks` 记录 `attempt_count`、`max_attempts`、`last_error_code`、`last_error_message`；`collection_attempts` 记录每次执行的 `executor_id`、`status`、`started_at`、`finished_at`、`error_code`、`error_message`。 |
| 生命周期 | 删除采集批次时级联删除任务和 attempt；删除项目不会级联删除采集批次，历史采集链路需要保留给分析、指标快照和审计追溯。 |
| 执行器关系 | `lease_owner` 和 `collection_attempts.executor_id` 均可在执行器删除时置空，避免历史 attempt 丢失。 |

本阶段只落 schema，不改旧 `/api/v1/query-jobs/fetch` 和 `/api/v1/query-jobs/report` 协议；Phase 4.2/4.3 再将领取和 attempt 上报映射到新模型。

### 2.4.2 Phase 4.2 领取协议落地说明

Phase 4.2 已新增执行器采集任务领取入口：

```text
GET /api/v1/collection-tasks/fetch?tenant_key={tenant_key}&collection_job_id={optional}&lease_seconds=300
```

请求要求：

| 参数 | 规则 |
|------|------|
| `executor_id` | 仍沿用执行器身份参数，并配合 `X-Executor-Key` 通过 `verify_executor` 校验。 |
| `tenant_key` | 必填；新领取协议不允许执行器不带租户边界做全局扫描。 |
| `collection_job_id` | 可选；传入时只在指定采集批次内领取任务。 |
| `lease_seconds` | 可选，默认 300 秒，当前限制为 1 到 3600 秒。 |

领取规则：

| 场景 | 结果 |
|------|------|
| `pending` 任务 | 可领取；领取后写入 `status='reserved'`、`lease_owner`、`lease_until`、`reserved_at`。 |
| `failed` 且 `attempt_count < max_attempts` | 可重新领取，为 Phase 4.3 失败重试预留。 |
| `reserved` 且 `lease_until` 未过期 | 不会被其他执行器领取。 |
| `reserved` 且 `lease_until` 已过期 | 可被重新领取，并覆盖 `lease_owner` 与新的 `lease_until`。 |
| 并发请求选中同一候选任务 | Repository 的条件更新会再次检查 `status` 和 `lease_until`，只有一个请求可以成功写入租约。 |

本阶段仍不修改旧 `/api/v1/query-jobs/fetch`，避免打断既有执行器客户端；旧 job 到新 collection task 的兼容映射需要等 Phase 4.3 attempt 上报模型一起收敛。

### 2.4.3 Phase 4.3 attempt start/complete 落地说明

Phase 4.3 已新增执行尝试生命周期入口：

```text
POST /api/v1/collection-attempts/{attempt_id}/start
POST /api/v1/collection-attempts/{attempt_id}/complete
```

`start` 请求体：

| 字段 | 规则 |
|------|------|
| `tenant_key` | 必填，必须与任务所属租户一致。 |
| `collection_task_id` | 必填，指向已被当前执行器领取的任务。 |

`complete` 请求体：

| 字段 | 规则 |
|------|------|
| `tenant_key` | 必填，必须与 attempt 所属租户一致。 |
| `status` | 必填，支持 `succeeded`、`failed`、`timeout`、`cancelled`。 |
| `error_code`、`error_message` | 失败、超时或取消时记录错误原因。 |
| `raw_response_id` | 成功时可记录原始回答或外部产物 ID。 |

状态推进：

| 场景 | 写入规则 |
|------|----------|
| start 成功 | 仅当任务为 `reserved`、`lease_owner` 等于当前执行器且 `lease_until` 未过期时创建 `collection_attempts`；任务状态改为 `running`，`attempt_count` 增加 1。 |
| complete succeeded | attempt 改为 `succeeded`，任务改为 `succeeded`，清空 `lease_owner` 和 `lease_until`，写入 `finished_at`。 |
| complete failed | attempt 改为 `failed`，任务改为 `failed`，记录 `last_error_code`/`last_error_message` 并释放 lease；若 `attempt_count < max_attempts`，Phase 4.2 fetch 可重新领取。 |
| complete timeout | attempt 改为 `timeout`，任务改为 `failed`，记录超时原因并释放 lease；达到 `max_attempts` 后不会再被 fetch 领取。 |
| 非 lease 持有者 start/complete | 返回 403，不创建或修改 attempt。 |

本阶段仍未把 `conversation/load` 绑定到 `attempt_id`；回答快照和 attempt 的强关联将在后续回答模型迁移阶段补齐。

### 2.4.4 Phase 4.4 平台采集健康度落地说明

Phase 4.4 已新增平台运营后台采集健康度入口：

```text
GET /api/v1/platform/collection-health?failedTaskLimit=20
```

权限与租户边界：

| 范围 | 规则 |
|------|------|
| 认证 | 必须携带 `Authorization: Bearer <access_token>`，且用户邮箱需要具备 `platform_admin` 角色。 |
| 租户头 | 平台 API 不发送也不读取 `X-Tenant-Key`；这是跨租户运营视角，不是租户成员视角。 |
| 普通用户 | 非平台管理员访问返回 403。 |
| 写入能力 | 该接口只读，不提供任务重试、取消、重新分配等操作。 |

返回数据分为三组：

| 数据组 | 说明 |
|--------|------|
| `summary` | 汇总执行器数量、启用/停用数量、pending/reserved/running/failed 任务数、可重试失败任务数和过期 lease 数。 |
| `executors` | 展示执行器基础信息、健康状态、活跃 lease 数、running attempt 数、失败 attempt 数和最近 attempt 时间。 |
| `queues` | 按 `tenant_key + project_id + collection_job_id` 汇总队列长度和各状态任务数。 |
| `failedTasks` | 展示最近失败任务、错误原因、尝试次数、是否仍可重试及其所属租户/项目/采集批次。 |

健康状态口径：

| 状态 | 计算规则 |
|------|----------|
| `inactive` | `executors.status` 不是 `active`。 |
| `error` | 执行器存在失败或超时 attempt。 |
| `active` | 执行器启用，且存在活跃 lease 或 running attempt。 |
| `idle` | 执行器启用，但当前没有活跃 lease 或 running attempt。 |

前端已新增 `/platform/executors` 页面，复用 `platformOptions(..., skipTenantHeader: true)` 调用该接口，确保平台后台请求不会把当前租户工作台的 `X-Tenant-Key` 误带到运营接口。

当前限制：系统尚无独立 heartbeat 或执行器运行事件表，因此“健康”是由任务租约和 attempt 状态推断得到，并不等价于真实在线心跳。后续若需要在线/离线秒级判断，应新增执行器心跳模型。

### 2.5 AnalysisRun / MetricSnapshot

| 实体 | 关键字段 | 说明 |
|------|----------|------|
| `analysis_runs` | `analysis_run_id`、`project_id`、`collection_job_id`、`status`、`plugin_versions`、`model_config_hash` | 分析运行记录。 |
| `metric_snapshots` | `snapshot_id`、`project_id`、`metric_date`、`brand_id`、`platform`、`keyword`、`metric_name`、`metric_value`、`metric_definition_version`、`analysis_run_id`、`coverage_rate` | dashboard 读模型。 |

### 2.5.1 Phase 5.1 analysis_runs 落地说明

本阶段先把分析运行纳入系统生命周期，但不调用 `analysis/` 插件，也不写入新的指标事实表。这样可以先固定“采集批次完成后如何生成、启动、完成和标记过期分析”的边界，避免后续插件接入时同时处理状态机、血缘和事实表幂等问题。

`analysis_runs` 的主业务键是 `(tenant_key, analysis_run_id)`。创建分析运行时，调用方只传入 `collection_job_id`，`project_id` 必须从同租户下的 `collection_jobs` 派生，避免一个分析运行错误绑定到另一个项目。表结构同时通过 `(tenant_key, collection_job_id)` 外键绑定采集批次，后续事实表和快照表应通过 `analysis_run_id` 追踪到对应的采集输入、插件版本和模型配置。

| 字段 | 说明 |
|------|------|
| `analysis_run_id` | 稳定业务 ID，用于 API、事实表和快照表引用。 |
| `project_id` | 从 `collection_jobs.project_id` 派生的项目 ID，不由调用方自由指定。 |
| `collection_job_id` | 本次分析消费的采集批次。 |
| `status` | `pending`、`running`、`succeeded`、`failed`、`stale`。 |
| `plugin_versions` | 本次分析使用的插件版本 JSON，兼容 SQLite 时以文本保存。 |
| `model_config_hash` | 模型和分析配置摘要，用于判断结果是否仍然新鲜。 |
| `input_watermark` | 输入数据水位，例如采集完成时间、批次版本或后续快照版本。 |
| `started_at` / `finished_at` / `stale_at` | 生命周期时间戳。 |
| `error_code` / `error_message` | 失败或过期原因。 |

状态迁移约束：

| 操作 | 合法迁移 | 说明 |
|------|----------|------|
| create | 无记录 -> `pending` | 创建时默认等待分析。 |
| start | `pending` -> `running` | 记录 `started_at`，清理历史错误字段。 |
| complete success | `running` -> `succeeded` | 记录 `finished_at`，清理错误字段。 |
| complete failure | `running` -> `failed` | 记录 `finished_at`、`error_code` 和 `error_message`。 |
| mark stale | `succeeded` / `failed` -> `stale` | 仅已完成或已失败的运行可因上游数据、插件版本或配置变化而过期。 |

`pending` 和 `running` 不能直接标记为 `stale`，因为它们还没有稳定输出；需要取消或失败时应通过后续 Phase 5.3 的失败/重试能力处理。

MySQL 迁移脚本：

```powershell
mysql -u root -p geo < api/database/migrations/20260607_add_analysis_run_model.mysql.sql
```

后续 Phase 5.2 的接入点：

| 后续能力 | 与本阶段的关系 |
|----------|----------------|
| 分析插件服务入口 | 以 `analysis_run_id` 作为运行上下文，读取同租户同采集批次的原始问答与引用。 |
| 事实表写入 | 所有分析事实必须带 `analysis_run_id`，并保留租户过滤。 |
| 指标快照生成 | Phase 6 从成功的 analysis run 生成 `metric_snapshots`。 |
| 重试与失败可观测 | Phase 5.3 基于 `failed` run 的错误字段和输入水位实现 retry。 |

### 2.5.2 Phase 5.2 系统分析服务与事实血缘

Phase 5.2 将 `analysis/` 下已有的 `mention_status` 与 `reference_status` 插件接入 API 侧的内部系统分析服务。服务入口为 `api/v1/services/analysis_runner.py`，本阶段暂不开放公开路由；调用方传入 `tenant_key` 和 `collection_job_id` 后，服务负责创建或复用 `analysis_run_id`、推进 `analysis_runs` 状态，并把分析事实写回带运行血缘的事实表。

兼容期内，原始回答和引用仍保存在旧表 `llm_conversations`、`llm_conversation_references`，并且旧表仍以 `job_id` 作为采集批次标识。因此本阶段使用 `collection_jobs.source_job_id` 作为桥接键读取旧原始数据；若 `source_job_id` 为空，则回退使用 `collection_job_id`。这个桥接策略只服务于兼容期，长期目标仍是让原始回答和引用直接持有新的采集批次、任务和 attempt 血缘。

品牌上下文来自同租户、同项目的 active `project_brands`。服务要求至少存在一个 active target brand；competitor brand 则作为插件上下文传入。插件运行后，事实写入规则如下：

| 事实表 | 新增血缘字段 | 幂等键策略 |
|--------|--------------|------------|
| `qa_brand_state` | `analysis_run_id`，可为空，外键引用 `(tenant_key, analysis_run_id)` | 继续按 `(tenant_key, job_id, conversation_id, brand)` upsert；重跑会更新同一事实行的 `analysis_run_id`。 |
| `qa_reference` | `analysis_run_id`，可为空，外键引用 `(tenant_key, analysis_run_id)` | 兼容期继续按 `(tenant_key, conversation_id, url)` upsert；重跑会更新同一引用事实的 `analysis_run_id`。 |

`analysis_run_id` 采用 nullable 字段，是为了保留历史事实行和旧 dashboard 查询的兼容性。它不进入旧唯一键，避免同一回答因为不同 analysis run 重复出现在兼容 dashboard 聚合里；后续 Phase 6 的指标快照会使用成功的 `analysis_runs` 生成稳定 read model，而不是直接把多个重跑事实暴露给用户。

MySQL 迁移脚本：

```powershell
mysql -u root -p geo < api/database/migrations/20260607_add_analysis_run_id_to_analysis_facts.mysql.sql
```

本阶段的服务成功条件是：采集批次必须已 `succeeded`，项目必须有 active target brand，至少有一类原始数据可供插件处理。任一插件或输入异常会把 `analysis_runs` 结束为 `failed` 并记录错误信息。更细的失败分类、重试入口和运行观测面留到 Phase 5.3 实现。

### 2.5.3 Phase 5.3 失败可观测与重试

Phase 5.3 新增 `analysis-runs` API，让分析运行的失败原因和重试能力进入系统接口，而不是只停留在内部 service 中。

| API | 权限 | 说明 |
|-----|------|------|
| `GET /api/v1/analysis-runs/{analysis_run_id}` | 当前租户成员 | 返回分析运行状态、采集批次、输入水位、错误编码、错误信息和 `can_retry`。 |
| `POST /api/v1/analysis-runs/{analysis_run_id}/retry` | 当前租户 admin | 对 failed/stale run 重新运行分析；请求体可选传入新的 `analysis_run_id`。 |

retry 不复用原始 `analysis_run_id`。服务会读取原 run 的 `collection_job_id`，为同一采集批次创建新的 analysis run，并按 Phase 5.2 的插件链路重新写入事实表。原 failed/stale run 保留原始错误原因，便于审计；新 run 独立记录自己的状态、输入水位和错误字段。若调用方传入与原 run 相同的 `analysis_run_id`，服务必须拒绝。

事实表仍沿用兼容期 upsert 语义。若失败 run 曾留下部分 `qa_brand_state` 或 `qa_reference` 事实，成功 retry 会把同一事实键的 `analysis_run_id` 更新为新的 succeeded run，从而减少失败运行对后续读取面的影响。

Phase 6 生成指标快照时必须只选择 `status='succeeded'` 的 analysis run。本阶段已在 Repository 层提供 `get_latest_successful_analysis_run_for_collection` 作为候选查询入口；它不会返回 failed/stale/pending/running run。这样即使失败运行曾写入过部分事实，也不会成为快照生成的合法输入。

本阶段的 retry 仍是同步 API 调用。后续如果分析耗时明显增加，应把 API 改为创建 pending retry run，由后台 worker 异步执行。

### 2.5.4 Phase 6.1 指标快照模型

Phase 6.1 新增 `metric_snapshots` 表，作为 dashboard、报告和后续告警的稳定 read model。本阶段只落 schema 和迁移，不生成指标、不改 dashboard 查询；Phase 6.2 再实现指标口径和快照生成，Phase 6.3 再迁移 dashboard 读取。

核心字段：

| 字段 | 说明 |
|------|------|
| `snapshot_id` | 稳定快照 ID，用于 API 或排障引用。 |
| `project_id` | 监测项目 ID；必须与当前租户下的 `monitoring_projects` 绑定。 |
| `analysis_run_id` | 生成该快照的分析运行；必须引用同租户的 `analysis_runs`。 |
| `metric_date` | 指标业务日期。 |
| `brand_id` / `brand_name` | 品牌维度。`brand_id` 为空字符串时表示全品牌聚合，`brand_name` 保存生成时展示名。 |
| `platform` | 平台维度。空字符串表示全平台聚合。 |
| `keyword` | 关键词维度。空字符串表示全关键词聚合。 |
| `metric_name` | 指标名，例如 `mention_rate`、`first_mention_rate`、`top3_mention_rate`、`reference_rate`。 |
| `metric_value` / `metric_unit` | 指标值和单位，单位可为 `ratio`、`count` 等。 |
| `metric_definition_version` | 指标口径版本，Phase 6.2 会为各指标定义稳定版本。 |
| `expected_task_count` / `succeeded_task_count` / `failed_task_count` | 采集覆盖数据。 |
| `analyzed_answer_count` | 本指标实际纳入分析的回答数。 |
| `coverage_rate` | 覆盖率，用于 dashboard 展示数据完整性。 |
| `source_watermark` | 输入数据水位，可记录 `analysis_runs.input_watermark` 或后续快照输入版本。 |
| `dimension_hash` | 品牌、平台、关键词等维度组合的 hash，用于幂等唯一键。 |
| `generated_at` | 快照生成时间，用于新鲜度展示。 |

幂等键为 `(tenant_key, project_id, metric_date, metric_name, metric_definition_version, analysis_run_id, dimension_hash)`。没有直接把 `brand_id + platform + keyword` 全量放进唯一键，是因为这些维度字段和 `tenant_key` 都是 `utf8mb4 varchar`，MySQL 复合唯一索引容易超过 3072-byte 上限；`dimension_hash` 能在保留原始维度字段的同时稳定支持重算 upsert。

MySQL 迁移脚本：

```powershell
mysql -u root -p geo < api/database/migrations/20260607_add_metric_snapshots.mysql.sql
```

生成器必须只使用 `status='succeeded'` 的 analysis run，且写入时必须携带同租户 `tenant_key`，不能跨项目或跨租户聚合。

### 2.5.5 Phase 6.2 指标快照生成口径

Phase 6.2 新增内部服务 `api/v1/services/metric_snapshots.py` 和仓储 `api/v1/repositories/metric_snapshots.py`，从成功的 `analysis_runs` 生成 `metric_snapshots`。本阶段仍不改 dashboard 查询；Phase 6.3 再让 dashboard 优先读取快照。

服务入口为 `generate_metric_snapshots_for_analysis_run(db, tenant_key, analysis_run_id)`。入口约束：

- `analysis_runs.status` 必须为 `succeeded`，否则返回 409，不写入快照。
- 所有读取都带 `tenant_key`，并通过 `analysis_run_id` 限定同一次分析输出。
- 当前生成粒度为 `(metric_date, brand, platform, keyword)`，`brand_id` 优先从同项目 active `project_brands.brand_name` 精确匹配；无匹配时暂以事实中的 `brand` 作为兼容回退。
- `coverage_rate = collection_jobs.succeeded_task_count / collection_jobs.expected_task_count`；当 expected 为 0 时保存为空，避免制造虚假的完整性。
- 快照写入使用 `metric_snapshots` 的幂等唯一键 upsert；重复生成同一个 analysis run 不会插入重复行。

首版口径版本为 `brand_metrics_v1`，所有值均以 `ratio` 写入，并保留 6 位小数：

| `metric_name` | 口径 |
|------|------|
| `mention_rate` | 同一品牌/日期/平台/关键词下，`is_mentioned = 1` 的去重回答数 / 纳入分析的去重回答数。 |
| `first_mention_rate` | `is_first_mentioned = 1` 的去重回答数 / 纳入分析的去重回答数。 |
| `top3_mention_rate` | `is_top3_mentioned = 1` 的去重回答数 / 纳入分析的去重回答数。 |
| `sentiment_positive_ratio` | `sentiment_status = positive` 的去重回答数 / 纳入分析的去重回答数。 |
| `sentiment_negative_ratio` | `sentiment_status = negative` 的去重回答数 / 纳入分析的去重回答数。 |
| `sentiment_neutral_ratio` | `sentiment_status = neutral` 的去重回答数 / 纳入分析的去重回答数。 |
| `sentiment_unknown_ratio` | 情绪值不属于 positive/negative/neutral 的去重回答数 / 纳入分析的去重回答数。 |
| `reference_rate` | 同一 analysis run、品牌、日期、平台和关键词下，在 `qa_reference` 中存在至少一条引用的去重回答数 / 纳入分析的去重回答数。 |

`reference_rate` 表达“回答是否带任意信源引用”，不等同于旧指标文档中的发稿链接覆盖率；后者依赖 `is_published_link`，应在后续作为独立指标或新口径版本扩展。

### 2.5.6 Phase 6.3 Dashboard 快照优先读取

Phase 6.3 将品牌提及类 dashboard 读取面迁移为快照优先。实现位置仍在 Repository 层，`DashboardService` 对外方法和 API 响应结构保持不变：

| Dashboard 读取面 | 快照来源 | 无快照时兜底 |
|------|------|------|
| `brand-metrics` | `metric_snapshots` 中的 `mention_rate`、`first_mention_rate`、`top3_mention_rate`，按品牌加权汇总。 | 旧 `qa_brand_state` 聚合。 |
| `brand-mention-trend` | 指定品牌、平台、关键词、日期的 `mention_rate` 快照。 | 旧 `qa_brand_state` 日聚合。 |
| `platform-metrics-by-brand` | 指定品牌下按平台加权汇总 `mention_rate`。 | 旧 `qa_brand_state` 平台聚合。 |
| `keyword-platform-brand-rates` | 按关键词、平台、品牌读取 `mention_rate`、`first_mention_rate`、`top3_mention_rate` 快照。 | 旧 `qa_brand_state` 聚合。 |

兼容期 dashboard 仍以 `tenant_key + job_id` 作为 URL 和 API 查询输入。快照查询会通过 `analysis_runs.collection_job_id = job_id` 或 `collection_jobs.source_job_id = job_id` 找到最新 succeeded analysis run，因此新采集批次 ID 和旧 legacy job ID 都可以进入同一读取路径。

本阶段暂不迁移以下读取面：

- `platform-mention-rates`：现有接口需要 `category` 维度，Phase 6.2 的 `metric_snapshots` 暂未保存 category。
- 引用域名、引用类型、URL 引用、发稿链接覆盖率相关接口：这些口径依赖 `qa_reference` 的 domain、content_type、url、`is_published_link` 等明细维度，不能由首版 `brand_metrics_v1` 直接替代。

当匹配不到可用快照时，Repository 返回空列表并继续执行旧明细聚合。这样旧 dashboard、历史 job 和尚未生成快照的采集批次仍能工作；Phase 6.4 再在前端展示快照新鲜度和覆盖率，帮助用户理解数据来源。

### 2.5.7 Phase 6.4 Dashboard 数据新鲜度与覆盖率

Phase 6.4 在 `brand-metrics` 响应的 `metadata` 中增加快照质量字段，不改变 `data` 数组中的品牌指标结构。前端首页继续通过同一个接口加载目标品牌和竞品列表，并使用 metadata 展示数据来源、指标生成时间、采集覆盖和分析完整性。

新增 metadata 字段：

| 字段 | 说明 |
|------|------|
| `data_source` | `metric_snapshot` 表示当前窗口匹配到指标快照；`legacy_aggregation` 表示回退到旧明细聚合。 |
| `snapshot_status` | `available` 表示快照可用；`missing` 表示快照未生成或当前窗口无可用快照。 |
| `metric_definition_version` | 当前质量信息对应的指标口径版本，首版为 `brand_metrics_v1`。 |
| `analysis_run_id` | 生成快照的分析运行 ID；旧明细聚合或快照缺失时为空。 |
| `metric_generated_at` | 快照生成时间，用于 dashboard 新鲜度展示。 |
| `metric_coverage_rate` | 采集覆盖率，值为 0-1 的比例；缺失时前端展示“覆盖率待生成”。 |
| `metric_expected_task_count` / `metric_succeeded_task_count` / `metric_failed_task_count` | 采集任务完整性计数，用于前端展示“成功 / 预期 / 失败”。 |
| `metric_analyzed_answer_count` | 当前指标窗口实际纳入分析的回答数，按日期和维度去重后汇总。 |
| `metric_snapshot_count` / `metric_dimension_count` | 当前窗口命中的快照行数和业务维度数，用于排障与后续数据质量页。 |

前端展示策略：

- 当 `data_source = metric_snapshot` 且 `snapshot_status = available` 时，展示“指标快照”、生成时间、覆盖率、分析完整性和纳入分析回答数。
- 当快照缺失或质量查询失败时，展示“明细聚合”和“快照未生成”，并明确提示当前数据来自历史明细聚合，避免用户把旧聚合误解为已生成快照。
- 空状态文案不再描述为“接口未返回可展示的数据”，而是提示当前筛选下没有品牌指标，若刚完成采集需等待分析和指标快照生成。

### 2.5.8 Phase 7.1 问答快照页

Phase 7.1 新增问答快照读面，用于从 dashboard 直接查看原始回答，并按品牌、平台、关键词、情绪和是否引用筛选。兼容期仍使用 `tenant_key + job_id` 作为入口；后续 Phase 8 再把旧 job 路由收敛到项目运行页。

API：

```text
GET /api/v1/dashboard/answer-snapshots
```

查询参数：

| 参数 | 说明 |
|------|------|
| `tenant_key` / `job_id` | 当前 dashboard 查询边界，所有 SQL 必须带租户过滤。 |
| `timeframe` / `start_date` / `end_date` | 复用 dashboard 时间窗口；`specific_day` 必须传起止日期。 |
| `brand` | 可选品牌筛选，来自 `qa_brand_state.brand`。 |
| `platform` / `keyword` | 可选原始回答维度筛选，来自 `llm_conversations`。 |
| `sentiment` | 可选情绪筛选，来自 `qa_brand_state.sentiment_status`。 |
| `has_reference` | 可选引用状态筛选，基于 `qa_reference` 当前品牌和时间窗口下的引用数。 |
| `limit` / `offset` | 分页参数，当前页面默认读取 50 条。 |

响应 `data` 中每条记录包含：

| 字段 | 来源与说明 |
|------|------|
| `conversation_id` | 原始回答 ID。 |
| `date` | 业务日期，格式 `YYYYMMDD`。 |
| `platform` / `brand` / `keyword` | 回答维度和筛选上下文。 |
| `query_content` / `answer_content` | 原始问题与回答内容。 |
| `sentiment_status` / `is_mentioned` | 品牌分析事实。 |
| `has_reference` / `reference_count` / `references` | 引用状态和最多当前页对应引用明细。 |

Repository 以 `llm_conversations` 为主表，左连接 `qa_brand_state` 和按 `conversation_id` 聚合后的 `qa_reference`。这样没有引用的回答仍能展示；当筛选 `has_reference=false` 时，可明确看到“无引用”回答。若传入 `brand` 或 `sentiment`，查询必须命中同租户同 job 的 `qa_brand_state`，避免用原始回答表的品牌字段误判分析结果。

### 2.5.9 Phase 7.2 真实情感分析页

Phase 7.2 将正式情感分析页面从硬编码 mock 统计切换为真实 dashboard 读面。兼容期仍使用 `tenant_key + job_id` 作为入口，后续 Phase 8 再统一收敛到项目运行页。

API：

```text
GET /api/v1/dashboard/sentiment-analysis
```

查询参数：

| 参数 | 说明 |
|------|------|
| `tenant_key` / `job_id` | 当前 dashboard 查询边界，所有 SQL 必须带租户过滤。 |
| `timeframe` / `start_date` / `end_date` | 复用 dashboard 时间窗口；`specific_day` 必须传起止日期。 |
| `brand` | 可选品牌筛选。快照读 `metric_snapshots.brand_name`，兜底读 `qa_brand_state.brand`。 |
| `platform` / `keyword` | 可选维度筛选。用于情绪分布和关键词情绪明细。 |

响应 `data`：

| 字段 | 说明 |
|------|------|
| `distribution` | 情绪分布数组，包含 `sentiment_status`、`answer_count`、`ratio`。 |
| `keywords` | 关键词情绪明细，包含 `keyword`、`platform`、`brand`、`sentiment_status`、`answer_count`、`ratio`。 |

响应 `metadata`：

| 字段 | 说明 |
|------|------|
| `data_source` | `metric_snapshot`、`legacy_fact` 或 `empty`。 |
| `sample_count` | 当前筛选窗口纳入情感统计的回答数。 |
| `snapshot_status` / `metric_definition_version` | 指标快照状态和口径版本。 |
| `metric_generated_at` / `metric_coverage_rate` | 当数据来自快照时展示生成时间和覆盖率。 |

Repository 先按最新成功 analysis run 读取 `metric_snapshots` 中的 `sentiment_positive_ratio`、`sentiment_negative_ratio`、`sentiment_neutral_ratio`、`sentiment_unknown_ratio`，并用 `analyzed_answer_count` 加权汇总。若快照缺失，则从 `qa_brand_state.sentiment_status` 按真实分析事实兜底聚合；若两者都没有，返回空数组和 `data_source=empty`，前端展示“暂无真实情感数据”，不再用 mock 统计填充正式页面。

### 2.5.10 Phase 7.3 告警规则与告警事件

Phase 7.3 新增 `alert_rules` 和 `alert_events`，把指标快照中的异常变化沉淀为可查询、可去重、可追溯的项目级告警事件。本阶段先落后端 MVP，不新增独立前端页面；后续报告和项目页可以直接消费项目告警读面。

核心表：

| 表 | 说明 |
|------|------|
| `alert_rules` | 告警规则配置，按 `tenant_key + project_id` 隔离，声明 `rule_type`、`metric_name`、指标口径版本、品牌/平台/关键词维度、阈值、严重级别和启停状态。 |
| `alert_events` | 告警触发事件，记录规则、项目、analysis run、collection job、指标日期、当前值、上期值、变化幅度、阈值、状态、标题和消息。 |

规则类型：

| `rule_type` | 触发口径 |
|------|------|
| `metric_drop` | 同一维度当前值相比上一条指标快照下降幅度大于等于 `threshold_value`。用于提及率下降等场景。 |
| `metric_rise` | 同一维度当前值相比上一条指标快照上升幅度大于等于 `threshold_value`。用于负面情绪上升等场景。 |
| `metric_change` | 同一维度当前值相比上一条指标快照的绝对变化大于等于 `threshold_value`。用于信源引用率变化等场景。 |

事件去重键为 `(tenant_key, alert_rule_id, analysis_run_id, metric_date, dimension_hash)`。同一个 analysis run 被重复评估时不会生成重复事件；事件仍保留 `alert_event_id` 作为外部稳定 ID，便于后续确认、解决和报告引用。

内部服务入口：

```python
evaluate_alert_rules_for_analysis_run(db, tenant_key, analysis_run_id)
```

服务只评估 `succeeded` analysis run，读取当前 run 的 `metric_snapshots`，再按同一 `project_id + metric_name + metric_definition_version + dimension_hash` 找到更早的最近一条快照作为比较基线。所有查询和写入都必须显式携带 `tenant_key`。

项目告警读取 API：

```text
GET /api/v1/projects/{project_id}/alerts
```

权限与返回：

| 范围 | 说明 |
|------|------|
| 权限 | 当前租户成员可读取；租户来自服务端鉴权上下文和 `X-Tenant-Key`，请求体不接受 `tenant_key`。 |
| `rules` | 当前项目下的规则列表，包含状态、阈值和维度。 |
| `events` | 当前项目下最近的告警事件，默认最多 100 条，可用 `event_limit` 调整。 |
| 租户隔离 | API 只查询当前租户的 `alert_rules` 和 `alert_events`，不同租户同名项目不会互相泄漏。 |

### 2.5.11 Phase 7.4 报告生成与报告结果

Phase 7.4 新增 `generated_reports`，把一次项目报告生成动作沉淀为可查询的报告结果。报告结果不是临时响应，而是包含时间窗口、核心指标快照、告警摘要和生成元数据的 read model；后续 PDF、CSV 或前端报告页都应优先消费该表。

核心表：

| 表 | 说明 |
|------|------|
| `generated_reports` | 项目报告结果，按 `tenant_key + report_id` 唯一，绑定 `project_id`，保存 `report_type`、`timeframe`、`start_date`、`end_date`、`summary_json`、`metrics_json`、`alerts_json`、`generated_by` 和 `generated_at`。 |

报告生成入口：

```text
POST /api/v1/projects/{project_id}/reports
GET  /api/v1/projects/{project_id}/reports
```

`POST /reports` 接收 `report_id`（可选）、`title`（可选）、`report_type`、`timeframe`、`start_date` 和 `end_date`。服务端使用当前认证用户和 `X-Tenant-Key` 解析出的租户上下文，不接受请求体传入 `tenant_key`。

数据来源：

| 数据 | 来源 | 说明 |
|------|------|------|
| 核心指标 | `metric_snapshots` | 读取 `mention_rate`、`first_mention_rate`、`top3_mention_rate`、`sentiment_negative_ratio`、`reference_rate`，按品牌和指标口径版本聚合。 |
| 时间窗口 | 请求参数 `start_date` / `end_date` | 同时写入报告行字段和 `summary_json.data_window`。 |
| 告警摘要 | `alert_events` | 按同一项目和指标日期窗口读取，写入事件数量、打开事件数量、严重级别统计和事件摘要。 |
| 生成元数据 | 当前用户与生成时间 | `generated_by` 记录用户 ID，`generated_at` 记录生成时间。 |

验收口径：

| 项 | 说明 |
|----|------|
| 生成报告 | 项目成员可调用 POST 生成一条 `generated_reports` 记录。 |
| 核心指标 | 响应和持久化 JSON 中包含核心指标和指标口径版本。 |
| 时间窗口 | 响应和持久化 JSON 中包含 `start_date`、`end_date` 和 `timeframe`。 |
| 租户隔离 | GET 列表只返回当前租户、当前项目下的报告结果，不泄漏其他租户同名项目。 |

### 2.5.12 Phase 7.5 数据质量页

Phase 7.5 新增项目级数据质量读面和前端页面，用于把失败采集、过期分析、指标覆盖率和可重算入口集中到项目上下文中。该页面不再以旧 `job_id` 为入口，而是从 `/projects/:tenantKey/:projectId/quality` 进入。

后端入口：

```text
GET /api/v1/projects/{project_id}/data-quality
```

数据来源：

| 数据 | 来源 | 说明 |
|------|------|------|
| 失败采集 | `collection_tasks` | 查询当前 `tenant_key + project_id` 下 `status='failed'` 的采集任务，并根据 `attempt_count < max_attempts` 标记是否可重新领取。 |
| 过期分析 | `analysis_runs` | 查询当前项目下 `status='stale'` 的 analysis run，并返回可重算动作元数据。 |
| 指标覆盖率 | `metric_snapshots` | 聚合项目级快照覆盖率、预期/成功/失败任务数、快照数、维度数和分析回答数。 |
| 可重算入口 | `analysis_runs` retry API | 页面按钮调用既有 `POST /api/v1/analysis-runs/{analysis_run_id}/retry`，不新增独立重算状态机。 |

前端入口：

```text
/projects/:tenantKey/:projectId/quality
```

验收口径：

| 项 | 说明 |
|----|------|
| 失败采集 | 页面展示失败 task、错误编码、错误信息、尝试次数和是否仍可重试。 |
| 过期分析 | 页面展示 stale analysis run、过期时间、原因和“重新分析”按钮。 |
| 指标覆盖率 | 页面展示覆盖率、任务计数、分析回答数、快照数和口径版本。 |
| 租户隔离 | API 只读取当前租户、当前项目的数据；其他租户同名项目不泄漏。 |

## 3. 状态机参考

### 3.1 项目状态

| 状态 | 含义 | 可进入状态 |
|------|------|------------|
| `draft` | 配置中，尚未开始采集。 | `active`、`archived` |
| `active` | 正常监测。 | `paused`、`archived` |
| `paused` | 暂停采集，保留历史数据。 | `active`、`archived` |
| `archived` | 归档，只读。 | 无 |

### 3.2 采集任务状态

| 状态 | 含义 | 触发 |
|------|------|------|
| `pending` | 等待领取。 | 采集批次生成任务。 |
| `reserved` | 已被执行器领取，lease 未过期。 | fetch 成功。 |
| `running` | 执行器确认开始。 | 执行器 start 上报。 |
| `succeeded` | 原始回答和引用入库成功。 | complete 成功。 |
| `failed` | 执行失败，可重试。 | complete 失败或执行器上报错误。 |
| `expired` | 超出生效窗口。 | 调度器扫描。 |
| `cancelled` | 用户或系统取消。 | 管理操作。 |

### 3.3 分析运行状态

| 状态 | 含义 |
|------|------|
| `pending` | 等待分析。 |
| `running` | 分析中。 |
| `succeeded` | 分析事实和指标快照写入完成。 |
| `failed` | 分析失败，记录错误。 |
| `stale` | 上游数据或分析配置变化，需要重算。 |

## 4. 旧表到目标模型映射

| 当前表 | 目标模型 | 迁移说明 |
|--------|----------|----------|
| `llm_query_jobs` | `collection_jobs`、`collection_tasks`、`prompt_items` | 兼容期保留，逐步拆分配置和执行状态。 |
| `llm_conversations` | `answer_snapshots` | 可先新增 project/attempt 字段，再迁移表名。 |
| `llm_conversation_references` | `answer_references` | 引入 `url_hash` 和引用规范化。 |
| `qa_brand_state` | `brand_mention_facts` | 增加唯一键和 `analysis_run_id`。 |
| `qa_reference` | `reference_classifications` | 增加 `analysis_run_id`、`answer_reference_id`。 |
| `qa_brand_summary` | `metric_snapshots` | 逐步迁移为通用指标快照。 |

## 5. API 契约草案

租户用户 API：

```text
GET  /api/v1/projects
POST /api/v1/projects
GET  /api/v1/projects/{project_id}
PATCH /api/v1/projects/{project_id}
POST /api/v1/projects/{project_id}/brands
POST /api/v1/projects/{project_id}/prompt-sets
POST /api/v1/projects/{project_id}/collection-jobs
GET  /api/v1/projects/{project_id}/collection-jobs
GET  /api/v1/projects/{project_id}/metrics/overview
GET  /api/v1/projects/{project_id}/metrics/trends
GET  /api/v1/projects/{project_id}/answers
GET  /api/v1/projects/{project_id}/alerts
GET  /api/v1/projects/{project_id}/data-quality
GET  /api/v1/projects/{project_id}/reports
POST /api/v1/projects/{project_id}/reports
```

执行器 API：

```text
GET  /api/v1/collection-tasks/fetch
POST /api/v1/collection-attempts/{attempt_id}/start
POST /api/v1/collection-attempts/{attempt_id}/complete
POST /api/v1/answers/load
```

分析 API 或内部任务：

```text
POST /api/v1/analysis-runs
GET  /api/v1/analysis-runs/{analysis_run_id}
POST /api/v1/analysis-runs/{analysis_run_id}/retry
```

### 5.1 Phase 3.2 项目 API 落地说明

已落地的项目 API：

| API | 权限 | 说明 |
|-----|------|------|
| `GET /api/v1/projects` | 当前租户成员 | 返回当前租户下的项目列表。 |
| `POST /api/v1/projects` | 当前租户 admin | 创建项目；请求体禁止携带 `tenant_key`，由 `X-Tenant-Key` 和认证令牌解析。 |
| `GET /api/v1/projects/{project_id}` | 当前租户成员 | 返回项目详情，并聚合品牌配置和问题集配置。 |
| `POST /api/v1/projects/{project_id}/brands` | 当前租户 admin | 按 `(tenant_key, project_id, brand_id, role)` 幂等新增或更新品牌配置。 |
| `POST /api/v1/projects/{project_id}/prompt-sets` | 当前租户 admin | 按 `prompt_set_id` 和 `prompt_item_id` 幂等新增或更新问题集及问题项。 |

边界约定：

- 项目 API 不接受客户端传入的 `tenant_key` 字段，租户上下文只能来自服务端鉴权依赖。
- Repository 查询和写入都必须显式携带 `tenant_key`。
- 读接口允许租户成员使用；配置写接口要求租户 admin。
- 本阶段只建立项目配置 API，不把旧 `llm_query_jobs` 立即迁移到项目模型；任务关联将在 Phase 3.4 处理。

### 5.2 Phase 3.3 前端项目入口落地说明

已落地的租户工作台项目入口：

| 前端入口 | 组件 | 说明 |
|----------|------|------|
| `/projects/:tenantKey` | `ProjectListPage` | 展示当前租户下的监测项目列表、项目状态和基础配置摘要。 |
| `/projects/:tenantKey/:projectId` | `ProjectDetailPage` | 展示项目详情壳层，聚合项目基本信息、品牌配置和问题集配置。 |

前端契约：

- 新增 `web/src/api/projects.js`，通过 `fetchProjects` 和 `fetchProjectDetail` 调用 `/api/v1/projects` 与 `/api/v1/projects/{project_id}`。
- 项目 API adapter 继续复用统一 `apiClient`，租户上下文由路由中的 `tenantKey` 注入 `X-Tenant-Key`，组件不直接拼接后端域名。
- `project_id` 只作为路径参数传递，并在构造详情路径时进行 URL 编码。
- `web/src/config/routes.js` 中 `projects` 进入主菜单；`project-detail` 为隐藏路由，下钻后侧边栏仍保持项目入口选中。
- 本阶段页面为只读壳层，不新增创建、编辑、删除表单；项目到旧 `job_id` 采集任务的关联将在 Phase 3.4 处理。

### 5.3 Phase 3.4 新建任务关联项目落地说明

已落地的兼容期任务关联：

| 范围 | 说明 |
|------|------|
| 数据库 | `llm_query_jobs` 新增 nullable `project_id` 字段和 `(tenant_key, project_id)` 索引。 |
| API | `POST /api/v1/query-jobs/load` 可接收 `project_id`；当字段存在时，后端按当前租户校验项目存在后再写入每条 query job。 |
| 前端 | `CreateQueryJob` 在基本信息区加载当前租户项目列表，用户可选择关联项目，也可选择“暂不关联项目”保留旧任务兼容路径。 |
| 旧入口 | `/dashboard/:tenantKey/:jobId`、`/task-status/:tenantKey/:jobId` 等旧 `job_id` 入口不变，任务状态查询仍按 `tenant_key + job_id` 工作。 |

边界约定：

- `project_id` 是兼容期桥接字段，不替代 `job_id`；旧 dashboard 和执行器仍以 `job_id` 识别任务批次。
- `llm_query_jobs.project_id` 暂不加外键。项目归属由 API 通过 `(tenant_key, project_id)` 校验，避免历史任务和项目删除策略互相阻塞。
- 同一个 `job_id` 下展开出的多条 query job 记录会写入相同 `project_id`，便于 Phase 4 迁移为 `collection_jobs.project_id`。
- 没有传 `project_id` 的旧请求仍可工作；后续主流程可逐步收紧为项目优先。

## 6. 幂等与唯一键要求

| 数据 | 唯一性建议 |
|------|------------|
| 项目 | `(tenant_key, project_id)` |
| 品牌角色 | `(tenant_key, project_id, brand_id, role)` |
| 问题项 | `(tenant_key, prompt_set_id, prompt_item_id)` |
| 采集任务 | `(tenant_key, collection_job_id, platform, prompt_item_id, run_index)` |
| 执行尝试 | `(tenant_key, attempt_id)` |
| 回答快照 | `(tenant_key, collection_attempt_id)` |
| 引用链接 | `(tenant_key, answer_snapshot_id, url_hash)` |
| 品牌提及事实 | `(tenant_key, analysis_run_id, answer_snapshot_id, brand_id)` |
| 引用分类事实 | `(tenant_key, analysis_run_id, answer_reference_id, brand_id)` |
| 指标快照 | `(tenant_key, project_id, metric_date, metric_name, brand_id, platform, keyword, snapshot_version)` |

兼容阶段至少修复 `qa_brand_state` 对 `(tenant_key, job_id, conversation_id, brand)` 的唯一约束，否则分析重跑会产生重复事实。

### 6.1 Phase 2.1 重复风险检查

兼容期先使用只读脚本盘点历史数据，再进入唯一键和 URL hash 调整：

```bash
uv run --project api python api/scripts/check_duplicate_analysis_rows.py --limit 20
```

如需检查指定数据库，可传入 SQLAlchemy URL：

```bash
uv run --project api python api/scripts/check_duplicate_analysis_rows.py --database-url "sqlite:///path/to/geo.db"
```

脚本覆盖以下检查：

| 检查项 | 风险含义 |
|--------|----------|
| `qa_brand_state_target_key_duplicates` | 同一 `(tenant_key, job_id, conversation_id, brand)` 存在多条品牌提及事实，重跑分析会污染提及率。 |
| `qa_reference_target_key_duplicates` | 同一 `(tenant_key, job_id, conversation_id, brand, url)` 存在多条引用分析事实。 |
| `qa_reference_current_key_cross_scope_collisions` | 旧唯一键 `(tenant_key, conversation_id, url)` 无法区分不同 job 或 brand，存在覆盖或跳过写入风险。 |
| `llm_conversation_references_target_key_duplicates` | 同一 `(tenant_key, job_id, conversation_id, brand, url)` 存在多条原始引用。 |
| `llm_conversation_references_current_key_cross_scope_collisions` | 原始引用旧唯一键无法区分不同 job 或 brand，后续迁移需纳入更细粒度键或 URL hash。 |

脚本返回码约定：未发现风险返回 `0`；发现重复或碰撞风险返回 `1`；数据库连接失败或缺少必需表时返回 `2`，便于在迁移前作为门禁使用。

### 6.2 Phase 2.2 `qa_brand_state` 幂等键

兼容期 schema 已为 `qa_brand_state` 增加 `uk_tenant_job_conv_brand`，服务于 `analysis/src/plugins/metrics/mention_status.py` 中的 `ON DUPLICATE KEY UPDATE`。MySQL 迁移脚本：

```bash
mysql -u root -p geo < api/database/migrations/20260606_add_qa_brand_state_idempotency_key.mysql.sql
```

迁移前必须先运行 Phase 2.1 重复风险检查；如果 `qa_brand_state_target_key_duplicates` 有结果，需要先清理历史重复数据再加唯一键。

MySQL 当前字段为 `tenant_key/job_id/conversation_id varchar(255)` 且使用 `utf8mb4`，完整复合索引可能超过 InnoDB 3072-byte 限制。因此兼容期唯一键使用 191 前缀：

```sql
UNIQUE KEY `uk_tenant_job_conv_brand`
  (`tenant_key`(191), `job_id`(191), `conversation_id`(191), `brand`)
```

当前 `tenant_key`、`job_id`、`conversation_id` 均为短生成 ID，191 前缀不会改变现有数据的幂等语义。长期目标模型可在引入规范化 ID、`analysis_run_id` 或 hash key 后移除这个兼容折中。

### 6.3 Phase 2.3 引用表唯一键与 URL hash 策略

本阶段不立即修改 `qa_reference` 和 `llm_conversation_references` 的 schema。原因是两张引用表当前都依赖旧唯一键 `uk_tenant_conversation_url (tenant_key, conversation_id, url(191))`，API 的 `reference_exists` / `insert_reference` 和分析插件 `reference_status` 的 `ON DUPLICATE KEY UPDATE` 也围绕这个键工作。只在 schema 层单独加入新唯一键，无法改变旧 upsert 语义，还可能在历史数据未清理时导致迁移失败。

当前兼容期策略如下：

| 范围 | 兼容期处理 | 说明 |
|------|------------|------|
| 原始引用 `llm_conversation_references` | 暂保留 `(tenant_key, conversation_id, url(191))` | 避免破坏现有 `conversation/load` 入库和外键关系。 |
| 分析引用 `qa_reference` | 暂保留 `(tenant_key, conversation_id, url(191))` | 避免 `reference_status` 重跑时出现无法预期的 upsert 目标。 |
| 迁移前检查 | 继续使用 Phase 2.1 脚本检查目标键重复和旧键跨作用域碰撞 | 只有目标数据库或导入 dump 检查干净后，才能推进唯一键替换。 |

目标迁移方案应分两步推进：

1. 先引入 URL 规范化与持久化 hash 字段，例如 `normalized_url` + `url_hash`。`url_hash` 建议使用 SHA-256，可存储为 `BINARY(32)` 或 `CHAR(64)`；若使用 MySQL 生成列，需要确认函数和字符集行为在目标版本中稳定。
2. 再替换唯一键。原始引用表目标键建议为 `(tenant_key, job_id, conversation_id, url_hash)`；分析引用表兼容期目标键建议为 `(tenant_key, job_id, conversation_id, brand, url_hash)`，长期模型再收敛到 `(tenant_key, analysis_run_id, answer_reference_id, brand_id)`。

URL 规范化规则需要先固定再写入 hash：去除首尾空白和包裹尖括号；scheme 与 host 小写；去除默认端口；去除 fragment；统一尾部斜杠；query 参数暂时保留，直到产品侧明确是否剔除追踪参数。这样可以先降低明显重复，又不提前合并可能具有业务差异的链接。

Phase 2 后续若要真正修改引用表唯一键，必须同时更新：

- `api/v1/repositories/conversation.py` 中的引用存在性检查和写入契约。
- `analysis/src/plugins/metrics/reference_status.py` 中的 URL 规范化、hash 生成和 upsert 目标。
- MySQL 与 SQLite schema、迁移脚本、schema 测试。
- Phase 2.1 重复风险检查脚本中的目标键定义。

### 6.4 Phase 2.5 采集入库与任务上报一致性

兼容期内，执行器完成一次问答采集后需要先调用 `POST /api/v1/conversation/load` 写入 `llm_conversations`，再调用 `POST /api/v1/query-jobs/report` 增加 `llm_query_jobs.executed_runs`。Phase 2.5 已为这条链路增加一致性门：如果任务结果尚未成功入库，`query-jobs/report` 返回 `success=false`，不会增加执行次数，也不会把任务状态推进到完成。

由于当前旧模型还没有 `collection_attempt_id`，`llm_conversations` 也没有保存 query job record id，本阶段只能使用以下兼容期关联判断任务结果是否已入库：

```text
llm_query_jobs.id + executor_id
  -> llm_query_jobs.(tenant_key, job_id, query_content)
  -> llm_conversations.(tenant_key, job_id, query_content)
```

这个门禁用于防止“入库失败但任务被错误计为完成”的数据污染。它不是长期目标：Phase 4 引入 `collection_attempts` 后，应将上报完成绑定到具体 `attempt_id` 和回答快照，而不是继续依赖 `query_content` 作为兼容关联键。

## 7. 数据质量字段建议

指标快照应包含：

- `expected_task_count`
- `succeeded_task_count`
- `failed_task_count`
- `analyzed_answer_count`
- `coverage_rate`
- `source_watermark`
- `generated_at`
- `metric_definition_version`

dashboard 展示时应能说明当前指标是否完整、是否过期、是否来自失败后部分数据。
