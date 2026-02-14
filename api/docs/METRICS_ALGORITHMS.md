# 指标算法说明（Dashboard）

本文用于对 Dashboard API 中各指标的计算口径做文字化说明，便于前后端与分析同学对齐理解。本文内容对应 [DASHBOARD_API_README.md] 中"品牌总指标 API / 平台指标 / 引用指标 / 域名分布"部分。

## 通用口径

### 时间范围（timeframe / date）

- timeframe 取值：`yesterday`、`7days`、`30days`、`specific_day`。
- 默认按数据库当前日期 `CURDATE()` 计算区间：
  - 区间下界：`date >= CURDATE() - INTERVAL <timeframe> DAY`
  - 多数接口包含上界：`date <= CURDATE()`
- `specific_day` 表示只统计 `date` 指定的那一天，不做任何相对前移。
- `date` 参数（`YYYYMMDD`）用于指定具体日期的场景；在 `specific_day` 下将区间收敛为只包含该天。

### "问题 / 对话"与"记录"粒度

- `conversation_id` 表示一次对话/一次回答记录的唯一标识；在当前库表定义中，它通常对应某个平台的一次 AI 对话，因此不同 AI 平台一般会是不同的 `conversation_id`。
- `qa_brand_state` 属于"品牌状态明细表"，通常是一条对话/回答会对应多条品牌记录（同一 `conversation_id` 下按 `brand` 拆分成多行）。
- `prompt_count` 使用 `COUNT(DISTINCT conversation_id)` 统计，对同一 `conversation_id` 的多行品牌记录去重后计数。
- `SUM(is_mentioned)` / `SUM(is_first_mentioned)` / `SUM(is_top3_mentioned)` 使用记录级别求和；在 `qa_brand_state` 按品牌拆分记录的前提下，它等价于"某品牌在多少个对话/回答中被提及/首提"的计数，再除以 `prompt_count` 得到该品牌在对话/回答维度的提及/首提比例。

### 返回精度

- 所有 rate 字段（`mention_rate`、`first_mention_rate`、`top3_mention_rate`）均返回 4 位小数（0.0000 格式）。
- 百分比字段（如 `domain_citation_rate`）保留 2 位小数。

## 1. 品牌总指标（/api/v1/dashboard/brand-metrics）

数据来源：`qa_brand_state`

### 请求参数

| 参数 | 必填 | 说明 |
|------|------|------|
| tenant_key | 是 | 租户标识 |
| job_id | 是 | 任务ID |
| timeframe | 是 | 时间范围 |
| start_date | 否 | 起始日期（specific_day 时必填） |
| end_date | 否 | 结束日期（specific_day 时必填） |
| brand | 否 | 品牌名称筛选 |
| platform | 否 | 平台名称筛选 |

### 指标：prompt_count（问题总数）

- 定义：在指定 tenant_key、job_id、时间范围内，该品牌相关数据覆盖的"问题"数量。
- 算法：`COUNT(DISTINCT conversation_id)`
- 说明：即使同一问题有多条明细记录，也只计 1 次。

### 指标：mention_rate（总提及率）

- 定义：品牌被提及的强度，按"记录级提及次数 / 问题总数"计算。
- 算法：`SUM(is_mentioned) / COUNT(DISTINCT conversation_id)`
- 解释：
  - `is_mentioned` 通常为 0/1，表示该条记录对应的回答/状态是否提及该品牌。
  - 在 `qa_brand_state` 按品牌拆分记录的情况下，该指标等价于"该品牌在多少个对话/回答中被提及 ÷ 对话/回答总数"。

### 指标：first_mention_rate（首位提及率）

- 定义：品牌作为"首个被提及品牌"的强度，按"记录级首提次数 / 问题总数"计算。
- 算法：`SUM(is_first_mentioned) / COUNT(DISTINCT conversation_id)`
- 解释：`is_first_mentioned` 通常为 0/1，表示该条记录对应的回答中该品牌是否为首次提及品牌；口径与 `mention_rate` 相同，只是事件从"提及"替换为"首提"。

### 指标：top3_mention_rate（前3位提及率）

- 定义：品牌在"前3个被提及品牌"中出现的强度，按"记录级前3提次数 / 问题总数"计算。
- 算法：`SUM(is_top3_mentioned) / COUNT(DISTINCT conversation_id)`
- 解释：`is_top3_mentioned` 通常为 0/1，表示该条记录对应的回答中该品牌是否在前3个被提及品牌中。

### 指标：keyword_coverage（关键词覆盖数）

- 定义：在答案提及品牌（`is_mentioned = 1`）的前提下，该品牌覆盖到的关键词数量（去重）。
- 算法：`COUNT(DISTINCT CASE WHEN is_mentioned = 1 THEN keyword END)`
- 解释：用于描述品牌被提及时的"话题覆盖面"，而不是提及强度。

### 维度参数

| 参数 | 说明 |
|------|------|
| brand | 不传时按 brand 分组返回所有品牌；传入时只返回指定品牌 |
| platform | 不传时返回所有平台数据；传入时只返回指定平台数据 |

### 排序规则

- 默认排序：`mention_rate DESC, brand ASC`
- 先按提及率降序，再按品牌名称升序

## 2. 品牌分平台提及率（/api/v1/dashboard/platform-metrics-by-brand）

数据来源：`qa_brand_state`

### 请求参数

| 参数 | 必填 | 说明 |
|------|------|------|
| tenant_key | 是 | 租户标识 |
| job_id | 是 | 任务ID |
| brand | 是 | 品牌名称 |
| timeframe | 是 | 时间范围 |
| start_date | 否 | 起始日期（specific_day 时必填） |
| end_date | 否 | 结束日期（specific_day 时必填） |

### 指标：platform 维度下的 mention_rate（平台提及率）

- 定义：在指定品牌下，不同平台的提及率，按"平台内提及记录数 / 平台内总记录数"计算。
- 算法：`SUM(is_mentioned) / COUNT(*)`，按 `platform` 分组。
- 解释：
  - 分母 `COUNT(*)` 是该品牌在该平台的记录条数（通常对应该平台回答覆盖的问题数/回答数）。
  - 分子 `SUM(is_mentioned)` 是该平台中提及该品牌的记录条数（或提及次数累计）。

## 3. 发文引用率与引用信源数（/api/v1/dashboard/post-citation-rate）

数据来源：`qa_reference`

### 请求参数

| 参数 | 必填 | 说明 |
|------|------|------|
| tenant_key | 是 | 租户标识 |
| job_id | 是 | 任务ID |
| brand | 是 | 品牌名称 |
| timeframe | 是 | 时间范围 |
| start_date | 否 | 起始日期（specific_day 时必填） |
| end_date | 否 | 结束日期（specific_day 时必填） |

### 指标：citation_source_count（引用信源数量）

- 定义：指定品牌在时间范围内被引用到的域名数量（去重）。
- 算法：`COUNT(DISTINCT qr.domain)`
- 说明：只统计 `qa_reference` 中出现过的 `domain`；若存在空域名，是否计入取决于数据清洗与查询条件（当前 SQL 未显式排除 NULL）。

### 指标：citation_rate_by_post（发文引用率）

- 定义：在时间范围内，有"发文引用链接"的问题占比。
- 算法（两段式）：
  - 先按 `conversation_id` 聚合：`has_published_link = MAX(is_published_link)`，表示该问题下是否至少存在 1 条 `is_published_link = 1` 的引用记录。
  - 再对所有问题取平均：`AVG(has_published_link)`，得到比例；若无数据则用 `COALESCE(..., 0)` 返回 0。
- 解释：该指标反映"问题层面是否出现过发文链接"的覆盖率，而非引用条数占比。

## 4. 域名引用率分布（/api/v1/dashboard/citation-domain-stats）

数据来源：`qa_reference`

### 请求参数

| 参数 | 必填 | 说明 |
|------|------|------|
| tenant_key | 是 | 租户标识 |
| job_id | 是 | 任务ID |
| brand | 是 | 品牌名称 |
| timeframe | 是 | 时间范围 |
| start_date | 否 | 起始日期（specific_day 时必填） |
| end_date | 否 | 结束日期（specific_day 时必填） |
| keyword | 否 | 关键词筛选 |
| platform | 否 | 平台筛选 |

### 指标：domain-citation-rate（域名引用率）

- 定义：在指定品牌、时间范围内，各域名在全部引用记录中的占比。
- 算法：
  - 分子：`COUNT(*)`（该域名出现的引用记录条数）
  - 分母：**仅受 `platform` 影响，不受 `keyword` 影响**（保证贡献度可加性）
  - 百分比：`COUNT(*) * 100.0 / total_count`，并 `ROUND(..., 2)` 保留两位小数
- 说明：
  - 查询显式要求 `domain IS NOT NULL`，因此只统计域名非空的引用记录。
  - 当筛选 `keyword` 时，分母保持不变（品牌/平台层级），以反映该关键词对整体的**贡献度**，而非细分市场占比。
  - 当筛选 `platform` 时，分母同步缩小为该平台内的总引用数。

## 5. 域名引用率汇总（/api/v1/dashboard/citation-domain-summary）

数据来源：`qa_reference`

### 请求参数

| 参数 | 必填 | 说明 |
|------|------|------|
| tenant_key | 是 | 租户标识 |
| job_id | 是 | 任务ID |
| brand | 是 | 品牌名称 |
| timeframe | 是 | 时间范围 |
| start_date | 否 | 起始日期（specific_day 时必填） |
| end_date | 否 | 结束日期（specific_day 时必填） |

### 返回指标

| 指标 | 说明 |
|------|------|
| citation_count | 域名引用次数 |
| keyword_coverage | 域名关键词覆盖数（去重） |
| platform_coverage | 域名平台覆盖数（去重） |
| domain-citation-rate | 域名总引用率（ 指标：百分比） |

###domain-citation-rate（域名总引用率）

- 定义：该域名引用次数占品牌总引用次数的比例。
- 算法：`COUNT(*) * 100.0 / total_count`，按 `domain` 分组降序排列。

## 6. 关键词-平台-品牌提及率明细（/api/v1/dashboard/keyword-platform-brand-rates）

数据来源：`qa_brand_state`

### 请求参数

| 参数 | 必填 | 说明 |
|------|------|------|
| tenant_key | 是 | 租户标识 |
| job_id | 是 | 任务ID |
| timeframe | 是 | 时间范围 |
| start_date | 否 | 起始日期（specific_day 时必填） |
| end_date | 否 | 结束日期（specific_day 时必填） |

### 返回指标

| 指标 | 说明 |
|------|------|
| keyword | 关键词 |
| platform | 平台名称 |
| brand | 品牌名称 |
| mention_rate | 提及率（4位小数） |
| first_mention_rate | 首位提及率（4位小数） |
| top3_mention_rate | 前3位提及率（4位小数） |

### 算法说明

- 按 `keyword + platform + brand` 聚合统计
- 使用 `NULLIF(COUNT(DISTINCT conversation_id), 0)` 避免除零错误
- 排序规则：`keyword ASC, platform ASC, mention_rate DESC`

## 7. 引用类型占比统计（/api/v1/dashboard/citation-type-stats）

数据来源：`qa_reference`

### 请求参数

| 参数 | 必填 | 说明 |
|------|------|------|
| tenant_key | 是 | 租户标识 |
| job_id | 是 | 任务ID |
| timeframe | 是 | 时间范围 |
| start_date | 否 | 起始日期（specific_day 时必填） |
| end_date | 否 | 结束日期（specific_day 时必填） |

### 返回指标

| 指标 | 说明 |
|------|------|
| total_rows | 引用记录总条数 |
| conversations | 去重对话数 |
| content_type | 引用内容类型 |
| type_pct | 该类型占比（百分比，2位小数） |

### 算法说明

- 汇总统计：`COUNT(*)` 和 `COUNT(DISTINCT conversation_id)`
- 类型占比：`COUNT(*) * 100.0 / total_rows`，按占比降序排列
