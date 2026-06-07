# 引用表唯一键与 URL hash 策略

> 日期：2026-06-06
> 类型：docs, architecture

## 变更

- 在领域数据参考文档中补充 Phase 2.3 决策，明确 `qa_reference` 与 `llm_conversation_references` 兼容期暂不立即修改 schema。
- 记录当前旧唯一键 `(tenant_key, conversation_id, url)` 与 API / analysis 写入路径的耦合关系，避免后续只做 schema 单点修改。
- 明确目标迁移方向：先引入 URL 规范化与 `url_hash`，再替换为包含 `job_id`、`brand` 或 `analysis_run_id` 的幂等键。
- 更新 active ExecPlan 的进度、发现和决策记录，并同步 `TASKS.md` 完成状态。

## 验证

- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `python scripts/validate_agents_docs.py --level ERROR`
- `python scripts/validate_agents_docs.py --level WARN`
- `TASKS.md` Phase 2.3 状态一致性检查
