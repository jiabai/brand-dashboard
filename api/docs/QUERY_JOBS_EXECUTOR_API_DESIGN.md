# 执行器任务获取与上报接口设计文档

本文档详细描述了执行器（Executor）如何从 API 获取待执行的 LLM 查询任务，以及如何上报执行结果。

## 1. 设计目标

- **顺序性**：任务应按照物理插入顺序（`id`）执行。
- **均匀性（多轮次循环）**：采用 Round-Robin 策略，确保所有任务都完成第 N 次执行后，才开始第 N+1 次执行。
- **可靠性**：支持执行器崩溃后的任务断点续传。
- **并发安全**：支持多个执行器同时工作而不重复领取相同任务（进阶实现）。

---

## 2. 获取任务接口 (Fetch)

用于执行器拉取当前最该执行的一个任务。

- **路径**: `GET /api/v1/query-jobs/fetch`
- **角色** : 执行器专用
- **认证**: 需要 `X-Executor-Key` (Header) 和 `executor_id` (Query)
- **认证方式**:
 - Header : X-Executor-Key (执行器密钥)
 - Query Param : executor_id (执行器唯一ID)
 - 注：复用现有的 verify_executor 依赖项进行身份校验
- **核心逻辑 (SQL)**:

任务筛选逻辑 (Server Side)

后端在收到请求时，应从 llm_query_jobs 表中筛选符合以下条件的记录：
1. 执行器匹配: executor_id 等于请求者的 ID。
2. 状态激活: query_status = 1 (生效中) 且 is_deleted = 0。
3. 周期未结束:
 - 当前时间在 effective_from 和 effective_to (如果非空) 之间。
4. 次数未达上限: executed_runs < total_runs。
5. **执行频率控制**: 支持同一天内多次执行。`last_executed_date <= CURRENT_DATE` 确保了即使今天已经执行过，只要总次数未满，仍可继续领取。

```sql
SELECT 
  id,job_id,tenant_key,category,brand,competitor,keyword,query_content 
FROM llm_query_jobs
WHERE executor_id = :executor_id
  AND query_status = 1           -- 仅生效任务
  AND is_deleted = 0             -- 未删除
  AND executed_runs < total_runs -- 还没跑满次数
  AND (last_executed_date IS NULL OR last_executed_date <= CURRENT_DATE) -- 支持单日多次执行
ORDER BY 
  executed_runs ASC,             -- 优先级1：跑得最少的轮次优先（实现多轮次循环）
  id ASC                         -- 优先级2：物理顺序优先（实现圈内 Q1->Q16 顺序）
LIMIT 1;
```

- **响应示例**:
  - **有任务时**: 返回任务详情 JSON。
  - **无任务时**: 返回 `200 OK`，`job: null`。

```json
{
  "success": true,
  "count": 1,
  "jobs": {
    "id": 1,
    "job_id": "job_20260123_172515_f38024e2",
    "tenant_key": "tn_1b02b3ef4fbd",
    "category": "游戏",
    "brand": "哈基桃电竞",
    "competitor": ["河马电竞俱乐部"],
    "keyword": "三角洲陪玩",
    "query_content": "三角洲陪玩有什么推荐？"
  }
}
```

---

## 3. 上报执行结果接口 (Report)

用于执行器完成一次抓取任务后同步状态。

- **路径**: `POST /api/v1/query-jobs/report`
- **认证**: 同上
- **请求体**:
```json
{
  "job_id": "job_20260123_172515_f38024e2",
  "status": "success",
  "result_data": { ... }
}
```

- **核心逻辑**:
  1. 将该任务的 `executed_runs` 字段自增1。
  2. 更新 `last_executed_date` 为当前日期。
  3. 将抓取到的对话内容存入 `llm_conversations` 表。

---

## 4. 运行流程示例 (Round-Robin)

假设有任务 Q1, Q2, Q3，每个任务要求跑 2 次 (`total_runs=2`)：

1. **第一圈**:
   - `fetch` -> Q1 (runs=0) -> 执行并 `report` -> Q1 (runs=1)
   - `fetch` -> Q2 (runs=0) -> 执行并 `report` -> Q2 (runs=1)
   - `fetch` -> Q3 (runs=0) -> 执行并 `report` -> Q3 (runs=1)
2. **第二圈**:
   - `fetch` -> Q1 (runs=1) -> 执行并 `report` -> Q1 (runs=2)
   - `fetch` -> Q2 (runs=1) -> 执行并 `report` -> Q2 (runs=2)
   - `fetch` -> Q3 (runs=1) -> 执行并 `report` -> Q3 (runs=2)
3. **结束**:
   - `fetch` -> 所有任务 `runs == total_runs` -> 返回 `null`。

---

## 5. 异常处理

- **并发领取**: 建议在 `fetch` 成功后，将该行记录锁定或标记为 `is_running`，防止其他请求领到同一个任务。
- **任务超时**: 如果一个任务被 `fetch` 后超过 30 分钟未收到 `report`，应重置其状态，允许再次被 `fetch`。
