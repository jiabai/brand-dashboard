# Phase 7.5 项目数据质量页

## 变更内容

- 新增 `GET /api/v1/projects/{project_id}/data-quality`，按项目聚合失败采集、过期分析、指标覆盖率和重算动作。
- 新增后端 `api/v1/repositories/data_quality.py` 与 `api/v1/services/data_quality.py`，所有查询均显式携带 `tenant_key + project_id`。
- 新增前端 `/projects/:tenantKey/:projectId/quality` 隐藏路由和 `ProjectDataQualityPage` 页面。
- 新增前端项目数据质量 API adapter、analysis retry adapter 和项目数据质量归一化展示工具。
- 项目详情页新增“数据质量”入口，数据质量页中的“重新分析”按钮复用既有 `POST /api/v1/analysis-runs/{analysis_run_id}/retry`。

## 边界说明

本阶段交付项目级质量可见性和重算入口，不新增独立重算状态机，也不处理失败采集任务的手动重新领取动作。失败采集的重新领取仍由 Phase 4 的 fetch/lease 协议承接。

## 验证

- 后端定向测试：`api/tests/test_project_data_quality.py` 通过（2 passed）。
- 前端定向测试：项目 API、analysis retry、路由、展示归一化和页面契约组合通过（18 passed）。
- 全量门禁：后端测试、前端测试、后端 ruff、前端 lint、前端 build 和文档 ERROR/WARN 验证均通过。
- 浏览器 smoke：系统 Chrome + Playwright 打开 `/projects/tn_acme/proj_acme/quality`，桌面和移动视口均可看到数据质量标题、失败采集、指标覆盖率和重新分析入口，且无横向溢出。
