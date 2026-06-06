# Brand Analysis AI Collaboration Rules

<!-- 由 vibe-coding-launcher 生成。修改长期规范时，同步更新相关 docs/ 文档。 -->

## 快速入口

- 架构：见 `docs/ARCHITECTURE.md`
- 核心信念：见 `docs/design-docs/core-beliefs.md`
- 设计规范：见 `docs/DESIGN.md`
- 安全规范：见 `docs/SECURITY.md`
- 工作流：见 `WORKFLOW.md`
- 完成门禁：见 `docs/EXECUTION_GATES.md`
- 产品规格：见 `docs/product-specs/index.md`
- 执行计划：见 `docs/exec-plans/index.md`
- 技术参考：见 `docs/references/index.md`
- 质量追踪：见 `docs/QUALITY_SCORE.md`

## 核心信念

- 配置驱动优先：插件启用、数据源、输出路径和 LLM 参数应从 `config/` 读取，不把业务参数散落在代码里。
- 插件边界稳定：新增指标优先实现 `AnalysisPlugin` 并通过 `PluginRegistry` 注册，不绕过 `PluginManager`。
- 外部依赖可降级：LLM、MySQL、文件输出等边界失败时应返回可诊断错误，插件内部避免让批处理整体无声失败。
- 数据形状先验证：来自 MySQL、JSON 配置、CLI 参数和 LLM 的输入都必须在边界处校验或归一化。
- 规范跟代码同步：改动插件合同、配置结构、数据库写入或 CLI 行为时，更新架构、产品规格或安全文档。

## 开发流程

非平凡改动走 `WORKFLOW.md` 的 Constitution -> Spec -> Plan -> Tasks -> Implementation 流程。轻量修复也要先 inspect 相关路径，再运行最小有效验证并在最终说明中列出验证结果。

## 约束机制

- 模式：`linter+agents`
- 配置：`pyproject.toml`

## 常用命令

- `pip install -r requirements.txt` — 安装运行依赖。
- `pip install -e ".[dev]"` — 安装开发依赖。
- `python -m src --help` — 检查 CLI 入口。
- `python -m src -b "海尔" -c .\config\analysis_config.json` — 运行品牌分析。
- `pytest` — 运行测试套件。
- `black --check src tests` — 检查格式。
- `isort --check-only src tests` — 检查 import 排序。
- `mypy src` — 运行类型检查，遵循 `pyproject.toml` 的模块覆盖配置。
- `python scripts/validate_agents_docs.py --level ERROR` — 验证协作文档硬门禁。
