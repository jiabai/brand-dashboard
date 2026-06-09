# 移除指标快照设计决策

## 背景

当前分支把 `metric_snapshots` 设计成 dashboard、报告、告警和数据质量的指标 read model，但快照生成没有接入分析成功后的主链路，也没有失效、重算和保留策略。生产上线后会出现“分析事实已更新，但快照仍缺失或过期”的数据解释问题。

本分支仍处于新设计阶段，优先选择更简单、可验证的数据链路：分析结果写入事实表，读取面直接按事实表聚合。后续只有在性能、审计冻结或异步导出确实需要时，才重新设计专门的 read model。

## 决策

移除指标快照机制。`metric_snapshots` 不再作为 schema、服务、仓储、测试或前端展示的一部分。

新的指标来源如下：

| 读取面 | 数据来源 | 说明 |
|------|------|------|
| Dashboard 品牌指标、趋势、平台指标 | `qa_brand_state` | 以成功分析运行绑定的品牌事实为主；旧兼容入口仍允许通过 `job_id` 读取历史事实。 |
| Dashboard 筛选元数据 | `qa_brand_state` | 关键词、平台、品牌维度直接从事实表聚合。 |
| 情感分析 | `qa_brand_state.sentiment_status` | 不再读取情绪快照比例。 |
| 报告核心指标 | `qa_brand_state`、`qa_reference`、`analysis_runs` | 报告结果仍保存在 `generated_reports`，但核心指标 JSON 来自事实聚合。 |
| 告警评估 | `qa_brand_state`、`qa_reference`、`analysis_runs` | 当前 run 与同项目上一条成功 run 的事实指标比较。 |
| 数据质量 | `collection_jobs`、`collection_tasks`、`analysis_runs`、`qa_brand_state` | 展示采集、分析和事实覆盖，不再展示快照覆盖率。 |

## 指标口径

指标口径保留 `brand_metrics_v1`，但含义从“快照口径版本”调整为“事实聚合口径版本”：

- `mention_rate`：提及该品牌的去重回答数 / 该维度去重回答数。
- `first_mention_rate`：首位提及该品牌的去重回答数 / 该维度去重回答数。
- `top3_mention_rate`：Top3 提及该品牌的去重回答数 / 该维度去重回答数。
- `sentiment_negative_ratio`：负面情绪去重回答数 / 有情绪标签的去重回答数。
- `reference_rate`：带引用的去重回答数 / 该维度去重回答数。

所有业务查询必须显式携带 `tenant_key`，项目级查询必须同时携带 `project_id`，并只把 `analysis_runs.status = 'succeeded'` 的运行纳入项目级指标。

## Schema 策略

本分支尚未作为生产基线发布，因此直接从 schema 和迁移清单中移除 `metric_snapshots`。如果某个外部环境已经手动执行过 `20260607_add_metric_snapshots.mysql.sql`，上线前应通过一次性清理脚本或追加 drop migration 处理；不要在生产库中依赖删除历史迁移文件来回滚。

`alert_rules`、`alert_events` 和 `generated_reports` 保留。它们仍是业务交付结果，只是输入指标从快照表改为事实聚合。

## 边界

- 不引入新的缓存、物化表或后台重算任务。
- 不改变旧 dashboard 的 URL 兼容入口。
- 不删除历史完成文档中的阶段记录；新增文档说明当前分支的设计修正。
- 不把前端接入数据库；前端仍只消费 API Adapter。

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 事实表实时聚合在大数据量下变慢 | 先用成功分析运行、时间窗口、品牌/平台/关键词索引控制查询范围；达到性能瓶颈后再评估 read model。 |
| 报告和告警缺少“生成时冻结指标” | 报告继续持久化 `generated_reports.metrics_json`；告警事件继续持久化触发时的 `current_value` 和 `previous_value`。 |
| 文档里遗留快照主线 | 同步更新架构、设计、API 字典和数据库字典，保留历史文档但不再作为当前目标态。 |
