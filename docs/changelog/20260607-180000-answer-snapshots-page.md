# Phase 7.1 问答快照页

## 背景

Phase 6 已完成 dashboard 指标快照 read model 和质量展示。Phase 7 开始补齐客户交付闭环，本阶段先让用户能从 dashboard 查看原始问答快照，并按业务维度定位单条回答。

## 变更

- 新增 `GET /api/v1/dashboard/answer-snapshots`，支持按品牌、平台、关键词、情绪、是否引用筛选原始回答。
- 新增 `api/v1/repositories/answer_snapshots.py`，以 `llm_conversations` 为主表，关联 `qa_brand_state` 和 `qa_reference` 输出回答、情绪与引用状态。
- 新增 `AnswerSnapshotItem` / `AnswerSnapshotsResponse` Pydantic 契约。
- 启用前端 `/snapshots/:tenantKey/:jobId` 路由和侧边栏“问答快照”入口。
- 新增 `AnswerSnapshotsPage`，提供品牌、平台、关键词、情绪和引用状态筛选，并展示原始问题、回答和引用明细。
- 新增前端 API adapter 与 `normalizeAnswerSnapshots` 工具函数。

## 边界

- 本阶段仍沿用兼容期 dashboard `tenant_key + job_id` 入口，暂不新增项目级问答快照路由。
- 页面默认读取前 50 条；后续可在数据质量页或项目运行页补充服务端分页。
- 情绪值来自 `qa_brand_state.sentiment_status`，Phase 7.2 会继续收敛真实情感分析页面口径。

## 验证

- 后端新增问答快照 API 定向测试。
- 前端新增 API adapter、归一化工具、页面展示契约和路由测试。
- 完整验证结果记录在 active ExecPlan 的 Validation and Acceptance 中。
