# Dashboard API 字典

> 更新日期：2026-06-09
> 事实源：`api/v1/routes/dashboard.py`、`api/v1/models/schemas.py`、`app.openapi()`
> 适用范围：`/api/v1/dashboard/*` 读取接口。该组接口仍以 `tenant_key + job_id` 为主要查询边界，主要服务历史 dashboard 页面、排障读面和部分当前前端页面。

## 1. 当前接口总览

当前 FastAPI OpenAPI 中共有 14 个 dashboard 接口：

| 接口 | 方法 | 用途 | 主要数据来源 |
|------|------|------|--------------|
| `/api/v1/dashboard/available-dates` | GET | 查询某租户/任务有数据的日期 | `qa_brand_state` |
| `/api/v1/dashboard/filter-metadata` | GET | 查询可用平台、关键词和平台-关键词组合 | `qa_brand_state` |
| `/api/v1/dashboard/brand-metrics` | GET | 品牌总指标排行 | `qa_brand_state` |
| `/api/v1/dashboard/platform-metrics-by-brand` | GET | 指定品牌的分平台提及率 | `qa_brand_state` |
| `/api/v1/dashboard/keyword-platform-brand-rates` | GET | 关键词-平台-品牌维度提及率明细 | `qa_brand_state` |
| `/api/v1/dashboard/brand-mention-trend` | GET | 指定品牌/平台/关键词的日趋势 | `qa_brand_state` |
| `/api/v1/dashboard/platform-mention-rates` | GET | legacy 品牌分平台提及率卡片 | `qa_brand_state` |
| `/api/v1/dashboard/answer-snapshots` | GET | 原始问答快照列表 | `llm_conversations`、`qa_brand_state`、`qa_reference` |
| `/api/v1/dashboard/sentiment-analysis` | GET | 情感分布和关键词情感明细 | `qa_brand_state` |
| `/api/v1/dashboard/post-citation-rate` | GET | 发文引用率和引用信源数 | `qa_reference` |
| `/api/v1/dashboard/citation-domain-summary` | GET | 域名引用汇总 | `qa_reference` |
| `/api/v1/dashboard/citation-domain-stats` | GET | 域名引用率分布 | `qa_reference` |
| `/api/v1/dashboard/citation-url-stats` | GET | 指定域名下的引用 URL 排名 | `qa_reference` |
| `/api/v1/dashboard/citation-type-stats` | GET | 引用内容类型占比 | `qa_reference` |

已不再存在的旧接口：brand mention rate dashboard 读面。不要在新代码或文档中继续引用它。

## 2. 通用约定

### 2.1 鉴权和租户上下文

所有 dashboard 接口挂载了 `get_current_tenant_for_dashboard_read` 依赖：

| 项 | 说明 |
|----|------|
| `Authorization` | 必须传 `Bearer <access_token>`。OpenAPI 中该 header 因 FastAPI 依赖写法显示为可选，但运行时没有有效 token 会返回 401。 |
| `tenant_key` | 当前 dashboard 读面仍通过 query 参数接收租户标识，绝大多数接口必填。 |
| `X-Tenant-Key` | 可作为 header 传入租户上下文。若同时传 `X-Tenant-Key` 和 query `tenant_key`，两者必须一致，否则返回 400。 |
| 租户成员 | 当前用户必须是该租户 active 成员，且租户、成员关系均为 active。 |
| 平台管理员 | 若用户具备 `platform_admin` 角色，可以只读访问 active 租户的 dashboard 数据，返回上下文角色为 `platform_admin_readonly`。 |

推荐请求格式：

```bash
curl -H "Authorization: Bearer <access_token>" \
  -H "X-Tenant-Key: tn_demo" \
  "http://localhost:8000/api/v1/dashboard/brand-metrics?tenant_key=tn_demo&job_id=job_demo&timeframe=30days"
```

### 2.2 时间窗口

`TimeFrame` 枚举：

| 值 | 含义 |
|----|------|
| `yesterday` | 昨日 |
| `7days` | 最近 7 天 |
| `30days` | 最近 30 天 |
| `specific_day` | 指定日期范围 |

通用规则：

- 使用 `specific_day` 时，绝大多数接口要求传 `start_date` 和 `end_date`，格式为 `YYYYMMDD`。
- `brand-mention-trend` 的 `start_date`、`end_date` 在路由层始终必填；当 `timeframe` 不是 `specific_day` 时，服务层仍按 `timeframe` 计算实际窗口。
- `platform-mention-rates` 使用单独的 `date` 参数作为指定日期，格式为 `YYYYMMDD`。
- `available-dates` 返回日期格式为 `YYYY-MM-DD`；其他响应 metadata 中的 `start_date`、`end_date` 通常为 `YYYYMMDD`。

### 2.3 rate 单位

不要只看字段名猜单位：

| 字段/接口 | 单位 |
|-----------|------|
| `brand-metrics.mention_rate`、`first_mention_rate`、`top3_mention_rate` | 比例，`0~1` |
| `platform-metrics-by-brand.mention_rate` | 比例，`0~1` |
| `keyword-platform-brand-rates.*_rate` | 比例，`0~1` |
| `brand-mention-trend.mention_rate` | 比例，`0~1` |
| `sentiment-analysis.ratio` | 比例，`0~1` |
| `post-citation-rate.citation_rate_by_post` | 比例，`0~1` |
| `platform-mention-rates.mention_rate`、`first_mention_rate` | 百分比数值，`0~100` |
| `citation-domain-stats.domain_citation_rate` | 百分比数值，`0~100` |
| `citation-domain-summary.domain-citation-rate` | 百分比数值，`0~100` |
| `citation-url-stats.citation_rate` | 百分比数值，`0~100` |
| `citation-type-stats.type_pct` | 百分比数值，`0~100` |

### 2.4 常见响应和错误

多数接口响应形态为：

```json
{
  "status": "success",
  "data": [],
  "metadata": {}
}
```

例外：

- `filter-metadata` 返回 `{ "code": 200, "message": "success", "data": ... }`。
- `citation-type-stats` 返回 `{ "status": "success", "summary": ..., "citation_type_stats": ..., "metadata": ... }`。
- 引用域名接口使用 `domain_distribution` 字段，而不是 `data`。

常见错误：

| HTTP 状态 | 场景 |
|-----------|------|
| 400 | 租户上下文冲突、缺少租户上下文、日期格式错误、`specific_day` 缺少日期、开始日期晚于结束日期 |
| 401 | 缺少或无效 `Authorization: Bearer <access_token>` |
| 403 | 无租户成员关系、租户/成员状态不可用、无平台管理员只读权限 |
| 500 | 数据库查询或服务层未预期异常 |

## 3. 公共参数字典

| 参数 | 类型 | 出现范围 | 说明 |
|------|------|----------|------|
| `tenant_key` | string | query | 租户唯一标识。dashboard 读面目前仍显式接收该参数。 |
| `job_id` | string | query | 历史采集/查询任务 ID。除 `available-dates` 可选外，其余接口必填。 |
| `timeframe` | enum | query | 时间窗口，取值见 `TimeFrame`。 |
| `start_date` | string | query | 起始日期，格式 `YYYYMMDD`。 |
| `end_date` | string | query | 结束日期，格式 `YYYYMMDD`。 |
| `brand` | string | query | 品牌名称。部分接口必填，部分接口作为过滤项。 |
| `platform` | string | query | 平台名称。 |
| `keyword` | string | query | 关键词。 |
| `category` | string | query | legacy 类目参数，仅 `platform-mention-rates` 使用。 |
| `domain` | string | query | 域名，仅 `citation-url-stats` 使用。 |
| `date` | string | query | 指定日期，格式 `YYYYMMDD`，仅 `platform-mention-rates` 使用。 |
| `sentiment` | string | query | 情绪状态过滤，仅 `answer-snapshots` 使用。 |
| `has_reference` | boolean | query | 是否有引用过滤，仅 `answer-snapshots` 使用。 |
| `limit` | integer | query | 分页条数，默认 50，范围 `1~100`。 |
| `offset` | integer | query | 分页偏移，默认 0，最小 0。 |

## 4. 接口字典

### 4.1 GET `/api/v1/dashboard/available-dates`

查询某租户下有 dashboard 明细数据的业务日期。用于时间筛选器初始化。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 否 | 任务 ID；不传时查询该租户全部可用日期。 |

响应字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | 固定为 `success`。 |
| `data` | string[] | 日期列表，格式 `YYYY-MM-DD`，按日期倒序。 |
| `metadata.tenant_key` | string | 请求租户。 |
| `metadata.job_id` | string/null | 请求任务 ID。 |
| `metadata.count` | integer | 日期数量。 |

数据来源：`qa_brand_state.date`。

### 4.2 GET `/api/v1/dashboard/filter-metadata`

查询 dashboard 当前数据窗口内可用的平台、关键词，以及有效的平台-关键词组合。用于筛选器选项。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `start_date` | 否 | 起始日期，`YYYYMMDD`。不传时使用该任务数据最小日期。 |
| `end_date` | 否 | 结束日期，`YYYYMMDD`。不传时使用该任务数据最大日期。 |

响应字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | integer | 当前返回 `200`。 |
| `message` | string | 当前返回 `success`。 |
| `data.platforms` | string[] | 去重平台列表。 |
| `data.keywords` | string[] | 去重关键词列表。 |
| `data.combinations` | object[] | 有效组合列表，元素包含 `platform`、`keyword`。 |

数据来源：`qa_brand_state.platform`、`qa_brand_state.keyword`。

### 4.3 GET `/api/v1/dashboard/brand-metrics`

返回品牌总指标列表，常用于品牌排名和核心 KPI 卡片。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `timeframe` | 是 | 时间窗口。 |
| `start_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `end_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `brand` | 否 | 品牌过滤；不传则返回所有品牌。 |
| `platform` | 否 | 平台过滤；不传则聚合所有平台。 |

响应 `data[]` 字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `brand` | string | - | 品牌名称。 |
| `mention_rate` | number | `0~1` | 总提及率。 |
| `first_mention_rate` | number | `0~1` | 首位提及率。 |
| `top3_mention_rate` | number | `0~1` | 前 3 位提及率。 |
| `prompt_count` | integer | 条 | 当前聚合窗口覆盖的回答/问题数。 |
| `keyword_coverage` | integer | 个 | 被提及时覆盖到的去重关键词数。 |

响应 `metadata` 重点字段：

| 字段 | 说明 |
|------|------|
| `calculation_method` | 当前为 `mention_count_ratio`。 |
| `row_count` | 返回品牌行数。 |
| `data_source` | 当前为 `analysis_fact`。 |
| `metric_definition_version` | 当前为 `brand_metrics_v1`。 |

数据来源：

- 从 `qa_brand_state` 按品牌聚合 `mention_rate`、`first_mention_rate`、`top3_mention_rate`。
- `brand_metrics_v1` 表示当前事实聚合口径版本。

### 4.4 GET `/api/v1/dashboard/platform-metrics-by-brand`

返回指定品牌在各平台下的提及率。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `brand` | 是 | 品牌名称。 |
| `timeframe` | 是 | 时间窗口。 |
| `start_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `end_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |

响应字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `data.brand` | string | - | 请求品牌。 |
| `data.platforms[].platform` | string | - | 平台名称。 |
| `data.platforms[].mention_rate` | number | `0~1` | 该平台下该品牌提及率。 |
| `metadata.calculation_method` | string | - | 当前为 `platform_metrics_by_brand`。 |
| `metadata.row_count` | integer | 条 | 平台数量。 |

数据来源：`qa_brand_state`。

### 4.5 GET `/api/v1/dashboard/keyword-platform-brand-rates`

返回 `keyword + platform + brand` 维度的提及率明细，适合做交叉表或钻取列表。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `timeframe` | 是 | 时间窗口。 |
| `start_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `end_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |

响应 `data[]` 字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `keyword` | string | - | 关键词。 |
| `platform` | string | - | 平台。 |
| `brand` | string | - | 品牌。 |
| `mention_rate` | number | `0~1` | 提及率。 |
| `first_mention_rate` | number | `0~1` | 首位提及率。 |
| `top3_mention_rate` | number | `0~1` | 前 3 位提及率。 |

metadata：

| 字段 | 说明 |
|------|------|
| `calculation_method` | 当前为 `distinct_conversation_ratio`。 |
| `rate_unit` | 当前为 `ratio_0_1`。 |
| `row_count` | 返回明细行数。 |

数据来源：`qa_brand_state`。

### 4.6 GET `/api/v1/dashboard/brand-mention-trend`

返回指定品牌、平台、关键词在日期维度上的提及率趋势。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `brand` | 是 | 品牌名称。 |
| `platform` | 是 | 平台名称。 |
| `keyword` | 是 | 关键词。 |
| `timeframe` | 是 | 时间窗口。 |
| `start_date` | 是 | 起始日期，格式 `YYYYMMDD`。 |
| `end_date` | 是 | 结束日期，格式 `YYYYMMDD`。 |

响应 `data[]` 字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `date` | string | - | 日期，格式 `YYYYMMDD`。 |
| `brand` | string | - | 品牌。 |
| `platform` | string | - | 平台。 |
| `keyword` | string | - | 关键词。 |
| `mention_rate` | number | `0~1` | 当日提及率。 |

metadata：

| 字段 | 说明 |
|------|------|
| `calculation_method` | 当前为 `mention_rate_by_day`。 |
| `points` | 趋势点数量。 |

数据来源：`qa_brand_state` 的日粒度提及事实。

### 4.7 GET `/api/v1/dashboard/platform-mention-rates`

legacy 品牌分平台提及率接口。当前 `web/src/api/dashboard.js` 未封装该接口，但后端仍保留路由。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `category` | 是 | 商品大类/类目。 |
| `brand` | 是 | 品牌名称。 |
| `keyword` | 是 | 品牌关键词；历史逻辑中 `"全部"` 表示不过滤关键词。 |
| `timeframe` | 是 | 时间窗口。 |
| `date` | 否 | 指定日期，格式 `YYYYMMDD`。 |

响应 `data[]` 字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `name` | string | - | 平台名称。 |
| `mention_rate` | number | `0~100` | 该平台品牌提及率百分比。 |
| `first_mention_rate` | number | `0~100` | 该平台品牌首位提及率百分比。 |
| `color` | string | - | 前端展示颜色。 |

metadata：

| 字段 | 说明 |
|------|------|
| `calculation_method` | 当前为 `platform_mention_rate`。 |
| `platform_count` | 平台数量。 |
| `queries` | 聚合到的查询/对话数量。 |

数据来源：`qa_brand_state`。

### 4.8 GET `/api/v1/dashboard/answer-snapshots`

返回原始问答快照列表，并附带品牌分析状态和引用明细。用于问答快照页面和排障阅读。

请求参数：

| 参数 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `tenant_key` | 是 | - | 租户标识。 |
| `job_id` | 是 | - | 任务 ID。 |
| `timeframe` | 是 | - | 时间窗口。 |
| `start_date` | 否 | - | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `end_date` | 否 | - | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `brand` | 否 | - | 品牌过滤。 |
| `platform` | 否 | - | 平台过滤。 |
| `keyword` | 否 | - | 关键词过滤。 |
| `sentiment` | 否 | - | 情绪过滤，匹配 `qa_brand_state.sentiment_status`。 |
| `has_reference` | 否 | - | 是否有引用。 |
| `limit` | 否 | 50 | 返回条数，范围 `1~100`。 |
| `offset` | 否 | 0 | 分页偏移，最小 0。 |

响应 `data[]` 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `conversation_id` | string | 原始回答 ID。 |
| `date` | string | 回答业务日期，`YYYYMMDD`。 |
| `platform` | string | 平台。 |
| `brand` | string | 品牌。 |
| `keyword` | string | 关键词。 |
| `query_content` | string | 问题内容。 |
| `answer_content` | string | 回答内容。 |
| `sentiment_status` | string | 情绪状态。 |
| `is_mentioned` | boolean | 是否提及该品牌。 |
| `has_reference` | boolean | 是否有引用。 |
| `reference_count` | integer | 引用 URL 数量。 |
| `references[].url` | string | 引用 URL。 |
| `references[].domain` | string/null | 引用域名。 |
| `references[].content_type` | string/null | 引用内容类型。 |
| `references[].is_published_link` | boolean | 是否为发稿链接。 |

metadata：

| 字段 | 说明 |
|------|------|
| `row_count` | 当前页返回条数。 |
| `total_count` | 命中过滤条件的总条数。 |
| `limit`、`offset` | 当前分页参数。 |
| 过滤字段 | 若请求中传入 `brand`、`platform`、`keyword`、`sentiment`、`has_reference`，metadata 会回显。 |

数据来源：

- 主表：`llm_conversations`。
- 品牌/情绪/提及状态：左连接 `qa_brand_state`。
- 引用数量和引用明细：聚合 `qa_reference`。

排序：`generated_date DESC, extracted_at DESC, id DESC`。

### 4.9 GET `/api/v1/dashboard/sentiment-analysis`

返回情绪分布和关键词情绪明细。用于情感分析页面。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `timeframe` | 是 | 时间窗口。 |
| `start_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `end_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `brand` | 否 | 品牌过滤。 |
| `platform` | 否 | 平台过滤。 |
| `keyword` | 否 | 关键词过滤。 |

响应字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `data.distribution[].sentiment_status` | string | - | 情绪状态，如 `positive`、`negative`、`neutral`、`unknown`。 |
| `data.distribution[].answer_count` | integer | 条 | 该情绪回答数。 |
| `data.distribution[].ratio` | number | `0~1` | 该情绪占比。 |
| `data.keywords[].keyword` | string | - | 关键词。 |
| `data.keywords[].platform` | string | - | 平台。 |
| `data.keywords[].brand` | string | - | 品牌。 |
| `data.keywords[].sentiment_status` | string | - | 情绪状态。 |
| `data.keywords[].answer_count` | integer | 条 | 当前维度回答数。 |
| `data.keywords[].ratio` | number | `0~1` | 当前 `brand + platform + keyword` 维度内的情绪占比。 |

metadata：

| 字段 | 说明 |
|------|------|
| `calculation_method` | 当前为 `sentiment_distribution`。 |
| `data_source` | `analysis_fact` 或 `empty`。 |
| `metric_definition_version` | 当前为 `brand_metrics_v1`。 |
| `sample_count` | 纳入情绪统计的回答数。 |
| `row_count` | 关键词情绪明细行数。 |

数据来源：

- 从 `qa_brand_state.sentiment_status` 聚合情绪分布和关键词情绪明细。
- 没有数据时返回空数组，并标记 `data_source=empty`。

### 4.10 GET `/api/v1/dashboard/post-citation-rate`

返回指定品牌的引用信源数量和发文引用率。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `brand` | 是 | 品牌名称。 |
| `timeframe` | 是 | 时间窗口。 |
| `start_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `end_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |

响应 `data[]` 字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `brand` | string | - | 品牌名称。 |
| `citation_source_count` | integer | 个 | 去重引用域名数量。 |
| `citation_rate_by_post` | number | `0~1` | 至少包含一个发稿链接的对话占比。 |

metadata：

| 字段 | 说明 |
|------|------|
| `calculation_method` | 当前为 `post_citation_rate`。 |
| `row_count` | 当前固定为 1。 |

数据来源：`qa_reference`。

### 4.11 GET `/api/v1/dashboard/citation-domain-summary`

按域名汇总指定品牌的引用次数、关键词覆盖、平台覆盖和总引用率。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `brand` | 是 | 品牌名称。 |
| `timeframe` | 是 | 时间窗口。 |
| `start_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `end_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |

响应 `domain_distribution[]` 字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `domain` | string | - | 域名。 |
| `chinese_name` | string | - | 域名中文名称。 |
| `citation_count` | integer | 次 | 该域名引用次数。 |
| `keyword_coverage` | integer | 个 | 该域名覆盖的去重关键词数。 |
| `platform_coverage` | integer | 个 | 该域名覆盖的去重平台数。 |
| `domain-citation-rate` | number | `0~100` | 该域名引用次数占该品牌总引用次数的百分比。 |

metadata：

| 字段 | 说明 |
|------|------|
| `calculation_method` | 当前为 `domain_citation_summary`。 |
| `row_count` | 域名数量。 |

数据来源：`qa_reference`，只统计 `domain IS NOT NULL` 的记录。

### 4.12 GET `/api/v1/dashboard/citation-domain-stats`

按域名返回引用率分布，可选按关键词和平台过滤。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `brand` | 是 | 品牌名称。 |
| `timeframe` | 是 | 时间窗口。 |
| `start_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `end_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `keyword` | 否 | 关键词过滤，只影响分子。 |
| `platform` | 否 | 平台过滤，同时影响分子和分母。 |

响应 `domain_distribution[]` 字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `domain` | string | - | 域名。 |
| `chinese_name` | string | - | 域名中文名称。 |
| `keywords` | string | - | 该域名关联的去重关键词，逗号分隔。 |
| `content_types` | string | - | 该域名关联的内容类型，逗号分隔。 |
| `platforms` | string | - | 该域名关联的平台，逗号分隔。 |
| `domain_citation_rate` | number | `0~100` | 域名引用率百分比。 |

metadata：

| 字段 | 说明 |
|------|------|
| `calculation_method` | 当前为 `domain_citation_rate`。 |
| `row_count` | 域名数量。 |

数据来源：`qa_reference`，只统计 `domain IS NOT NULL` 的记录。

注意：传入 `keyword` 时，分子按关键词过滤，分母不受关键词影响；传入 `platform` 时，分子和分母都限制在该平台内。

### 4.13 GET `/api/v1/dashboard/citation-url-stats`

返回指定 `keyword + domain` 下的引用 URL 排名。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `keyword` | 是 | 关键词。 |
| `domain` | 是 | 域名。 |
| `timeframe` | 是 | 时间窗口。 |
| `start_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `end_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |

响应 `data[]` 字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `answer_reference_url` | string | - | 引用 URL。 |
| `citation_count` | integer | 次 | URL 引用次数。 |
| `total_questions` | integer | 条 | 当前租户/任务/时间窗口内去重对话数。 |
| `chinese_name` | string | - | URL 解析出的域名中文名称。 |
| `citation_rate` | number | `0~100` | `citation_count / total_questions * 100`。 |

metadata：

| 字段 | 说明 |
|------|------|
| `calculation_method` | 当前为 `citation_url_count`。 |
| `url_count` | URL 数量。 |

数据来源：`qa_reference.url`。

### 4.14 GET `/api/v1/dashboard/citation-type-stats`

返回引用内容类型占比统计。

请求参数：

| 参数 | 必填 | 说明 |
|------|------|------|
| `tenant_key` | 是 | 租户标识。 |
| `job_id` | 是 | 任务 ID。 |
| `timeframe` | 是 | 时间窗口。 |
| `start_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |
| `end_date` | 否 | `specific_day` 时必填，格式 `YYYYMMDD`。 |

响应字段：

| 字段 | 类型 | 单位 | 说明 |
|------|------|------|------|
| `summary.total_rows` | integer | 条 | 引用记录总数。 |
| `summary.conversations` | integer | 条 | 去重对话数。 |
| `citation_type_stats[].content_type` | string | - | 引用内容类型；空值会返回 `unknown`。 |
| `citation_type_stats[].type_pct` | number | `0~100` | 该类型引用数占总引用记录数的百分比。 |

metadata：

| 字段 | 说明 |
|------|------|
| `calculation_method` | 当前为 `content_type_pct`。 |
| `row_count` | 内容类型数量。 |

数据来源：`qa_reference.content_type`。

注意：当前前端 adapter 可能会额外带上 `brand` 参数，但后端路由没有声明该参数，服务层也不会使用它。

## 5. 维护规则

- 修改 `api/v1/routes/dashboard.py` 的端点、参数或 response model 后，应同步更新本文。
- 修改 `api/v1/models/schemas.py` 中 dashboard response 字段后，应同步更新本文字段表。
- 修改 `api/v1/repositories/*` 的聚合口径后，应同步更新数据来源、单位和算法说明。
- 当前运行时权威契约以 `app.openapi()` 或 `/api/v1/openapi.json` 为准；本文用于人读，不替代自动生成的 OpenAPI。
