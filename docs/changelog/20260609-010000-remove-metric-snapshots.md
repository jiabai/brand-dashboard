# 移除指标快照

## 变更内容

- 将当前分支的指标读取策略从 `metric_snapshots` 快照 read model 调整为基于 `qa_brand_state`、`qa_reference` 和 `analysis_runs` 的事实聚合。
- 移除指标快照 schema、迁移、生成服务、仓储、前端质量面板和快照专属测试。
- 报告、告警和数据质量保留业务结果表，但输入指标改为事实聚合。

## 背景

快照生成未接入分析主链路，也缺少失效和重算策略。继续上线会让 dashboard、报告、告警和数据质量出现事实数据与快照数据不一致的解释成本。本分支作为新设计，优先采用更简单的事实聚合链路。

## 验证

- `rg -n "metric_snapshots|metric_snapshot|snapshot_status|metricSnapshot|MetricSnapshot|SnapshotQuality" api\v1 api\database analysis\database web\src`：无运行时残留。
- `uv run --project api ruff check api`：通过。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：158 passed。
- `npm --prefix web test`：87 passed。
- `npm --prefix web run lint`：0 errors，8 个既有 warnings。
- `npm --prefix web run build`：通过。
- `git diff --check`：通过，仅有 CRLF 提示。
