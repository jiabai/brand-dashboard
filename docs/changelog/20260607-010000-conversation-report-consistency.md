# 采集入库与任务上报一致性

> 日期：2026-06-07
> 类型：api, test, docs

## 变更

- 新增 `api/tests/test_conversation_report_consistency.py`，覆盖执行器先入库、再上报的兼容期顺序。
- 为 `query-jobs/report` 增加上报前校验：任务结果尚未成功写入 `llm_conversations` 时返回 `success=false`，不增加 `executed_runs`。
- 新增 `query_job_has_loaded_conversation` 仓储函数，通过旧模型中的 `(tenant_key, job_id, query_content)` 判断任务结果是否已入库。
- 保留成功路径：`conversation/load` 成功写入后，`query-jobs/report` 仍可正常增加执行次数。
- 更新领域数据参考、active ExecPlan 和 `TASKS.md`，说明该关联方式只是 Phase 4 引入 `collection_attempt_id` 前的兼容期门禁。

## 验证

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api\tests\test_conversation_report_consistency.py -q`
- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `python scripts/validate_agents_docs.py --level ERROR`
- `python scripts/validate_agents_docs.py --level WARN`
