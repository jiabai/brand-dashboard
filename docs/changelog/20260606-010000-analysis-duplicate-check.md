# 分析明细重复风险检查

> 日期：2026-06-06
> 类型：test, docs

## 变更

- 新增只读脚本 `api/scripts/check_duplicate_analysis_rows.py`，用于盘点分析明细重复数据风险。
- 新增测试 `api/tests/test_analysis_duplicate_checks.py`，覆盖目标幂等键重复和旧唯一键跨 scope 碰撞。
- 脚本在数据库连接失败或必需表缺失时返回 `2`，避免执行门禁只看到 Python traceback。
- 更新领域参考、active ExecPlan 和 `TASKS.md`，记录 Phase 2.1 的交付和后续迁移门禁。

## 验证

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_analysis_duplicate_checks.py -q`
- `api\.venv\Scripts\python.exe api\scripts\check_duplicate_analysis_rows.py --limit 20`：本地 SQLite 缺少业务表，按预期返回 `2` 并输出清晰错误。
