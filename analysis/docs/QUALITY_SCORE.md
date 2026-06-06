# Quality Score

Last updated: 2026-05-11

## Scoring Key

- Green: 清晰、可测试、文档和边界基本完整。
- Yellow: 可用但存在可维护性、验证或文档风险。
- Red: 当前不应扩展，需先修复基础问题。

## Module Score

| 模块 | 可维护性 | 测试覆盖 | 文档完整度 | 综合 | 说明 |
|------|----------|----------|------------|------|------|
| `src/analyzer.py` | Yellow | Yellow | Green | Yellow | 编排能力完整，但文件承担配置、CLI、数据库、批处理和输出多重职责。 |
| `src/core/` | Yellow | Yellow | Green | Yellow | 插件和 LLM 适配边界清楚，仍需保持 provider 兼容测试。 |
| `src/plugins/metrics/` | Green | Yellow | Yellow | Yellow | 插件职责明确，新增指标时需要加强每个插件的输入/聚合测试。 |
| `src/plugins/utils/` | Yellow | Yellow | Yellow | Yellow | 工具插件覆盖运行诊断、来源提取和导入，真实 IO 风险需隔离。 |
| `config/` | Yellow | Red | Yellow | Yellow | 配置结构集中，但本地凭据和样例配置边界需要收紧。 |
| `database/` | Yellow | Yellow | Yellow | Yellow | schema 有来源文件，迁移策略和写入幂等测试需补强。 |
| `tests/` | Yellow | Yellow | Yellow | Yellow | 测试入口较多，需区分离线单测、集成测试和真实 provider smoke test。 |
| `docs/` | Green | N/A | Green | Green | 已补齐协作规范、架构、安全、规格和门禁入口。 |

## Improvement Priorities

| 优先级 | 主题 | 完成条件 |
|--------|------|----------|
| High | 配置样例与真实凭据分离 | 默认配置不携带真实密码，README 说明环境变量或私有配置方式。 |
| Medium | 打包入口与实际包结构修正 | 包名、entry point 与当前 `src` 导入方式一致，并通过安装后命令验证。 |
| Medium | 插件 focused tests | 每个核心插件至少有离线 analyze 和 aggregate 测试。 |
| Low | 编排层拆分 | 数据库读取、批处理、输出保存可独立测试且不扩大 public contract。 |
