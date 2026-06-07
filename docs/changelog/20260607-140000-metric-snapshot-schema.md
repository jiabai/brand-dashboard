# Phase 6.1 指标快照模型

## 背景

Phase 5 已经将采集批次、分析运行、插件事实和失败重试串入系统生命周期。Phase 6 开始建设 dashboard read model，本阶段先新增 `metric_snapshots` 表，让后续指标生成和 dashboard 迁移有稳定落点。

## 变更

- 新增 `metric_snapshots` MySQL/SQLite schema，并同步 `analysis/database` 镜像 schema。
- 新增 MySQL 迁移脚本 `api/database/migrations/20260607_add_metric_snapshots.mysql.sql`。
- 快照字段覆盖指标名、指标值、业务日期、品牌、平台、关键词、指标口径版本、analysis run 血缘、覆盖率和生成水位。
- 使用 `dimension_hash` 支撑幂等唯一键，避免 MySQL 长 varchar 复合索引超限。
- 新增 `api/tests/test_metric_snapshot_schema.py`，验证 schema、SQLite 外键/唯一键和迁移脚本。

## 边界

- 本阶段不生成指标快照。
- 本阶段不改造 dashboard 查询。
- Phase 6.2 负责指标口径和快照生成，Phase 6.3 再迁移 dashboard 到快照优先读取。

## 验证

- 定向 schema 测试已覆盖 `metric_snapshots`。
- 完整验证结果记录在 active ExecPlan 的 Validation and Acceptance 中。
