# Project Workflow

## Purpose

本文件定义 Brand Analysis 项目的默认协作流程。目标是让需求、架构边界、验证和交付状态在进入实现前可审查、可恢复。

## Mandatory Rule

除非任务同时满足低风险、小范围、无新边界、无运行时 contract 变化、30 分钟内可完成，否则按以下流程推进：

1. Constitution and context
2. Spec
3. Technical plan
4. Task breakdown
5. Implementation and validation

## Constitution

开始非平凡任务前先读：

- `AGENTS.md`
- `docs/design-docs/core-beliefs.md`
- `docs/ARCHITECTURE.md`
- `docs/DESIGN.md`
- `docs/SECURITY.md`
- 相关功能文档，如 `docs/references/unified-llm-operator.md`、`docs/references/metrics-analysis.md`

## Spec

以下改动需要在 `docs/product-specs/` 创建或更新规格：

- 改变 CLI 参数、配置结构、输出 JSON 结构或数据库写入语义。
- 新增或重写分析插件、LLM provider、数据源类型或批处理模式。
- 影响 API Key、数据库连接、持久化、幂等写入或数据安全边界。
- 改变用户可见的统计口径、错误语义或结果解释。

## Plan

非平凡任务在 `docs/exec-plans/active/` 创建 ExecPlan。计划必须说明：

- 触碰的文件和模块边界。
- 实施顺序与回滚/兼容策略。
- 最小验证命令和可观察结果。
- 需要同步的 durable docs。

## Lightweight Path

轻量任务可以直接实现，但仍需：

- inspect 受影响代码或文档事实来源。
- 做最小范围改动。
- 运行相关 focused validation。
- 需要时同步 `AGENTS.md`、架构、安全或产品规格。

## File Placement

- 用户可见意图：`docs/product-specs/`
- 长期设计决策：`docs/design-docs/`
- 外部资料和接口参考：`docs/references/`
- 进行中计划：`docs/exec-plans/active/`
- 已完成或废弃计划：`docs/exec-plans/completed/`
- 跨任务技术债：`docs/exec-plans/tech-debt-tracker.md`
- 临时恢复清单：`TASKS.md`
