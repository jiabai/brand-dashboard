# 移除指标快照 ExecPlan

## 目标

把当前分支从“指标快照 read model”调整为“基于分析事实表实时聚合”。移除 `metric_snapshots` schema、迁移、生成服务、仓储读取、前端展示和相关测试，避免生产上线后出现快照缺失、失效或重算策略不清导致的数据问题。

## 范围

- 更新设计文档、架构文档、API 字典、数据库字典和变更记录。
- 删除 `metric_snapshots` 表定义、迁移脚本、生成服务和仓储。
- Dashboard、筛选元数据、情感分析、报告、告警、数据质量改为读取事实表。
- 前端移除指标快照质量面板与快照来源文案。
- 删除或改写快照专属测试，新增事实聚合路径回归测试。

## 非目标

- 不新增缓存层、异步 read model 或后台重算任务。
- 不重做旧 dashboard 路由收敛。
- 不删除 `alert_rules`、`alert_events`、`generated_reports`。
- 不改动用户认证、执行器认证和平台后台权限模型。

## 实施结果

1. 文档先行：新增去快照设计决策、ExecPlan、changelog，并更新核心架构、设计、安全、API 字典和数据库字典。
2. 测试先行：新增运行时扫描测试，删除快照 schema/generation/priority 专属测试，改写 dashboard metadata、情感分析、报告、告警和数据质量测试。
3. 后端实现：删除 `metric_snapshots` 服务、仓储、schema 和迁移，新增事实指标聚合仓储 `fact_metrics.py`。
4. 前端实现：删除快照 metadata 工具和质量面板，展示改为基于分析事实 API。
5. 收尾清理：活动计划归档，临时 `TASKS.md` 删除。

## 决策记录

| 决策 | 原因 |
|------|------|
| 直接移除 `metric_snapshots` | 本分支未生产发布，保留半成品 read model 会增加上线数据风险。 |
| 保留 `brand_metrics_v1` | 指标口径仍需要版本名，但版本指向事实聚合路径，不再指向快照表。 |
| 告警继续保留事件表 | 告警事件是业务结果，输入来源变化不影响事件持久化价值。 |
| 报告继续持久化 JSON | 报告需要生成时冻结结果，`generated_reports` 可以承担该职责。 |

## 验证记录

- `rg -n "metric_snapshots|metric_snapshot|snapshot_status|metricSnapshot|MetricSnapshot|SnapshotQuality" api\v1 api\database analysis\database web\src`：无运行时残留。
- `uv run --project api ruff check api`：通过。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：158 passed。
- `npm --prefix web test`：87 passed。
- `npm --prefix web run lint`：0 errors，8 个既有 warnings。
- `npm --prefix web run build`：通过。
- `git diff --check`：通过，仅有 CRLF 提示。
