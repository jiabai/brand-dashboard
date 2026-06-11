# 项目看板入口改源 collection_jobs 规格

## 变更

- 新增产品规格 `docs/product-specs/20260611-010000-project-dashboard-entry-collection-jobs.md`：把项目详情页「进入看板」Sheet 的采集任务来源从 `llm_query_jobs`（每条查询一行、导致重复项）改为 `collection_jobs`（一次采集任务一行），经 `source_job_id` 进 legacy 看板，品牌取项目目标品牌。
- 更新 `docs/product-specs/index.md` 索引（随分支批次提交）。

## 边界

- 本次提交仅含规格文档，不含实现。
- 修订前一份规格的数据源决策；其余产品意图不变。不改看板页与授权模型。

## 验证

- `python scripts/validate_agents_docs.py --level ERROR`
