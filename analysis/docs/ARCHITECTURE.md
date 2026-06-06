# Architecture

## 概述

Brand Analysis 是一个 Python CLI/库式工具，用于从 MySQL 数据源读取问答或引用数据，通过插件体系和统一 LLM 适配层生成品牌认知、引用状态、来源识别等分析结果。

主流程是：CLI 参数和 JSON 配置 -> `BrandAnalyzer` -> `PluginManager` -> 分析插件 -> JSON 输出和可选 MySQL UPSERT。

## 代码地图

| 区域 | 职责 |
|------|------|
| `src/__main__.py` | `python -m src` 入口，委托 `src.analyzer.main`。 |
| `src/analyzer.py` | 配置加载、CLI 参数解析、数据表读取、批次分组、插件调用、结果聚合和输出保存。 |
| `src/core/plugin_interface.py` | `AnalysisPlugin` 合同、插件注册表、默认聚合逻辑。 |
| `src/core/plugin_manager.py` | 动态发现插件、按配置启用插件、注入全局配置和插件配置。 |
| `src/core/llm_operator.py`、`src/core/*_adapter.py` | 多供应商 LLM 调用适配层。 |
| `src/business_services/llm_brand_recognizer.py` | 面向品牌识别的 LLM 业务服务。 |
| `src/plugins/metrics/` | 面向指标结果的分析插件，如 `mention_status`、`reference_status`。 |
| `src/plugins/utils/` | 工具类插件，如 LLM ping、URL 来源提取、结果导入。 |
| `config/` | 分析流程、插件、数据库和 LLM provider 配置。 |
| `database/` | MySQL schema 和业务表定义。 |
| `tests/` | 单元测试、集成风格测试、重构验证脚本和 LLM 连接示例。 |
| `output/` | 运行时生成的插件结果目录，默认不应作为规范事实来源。 |

## 模块关系

```text
CLI
  -> BrandAnalyzer
    -> PluginManager
      -> PluginRegistry
      -> AnalysisPlugin implementations
    -> LLMBrandRecognizer
      -> LLMOperator / adapters
    -> SQLAlchemy engine
    -> output JSON files
```

插件不应直接控制 CLI 生命周期。插件可以读取被注入的 `app_config` 和 `plugin_config`，但应通过 `analyze` 和 `aggregate_results` 返回结果，由 `BrandAnalyzer` 统一保存、聚合或写库。

## 关键文件

- `README.md`：用户安装、运行、配置和插件开发说明。
- `config/analysis_config.json`：当前默认运行配置，包含插件启用状态、数据源字段、输出路径和 LLM 基础参数。
- `config/llm_providers.json`：LLM provider 默认参数、能力和监控配置。
- `database/schema*.sql`：数据库结构来源。
- `docs/references/`：指标、插件和 LLM 组件的详细参考资料。
- `pyproject.toml`：打包元数据、测试、格式、类型检查和安全扫描配置。

## 架构不变量

- `BrandAnalyzer` 是批处理编排层；插件只负责单条文本分析和结果聚合，不负责遍历数据表。
- 新插件必须实现 `AnalysisPlugin`，使用 `PluginRegistry.register` 注册，并在配置中声明启用状态和数据源。
- 表名和字段来自配置时必须校验，不能拼接未经验证的 SQL 标识符。
- LLM 配置优先从配置文件读取，缺失或占位时可由环境变量补全；API Key 不应硬编码到代码。
- 输出目录结构保持 `output/<plugin_name>/<YYYYMMDD>/`，缺失 `generated_date` 时使用 `unknown_date`。

## 层级边界

- CLI 层只解析用户输入并返回进程退出码。
- 编排层负责配置、数据批次和插件调度。
- 插件层只依赖核心接口和必要业务服务，不反向导入 CLI。
- LLM 适配层隔离供应商差异，业务代码不直接拼供应商 SDK 细节。
- 数据库 schema 和写入语义改变时，同步 `database/`、README、产品规格和安全文档。

## 横切关注点

- 日志使用标准 `logging`，错误应包含插件名、表名或 provider 等定位信息。
- 外部资源包括 MySQL、LLM HTTP API、文件系统输出和环境变量。
- 测试默认使用 `pytest`；网络、真实 LLM、真实数据库测试应显式标记或隔离。
- 文档规范通过 `python scripts/validate_agents_docs.py --level ERROR` 验证。
