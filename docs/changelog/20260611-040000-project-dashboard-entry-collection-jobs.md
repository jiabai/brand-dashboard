# 项目看板入口改用 collection_jobs 数据源

## 变更

- 新增 `GET /api/v1/projects/{project_id}/collection-jobs`：按 `tenant_key + project_id` 列出该项目的采集任务（仅 `source_job_id` 非空），按时间窗倒序，并返回项目目标品牌（`project_brands.role='target'`）。
- 项目详情页「进入看板」Sheet 改源：从 `llm_query_jobs`（每条查询一行、导致重复项）改为 `collection_jobs`（一次采集一行）；每行展示状态、采集时间窗、成功/期望任务数；选择后经 `source_job_id` + 目标品牌进 legacy 首页看板。
- 前端新增 `fetchProjectCollectionJobs` 适配器、`normalizeProjectCollectionJobs` 与 `getCollectionJobStatusMeta`。
- 删除改源后变死代码的 `normalizeProjectJobRecords` 及其单测。

## 边界

- 不展示 `source_job_id` 为空的采集任务；不改 legacy 看板页与授权模型。
- 保留上一阶段 `/query-jobs/status?project_id` 过滤参数（向后兼容，未回滚）。

## 验证

- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `npm --prefix web test`
- `npm --prefix web run build`
- `python scripts/validate_agents_docs.py --level ERROR`
