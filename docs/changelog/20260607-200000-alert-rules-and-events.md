# Phase 7.3 告警规则与告警事件

## 背景

Phase 6 已经把 dashboard 核心指标沉淀为 `metric_snapshots`，Phase 7.1/7.2 又补齐了问答快照和真实情感分析读面。为了让品牌监测系统从“看指标”进入“发现异常并形成业务动作”，Phase 7.3 新增项目级告警规则和告警事件。

## 本次变更

- 新增 `alert_rules` 和 `alert_events` 表，并提供 MySQL 迁移脚本。
- 新增告警仓储和评估服务，支持从 `metric_snapshots` 比较同一维度的前后两次指标变化。
- 支持 `metric_drop`、`metric_rise`、`metric_change` 三类规则，覆盖提及率下降、负面情绪上升和信源引用率变化。
- 新增 `GET /api/v1/projects/{project_id}/alerts`，按当前租户读取项目告警规则和事件。
- 新增 `api/tests/test_alert_rules.py`，覆盖 schema、触发逻辑、幂等去重和租户隔离读取。

## 设计约束

- 告警事件必须绑定 `tenant_key`、`project_id`、`analysis_run_id` 和 `collection_job_id`，避免脱离数据生命周期。
- 事件去重使用 `(tenant_key, alert_rule_id, analysis_run_id, metric_date, dimension_hash)`，重复评估不会产生重复告警。
- 本阶段只落后端 MVP 和项目读面，不新增前端告警页；后续报告和项目页可直接消费该 API。

## 验证

- 定向测试：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_alert_rules.py -q`
