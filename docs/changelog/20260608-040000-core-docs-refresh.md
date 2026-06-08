# Phase 8.2 核心文档更新

## 变更内容

- 重写 `docs/ARCHITECTURE.md`，把系统主线更新为监测项目、采集生命周期、分析运行、指标快照、告警、报告和数据质量。
- 重写 `docs/DESIGN.md`，同步项目优先导航、legacy 路由、项目 API、指标快照和前端状态管理规范。
- 重写 `docs/SECURITY.md`，补充项目 API、数据质量、报告、analysis retry 和 legacy dashboard 的安全边界。
- 重写 README，更新项目定位、功能列表、目录结构、环境变量、API 概览和前端入口说明。

## 边界说明

本阶段只更新核心入口文档，不迁移 ExecPlan，也不删除 `TASKS.md`。详细领域模型、兼容策略和逐阶段验证仍以 `docs/references/20260606-brand-monitoring-domain-data-reference.md` 和 active ExecPlan 为准。

## 验证

- `python scripts/validate_agents_docs.py --level ERROR` 通过，0 错误。
- `python scripts/validate_agents_docs.py --level WARN` 通过，0 警告。
- 核心文档陈旧表述搜索未再发现旧 dashboard/job 作为主线的表述，仅保留 README 中旧任务兼容环境变量说明。
- `git diff --check` 通过，仅输出既有 LF/CRLF 换行提示。
