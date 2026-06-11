# 项目详情页进入看板入口

## 变更

- `GET /api/v1/query-jobs/status` 新增可选 `project_id` 查询参数，按 `tenant_key + project_id` 过滤；不传时行为不变（向后兼容）。授权沿用 `get_current_tenant`。
- 前端 `fetchQueryJobStatus` 透传 `project_id`；项目展示层新增 `normalizeProjectJobRecords` 与 `buildProjectDashboardPath` 纯函数。
- 项目详情页新增「进入看板」按钮，点击打开右侧 Sheet 列出该项目的采集 job（品牌 + 状态徽章 + 生效区间），选择后跳转 legacy 首页看板 `/dashboard/{tenantKey}/{jobId}?brand=`；无 job 显示空状态。

## 边界

- 仅项目详情页入口；用户明确选 job（不自动选最新）；落地仅首页看板。
- 不改看板页与授权模型；复用既有 `llm_query_jobs.project_id` 关联。

## 验证

- `uv run --project api ruff check api`（All checks passed）
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`（222 passed）
- `npm --prefix web test`（137 pass）
- `npm --prefix web run build`（构建成功）
- `python scripts/validate_agents_docs.py --level ERROR`（0 错误）
