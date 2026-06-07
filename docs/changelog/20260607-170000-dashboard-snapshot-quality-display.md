# Phase 6.4 Dashboard 快照质量展示

## 背景

Phase 6.3 已让品牌提及类 dashboard 查询优先读取 `metric_snapshots`。本阶段将快照新鲜度、采集覆盖率和分析完整性透出给前端，帮助用户判断当前看板数据是否可信。

## 变更

- `brand-metrics` 响应 metadata 新增 `data_source`、`snapshot_status`、`metric_generated_at`、`metric_coverage_rate`、采集任务计数和分析回答数等字段。
- 新增 `DashboardService.get_metric_snapshot_metadata` 与 `query_snapshot_quality_metadata`，按最新 succeeded analysis run 聚合当前时间窗口的快照质量信息。
- `BrandMentionRate` 增加指标质量面板，展示指标生成时间、采集覆盖、分析完整性和分析回答数。
- 新增前端 metadata 归一化工具，缺快照时展示“明细聚合”“快照未生成”和“覆盖率待生成”。
- 空状态文案改为提示当前筛选下无品牌指标，若刚完成采集需等待分析和指标快照生成。

## 边界

- 本阶段不改变 `brand-metrics.data` 的品牌指标结构。
- 快照质量展示先接入首页品牌提及卡片；独立数据质量页留到 Phase 7.5。
- 引用域名、引用 URL、引用类型和发稿链接覆盖率仍按旧明细读取，不在本阶段展示快照质量。

## 验证

- 后端新增快照质量 metadata 定向测试。
- 前端新增 metadata 归一化与展示契约测试。
- 完整验证结果记录在 active ExecPlan 的 Validation and Acceptance 中。
