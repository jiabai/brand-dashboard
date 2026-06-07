# Phase 5.2 分析插件服务接入

## 背景

Phase 5.1 已经落地 `analysis_runs` 生命周期表和状态机，但分析运行还没有真正调用 `analysis/` 插件，也无法把本次运行血缘写回事实表。Phase 5.2 的目标是打通一条最小可用链路：对已成功的采集批次运行品牌提及和引用分析插件，并把事实行绑定到 `analysis_run_id`。

## 变更

- 新增内部系统分析服务 `api/v1/services/analysis_runner.py`，负责校验采集批次、解析项目品牌上下文、创建/启动/完成 `analysis_runs`，并执行 `mention_status` 与 `reference_status` 插件。
- `qa_brand_state` 和 `qa_reference` 新增 nullable `analysis_run_id` 字段、索引和到 `analysis_runs` 的复合外键；新增 MySQL 迁移脚本 `api/database/migrations/20260607_add_analysis_run_id_to_analysis_facts.mysql.sql`。
- `mention_status` 插件写入 `qa_brand_state` 时携带 `analysis_run_id`，并支持 SQLite/MySQL upsert；重跑同一事实键会更新运行血缘。
- `reference_status` 插件写入 `qa_reference` 时携带 `analysis_run_id`，并支持 SQLite/MySQL upsert；兼容期仍沿用旧引用唯一键语义。
- `analysis/src/plugins/__init__.py` 将工具类插件改为可选导入，避免 API 测试环境因未安装工具插件依赖而无法加载 metrics 插件。

## 边界

- 本阶段只新增内部 service，不开放公开 API route。
- 原始数据仍通过 `collection_jobs.source_job_id` 读取旧 `llm_conversations` 和 `llm_conversation_references`，这是兼容期桥接方案。
- `analysis_run_id` 暂不进入旧事实表唯一键，避免兼容 dashboard 因分析重跑产生重复明细。
- 分析失败可观测、重试入口和更细错误分类留到 Phase 5.3。

## 验证

- 已新增 schema、插件事实血缘和系统分析服务测试。
- 定向测试已通过：`api/tests/test_analysis_fact_lineage_schema.py`、`api/tests/test_analysis_plugins_fact_lineage.py`、`api/tests/test_analysis_runner_service.py`。
- 完整验证结果记录在 active ExecPlan 的 Validation and Acceptance 中。
