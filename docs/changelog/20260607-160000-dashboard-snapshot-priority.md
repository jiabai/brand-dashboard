# Phase 6.3 Dashboard 快照优先读取

## 背景

Phase 6.2 已能从成功的 analysis run 生成 `brand_metrics_v1` 指标快照。本阶段将 dashboard 的品牌提及类读取面迁移到快照优先，降低 dashboard 对分析明细表实时聚合的依赖。

## 变更

- 扩展 `api/v1/repositories/metric_snapshots.py`，新增 dashboard 读取所需的快照查询函数。
- `query_brand_metrics`、`query_brand_platform_keyword_daily_mention_rates`、`query_platform_metrics_by_brand` 和 `query_keyword_platform_brand_rates` 先读取 `metric_snapshots`，缺失时继续执行旧 `qa_brand_state` 聚合。
- 快照查询通过 `analysis_runs.collection_job_id` 或 `collection_jobs.source_job_id` 兼容新采集批次 ID 与旧 dashboard `job_id`。
- 新增 `api/tests/test_dashboard_metric_snapshot_priority.py`，覆盖品牌总指标、日趋势、平台指标、关键词-平台-品牌表格的快照优先读取，以及无快照时旧明细兜底。

## 边界

- 本阶段不改前端响应结构和页面展示。
- `platform-mention-rates` 暂不迁移，因为现有接口仍需要 category 维度。
- 引用域名、引用类型、URL 引用和发稿链接覆盖率仍读旧引用明细，等待后续更细粒度引用快照或新口径版本。

## 验证

- 新增快照优先定向测试已通过。
- 旧 dashboard 回归测试已通过。
- 完整验证结果记录在 active ExecPlan 的 Validation and Acceptance 中。
