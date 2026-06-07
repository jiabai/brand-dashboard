# Phase 5.3 分析失败可观测与重试

## 背景

Phase 5.2 已经可以运行分析插件并写入带 `analysis_run_id` 的事实表，但失败运行仍缺少系统入口供用户或内部流程查看原因、触发重试。Phase 5.3 补齐这条链路，并为后续指标快照生成明确失败隔离规则。

## 变更

- 新增 `GET /api/v1/analysis-runs/{analysis_run_id}`，当前租户成员可查看分析运行状态、输入水位、错误编码、错误信息和是否可重试。
- 新增 `POST /api/v1/analysis-runs/{analysis_run_id}/retry`，当前租户 admin 可对 failed/stale run 触发重试。
- `analysis_runner.retry_analysis_run` 会为同一采集批次创建新的 analysis run，不覆盖原失败 run 的错误原因。
- retry 成功后，兼容期事实表通过 upsert 把同一事实键重新绑定到新的 succeeded run，减少失败 run 残留事实对后续读取面的影响。
- `analysis_runs` Repository 新增 succeeded-only 快照候选查询，Phase 6 生成指标快照时不应使用 failed/stale/pending/running run。

## 边界

- retry API 当前同步执行分析插件；后续如插件耗时过长，应改为后台 worker 异步执行。
- succeeded run 不允许通过 retry API 重跑，避免覆盖已经稳定的输出。
- 本阶段不新增前端页面，只提供 API 和内部服务能力。

## 验证

- 已新增 API、retry service 和快照候选测试。
- 完整验证结果记录在 active ExecPlan 的 Validation and Acceptance 中。
