# Phase 5.1 分析运行模型落地

## 背景

Phase 4 已经把采集批次、采集任务和执行 attempt 拆开，但分析过程仍然没有系统级生命周期。旧链路里，`analysis/` 目录下的插件更像离线批处理能力，缺少可追踪的运行记录、输入水位、插件版本和失败原因。Phase 5.1 先补齐 `analysis_runs`，让后续插件接入、事实表写入和指标快照生成都有统一血缘。

## 本次变更

- 新增 `analysis_runs` schema，覆盖 MySQL 完整 schema、业务 schema、analysis 镜像 schema 和 SQLite 测试 schema。
- 新增 MySQL 迁移脚本 `api/database/migrations/20260607_add_analysis_run_model.mysql.sql`。
- 新增 `api/v1/repositories/analysis_runs.py`，提供创建、启动、完成和标记过期的状态机操作。
- 新增 schema 与 repository 测试，覆盖 `pending`、`running`、`succeeded`、`failed`、`stale` 状态，以及非法状态跳转拒绝。
- 更新 `TASKS.md`、ExecPlan 和领域数据参考，标记 Phase 5.1 完成并记录下一步 Phase 5.2。

## 关键决策

- `project_id` 从同租户下的 `collection_jobs` 派生，创建 analysis run 时不允许调用方自由传入，避免分析血缘跨项目错绑。
- `analysis_run_id` 使用 `(tenant_key, analysis_run_id)` 作为业务唯一键，便于后续 API、事实表和快照表统一引用。
- `stale` 只允许从 `succeeded` 或 `failed` 进入；`pending` 和 `running` 尚无稳定输出，不应被标记为过期快照。
- 本阶段不调用 `analysis/` 插件，也不新增事实表写入逻辑。插件服务入口和带 `analysis_run_id` 的事实表幂等写入放入 Phase 5.2。

## 验证记录

- 已完成红绿测试：schema 测试先因缺少 `analysis_runs` 和迁移脚本失败，补齐后通过。
- 已完成红绿测试：repository 测试先因缺少 `api.v1.repositories.analysis_runs` 模块失败，补齐后通过。
- 定向验证：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_analysis_run_schema.py api/tests/test_analysis_runs_repository.py -q` 通过（8 passed, 78 warnings）。
- 收口验证：`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（129 passed, 828 warnings）；文档 ERROR/WARN 门禁均为 0 错误、0 警告；`git diff --check` 通过，仅有既有 LF/CRLF 换行提示。
