# 移除 legacy qa_brand_summary 汇总表

## 变更内容

- 删除 `qa_brand_summary` 建表/索引/触发器：`api/database/schema.sql`、`schema_business.sql`、`schema_sqlite.sql` 以及 `analysis/database/schema.sql`、`schema_business.sql`。
- 删除迁移写入逻辑：`scripts/migrate_legacy_geo_sqlite.py` 的 `_insert_qa_brand_summary()` 函数及其调用。
- 删除相关测试断言：`api/tests/test_legacy_geo_migration.py` 中对 `qa_brand_summary` 的计数校验。
- 同步参考文档：`api/database/README.md`、`docs/references/20260609-database-dictionary.md`（含 9.x 小节重排）、`docs/references/20260606-brand-monitoring-domain-data-reference.md` 移除该表条目。

## 原因

- `qa_brand_summary` 仅被 legacy 迁移脚本写入，API/分析层无任何读取（`api/v1/repositories/` 零引用）；经确认当前无外部消费者（报表/BI/下游）。
- 该表结构未经设计推敲，且当前指标读取已统一以 `qa_brand_state` / `qa_reference` 事实聚合为准（见架构 refactor 设计文档）。
- 它本就是事实表的派生汇总，未来若需类似汇聚表，按届时真实需求重建即可，无需迁就旧结构。

## 保留项

- `docs/design-docs/20260606-brand-monitoring-business-architecture-refactor.md` 与 `docs/changelog/20260609-020000-legacy-geo-sqlite-migration.md` 作为历史设计/变更记录保留，不改写既往事实。

## 验证

- `api\.venv\Scripts\python.exe -m pytest api\tests\test_legacy_geo_migration.py -q`：1 passed。
- `api\.venv\Scripts\python.exe -m pytest api\tests\ -q`：227 passed（无新增失败，仅既有 deprecation 警告）。
- `ruff check api scripts/migrate_legacy_geo_sqlite.py`：All checks passed。
- `python scripts/validate_agents_docs.py --level ERROR`：0 错误。
- 全仓库 grep `qa_brand_summary`：仅剩上述两处历史文档。

## 残余风险

- 无。若未来发现遗漏的外部直查消费者，可从 `qa_brand_state` 重新聚合恢复（聚合口径见本次删除前的 `_insert_qa_brand_summary` 实现，可在 git 历史检索）。
