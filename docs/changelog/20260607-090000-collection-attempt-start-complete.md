# feat: 新增采集 attempt start/complete 接口

## 背景

Phase 4.2 已经让执行器可以领取 `collection_tasks` 并获得 lease，但任务执行过程仍没有单次 attempt 记录。Phase 4.3 补齐 start/complete 接口，让执行器的开始、成功、失败、超时和重试路径都能被系统追踪。

## 变更

- 新增 `POST /api/v1/collection-attempts/{attempt_id}/start`，仅允许当前 lease 持有者启动 attempt。
- 新增 `POST /api/v1/collection-attempts/{attempt_id}/complete`，支持 `succeeded`、`failed`、`timeout`、`cancelled` 状态上报。
- 新增 `StartCollectionAttemptRequest`、`CompleteCollectionAttemptRequest`、`CollectionAttemptDetail`、`CollectionAttemptResponse`。
- 新增 `api/v1/repositories/collection_attempts.py`，集中处理 attempt 创建、任务状态推进、失败原因记录和 lease 释放。
- 新增 `api/tests/test_collection_attempts_api.py`，覆盖 start 成功、非 lease 持有者拒绝、complete 成功、失败后可重试、timeout 达重试上限后不再领取。
- 更新 active ExecPlan、`TASKS.md` 和领域数据参考文档。

## 兼容边界

- 本阶段仍不修改旧 `/api/v1/query-jobs/report`。
- `conversation/load` 尚未绑定 `attempt_id`；回答快照与 attempt 的强关联将在后续回答模型迁移阶段补齐。
- `attempt_count` 在 start 阶段递增，表示执行器已经开始消耗一次尝试额度；complete 只负责记录结果并推进 task 状态。

## 验证

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_collection_attempts_api.py -q`：5 passed。
- `uv run --project api ruff check api`：通过。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：119 passed。
- `python scripts/validate_agents_docs.py --level ERROR`：通过。
- `python scripts/validate_agents_docs.py --level WARN`：通过。
- Phase 4.3 未改前端，未运行前端构建。
