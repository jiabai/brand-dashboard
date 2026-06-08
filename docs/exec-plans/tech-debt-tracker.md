# Tech Debt Tracker

> Last updated: 2026-06-07

## Phase 2 兼容债

| Topic | Why it matters | Source | Removal Condition |
|------|----------------|--------|-------------------|
| 历史重复数据风险尚未在目标数据库完成审计 | Phase 2.1 已提供只读检查脚本，但本地 `api/.env` 指向的 SQLite 文件缺少业务表，不能代表线上或 dump 的真实重复风险。 | `api/scripts/check_duplicate_analysis_rows.py`, `docs/exec-plans/completed/20260606-brand-monitoring-system-refactor.md` | 连接目标 MySQL 或导入 `data/geo_dump_20260509_135617.sql` 后运行 Phase 2.1 脚本；清理所有阻塞迁移的重复/碰撞记录，并把审计结果记录到 ExecPlan 或 changelog。 |
| `qa_brand_state` 使用兼容期前缀唯一键 | 当前 MySQL `tenant_key/job_id/conversation_id varchar(255)` + `utf8mb4` 可能超过 InnoDB 3072-byte 索引限制，因此使用 191 前缀唯一键；这依赖当前 ID 均较短。 | `api/database/schema_business.sql`, `analysis/database/schema_business.sql`, `api/database/migrations/20260606_add_qa_brand_state_idempotency_key.mysql.sql` | 引入规范化短 ID、`analysis_run_id` 或 hash key 后，用完整目标键替换前缀键；迁移脚本和 schema 测试覆盖新约束。 |
| 引用表仍使用旧唯一键 `(tenant_key, conversation_id, url)` | `qa_reference` 和 `llm_conversation_references` 旧键无法区分不同 job 或 brand，存在跨作用域碰撞和 upsert 语义不准的风险。 | `docs/references/20260606-brand-monitoring-domain-data-reference.md`, `api/v1/repositories/conversation.py`, `analysis/src/plugins/metrics/reference_status.py` | 引入 URL 规范化与 `url_hash`，更新 API 入库、analysis upsert、MySQL/SQLite schema 和重复检查脚本；完成历史数据去重后替换旧唯一键。 |
| `query-jobs/report` 兼容期依赖 `query_content` 判断入库成功 | Phase 2.5 已阻止入库失败后错误完成任务，但旧模型没有 `attempt_id` 或 query job record id，只能用 `(tenant_key, job_id, query_content)` 做临时关联；重复问题文本时仍不够精确。 | `api/v1/routes/query_jobs.py`, `api/v1/repositories/query_jobs.py`, `api/tests/test_conversation_report_consistency.py` | Phase 4 引入 `collection_attempts` 后，将 `conversation/load` 和 `report/complete` 绑定到具体 `attempt_id`；`llm_conversations` 或目标 `answer_snapshots` 保存 attempt 外键，并移除兼容期 `query_content` 判断。 |
| `analysis/` 插件仍未进入 API 系统生命周期 | Phase 2 修复了配置和幂等风险，但分析仍主要作为外部批处理运行，dashboard 指标仍依赖旧明细或手动分析产物。 | `analysis/src/analyzer.py`, `analysis/src/plugins/metrics/*`, `docs/design-docs/20260606-brand-monitoring-target-architecture.md` | Phase 5 新增 `analysis_runs`，由系统服务触发分析插件，结果写入带 `analysis_run_id` 的事实表；失败、重试、版本和血缘可追踪。 |
| 情感分析正式页面仍存在 mock 口径 | Phase 2 未处理 UI 数据真实性问题，继续保留 mock 可能误导客户对正式分析能力的判断。 | `docs/exec-plans/completed/20260606-brand-monitoring-system-refactor.md`, `web/src/components/*` | Phase 7 接入真实情感事实或明确空状态；正式页面不再用纯 mock 统计代表真实业务数据。 |
| `llm_query_jobs.project_id` 是兼容期桥接字段 | Phase 3.4 为了不破坏旧 `job_id` dashboard，只能把 `project_id` 写入每条旧 query job 明细，且暂不加外键；这还不是完整采集批次生命周期。 | `api/v1/routes/query_jobs.py`, `api/database/migrations/20260607_add_project_id_to_query_jobs.mysql.sql`, `docs/references/20260606-brand-monitoring-domain-data-reference.md` | Phase 4 引入 `collection_jobs.project_id` 后，将旧 `llm_query_jobs.project_id` 作为迁移来源或兼容字段；项目删除、采集批次和任务明细的生命周期关系由新模型承接。 |

## Existing Platform Debt

| Topic | Why it matters | Source | Removal Condition |
|------|----------------|--------|-------------------|
| 业务路由未消费登录 accessToken | 当前登录会签发 token，但 dashboard/config/executors/query-jobs/conversation 等业务路由仍主要依赖显式 tenant_key 或 executor key，缺少用户身份与租户成员关系校验 | 2026-05-17 API review | 引入 `get_current_user`/租户授权依赖，并覆盖所有敏感业务路由 |
| `api/config/llm_settings.json` 被 Git 跟踪 | LLM 配置文件容易承载 API Key，跟踪真实配置会增加密钥泄露风险 | 2026-05-17 API review | 改为提交 `.example` 模板，真实配置通过环境变量或未跟踪本地文件注入 |
| 数据库 engine 在 import 时创建 | 测试导入路由时会触发默认数据库连接，导致测试出现 ResourceWarning，也让依赖注入边界不够清晰 | 2026-05-17 API review | 将 engine 创建延迟到应用 lifespan 或显式 app factory，并让测试覆盖 dependency override |
