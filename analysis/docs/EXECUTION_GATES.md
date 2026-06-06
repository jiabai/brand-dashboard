# Execution Gates

## Purpose

本文件定义 Brand Analysis 任务完成前必须满足的检查。验证深度按风险调整，但最终交付必须透明说明已验证项、未运行项和残余风险。

## Hard Gates

- 已 inspect 受影响代码路径、配置文件、数据库 schema 或文档事实来源。
- 受影响区域的最小有效测试或检查通过。
- 文档结构验证通过：`python scripts/validate_agents_docs.py --level ERROR`。
- 如果触碰 active ExecPlan，其 `Progress`、`Decision Log`、验证记录和遗留风险已更新。
- 改动插件合同、配置结构、数据库写入、安全边界、CLI 参数或输出 JSON 时，已同步 durable docs。

## Area Gates

| 改动范围 | 最小验证 |
|----------|----------|
| 文档/规范 | `python scripts/validate_agents_docs.py --level ERROR` |
| CLI 参数或入口 | `python -m src --help`，必要时运行目标 CLI 命令 |
| 插件分析逻辑 | 对应插件测试，至少运行相关 `pytest tests/test_*.py` |
| LLM provider 或 LLMOperator | mock 测试优先；真实 provider 测试需显式记录密钥和网络依赖未暴露 |
| MySQL 读取/写入 | focused 测试或本地数据库验证，并记录 schema 假设 |
| 配置结构 | 配置加载测试和 README/产品规格同步 |
| 安全相关 | 检查密钥、SQL 标识符、外部输入和日志泄露风险 |

## Soft Gates

- 全量 `pytest`。
- `black --check src tests` 和 `isort --check-only src tests`。
- `mypy src`。
- `bandit -r src -f json`。
- 对真实数据库或真实 LLM 的手动 smoke test。

跳过软门禁时，在最终说明或 ExecPlan 中写明原因。

## Definition Of Done

1. 用户请求行为已实现、修复，或明确记录为 out of scope。
2. 所有受影响区域的硬门禁通过。
3. 相关 spec、architecture、security、design、AGENTS map 或 ExecPlan 已同步。
4. 新技术债已记录到 active plan 或 `docs/exec-plans/tech-debt-tracker.md`。
5. 最终交付包含 Passed、Not run 和 Residual risk。
