# Phase 3.1 监测项目数据模型落地
> 日期：2026-06-07
> 类型：schema, docs, architecture

## 变更

- 新增 `api/tests/test_monitoring_project_schema.py`，用 schema 测试约束监测项目、项目品牌、问题集和问题项四张表。
- 在 `api/database/schema.sql`、`api/database/schema_business.sql`、`analysis/database/schema.sql`、`analysis/database/schema_business.sql` 和 `api/database/schema_sqlite.sql` 中新增 `monitoring_projects`、`project_brands`、`prompt_sets`、`prompt_items`。
- 新增 MySQL 迁移脚本 `api/database/migrations/20260607_add_monitoring_project_model.mysql.sql`。
- 更新领域模型参考、数据库 README、active ExecPlan 和 `TASKS.md`，记录 Phase 3.1 的唯一键、复合外键和生命周期边界。

## 验证

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api\tests\test_monitoring_project_schema.py -q`
- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `python scripts/validate_agents_docs.py --level ERROR`
- `python scripts/validate_agents_docs.py --level WARN`
