# 品牌监测业务系统重构任务清单

> 对应 ExecPlan：`docs/exec-plans/active/20260606-brand-monitoring-system-refactor.md`
> 使用规则：本文件仅在重构进行中保留；全部完成后删除，并将 ExecPlan 移动到 `docs/exec-plans/completed/`。

## 进行中

当前无进行中任务。下一步为 Phase 5.2。

## 待办

- [ ] Phase 5.2 将 `analysis/` 插件接入系统分析服务。✅ 验证条件：分析服务可以对指定项目/采集批次运行插件，并写入带 `analysis_run_id` 的事实表。
- [ ] Phase 5.3 分析失败可观测和可重试。✅ 验证条件：失败原因入库，retry API 或内部重试入口可用，失败不会污染指标快照。
- [ ] Phase 6.1 新增指标快照模型。✅ 验证条件：`metric_snapshots` 支持 metric name、value、date、brand、platform、keyword、definition version、analysis run、coverage 字段。
- [ ] Phase 6.2 生成品牌指标快照。✅ 验证条件：提及率、首位提及率、Top3 提及率、情绪占比和信源引用率口径测试通过。
- [ ] Phase 6.3 迁移 dashboard 查询到快照优先。✅ 验证条件：`DashboardService` 优先读快照，缺失时兼容旧明细聚合，现有 dashboard 测试通过。
- [ ] Phase 6.4 前端展示数据新鲜度和覆盖率。✅ 验证条件：dashboard 可显示指标生成时间、采集覆盖率、分析完整性，空状态不误导用户。
- [ ] Phase 7.1 新增问答快照页。✅ 验证条件：可按品牌、平台、关键词、情绪、是否引用过滤原始回答，页面构建通过。
- [ ] Phase 7.2 接入真实情感分析数据。✅ 验证条件：正式情感页面不再依赖纯 mock 统计，真实无数据时展示明确空状态。
- [ ] Phase 7.3 新增告警规则与告警事件。✅ 验证条件：提及率下降、负面情绪上升、信源变化至少一种规则可触发并记录事件。
- [ ] Phase 7.4 新增报告导出基础能力。✅ 验证条件：项目可生成或导出一个包含核心指标和时间窗口的报告结果。
- [ ] Phase 7.5 新增数据质量页。✅ 验证条件：页面展示失败采集、过期分析、指标覆盖率和可重算入口。
- [ ] Phase 8.1 清理旧 job 主导航暴露。✅ 验证条件：用户主流程以项目为入口，旧任务入口仍可通过兼容路径排障。
- [ ] Phase 8.2 更新核心架构文档和 README。✅ 验证条件：`docs/ARCHITECTURE.md`、`docs/DESIGN.md`、`docs/SECURITY.md`、README 与新架构一致。
- [ ] Phase 8.3 归档 ExecPlan 并删除本文件。✅ 验证条件：所有任务完成，ExecPlan 移动到 `docs/exec-plans/completed/`，`TASKS.md` 删除，`python scripts/validate_agents_docs.py --level WARN` 通过。

## 已完成

- [x] Phase 5.1 新增 `analysis_runs`。✅ 验证条件：分析运行状态机覆盖 pending、running、succeeded、failed、stale，测试通过。
- [x] Phase 4.4 平台后台展示采集健康度。✅ 验证条件：平台管理员可看到执行器健康、队列长度、失败任务，不发送 `X-Tenant-Key`。
- [x] Phase 4.3 新增 attempt start/complete 接口。✅ 验证条件：成功、失败、超时、重试路径都有 API 测试。
- [x] Phase 4.2 改造执行器领取协议。✅ 验证条件：并发 fetch 不会领取同一任务，lease 超时后任务可重新领取，执行器 scope 测试通过。
- [x] Phase 4.1 新增采集批次、任务和 attempt 表。✅ 验证条件：schema 支持任务定义、任务领取、执行尝试、失败原因、lease 到期时间和租户隔离。
- [x] Phase 3.4 将新建任务关联到项目。✅ 验证条件：创建采集批次时能保存 `project_id` 映射，旧 `job_id` dashboard 入口仍可用。
- [x] Phase 3.3 新增项目前端入口。✅ 验证条件：租户工作台可进入项目列表和项目详情壳层，前端测试和构建通过。
- [x] Phase 3.2 新增项目 API。✅ 验证条件：项目列表、创建、详情、品牌配置、问题集配置 API 具备 Pydantic 契约和权限测试。
- [x] Phase 3.1 新增监测项目数据模型。✅ 验证条件：`monitoring_projects`、`project_brands`、`prompt_sets`、`prompt_items` 的 schema 设计和迁移策略已落档，后端 schema 测试通过。
- [x] Phase 2.6 更新技术债记录。✅ 验证条件：`docs/exec-plans/tech-debt-tracker.md` 已记录 Phase 2 无法立即关闭的兼容风险和清理条件，包括历史重复审计、引用表 URL hash、前缀唯一键、临时上报关联、analysis 生命周期和情感 mock 口径。
- [x] Phase 2.5 补充采集入库与任务上报一致性测试。✅ 验证条件：已新增 `api/tests/test_conversation_report_consistency.py`，证明 `conversation/load` 失败回滚后 `query-jobs/report` 不会增加 `executed_runs`，且成功入库后才能上报完成。
- [x] Phase 2.4 清理 `analysis/config/analysis_config.json` 中的真实数据库连接配置。✅ 验证条件：已将数据库字段改为 `ANALYSIS_DB_*` 环境变量占位符，新增 `analysis/.env.example` 和 `analysis/tests/test_database_config.py`，并更新 analysis README / SECURITY 说明。
- [x] Phase 2.3 评估引用表唯一键与 URL hash 策略。✅ 验证条件：已在 `docs/references/20260606-brand-monitoring-domain-data-reference.md` 明确兼容期暂不立即修改 `qa_reference` / `llm_conversation_references` schema，并记录目标 `url_hash` 唯一键迁移条件。
- [x] Phase 2.2 为 `qa_brand_state` 补齐兼容期幂等约束。✅ 验证条件：已更新 MySQL/SQLite schema 和 `api/database/migrations/20260606_add_qa_brand_state_idempotency_key.mysql.sql`，`api/tests/test_qa_brand_state_idempotency_schema.py` 验证 `mention_status` 重跑不会插入同一 `(tenant_key, job_id, conversation_id, brand)` 的重复事实。
- [x] Phase 2.1 盘点现有分析明细重复数据风险。✅ 验证条件：已新增 `api/scripts/check_duplicate_analysis_rows.py` 和 `api/tests/test_analysis_duplicate_checks.py`，覆盖 `qa_brand_state`、`qa_reference`、`llm_conversation_references`，并已在 ExecPlan 的 Surprises & Discoveries 记录发现。
- [x] Phase 0 完成现有架构评估。✅ 验证条件：`docs/design-docs/20260606-brand-monitoring-business-architecture-refactor.md` 已落档并进入设计文档索引。
- [x] Phase 1 落档重构规格、目标架构、领域数据参考和 active ExecPlan。✅ 验证条件：`docs/product-specs/20260606-brand-monitoring-system-refactor.md`、`docs/design-docs/20260606-brand-monitoring-target-architecture.md`、`docs/references/20260606-brand-monitoring-domain-data-reference.md`、`docs/exec-plans/active/20260606-brand-monitoring-system-refactor.md` 均已创建并进入对应索引。
