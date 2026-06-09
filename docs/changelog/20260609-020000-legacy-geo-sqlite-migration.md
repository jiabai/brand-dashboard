# 迁移 legacy GEO SQLite 数据

## 变更内容

- 新增 `scripts/migrate_legacy_geo_sqlite.py`，将旧版 `data/geo_csv/geo.db` 只读抽取并迁移到当前 `schema_sqlite.sql` 对应的新库结构。
- 生成 `data/geo_csv/geo_migrated.db`，补齐项目、问题集、采集批次、采集任务、分析运行和事实 lineage。
- 将 legacy `llm_query_jobs.project_id`、`qa_brand_state.analysis_run_id`、`qa_reference.analysis_run_id` 回填到新库中。
- 本地 `api/.env` 与 `docker-compose.sqlite.yml` 的 SQLite 路径切换到 `geo_migrated.db`。

## 数据映射

- 每个旧 `(tenant_key, job_id)` 映射为一个 `monitoring_projects` 项目、一个 `collection_jobs` 批次和一个 `analysis_runs` 运行。
- `project_brands` 从 `llm_query_jobs.brand`、`competitor` 和 `qa_brand_state.brand` 推断。
- `prompt_sets` / `prompt_items` 从旧 query job 和 conversation 的问题内容生成。
- `qa_brand_summary` 从迁移后的 `qa_brand_state` 聚合生成，作为 legacy 汇总兼容数据。

## 验证

- `api\.venv\Scripts\python.exe -m pytest tests\test_legacy_geo_migration.py -q`：1 passed。
- 真实迁移结果：3 jobs、3 projects、3 analysis runs、692 conversations、29 query jobs、4178 brand-state facts、3232 references。
- `data/geo_csv/geo_migrated.db` 验证：`PRAGMA integrity_check = ok`，23/23 张目标表存在，lineage 缺失数为 0。
- 代表性 repository 查询通过：项目列表、query job status、`fact_metrics` 聚合查询；QuickCEP legacy job 返回 595 条 fact metric 行。
