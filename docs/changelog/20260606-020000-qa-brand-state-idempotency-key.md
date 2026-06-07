# qa_brand_state 幂等唯一键

> 日期：2026-06-06
> 类型：schema, test, docs

## 变更

- 为 `qa_brand_state` 增加兼容期唯一键 `uk_tenant_job_conv_brand`，支撑 `mention_status` 的 `ON DUPLICATE KEY UPDATE`。
- 新增 MySQL 迁移脚本 `api/database/migrations/20260606_add_qa_brand_state_idempotency_key.mysql.sql`，要求先运行 Phase 2.1 重复风险检查。
- 更新 API/analysis MySQL schema 与 SQLite schema，保持新建环境一致。
- 新增 `api/tests/test_qa_brand_state_idempotency_schema.py`，验证 schema 声明、SQLite upsert 幂等行为和迁移脚本内容。
- 更新 ExecPlan、领域参考和 `TASKS.md`。

## 验证

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_qa_brand_state_idempotency_schema.py -q`
