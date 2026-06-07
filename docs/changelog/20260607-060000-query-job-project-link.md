# feat: 新建查询任务支持关联监测项目

## 背景

Phase 3.3 已经让租户工作台可以进入监测项目列表和详情，但旧的新建任务流程仍只围绕 `job_id`。Phase 3.4 将新建查询任务与监测项目建立兼容期映射，为后续 Phase 4 的 `collection_jobs`、`collection_tasks` 和 attempt 生命周期做准备。

## 变更

- `llm_query_jobs` 新增 nullable `project_id` 字段，并添加 `(tenant_key, project_id)` 索引。
- 新增 MySQL 迁移脚本 `api/database/migrations/20260607_add_project_id_to_query_jobs.mysql.sql`。
- `POST /api/v1/query-jobs/load` 可接收 `project_id`；传入时按当前租户校验项目存在，再写入展开后的每条 query job。
- `fetch` 和 `status` 响应模型补充可选 `project_id` 字段，旧 `job_id` 查询路径保持可用。
- `CreateQueryJob` 新增“关联监测项目”选择控件，项目列表来自 `/api/v1/projects`；选择“暂不关联项目”时保留旧任务兼容行为。
- 新增后端项目关联 API 测试、schema/migration 测试和前端表单规范化测试。
- 更新 ExecPlan、TASKS、领域参考文档和技术债记录。

## 兼容边界

- `project_id` 不是 Phase 4 目标采集批次主键，只是旧 `llm_query_jobs` 到新项目模型的桥接字段。
- 字段允许为空，未传 `project_id` 的旧请求仍可创建任务。
- 本阶段不新增外键，项目归属由 API 校验；完整生命周期关系将在 `collection_jobs` 中承接。

## 验证

- `uv run --project api ruff check api`：通过。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：106 passed。
- `npm --prefix web test`：64 passed。
- `npm --prefix web run lint`：0 errors，保留既有 9 warnings。
- `npm --prefix web run build`：通过。
- 系统 Chrome + Playwright smoke test：新建任务页加载项目列表、选择项目后提交，POST body 包含 `project_id=proj_active`；桌面和移动视口截图检查无明显遮挡或横向溢出。
- `python scripts/validate_agents_docs.py --level ERROR`：通过。
- `python scripts/validate_agents_docs.py --level WARN`：通过。
