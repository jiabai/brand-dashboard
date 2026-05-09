# Project Workflow

## Purpose

本文件定义项目默认工作流。目标是让非平凡改动先形成可审查的意图和计划，再进入实现。

## Mandatory Rule

除非任务是低风险、小范围、无新边界的轻量改动，否则按以下流程推进：

1. Constitution and context
2. Spec
3. Technical plan
4. Task breakdown
5. Implementation and validation

## Constitution

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/DESIGN.md`（如存在）
- `docs/SECURITY.md`（如存在）

## Spec

当任务改变用户可见行为、新增边界、影响认证/权限/数据/部署/安全时，在 `docs/product-specs/` 创建或更新 spec。

## Plan

非平凡任务在 `docs/exec-plans/active/` 创建 ExecPlan，并在计划确认后实现。

## Lightweight Path

轻量任务可以直接实现，但仍需 inspect、最小验证、必要文档同步和最终验证说明。

轻量路径条件（必须同时满足所有）：
- 低风险：不影响认证、权限、数据安全或核心功能
- 改动范围小：只修改单个模块或目录
- 无新边界：不新增产品、架构、数据、部署或安全边界
- 时间可控：预估 30 分钟内完成

## File Placement

- 用户意图：`docs/product-specs/`
- 设计决策：`docs/design-docs/`
- 外部参考：`docs/references/`
- 进行中计划：`docs/exec-plans/active/`
- 完成计划：`docs/exec-plans/completed/`
- 技术债：`docs/exec-plans/tech-debt-tracker.md`

## Coding Conventions

- 前端：函数组件 + hooks，PascalCase 组件名，camelCase 变量，2 空格缩进，ES modules
- 后端：类型注解，小路由/处理器，复用 `api/v1/models/schemas.py` 的 Pydantic 模型
- 样式：优先 Tailwind 工具类，自定义 CSS 放 `web/src/styles/`
- 提交：Conventional Commits，每次提交更新 `agents_chat/` 记录
