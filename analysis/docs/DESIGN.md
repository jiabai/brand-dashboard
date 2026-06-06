# Design Standards

## Purpose

本文件记录长期有效的代码、配置和接口设计规范。产品目标和用户可见范围放在 `docs/product-specs/`，实施计划放在 `docs/exec-plans/`。

## Plugin Contract

- 插件必须继承 `AnalysisPlugin`，实现 `name`、`description`、`analyze`。
- 插件通过 `PluginRegistry.register` 声明类型、LLM 需求和默认启用状态。
- 插件需要配置时实现 `set_app_config(app_config, plugin_config)` 或使用注入的同名属性。
- 单条分析结果应是可 JSON 序列化的 dict；批量汇总放在 `aggregate_results`。
- 插件内部不要直接终止进程或保存最终批量文件，统一交给编排层处理。

## Configuration Shape

- 根对象使用 `brand_analysis`。
- `plugins.<plugin_name>.enabled` 必须是 bool。
- 插件数据源优先使用 `datasources: [{ table, fields }]`，兼容单 `table`。
- 表名只允许字母、数字和下划线；字段名由代码和数据库 inspector 共同过滤。
- LLM provider 配置应保持 `provider`、`apiKey`、`baseURL`、`model`、`timeout`、`maxRetries`、`maxTokens` 的兼容映射。

## Data And Output Shape

- 输入行优先组合 `query_content` 和 `answer_content`。
- 缺少问答字段时，按 `text/content/message/answer` 降级，最后才序列化整行。
- 批次目录来自 `generated_date` 的 `YYYYMMDD`；缺失时写入 `unknown_date`。
- 输出文件结构保持 `brand_name`、`plugin_name`、`analysis_timestamp`、`date_directory`、`data`。
- 数据库写入必须保持幂等语义，使用稳定业务键避免重复结果。

## Error Handling

- 配置错误在启动或初始化阶段尽早失败。
- 单插件分析失败应记录插件名并返回结构化错误，不吞掉批次上下文。
- 外部服务不可用时优先给出可定位的错误或降级路径。
- 日志不得输出 API Key、数据库密码或完整敏感连接串。

## Code Style

- Python 代码按 `pyproject.toml` 中 black、isort、pytest、mypy 配置维护。
- 新代码优先使用类型注解和小函数，避免把新的业务分支继续塞进超长编排函数。
- 测试中真实网络或真实数据库依赖要显式隔离，默认测试应可离线运行。
