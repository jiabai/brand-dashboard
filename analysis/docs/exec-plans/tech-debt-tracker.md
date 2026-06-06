# Tech Debt Tracker

Last updated: 2026-05-11

## High Priority

| Topic | Why it matters | Source | Removal Condition |
|------|----------------|--------|-------------------|
| 配置样例与真实凭据分离 | 默认配置含数据库连接字段，容易混淆本地私有配置和可提交样例。 | `config/analysis_config.json`, `docs/SECURITY.md` | 提供 sample 配置或私有配置策略，默认提交文件不含真实凭据。 |

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
