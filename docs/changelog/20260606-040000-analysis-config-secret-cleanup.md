# Analysis 数据库配置敏感信息清理

> 日期：2026-06-06
> 类型：security, config, test, docs

## 变更

- 将 `analysis/config/analysis_config.json` 中的真实数据库连接改为 `ANALYSIS_DB_*` 环境变量占位符，数据库密码不提供默认值。
- 新增 `analysis/.env.example`，说明本地 analysis 数据库连接所需环境变量。
- 新增 `analysis/src/core/database_config.py`，统一解析 `${ENV}` 与 `${ENV:-default}` 占位符，并集中构造 MySQL SQLAlchemy URL。
- 将 `BrandAnalyzer`、`mention_status`、`reference_status`、`import_mention_data` 和旧导出脚本切换到共享数据库配置解析器。
- 新增 `analysis/tests/test_database_config.py`，防止版本化 analysis 配置重新写入真实连接值。
- 更新 analysis README、SECURITY、architecture diagnosis 和 tech debt tracker，明确真实凭据只允许通过环境变量、未跟踪 `.env` 或密钥管理器注入。
- 更新 active ExecPlan 和 `TASKS.md` 的 Phase 2.4 状态。

## 验证

- `$env:PYTHONPATH='analysis'; api\.venv\Scripts\python.exe -m pytest analysis\tests\test_database_config.py -q`
- `uv run --with pytest --with requests --with sqlalchemy --with pymysql --python 3.13 python -m pytest analysis\tests\test_database_config.py analysis\tests\test_reference_status.py analysis\tests\test_import_data.py analysis\tests\test_save_plugin_batch_result.py -q`
- `uv run --with ruff --python 3.13 ruff check analysis\src\core\database_config.py analysis\src\analyzer.py analysis\src\plugins\metrics\mention_status.py analysis\src\plugins\metrics\reference_status.py analysis\src\plugins\utils\import_mention_data.py analysis\tests\test_database_config.py analysis\tests\export_brands_found.py`
- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- 固定字符串搜索确认旧本地数据库 host 不再出现在 `analysis`、`api`、`docs`。
- 固定字符串搜索确认旧明文数据库密码字段不再出现在 `analysis`、`api`、`docs`。
- `python scripts/validate_agents_docs.py --level ERROR`
- `python scripts/validate_agents_docs.py --level WARN`
