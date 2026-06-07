# feat: 新增采集任务领取 lease 协议

## 背景

Phase 4.1 已经新增 `collection_jobs`、`collection_tasks` 和 `collection_attempts` 三张生命周期表，但执行器仍只能通过旧 `query-jobs/fetch` 领取没有租约保护的任务。Phase 4.2 在新采集任务模型上补齐领取入口，先解决重复领取和 lease 超时重领，为 Phase 4.3 的 attempt start/complete 接口铺路。

## 变更

- 新增 `GET /api/v1/collection-tasks/fetch`，执行器通过 `executor_id` + `X-Executor-Key` 复用既有身份校验。
- 新增 `CollectionTaskDetail` 和 `FetchCollectionTaskResponse` Pydantic 响应模型。
- 新增 `api/v1/repositories/collection_tasks.py`，用条件更新写入 `status='reserved'`、`lease_owner`、`lease_until` 和 `reserved_at`。
- 新接口要求显式传入 `tenant_key`，并支持可选 `collection_job_id` 和 `lease_seconds`。
- 新增 `api/tests/test_collection_tasks_fetch.py`，覆盖 pending 领取、连续领取不重复、活跃租约隔离、lease 过期重领和租户过滤。
- 更新 active ExecPlan、`TASKS.md` 和领域数据参考文档。

## 兼容边界

- 本阶段不修改旧 `/api/v1/query-jobs/fetch` 和 `/api/v1/query-jobs/report`，既有执行器客户端仍可按旧协议运行。
- 新接口当前只负责领取并写入 lease；attempt start/complete、成功/失败回写和回答入库绑定将在 Phase 4.3 处理。
- 当前系统还没有独立的执行器租户授权表；本阶段先通过必填 `tenant_key`、执行器身份校验和活跃租约隔离控制领取边界。

## 验证

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_collection_tasks_fetch.py -q`：5 passed。
- `uv run --project api ruff check api`：通过。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：114 passed。
- `python scripts/validate_agents_docs.py --level ERROR`：通过。
- `python scripts/validate_agents_docs.py --level WARN`：通过。
- Phase 4.2 未改前端，未运行前端构建。
