# feat: 新增采集生命周期数据模型

## 背景

Phase 3 已经建立监测项目和问题集配置，并让旧查询任务可以关联 `project_id`。旧 `llm_query_jobs` 仍同时承担采集批次、任务明细和执行状态，无法表达任务领取 lease、单次 attempt、失败原因和后续分析血缘。Phase 4.1 先补齐采集生命周期 schema，为后续改造执行器领取协议和 attempt 上报接口提供数据基础。

## 变更

- 新增 `collection_jobs`，用 `(tenant_key, collection_job_id)` 表达一次采集批次，并绑定监测项目、问题集版本、采集窗口和任务计数。
- 新增 `collection_tasks`，用 `(tenant_key, collection_task_id)` 表达可领取任务，保存 `lease_owner`、`lease_until`、执行时间、重试次数和最后失败原因。
- 新增 `collection_attempts`，记录每次执行尝试的执行器、状态、开始/完成时间、错误编码、错误信息和原始响应标识。
- 在 `api/database/schema.sql`、`api/database/schema_business.sql`、`api/database/schema_sqlite.sql`、`analysis/database/schema.sql`、`analysis/database/schema_business.sql` 中同步 schema。
- 新增 MySQL 迁移脚本 `api/database/migrations/20260607_add_collection_lifecycle_model.mysql.sql`。
- 新增 `api/tests/test_collection_lifecycle_schema.py`，覆盖 MySQL schema 文本、迁移脚本和 SQLite 复合外键运行时行为。
- 更新 active ExecPlan、`TASKS.md` 和领域数据参考文档。

## 兼容边界

- 本阶段不改旧 `/api/v1/query-jobs/fetch`、`/api/v1/query-jobs/report` 和执行器客户端协议。
- `source_job_id` 只用于兼容期追溯旧 `llm_query_jobs.job_id`，目标态仍以 `collection_job_id` 作为采集批次业务键。
- `collection_jobs` 绑定项目但不随项目删除级联，采集历史需要保留给分析运行、指标快照和审计追踪。
- 任务领取并发控制、lease 超时重领和 attempt start/complete API 将在 Phase 4.2/4.3 实现。

## 验证

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_collection_lifecycle_schema.py -q`：3 passed。
- `uv run --project api ruff check api`：通过。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：109 passed。
- `python scripts/validate_agents_docs.py --level ERROR`：通过。
- `python scripts/validate_agents_docs.py --level WARN`：通过。
- Phase 4.1 未改前端，未运行前端构建。
