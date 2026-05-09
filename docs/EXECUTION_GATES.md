# Execution Gates

## Purpose

本文件定义任务完成前必须满足的检查。验证应与风险成比例，并在最终交付中可见。

## Hard Gates

- 受影响代码路径或文档事实来源已 inspect
- 受影响区域的最小有效测试或检查通过
- 文档结构验证通过：`python scripts/validate_agents_docs.py --level ERROR`
- touched active ExecPlan 的 Progress、Decision Log 和验证记录已更新
- 架构、安全、流程、运行时 contract 或运维行为变化已同步到 durable docs

## Soft Gates

- 更广范围回归测试
- 手动运行时检查（浏览器验证 UI 渲染）
- 依赖或安全扫描
- 覆盖率报告

跳过相关软门禁时，在最终说明或 active ExecPlan 中记录原因和残余风险。

## Definition Of Done

1. 请求行为已实现、修复，或明确记录为 out of scope
2. 所有受影响区域的硬门禁通过
3. 相关 spec、design doc、reference、AGENTS map 或 ExecPlan 已同步
4. 新技术债已记录到 active plan 或 `docs/exec-plans/tech-debt-tracker.md`
5. 最终交付列出 Passed、Not run 和 Residual risk

## 项目特定验证

| 区域 | 验证方式 | 命令 |
|------|---------|------|
| 后端代码风格 | ruff 检查 | `ruff check api` |
| 前端构建 | Vite 构建 | `npm --prefix web run build` |
| 前端测试 | Vitest/Node test | `npm --prefix web test` |
| 后端测试 | pytest | `pytest api/tests/` |
| 文档结构 | 验证脚本 | `python scripts/validate_agents_docs.py --level ERROR` |
| API 健康 | HTTP 请求 | `curl localhost:8000/api/v1/health` 返回 200 |
| 前端渲染 | 浏览器访问 | `localhost:3000` 仪表板正常加载 |
