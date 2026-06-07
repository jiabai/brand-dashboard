# Phase 7.2 真实情感分析数据

## 背景

Phase 7.1 已补齐问答快照页。本阶段继续收敛客户交付页面中的 mock 口径，让正式“情感分析”页面读取真实分析事实或明确展示无数据状态。

## 变更

- 新增 `GET /api/v1/dashboard/sentiment-analysis`，支持按品牌、平台、关键词和时间窗口读取情绪分布。
- 新增 `api/v1/repositories/sentiment_analysis.py`，优先读取 `metric_snapshots` 情绪比例，缺失时兜底读取 `qa_brand_state.sentiment_status`。
- 新增 `SentimentAnalysisResponse` 等 Pydantic 契约。
- 前端新增 `fetchSentimentAnalysis` 和 `normalizeSentimentAnalysis`，情感页不再使用 `MOCK_SENTIMENT` / `WORD_CLOUD_DATA`。
- 情感页关键词栏改为真实筛选入口，真实无数据时展示“暂无真实情感数据”空状态。

## 说明

- 本阶段仍沿用兼容期 dashboard `tenant_key + job_id` 入口，暂不新增项目级情感分析路由。
- `metadata.data_source` 会标记为 `metric_snapshot`、`legacy_fact` 或 `empty`，用于前端区分指标快照、历史明细兜底和真实无数据。

## 验证

- 后端新增情感分析 API 定向测试。
- 前端新增 API adapter、归一化工具和页面契约测试。
- 完整验证结果记录在 active ExecPlan 的 Validation and Acceptance 中。
