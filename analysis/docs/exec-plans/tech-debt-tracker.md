# Tech Debt Tracker

Last updated: 2026-06-06

## High Priority

| Topic | Why it matters | Source | Removal Condition |
|------|----------------|--------|-------------------|
| 暂无 | - | - | - |

## Medium Priority

| Topic | Why it matters | Source | Removal Condition |
|------|----------------|--------|-------------------|
| 打包入口与实际包结构不一致 | `pyproject.toml` 的 script 指向 `brand_analysis.analyzer:main`，当前运行入口是 `python -m src`。 | `pyproject.toml`, `src/__main__.py` | entry point、包名和安装后命令均验证通过。 |
| 真实 provider 测试隔离不足 | `tests/*_test.py` 可能依赖网络或密钥，默认测试环境风险不清晰。 | `tests/` | 测试标记区分 unit/integration/manual，并在 CI 或 README 中说明。 |

## Low Priority

| Topic | Why it matters | Source | Removal Condition |
|------|----------------|--------|-------------------|
| `src/analyzer.py` 职责偏多 | 配置、数据库、批处理、CLI 和输出保存集中在单文件，后续扩展测试成本会上升。 | `src/analyzer.py` | 拆分出可独立测试的配置、数据访问或输出组件，public 行为保持兼容。 |

## Debt Handling Rules

- Add debt here only when it spans more than one file or more than one task.
- Remove or downgrade debt when a change clearly addresses it.
- Link back to the plan, design doc or code path that best explains the issue.

## Resolved

| Topic | Resolution | Date |
|------|------------|------|
| 配置样例与真实凭据分离 | `config/analysis_config.json` 已改为 `ANALYSIS_DB_*` 环境变量占位符，新增 `.env.example`，并由 `tests/test_database_config.py` 防止真实连接信息重新进入版本化配置。 | 2026-06-06 |
