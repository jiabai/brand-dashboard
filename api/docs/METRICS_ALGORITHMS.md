# 指标算法说明（Dashboard）

本文用于对 Dashboard API 中各指标的计算口径做文字化说明，便于前后端与分析同学对齐理解。本文内容对应 [DASHBOARD_API_README.md] 中“品牌总指标 API / 平台指标 / 引用指标 / 域名分布”部分。

## 通用口径

### 时间范围（timeframe / date）

- timeframe 取值：`yesterday`、`7days`、`30days`，在 SQL 中作为 `<timeframe>` 天数使用。
- 默认按数据库当前日期 `CURDATE()` 计算区间：
  - 区间下界：`date >= CURDATE() - INTERVAL <timeframe> DAY`
  - 多数接口包含上界：`date <= CURDATE()`
- `date` 参数（`YYYYMMDD`）用于指定具体日期的场景；若实现侧支持，通常等价于将日期过滤为该天（`date = <date>`）或将区间收敛为只包含该天。

### “问题 / 对话”与“记录”粒度

- `conversation_id` 表示一次对话/一次回答记录的唯一标识；在当前库表定义中，它通常对应某个平台的一次 AI 对话，因此不同 AI 平台一般会是不同的 `conversation_id`。
- `qa_brand_state` 属于“品牌状态明细表”，通常是一条对话/回答会对应多条品牌记录（同一 `conversation_id` 下按 `brand` 拆分成多行）。
- `prompt_count` 使用 `COUNT(DISTINCT conversation_id)` 统计，对同一 `conversation_id` 的多行品牌记录去重后计数。
- `SUM(is_mentioned)` / `SUM(is_first_mentioned)`使用记录级别求和；在 `qa_brand_state` 按品牌拆分的前提下，它等价于“某品牌在多少个对话/回答中被提及/首提”的计数，再除以 `prompt_count` 得到该品牌在对话/回答维度的提及/首提比例。

## 1. 品牌总指标（/api/dashboard/brand-metrics）

数据来源：`qa_brand_state`

### 指标：prompt_count（问题总数）

- 定义：在指定 user_id、job_id、时间范围内，该品牌相关数据覆盖的“问题”数量。
- 算法：`COUNT(DISTINCT conversation_id)`
- 说明：即使同一问题有多条明细记录，也只计 1 次。

### 指标：mention_rate（总提及率）

- 定义：品牌被提及的强度，按“记录级提及次数 / 问题总数”计算。
- 算法：`SUM(is_mentioned) / COUNT(DISTINCT conversation_id)`
- 解释：
  - `is_mentioned` 通常为 0/1，表示该条记录对应的回答/状态是否提及该品牌。
  - 在 `qa_brand_state` 按品牌拆分记录的情况下，该指标等价于“该品牌在多少个对话/回答中被提及 ÷ 对话/回答总数”。

### 指标：first_mention_rate（首位提及率）

- 定义：品牌作为“首个被提及品牌”的强度，按“记录级首提次数 / 问题总数”计算。
- 算法：`SUM(is_first_mentioned) / COUNT(DISTINCT conversation_id)`
- 解释：`is_first_mentioned` 通常为 0/1，表示该条记录对应的回答中该品牌是否为首次提及品牌；口径与 `mention_rate` 相同，只是事件从“提及”替换为“首提”。

### 指标：keyword_coverage（关键词覆盖数）

- 定义：在答案提及品牌（`is_mentioned = 1`）的前提下，该品牌覆盖到的关键词数量（去重）。
- 算法：`COUNT(DISTINCT CASE WHEN is_mentioned = 1 THEN keyword END)`
- 解释：用于描述品牌被提及时的“话题覆盖面”，而不是提及强度。

### 指标：citation_rate_by_post / citation_source_count

- 当前算法：在该接口中固定为 0（占位字段），对应的真实计算由引用相关接口提供。

### 维度：brand 参数

- 不传 `brand`：按 `brand` 分组返回所有品牌指标，并按 `mention_rate DESC, brand ASC` 排序。
- 传 `brand=xxx`：只返回指定品牌的指标。

## 2. 品牌分平台提及率（/api/dashboard/platform-metrics-by-brand）

数据来源：`qa_brand_state`

### 指标：platform 维度下的 mention_rate（平台提及率）

- 定义：在指定品牌下，不同平台的提及率，按“平台内提及记录数 / 平台内总记录数”计算。
- 算法：`SUM(is_mentioned) / COUNT(*)`，按 `platform` 分组。
- 解释：
  - 分母 `COUNT(*)` 是该品牌在该平台的记录条数（通常对应该平台回答覆盖的问题数/回答数）。
  - 分子 `SUM(is_mentioned)` 是该平台中提及该品牌的记录条数（或提及次数累计）。

## 3. 发文引用率与引用信源数（/api/dashboard/post-citation-rate）

数据来源：`qa_reference`

### 指标：citation_source_count（引用信源数量）

- 定义：指定品牌在时间范围内被引用到的域名数量（去重）。
- 算法：`COUNT(DISTINCT qr.domain)`
- 说明：只统计 `qa_reference` 中出现过的 `domain`；若存在空域名，是否计入取决于数据清洗与查询条件（当前 SQL 未显式排除 NULL）。

### 指标：citation_rate_by_post（发文引用率）

- 定义：在时间范围内，有“发文引用链接”的问题占比。
- 算法（两段式）：
  - 先按 `conversation_id` 聚合：`has_published_link = MAX(is_published_link)`，表示该问题下是否至少存在 1 条 `is_published_link = 1` 的引用记录。
  - 再对所有问题取平均：`AVG(has_published_link)`，得到比例；若无数据则用 `COALESCE(..., 0)` 返回 0。
- 解释：该指标反映“问题层面是否出现过发文链接”的覆盖率，而非引用条数占比。

## 4. 域名引用率分布（/api/dashboard/domain-citation-rate）

数据来源：`qa_reference`

### 指标：domain-citation-rate（域名引用率）

- 定义：在指定品牌、时间范围内，各域名在全部引用记录中的占比。
- 算法：
  - 分子：`COUNT(*)`（该域名出现的引用记录条数）
  - 分母：同口径过滤条件下的全部引用记录条数 `SELECT COUNT(*) ...`
  - 百分比：`COUNT(*) * 100.0 / total_count`，并 `ROUND(..., 2)` 保留两位小数
- 说明：
  - 查询显式要求 `domain IS NOT NULL`，因此只统计域名非空的引用记录。
  - 时间过滤在示例 SQL 中只写了下界 `date >= CURDATE() - INTERVAL <timeframe> DAY`（未写上界），口径上等价于“从当前日期往前 N 天（含）到现在的数据”，实际是否包含未来日期取决于数据本身。
