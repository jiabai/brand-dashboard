# Phase 7.4 报告生成基础能力

## 变更内容

- 新增 `generated_reports` 报告结果 read model，并同步更新 MySQL、SQLite schema 和 MySQL 迁移脚本。
- 新增项目报告生成与列表读取后端能力：
  - `POST /api/v1/projects/{project_id}/reports`
  - `GET /api/v1/projects/{project_id}/reports`
- 报告生成从 `metric_snapshots` 读取核心指标，从 `alert_events` 读取同窗口告警摘要，并将时间窗口、指标 JSON、告警 JSON 和生成者写入持久化结果。
- 新增 `api/tests/test_project_reports.py`，覆盖 schema/迁移、SQLite 外键、报告生成持久化、报告列表租户隔离。

## 边界说明

本阶段先交付可生成、可读取、可追溯的报告结果，不新增前端页面，也不生成 PDF/CSV 文件。后续导出文件时应优先基于 `generated_reports` 的稳定结果扩展。
