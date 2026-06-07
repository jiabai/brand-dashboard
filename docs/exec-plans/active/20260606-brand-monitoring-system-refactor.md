# 品牌监测业务系统重构实施计划

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

把当前以 `tenant_key + job_id` 为中心的品牌分析 dashboard，分阶段重构为以“监测项目”为中心的品牌 AI 认知监测业务系统。计划要求保留现有 dashboard 和执行器能力，同时补齐领域模型、采集 attempt、分析运行、指标快照、问答快照、告警和报告的演进路径。

## Progress

- [x] Phase 0: 完成现有架构评估，形成重构方向（2026-06-06）
- [x] Phase 1: 落档产品规格、目标架构设计、领域数据参考和本 ExecPlan（2026-06-06）
- [x] Phase 1.1: 补充根目录 `TASKS.md`，为后续重构提供可校验执行清单（2026-06-06）
- [x] Phase 2: 稳定现有 MVP 的数据幂等性和敏感配置（2026-06-07）
- [x] Phase 2.1: 新增分析明细重复风险检查脚本，覆盖 `qa_brand_state`、`qa_reference`、`llm_conversation_references`（2026-06-06）
- [x] Phase 2.2: 为 `qa_brand_state` 补齐兼容期幂等唯一键和 MySQL 迁移脚本（2026-06-06）
- [x] Phase 2.3: 完成引用表唯一键与 URL hash 策略评估，兼容期暂不修改 schema（2026-06-06）
- [x] Phase 2.4: 清理 analysis 版本化配置中的真实数据库连接，并改为环境变量注入（2026-06-06）
- [x] Phase 2.5: 为采集入库与任务上报补充一致性门和回归测试（2026-06-07）
- [x] Phase 2.6: 更新技术债记录，集中登记 Phase 2 未关闭的兼容风险（2026-06-07）
- [x] Phase 3.1: 新增监测项目、项目品牌、问题集和问题项 schema 与 MySQL 迁移脚本（2026-06-07）
- [x] Phase 3.2: 新增项目列表、创建、详情、品牌配置和问题集配置 API（2026-06-07）
- [x] Phase 3.3: 新增租户工作台项目列表、项目详情壳层、前端 API adapter 和路由入口（2026-06-07）
- [x] Phase 3.4: 新建查询任务可选择监测项目，并把 `job_id` 与 `project_id` 关联（2026-06-07）
- [x] Phase 3: 引入监测项目与项目设置模型（2026-06-07）
- [x] Phase 4.1: 新增采集批次、任务和 attempt schema 与 MySQL 迁移脚本（2026-06-07）
- [x] Phase 4.2: 新增采集任务领取 API 和 lease 防重复领取逻辑（2026-06-07）
- [x] Phase 4.3: 新增 attempt start/complete API 和成功、失败、超时状态推进（2026-06-07）
- [x] Phase 4.4: 新增平台后台采集健康度 API 与执行器健康页面（2026-06-07）
- [x] Phase 4: 拆分采集任务、执行尝试和执行器 lease（2026-06-07）
- [x] Phase 5.1: 新增 analysis_runs schema、迁移和状态机 repository（2026-06-07）
- [x] Phase 5.2: 将 analysis 插件接入内部系统分析服务并写入事实血缘（2026-06-07）
- [x] Phase 5.3: 新增分析失败可观测、retry API 和 succeeded-only 快照候选（2026-06-07）
- [x] Phase 5: 将分析引擎接入系统级分析运行（系统侧能力，2026-06-07）
- [x] Phase 6.1: 新增 metric_snapshots schema、迁移和 analysis 镜像 schema（2026-06-07）
- [x] Phase 6.2: 新增指标快照生成 service/repository，并固定 `brand_metrics_v1` 口径（2026-06-07）
- [x] Phase 6.3: 品牌提及类 dashboard 查询改为快照优先、旧明细兜底（2026-06-07）
- [x] Phase 6.4: 前端展示指标生成时间、采集覆盖和分析完整性（2026-06-07）
- [x] Phase 6: 建设指标快照 read model 并迁移 dashboard 查询（2026-06-07）
- [ ] Phase 7: 完善问答快照、告警、报告和数据质量页面
- [ ] Phase 8: 清理兼容层，归档计划

## Surprises & Discoveries

- 2026-06-06：`analysis/` 已具备插件化分析雏形，但它与 API 服务尚未形成统一生命周期。
- 2026-06-06：`mention_status` 插件注释依赖 `qa_brand_state` 的唯一键，但当前 schema 中未声明该唯一约束，重跑分析存在重复数据风险。
- 2026-06-06：情感分析页面仍使用 mock 数据，需要在后续真实分析链路中收敛。
- 2026-06-06：重构范围较大，active ExecPlan 之外需要根目录 `TASKS.md` 承载阶段任务和验证条件，便于项目验证脚本和人工检查。
- 2026-06-06：Phase 2.1 已落地只读检查脚本 `api/scripts/check_duplicate_analysis_rows.py`。检查范围包括 `qa_brand_state` 的目标幂等键重复，以及 `qa_reference`、`llm_conversation_references` 的目标键重复和旧唯一键跨任务/跨品牌碰撞；是否存在实际线上重复需在目标数据库执行脚本确认。
- 2026-06-06：本地 `api/.env` 指向的 SQLite 文件缺少业务表，不能代表历史数据审计结果；仓库中的 `data/geo_dump_20260509_135617.sql` 包含三张表的数据插入，后续如需确认实际重复，应先导入该 dump 或连接目标 MySQL 后运行 Phase 2.1 脚本。
- 2026-06-06：Phase 2.2 发现完整 `(tenant_key, job_id, conversation_id, brand)` 复合唯一键在当前 `varchar(255)` + `utf8mb4` 下可能超过 InnoDB 3072-byte 索引长度，因此兼容期采用 `tenant_key/job_id/conversation_id` 的 191 前缀唯一键；当前 ID 生成形态远短于 191，后续长期模型可用规范化 ID 或 hash key 收敛。
- 2026-06-06：Phase 2.3 发现引用表的 schema、API 入库路径和 `reference_status` 分析插件都仍围绕旧唯一键 `(tenant_key, conversation_id, url)` 工作；若只改 schema 而不同时引入 URL hash、更新 upsert 目标和清理历史数据，反而会保留旧碰撞语义或造成迁移失败。
- 2026-06-06：Phase 2.4 发现除 `analysis/config/analysis_config.json` 外，`analysis/tests/export_brands_found.py` 也含有旧本地数据库连接；已一并改为 `ANALYSIS_DB_*` 环境变量注入，避免测试脚本继续携带真实连接信息。
- 2026-06-07：Phase 2.5 发现 `conversation/load` 和 `query-jobs/report` 是两个独立请求；旧模型没有 attempt id 或 query job record id 写入对话表，因此兼容期只能用 `(tenant_key, job_id, query_content)` 判断任务结果是否已入库。
- 2026-06-07：Phase 2.6 将仍需后续关闭的兼容风险集中写入根技术债记录，包括历史重复审计、引用表 URL hash、前缀唯一键、临时上报关联、analysis 生命周期和情感 mock 口径。
- 2026-06-07：Phase 3.1 可以先作为纯配置模型落地，不需要立即改动旧 `llm_query_jobs` 执行链路；项目删除会级联清理品牌配置和问题集配置，但不会触碰既有采集明细和分析事实。
- 2026-06-07：Phase 3.2 的项目 API 可以复用现有租户鉴权依赖；读取项目只需要当前租户成员，创建和配置写入必须是租户 admin。请求体不接收 `tenant_key`，避免客户端覆盖服务端租户上下文。
- 2026-06-07：Phase 3.3 可以在不消费 `job_id` 的情况下先挂出项目列表和项目详情壳层；现有租户工作台布局仍带有 dashboard 时间筛选区，本阶段先复用外壳，后续在项目概览和 Phase 8 收敛主导航与时间筛选语义。
- 2026-06-07：Phase 3.4 发现旧 `llm_query_jobs` 既承担采集批次又承担任务明细，当前只能把 `project_id` 写到每条展开后的 query job 记录；真正的一次采集批次模型需要等 Phase 4 引入 `collection_jobs`。
- 2026-06-07：Phase 4.1 只落采集生命周期 schema，不立即改旧执行器接口；`collection_tasks` 和 `collection_attempts` 需要引用 `executors`，因此新表在完整 schema 中放在 `executors` 之后，保证空库建表顺序可执行。
- 2026-06-07：Phase 4.2 继续复用旧执行器身份依赖 `verify_executor`；当前系统尚无独立的“执行器-租户授权表”，因此新领取协议先用必填 `tenant_key` 和任务租约状态保证租户过滤与活跃租约隔离，后续如需更细粒度调度再新增执行器 scope 模型。
- 2026-06-07：Phase 4.3 将 `attempt_count` 的递增放在 start 阶段，而不是 complete 阶段；这样执行器启动后即便超时失联，后续补偿或 timeout complete 也能正确消耗一次尝试额度。
- 2026-06-07：Phase 4.4 发现当前执行器还没有独立 heartbeat 表，因此平台健康度先由 `executors.status`、活跃 lease、running attempt、失败任务和租约过期任务组合计算；后续如要展示真实在线状态，需要新增心跳或执行器运行事件模型。
- 2026-06-07：Phase 5.1 只落 `analysis_runs` 生命周期模型和状态机，不在本阶段调用 `analysis/` 插件；这样可以先把分析血缘和状态边界固定，再在 Phase 5.2 接入插件执行和事实表写入。
- 2026-06-07：Phase 5.2 发现 API 侧导入 `analysis.src.plugins` 时会被工具插件的 `requests` 依赖阻塞；已将工具类插件改为可选导入，保证 metrics 插件能在 API 测试环境中加载。
- 2026-06-07：Phase 5.2 仍需通过 `collection_jobs.source_job_id` 读取旧 `llm_conversations` / `llm_conversation_references` 原始数据；这是采集原始表尚未持有新 collection 字段前的兼容桥。
- 2026-06-07：Phase 5.3 发现失败分析运行可能在插件聚合中留下部分事实；retry 必须创建新的 `analysis_run_id` 并通过 upsert 重新绑定事实血缘，Phase 6 快照生成也只能选择 succeeded run。
- 2026-06-07：Phase 5.3 的 retry API 先采用同步执行，满足内部可用和测试闭环；若后续真实插件耗时过长，需要改成提交 pending retry run 后由后台 worker 执行。
- 2026-06-07：Phase 6.1 发现指标快照的自然维度键会把 `tenant_key/project_id/metric/brand/platform/keyword/definition/analysis_run` 组合得很长；在 MySQL `utf8mb4` 下直接做完整复合唯一键容易超过索引长度，因此需要用 `dimension_hash` 收敛维度唯一性。
- 2026-06-07：Phase 6.2 需要区分“任意信源引用率”和“发稿链接覆盖率”。本阶段的 `reference_rate` 只判断同一回答是否存在至少一条 `qa_reference`，不依赖 `is_published_link`；发稿链接覆盖率后续可作为单独指标扩展。
- 2026-06-07：Phase 6.3 发现并非所有 dashboard 查询都能直接由首版快照替代；`platform-mention-rates` 仍需要 category 维度，引用相关接口仍需要 domain/url/content_type/`is_published_link` 明细，因此本阶段只迁移品牌提及类读面。
- 2026-06-07：Phase 6.4 可以直接复用 `brand-metrics` 作为首页指标质量入口；前端已依赖该接口加载目标品牌和竞品列表，因此把新鲜度、覆盖率和分析完整性放入 response metadata，不需要新增页面级请求。

## Decision Log

| Decision | Rationale | Date/Author |
|---|---|---|
| 先采用模块化单体，不拆微服务 | 当前主要问题是领域模型和数据生命周期，过早拆服务会增加运维复杂度 | 2026-06-06 / agent |
| 以 MonitoringProject 作为新业务主线 | 品牌监测是长期项目，不是一次 job 批次 | 2026-06-06 / agent |
| 保留旧 dashboard 和执行器接口兼容期 | 避免重构初期打断现有 MVP 和数据采集 | 2026-06-06 / agent |
| dashboard 目标态读取指标快照 | 快照能表达口径版本、新鲜度、完整性和生成血缘 | 2026-06-06 / agent |
| 根目录保留 TASKS.md 直到重构完成 | 项目规则要求进行中任务创建执行清单，全部完成后删除 | 2026-06-06 / agent |
| Phase 2.1 先采用只读检查脚本，不立即改 schema | 先盘点重复风险，避免在未知历史数据上直接添加唯一约束导致迁移失败 | 2026-06-06 / agent |
| Phase 2.2 使用前缀复合唯一键 | 兼容当前 `varchar(255)` 字段和 MySQL `utf8mb4` 索引长度限制，同时满足现有短 ID 的幂等写入 | 2026-06-06 / agent |
| Phase 2.3 暂不立即替换引用表唯一键 | 引用表唯一键迁移需要 URL 规范化、持久化 hash、API 入库契约、分析插件 upsert 目标和历史数据清理同步推进，单独改 schema 风险高 | 2026-06-06 / agent |
| Phase 2.4 使用环境变量占位符作为 analysis 数据库配置契约 | 版本化 JSON 保留配置结构和默认本地 host/port/user/name，但真实密码无默认值，必须通过环境变量、未跟踪 `.env` 或密钥管理器注入 | 2026-06-06 / agent |
| Phase 2.5 上报前校验任务结果已入库 | 兼容期通过 `llm_query_jobs.(tenant_key, job_id, query_content)` 匹配 `llm_conversations`，防止入库失败后仍增加执行次数；长期应由 `collection_attempt_id` 替代 | 2026-06-07 / agent |
| Phase 2.6 用技术债记录承接未关闭兼容风险 | Phase 2 已完成 MVP 稳定化的最小门禁，但若把剩余折中散落在实现注释中，后续 Phase 3-7 很难按证据关闭 | 2026-06-07 / agent |
| Phase 3.1 使用 `tenant_key` + 稳定业务 ID 作为项目配置外键 | 项目、品牌和问题集需要跨 API、执行器和分析链路稳定引用；复合外键同时保留租户隔离边界，并允许删除项目时回收配置数据 | 2026-06-07 / agent |
| Phase 3.2 项目 API 请求体禁止携带 `tenant_key` | 用户侧 API 的租户边界必须来自 `Authorization` 和 `X-Tenant-Key` 解析出的服务端上下文，不能由请求体决定 | 2026-06-07 / agent |
| Phase 3.3 项目详情路由不进入主菜单，侧边栏仍高亮项目入口 | 项目详情是项目列表的下钻页，不应成为并列导航项；`/projects/:tenantKey/:projectId` 通过隐藏路由进入，路径识别回到 `projects` 以保持导航上下文 | 2026-06-07 / agent |
| Phase 3.4 `llm_query_jobs.project_id` 采用 nullable 字段且不加外键 | 兼容旧 `job_id` dashboard 和历史任务；项目归属由 API 按当前租户校验，后续 Phase 4 再用 `collection_jobs` 建立更强生命周期关系 | 2026-06-07 / agent |
| Phase 4.1 使用 `tenant_key` + 生命周期业务 ID 作为采集外键 | `collection_jobs`、`collection_tasks`、`collection_attempts` 都需要跨 API、执行器和分析链路稳定追踪；复合唯一键和复合外键同时固定租户隔离边界 | 2026-06-07 / agent |
| Phase 4.1 将项目删除与采集历史解耦 | `collection_jobs` 强绑定 `(tenant_key, project_id)`，但不对项目删除级联；历史采集批次、任务和 attempt 应作为后续分析和审计血缘保留 | 2026-06-07 / agent |
| Phase 4.2 新领取接口要求显式 `tenant_key` | 项目规则要求业务查询携带租户边界；新 `/collection-tasks/fetch` 不沿用旧 `query-jobs/fetch` 的可选租户参数，避免执行器全局扫描任务 | 2026-06-07 / agent |
| Phase 4.2 使用条件更新实现 lease 领取 | 领取逻辑先筛选可领取任务，再用带状态和 `lease_until` 条件的 `UPDATE` 写入 `reserved`、`lease_owner`、`lease_until`；即使并发请求选中同一候选，也只有一个请求能成功更新 | 2026-06-07 / agent |
| Phase 4.3 start 由 lease 持有者创建 running attempt | 只有 `collection_tasks.status='reserved'`、`lease_owner` 等于当前执行器且 `lease_until` 未过期时才能启动 attempt，防止非持有者伪造执行结果 | 2026-06-07 / agent |
| Phase 4.3 失败和超时都回写 task 为 `failed` | `collection_tasks.status='failed'` 配合 `attempt_count < max_attempts` 表达可重试；达到上限后仍是 failed，但 fetch 条件不会再领取 | 2026-06-07 / agent |
| Phase 4.4 平台健康 API 不接收 `X-Tenant-Key` | 平台后台是运营视角，需要跨租户汇总执行器、队列和失败任务；权限边界由 `Authorization` 中的平台管理员身份控制，而不是租户头 | 2026-06-07 / agent |
| 旧 `/query-jobs/fetch` 到新 collection task 的兼容映射延期 | 直接改旧执行器协议会影响现有 MVP 采集客户端；Phase 4 先完成新 collection 生命周期和平台可观测面，旧入口继续保留，后续在兼容层清理时再收敛 | 2026-06-07 / agent |
| Phase 5.1 `analysis_runs.project_id` 从 `collection_jobs` 派生 | 分析运行必须绑定采集批次和项目，但创建 run 时不允许调用方传入另一个 project_id，避免跨项目血缘错挂 | 2026-06-07 / agent |
| Phase 5.1 stale 只从 succeeded/failed 进入 | `pending` 和 `running` 还没有稳定输出，不应标记为过期快照；已完成或失败的 run 才能因上游数据/配置变化转为 `stale` | 2026-06-07 / agent |
| Phase 5.2 用 `source_job_id` 读取兼容期原始数据 | 旧原始回答和引用表仍按 `job_id` 存储，直接重命名会影响现有入库与 dashboard；通过 `collection_jobs.source_job_id` 桥接可以先接上分析生命周期 | 2026-06-07 / agent |
| Phase 5.2 事实表 `analysis_run_id` nullable 且不进入旧唯一键 | 历史事实行需要继续有效，兼容 dashboard 也不应因为重跑分析看到重复明细；upsert 更新同一事实行的最新运行血缘 | 2026-06-07 / agent |
| Phase 5.2 先落内部 service，不开放公开 API route | 分析运行的触发权限、重试策略和失败观测还未完成；先用内部服务固定插件执行和状态推进边界，Phase 5.3 再补 retry/observability | 2026-06-07 / agent |
| Phase 5.3 retry 创建新的 analysis run | 失败运行需要保留原始错误用于审计，不能在原 run 上覆盖状态和错误；新的 run 承担重试输出和事实血缘 | 2026-06-07 / agent |
| Phase 5.3 retry 仅允许 failed/stale run | succeeded run 已是稳定输出，不应被 retry API 覆盖；pending/running run 还未结束，重试会造成并发分析歧义 | 2026-06-07 / agent |
| Phase 5.3 快照候选只认 succeeded run | 失败或过期 run 可能没有完整事实，不能成为 Phase 6 指标快照输入；Repository 提供 succeeded-only 查询入口 | 2026-06-07 / agent |
| Phase 6.1 使用 `dimension_hash` 做快照幂等键 | 品牌、平台、关键词等原始维度仍保留为可读字段，但唯一键只引用 hash，避免 MySQL 长 varchar 组合索引超限 | 2026-06-07 / agent |
| Phase 6.1 聚合维度用空字符串表示 all | MySQL 唯一键遇到 NULL 会允许重复行；空字符串能稳定表达全品牌/全平台/全关键词聚合并支持幂等 upsert | 2026-06-07 / agent |
| Phase 6.1 只落 schema，不生成快照 | 指标口径、生成器和 dashboard 迁移分别属于 Phase 6.2/6.3，先固定 read model 能降低后续实现耦合 | 2026-06-07 / agent |
| Phase 6.2 使用 `brand_metrics_v1` 作为首版指标口径 | 快照必须能解释“当时为什么这样算”，先把提及、首提、Top3、情绪占比和信源引用率绑定到稳定版本，后续新口径通过新版本并存 | 2026-06-07 / agent |
| Phase 6.2 快照生成只接受 succeeded analysis run | 失败、运行中或 stale run 都可能缺少完整事实；生成服务在入口拒绝非 succeeded run，避免 dashboard 后续读取到不完整指标 | 2026-06-07 / agent |
| Phase 6.2 指标按回答维度去重 | `qa_brand_state` 和 `qa_reference` 仍是明细表，快照口径统一使用 `COUNT(DISTINCT conversation_id)` 作为分母或事件计数，减少重复事实对比例的影响 | 2026-06-07 / agent |
| Phase 6.3 保持 DashboardService/API 响应契约不变 | 前端暂不改展示；Repository 层先实现快照优先和明细兜底，可让现有 dashboard 回归测试继续覆盖 API 行为 | 2026-06-07 / agent |
| Phase 6.3 用 `collection_jobs.source_job_id` 桥接旧 dashboard job_id | 兼容期 URL 仍传 legacy `job_id`，快照绑定的是新 `collection_job_id` 和 `analysis_run_id`；通过 source job 桥接避免打断旧入口 | 2026-06-07 / agent |
| Phase 6.3 只迁移 `brand_metrics_v1` 能完整表达的读取面 | category、domain、url、content_type 和发稿链接等明细维度暂未进入指标快照；直接迁移会造成口径丢失 | 2026-06-07 / agent |
| Phase 6.4 将快照质量信息挂在 `brand-metrics.metadata` | 首页 dashboard 已读取 `brand-metrics`，metadata 能承载数据来源、新鲜度、覆盖率和分析完整性，且不破坏现有 data 数组契约 | 2026-06-07 / agent |
| Phase 6.4 快照质量查询失败时降级为 `legacy_aggregation` 标记 | 质量提示不能让核心 dashboard 数据读取失败；缺失快照或兼容期旧数据应明确展示为明细聚合和快照未生成 | 2026-06-07 / agent |

## Context and Orientation

已落档文档：

| 类型 | 文件 |
|---|---|
| 产品规格 | `docs/product-specs/20260606-brand-monitoring-system-refactor.md` |
| 架构设计 | `docs/design-docs/20260606-brand-monitoring-target-architecture.md` |
| 架构评估 | `docs/design-docs/20260606-brand-monitoring-business-architecture-refactor.md` |
| 参考文档 | `docs/references/20260606-brand-monitoring-domain-data-reference.md` |
| 执行计划 | `docs/exec-plans/active/20260606-brand-monitoring-system-refactor.md` |

关键现有代码区域：

| 区域 | 说明 |
|---|---|
| `api/database/schema_business.sql` | 当前业务表，后续要迁移或兼容。 |
| `api/v1/routes/query_jobs.py` | 当前任务加载、领取、上报入口。 |
| `api/v1/routes/conversation.py` | 当前原始对话和引用入库入口。 |
| `api/v1/services/dashboard_service.py` | 当前 dashboard 读服务。 |
| `api/v1/repositories/*` | 当前 SQL 查询和任务状态更新。 |
| `analysis/src/analyzer.py` | 当前分析批处理编排器。 |
| `analysis/src/plugins/metrics/*` | 当前品牌提及和引用分析插件。 |
| `web/src/config/routes.js` | 当前租户工作台路由。 |
| `web/src/components/*` | 当前 dashboard、任务和账户页面。 |

## Plan of Work

### Phase 2: 稳定现有 MVP

目标：先修复会污染后续迁移的数据风险。

1. 检查 `qa_brand_state`、`qa_reference`、`llm_conversation_references` 的重复数据。
2. 为 `qa_brand_state` 增加兼容期唯一键 `(tenant_key, job_id, conversation_id, brand)`。
3. 评估引用表唯一键是否需要纳入 `job_id` 和 `url_hash`。
4. 将 `analysis/config/analysis_config.json` 中的真实数据库连接迁移为 example 和环境变量。
5. 为 `conversation/load` 与 `query-jobs/report` 补充一致性测试，明确入库失败时不能完成执行次数。
6. 更新 `docs/exec-plans/tech-debt-tracker.md`，记录暂不处理的兼容风险。

验证：

- `pytest api/tests/`
- `ruff check api`
- `python scripts/validate_agents_docs.py --level ERROR`

### Phase 3: 引入监测项目

目标：新增项目模型，但不破坏旧 dashboard。

1. 新增项目相关 schema：`monitoring_projects`、`project_brands`、`prompt_sets`、`prompt_items`。
2. 新增后端项目 Repository、Service、Route 和 Pydantic schema。
3. 新增前端项目列表、项目详情壳层和项目设置初版。
4. 新建任务时允许选择项目，并将 `job_id` 与 `project_id` 关联。
5. 平台租户列表和租户工作台保留旧任务入口，同时新增项目入口。

验证：

- 项目 CRUD 后端测试。
- 前端项目路由和 API adapter 测试。
- `npm --prefix web run build`

### Phase 4: 拆分采集运行模型

目标：让执行器采集过程可追踪。

1. 新增 `collection_jobs`、`collection_tasks`、`collection_attempts`。
2. 为执行器 fetch 增加 lease，防止并发重复领取。
3. 新增 attempt start/complete API。
4. 将旧 `/api/v1/query-jobs/fetch` 兼容映射到新任务模型。
5. 平台后台展示执行器健康、队列长度和失败任务。

验证：

- 并发领取测试。
- attempt 失败重试测试。
- 执行器 scope 安全测试。

### Phase 5: 接入分析运行

目标：让分析过程进入系统生命周期。

1. 新增 `analysis_runs` 和分析运行 Repository/Service。
2. 将 `analysis/` 中可复用插件封装为内部 service 调用入口。
3. 分析结果写入事实表时绑定 `analysis_run_id`。
4. dashboard 和任务状态页展示采集完成但分析中的状态。
5. 失败时记录错误并支持 retry。

验证：

- analysis run 状态机测试。
- 插件入库幂等测试。
- 失败重试测试。

### Phase 6: 建设指标快照

目标：dashboard 从稳定 read model 取数。

1. 新增 `metric_snapshots`。
2. 明确品牌提及率、首位提及率、Top3 提及率、信源引用率、情绪占比的口径版本。
3. 分析成功后生成指标快照。
4. 改造 `DashboardService`，优先读快照，缺失时兼容旧明细聚合。
5. 前端展示数据新鲜度和覆盖率。

验证：

- 指标口径单元测试。
- 旧 dashboard 回归测试。
- 前端数据完整性展示测试。

### Phase 7: 完善客户交付闭环

目标：补齐业务系统体验。

1. 新增问答快照页，支持按平台、关键词、品牌、情绪和引用过滤。
2. 接入真实情感分析数据，移除正式页面 mock 口径。
3. 新增告警规则和告警事件。
4. 新增报告列表和报告导出基础能力。
5. 增加数据质量页面，展示失败采集、过期分析和指标覆盖率。

验证：

- 关键页面构建和交互测试。
- 告警规则触发测试。
- 报告导出契约测试。

### Phase 8: 清理兼容层

目标：当项目模型和新 read model 稳定后，减少旧概念暴露。

1. 将旧 job 路由从主导航隐藏或跳转到项目运行页。
2. 将旧 dashboard 路由改为项目路由的兼容入口。
3. 清理不再使用的 mock、旧配置和重复文档。
4. 更新 `docs/ARCHITECTURE.md`、`docs/DESIGN.md`、`docs/SECURITY.md` 和 README。
5. 完成后移动本 ExecPlan 到 `docs/exec-plans/completed/` 并更新索引。

验证：

- 全量后端测试。
- 全量前端测试。
- 前端构建。
- 文档 ERROR/WARN 验证。

## Validation and Acceptance

验证记录：

- 2026-06-06 / Phase 2.3：`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（88 passed, 184 warnings）；`python scripts/validate_agents_docs.py --level ERROR` 和 `--level WARN` 均为 0 错误、0 警告；`TASKS.md` Phase 2.3 状态一致性检查通过。
- 2026-06-06 / Phase 2.4：先新增 `analysis/tests/test_database_config.py` 并确认在旧配置下失败；完成后 `$env:PYTHONPATH='analysis'; api\.venv\Scripts\python.exe -m pytest analysis\tests\test_database_config.py -q` 通过；`uv run --with pytest --with requests --with sqlalchemy --with pymysql --python 3.13 python -m pytest analysis\tests\test_database_config.py analysis\tests\test_reference_status.py analysis\tests\test_import_data.py analysis\tests\test_save_plugin_batch_result.py -q` 通过（15 passed）；analysis 受影响文件 ruff 通过；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（88 passed, 184 warnings）；文档 ERROR/WARN 验证通过；固定字符串搜索未再发现旧本地数据库 host 或旧明文密码字段；`TASKS.md` Phase 2.4 状态一致性检查通过。
- 2026-06-07 / Phase 2.5：先新增 `api/tests/test_conversation_report_consistency.py` 并确认旧实现下 `conversation/load` 失败后 `query-jobs/report` 仍返回 success=True；修复后该测试文件通过（2 passed）；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（90 passed, 196 warnings）；文档 ERROR/WARN 验证通过；`TASKS.md` Phase 2.5 状态一致性检查通过。
- 2026-06-07 / Phase 2.6：更新 `docs/exec-plans/tech-debt-tracker.md`，记录 Phase 2 未关闭兼容风险及清理条件；`python scripts/validate_agents_docs.py --level ERROR` 和 `--level WARN` 均为 0 错误、0 警告；`TASKS.md` Phase 2.6 状态一致性检查通过。
- 2026-06-07 / Phase 3.1：先新增 `api/tests/test_monitoring_project_schema.py` 并确认旧 schema 缺少监测项目模型时失败；补齐 MySQL/SQLite schema 和迁移脚本后，定向 schema 测试通过（3 passed）；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（93 passed, 196 warnings）；文档 ERROR/WARN 验证通过；`TASKS.md` Phase 3.1 状态一致性检查通过。
- 2026-06-07 / Phase 3.2：先新增 `api/tests/test_projects_api.py` 并确认缺少 `projects` 路由时失败；补齐 Pydantic 契约、Repository、Service、Route 和 `/api/v1/projects` 注册后，定向项目 API 测试通过（8 passed）；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（101 passed, 277 warnings）；文档 ERROR/WARN 验证通过；`TASKS.md` Phase 3.2 状态一致性检查通过。
- 2026-06-07 / Phase 3.3：先新增项目 API adapter、路由和展示纯函数测试，并确认缺少前端入口时失败；补齐 `ProjectListPage`、`ProjectDetailPage`、`fetchProjects`、`fetchProjectDetail`、路由配置和侧边栏图标后，前端定向测试通过（12 passed）；`npm --prefix web test` 通过（60 passed）；`npm --prefix web run lint` 无错误（保留既有 warning）；`npm --prefix web run build` 通过；使用系统 Chrome + Playwright 对 `/projects/:tenantKey` 和 `/projects/:tenantKey/:projectId` 做桌面/移动 smoke test 通过；文档 ERROR/WARN 验证通过；`TASKS.md` Phase 3.3 状态一致性检查通过。
- 2026-06-07 / Phase 3.4：先新增 `api/tests/test_query_jobs_project_link.py`、`api/tests/test_query_job_project_link_schema.py` 和 `web/src/components/query-jobs/__tests__/queryJobForm.test.js` 并确认旧实现下失败；补齐 `llm_query_jobs.project_id` schema/迁移、`LoadQueryJobsRequest.project_id`、项目归属校验、query job 插入映射和前端项目选择后，`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（106 passed, 321 warnings）；`npm --prefix web test` 通过（64 passed）；`npm --prefix web run lint` 无错误（保留既有 9 warnings）；`npm --prefix web run build` 通过；系统 Chrome + Playwright 桌面/移动 smoke test 通过；文档 ERROR/WARN 验证通过；`TASKS.md` Phase 3.4 状态一致性检查通过。
- 2026-06-07 / Phase 4.1：先新增 `api/tests/test_collection_lifecycle_schema.py` 并确认缺少 `collection_jobs`、`collection_tasks`、`collection_attempts` 和迁移脚本时失败；补齐 MySQL/SQLite schema、analysis schema 镜像和 `api/database/migrations/20260607_add_collection_lifecycle_model.mysql.sql` 后，定向 schema 测试通过（3 passed）；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（109 passed, 321 warnings）。本阶段未改前端。
- 2026-06-07 / Phase 4.2：先新增 `api/tests/test_collection_tasks_fetch.py` 并确认缺少 `collection_tasks` 路由时失败；补齐 `GET /api/v1/collection-tasks/fetch`、`FetchCollectionTaskResponse`/`CollectionTaskDetail` 和 `api/v1/repositories/collection_tasks.py` 后，定向领取测试通过（5 passed），覆盖 pending 领取、连续领取不重复、活跃租约隔离、lease 过期重领和租户过滤；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（114 passed, 513 warnings）；文档 ERROR/WARN 验证通过。本阶段未改前端。
- 2026-06-07 / Phase 4.3：先新增 `api/tests/test_collection_attempts_api.py` 并确认缺少 `collection_attempts` 路由时失败；补齐 `POST /api/v1/collection-attempts/{attempt_id}/start`、`POST /api/v1/collection-attempts/{attempt_id}/complete`、Pydantic 契约和 `api/v1/repositories/collection_attempts.py` 后，定向 attempt 测试通过（5 passed），覆盖 start 成功、非 lease 持有者拒绝、complete 成功、失败后重试和 timeout 达上限终止；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（119 passed, 651 warnings）；文档 ERROR/WARN 验证通过。本阶段未改前端。
- 2026-06-07 / Phase 4.4：先新增 `api/tests/test_platform_collection_health.py`、`web/src/api/__tests__/platform.test.js` 和 `web/src/components/platform/__tests__/executorHealthPresentation.test.js` 并确认缺少平台采集健康接口、前端 API 导出和展示归一化模块时失败；补齐 `GET /api/v1/platform/collection-health`、`api/v1/repositories/platform_health.py`、`PlatformExecutorsPage` 和 `/platform/executors` 路由后，后端定向测试通过（2 passed），前端定向测试通过（6 passed）；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（121 passed, 750 warnings）；`npm --prefix web test` 通过（67 passed）；`npm --prefix web run lint` 无错误，保留既有 9 个 warning；`npm --prefix web run build` 通过；系统 Chrome 对 `http://127.0.0.1:3001/platform/executors` 做 mock 数据 smoke test 通过；文档 ERROR/WARN 验证通过。
- 2026-06-07 / Phase 5.1：先新增 `api/tests/test_analysis_run_schema.py` 并确认 MySQL/SQLite/analysis schema 与迁移脚本缺少 `analysis_runs` 时失败；补齐 `analysis_runs` schema、analysis 镜像 schema 和 `api/database/migrations/20260607_add_analysis_run_model.mysql.sql` 后，schema 定向测试通过（3 passed）。随后新增 `api/tests/test_analysis_runs_repository.py` 并确认缺少 repository 模块时失败；补齐 `api/v1/repositories/analysis_runs.py` 后，状态机定向测试通过（5 passed），覆盖 pending 创建、running 启动、succeeded 完成、failed 错误记录、stale 标记和非法跳转拒绝；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（129 passed, 828 warnings）；`python scripts/validate_agents_docs.py --level ERROR` 和 `--level WARN` 均为 0 错误、0 警告；`git diff --check` 通过，仅输出既有 LF/CRLF 换行提示。本阶段未改前端。
- 2026-06-07 / Phase 5.2：先新增 `api/tests/test_analysis_fact_lineage_schema.py`、`api/tests/test_analysis_plugins_fact_lineage.py` 和 `api/tests/test_analysis_runner_service.py` 并确认缺少事实血缘字段、插件 upsert 写入和系统分析服务时失败；补齐 `qa_brand_state` / `qa_reference.analysis_run_id` schema 与迁移、插件写入 lineage、`analysis_runner` 内部服务和可选插件导入后，定向测试通过（6 passed, 28 warnings）；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（135 passed, 856 warnings）；`$env:PYTHONPATH='analysis'; uv run --with pytest --with requests --with sqlalchemy --with pymysql --python 3.13 python -m pytest analysis\tests\test_database_config.py analysis\tests\test_reference_status.py analysis\tests\test_import_data.py analysis\tests\test_save_plugin_batch_result.py -q` 通过（15 passed）；`python scripts/validate_agents_docs.py --level ERROR` 和 `--level WARN` 均为 0 错误、0 警告；`git diff --check` 通过，仅输出既有 LF/CRLF 换行提示。本阶段未改前端。
- 2026-06-07 / Phase 5.3：先新增 `api/tests/test_analysis_runs_api.py`、`api/tests/test_analysis_run_retry_service.py`，并扩展 `api/tests/test_analysis_runs_repository.py`；确认缺少 `analysis_runs` 路由、`retry_analysis_run` service 和 succeeded-only 快照候选查询时失败。补齐 `GET /api/v1/analysis-runs/{analysis_run_id}`、`POST /api/v1/analysis-runs/{analysis_run_id}/retry`、Pydantic 契约、retry service 和 `get_latest_successful_analysis_run_for_collection` 后，定向测试通过（11 passed, 221 warnings）；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（141 passed, 993 warnings）；`python scripts/validate_agents_docs.py --level ERROR` 和 `--level WARN` 均为 0 错误、0 警告；`git diff --check` 通过，仅输出既有 LF/CRLF 换行提示。本阶段未改前端。
- 2026-06-07 / Phase 6.1：先新增 `api/tests/test_metric_snapshot_schema.py` 并确认缺少 `metric_snapshots` 表和迁移脚本时失败；补齐 API MySQL/SQLite schema、analysis schema 镜像和 `api/database/migrations/20260607_add_metric_snapshots.mysql.sql` 后，定向 schema 测试通过（3 passed）；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（144 passed, 993 warnings）；`python scripts/validate_agents_docs.py --level ERROR` 和 `--level WARN` 均为 0 错误、0 警告；`git diff --check` 通过，仅输出既有 LF/CRLF 换行提示。本阶段未改前端，也未实现快照生成逻辑。
- 2026-06-07 / Phase 6.2：先新增 `api/tests/test_metric_snapshot_generation.py` 并确认缺少 `metric_snapshots` 服务时失败；补齐 `api/v1/services/metric_snapshots.py` 和 `api/v1/repositories/metric_snapshots.py` 后，定向指标快照生成测试通过（2 passed, 68 warnings），覆盖提及率、首位提及率、Top3 提及率、正/负/中性/未知情绪占比、任意信源引用率、失败 run 拒绝和重复生成幂等性；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（146 passed, 1061 warnings）；`python scripts/validate_agents_docs.py --level ERROR` 和 `--level WARN` 均为 0 错误、0 警告；`git diff --check` 通过，仅输出既有 LF/CRLF 换行提示。本阶段未改前端，也未迁移 dashboard 查询。
- 2026-06-07 / Phase 6.3：先新增 `api/tests/test_dashboard_metric_snapshot_priority.py` 并确认当前 dashboard 仍返回旧明细聚合结果；补齐 `metric_snapshots` dashboard 读函数，并让 `brand_mention` / `filter_metadata` 相关仓储快照优先、旧明细兜底后，定向快照优先测试通过（5 passed, 88 warnings），旧 dashboard 回归组合通过（26 passed, 88 warnings）；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（151 passed, 1143 warnings）；`python scripts/validate_agents_docs.py --level ERROR` 和 `--level WARN` 均为 0 错误、0 警告；`git diff --check` 通过，仅输出既有 LF/CRLF 换行提示。本阶段未改前端，也未迁移 category 或引用明细相关 dashboard 读取面。
- 2026-06-07 / Phase 6.4：先新增后端快照质量 metadata 测试、`brand-metrics` 路由透传测试、前端 metadata 归一化测试和 `BrandMentionRate` 展示契约测试，并确认旧实现缺少对应方法、工具和展示文案时失败；补齐 `query_snapshot_quality_metadata`、`DashboardService.get_metric_snapshot_metadata`、`brand-metrics.metadata` 扩展、前端指标质量面板和空状态文案后，后端定向组合通过（29 passed, 110 warnings），前端定向组合通过（4 passed）；`uv run --project api ruff check api` 通过；`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` 通过（154 passed, 1165 warnings）；`npm --prefix web test` 通过（71 passed）；`npm --prefix web run lint` 无错误，保留既有 9 个 warning；`npm --prefix web run build` 通过；系统 Chrome + Playwright 对首页 dashboard 做桌面/移动 mock smoke test 通过，确认质量面板不横向溢出且生成时间、覆盖率、分析完整性完整可见；文档 ERROR/WARN 验证通过；`git diff --check` 通过，仅输出既有 LF/CRLF 换行提示。

阶段性验收：

- 每个阶段结束时，更新本计划 Progress、Decision Log 和验证记录。
- 涉及业务行为的阶段必须新增或更新 product spec/design/reference 文档。
- 所有业务查询继续强制携带服务端校验后的 `tenant_key`。
- 旧 dashboard 和执行器兼容期内必须有回归测试。

最终验收：

- 租户用户以监测项目为主线使用系统。
- 采集、分析、指标和看板都能追溯到项目、采集批次、attempt 和 analysis run。
- dashboard 指标来自可版本化、可解释的快照。
- 问答快照、告警、报告和数据质量至少具备可用 MVP。
- 不再依赖手动运行外部 CLI 才能让 dashboard 获得核心指标。

## Outcomes & Retrospective

待后续实施阶段更新。
