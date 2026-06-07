# Phase 6.2 指标快照生成

## 背景

Phase 6.1 已经新增 `metric_snapshots` 读模型。本阶段补齐从成功 `analysis_run` 生成品牌指标快照的内部能力，让后续 dashboard 迁移可以读取可版本化、可追溯、可幂等重算的指标。

## 变更

- 新增 `api/v1/services/metric_snapshots.py`，提供 `generate_metric_snapshots_for_analysis_run` 内部入口。
- 新增 `api/v1/repositories/metric_snapshots.py`，按当前 session 方言执行 SQLite/MySQL upsert。
- 固定首版 `brand_metrics_v1` 口径，覆盖提及率、首位提及率、Top3 提及率、正/负/中性/未知情绪占比和信源引用率。
- 快照只接受 `status='succeeded'` 的 analysis run，所有查询均带 `tenant_key` 和 `analysis_run_id`。
- 快照写入携带 `metric_definition_version`、`analysis_run_id`、采集覆盖计数、`coverage_rate`、`source_watermark` 和稳定 `dimension_hash`。
- 新增 `api/tests/test_metric_snapshot_generation.py`，验证指标口径、失败 run 拒绝和重复生成幂等性。

## 边界

- 本阶段不迁移 dashboard 查询；Phase 6.3 再实现快照优先读取和旧明细聚合兼容。
- `reference_rate` 表达“回答是否存在任意信源引用”，不等同于依赖 `is_published_link` 的发稿链接覆盖率。
- 当前生成粒度为 `(metric_date, brand, platform, keyword)`；全品牌/全平台/全关键词汇总可在后续按 dashboard 需要扩展。

## 验证

- 定向指标快照生成测试已通过。
- 完整后端、文档和 diff 验证结果记录在 active ExecPlan 的 Validation and Acceptance 中。
