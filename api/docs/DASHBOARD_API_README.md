# Dashboard API 文档

## 品牌总指标 API

---------------------

### 接口信息
- **路径**: `/api/v1/dashboard/brand-metrics`
- **方法**: `GET`
- **描述**: 获取品牌总指标，基于`qa_brand_state`表计算

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 是 | 任务ID |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days`, `specific_day` |
| start_date | string | 否 | 起始日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |
| end_date | string | 否 | 结束日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |
| brand | string | 否 | 品牌名称 |
| platform | string | 否 | 平台名称 |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/brand-metrics?tenant_key=tn_xxx&job_id=job_456&timeframe=30days"
```

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/brand-metrics?tenant_key=tn_xxx&job_id=job_456&timeframe=specific_day&start_date=20260131&end_date=20260131"
```

### 响应格式

```json
{
  "status": "success",
  "data": [
    {
      "brand": "学而思",
      "mention_rate": 0.3333,
      "first_mention_rate": 0.0000,
      "top3_mention_rate": 0.0667,
      "prompt_count": 15,
      "keyword_coverage": 3
    },
    {
      "brand": "新东方",
      "mention_rate": 0.2667,
      "first_mention_rate": 0.1333,
      "top3_mention_rate": 0.0667,
      "prompt_count": 15,
      "keyword_coverage": 2
    },
    {
      "brand": "作业帮",
      "mention_rate": 0.2000,
      "first_mention_rate": 0.0000,
      "top3_mention_rate": 0.0667,
      "prompt_count": 15,
      "keyword_coverage": 3
    },
    ......
  ],
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_456",
    "timeframe": "30days",
    "start_date": "20260102",
    "end_date": "20260131",
    "calculation_method": "mention_count_ratio",
    "row_count": 5
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| brand | string | 品牌名称 |
| mention_rate | float | 品牌总提及率（比例，0~1） |
| first_mention_rate | float | 首次提及 brand 率（比例，0~1） |
| top3_mention_rate | float | 前3次提及 brand 率（比例，0~1） |
| prompt_count | int | 问题总数 |
| keyword_coverage | int | 问题的答案提及品牌时，问题所属关键词的个数 |

### 数据计算逻辑

当请求参数不带brand='xxx'时，返回所有品牌的指标：
```sql
SELECT 
    brand,
    COUNT(DISTINCT conversation_id) AS prompt_count,
    SUM(is_mentioned) / COUNT(DISTINCT conversation_id) AS mention_rate,
    SUM(is_first_mentioned) / COUNT(DISTINCT conversation_id) AS first_mention_rate,
    SUM(is_top3_mentioned) / COUNT(DISTINCT conversation_id) AS top3_mention_rate,
    COUNT(DISTINCT CASE WHEN is_mentioned = 1 THEN keyword END) AS keyword_coverage
FROM qa_brand_state
WHERE 
    tenant_key = <tenant_key>
    AND job_id = <job_id>
    AND `date` BETWEEN :start_date AND :end_date
GROUP BY brand
ORDER BY mention_rate DESC, brand ASC;
```

当请求参数不带brand='xxx'，带platform='oooo'时，返回platform下所有品牌的指标：
```sql
SELECT 
    brand,
    COUNT(DISTINCT conversation_id) AS prompt_count,
    SUM(is_mentioned) / COUNT(DISTINCT conversation_id) AS mention_rate,
    SUM(is_first_mentioned) / COUNT(DISTINCT conversation_id) AS first_mention_rate,
    SUM(is_top3_mentioned) / COUNT(DISTINCT conversation_id) AS top3_mention_rate,
    COUNT(DISTINCT CASE WHEN is_mentioned = 1 THEN keyword END) AS keyword_coverage
FROM qa_brand_state
WHERE 
    tenant_key = <tenant_key>
    AND platform = <platform>
    AND job_id = <job_id>
    AND `date` BETWEEN :start_date AND :end_date
GROUP BY brand
ORDER BY mention_rate DESC, brand ASC;
```

当请求参数带brand='xxx'时，返回指定品牌的指标：
```sql
SELECT 
    brand,
    COUNT(DISTINCT conversation_id) AS prompt_count,
    SUM(is_mentioned) / COUNT(DISTINCT conversation_id) AS mention_rate,
    SUM(is_first_mentioned) / COUNT(DISTINCT conversation_id) AS first_mention_rate,
    SUM(is_top3_mentioned) / COUNT(DISTINCT conversation_id) AS top3_mention_rate,
    COUNT(DISTINCT CASE WHEN is_mentioned = 1 THEN keyword END) AS keyword_coverage
FROM qa_brand_state
WHERE 
    tenant_key = <tenant_key>
    AND job_id = <job_id>
    AND brand = <brand>
    AND `date` BETWEEN :start_date AND :end_date
```

--------------------------

### 接口信息
- **路径**: `/api/v1/dashboard/platform-metrics-by-brand`
- **方法**: `GET`
- **描述**: 获取平台指标，基于`qa_brand_state`表计算

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 是 | 任务ID |
| brand | string | 是 | 品牌名称 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days`, `specific_day` |
| start_date | string | 否 | 起始日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |
| end_date | string | 否 | 结束日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/platform-metrics-by-brand?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=30days"
```

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/platform-metrics-by-brand?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=specific_day&start_date=20260102&end_date=20260131"
```

### 响应格式

```json
{
  "status": "success",
  "data": {
      "brand": "学而思",
      "platforms": [
        {
          "platform": "deepseek",
          "mention_rate": 0.3333,
        },
        {
          "platform": "豆包",
          "mention_rate": 0.4667,
        },
        {
          "platform": "千问",
          "mention_rate": 0.2465,
        },
      ]
  },
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_456",
    "timeframe": "30days",
    "start_date": "20260102",
    "end_date": "20260131",
    "calculation_method": "platform_metrics_by_brand",
    "row_count": 5
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| brand | string | 品牌名称 |
| platforms | array | platform 指标列表 |
| platforms.platform | string | 平台名称 |
| platforms.mention_rate | float | 平台提及率（比例，0~1） |

### 数据计算逻辑

```sql
SELECT 
    platform,
    SUM(is_mentioned) / COUNT(*) AS mention_rate
FROM qa_brand_state
WHERE 
    tenant_key = <tenant_key>
    AND job_id = <job_id>
    AND brand = <brand>
    AND `date` BETWEEN :start_date AND :end_date
GROUP BY platform
ORDER BY platform ASC;
```
---------------------

### 接口信息
- **路径**: `/api/v1/dashboard/post-citation-rate`
- **方法**: `GET`
- **描述**: 获取品牌参考引用信息，基于`qa_reference`表计算

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 是 | 任务ID |
| brand | string | 是 | 品牌名称 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days`, `specific_day` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/post-citation-rate?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=7days"
```

### 响应格式

```json
{
  "status": "success",
  "data": [
    {
      "brand": "xxx",
      "citation_source_count": 104,
      "citation_rate_by_post": 0.0
    }
  ],
  "metadata": {
    "timeframe": "7days",
    "calculation_method": "post_citation_rate"
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| brand | string | 品牌名称 |
| citation_source_count | int | 引用信源数量 |
| citation_rate_by_post | float | 发文引用率（有发文引用的对话占总对话的比例） |

> 指标名为“引用信源数量”，代表信源多样性。在互联网分析中，一个“信源”通常指一个独立的发布平台（如知乎、小红书、新浪新闻）。使用域名去重可以准确反映： 有多少个不同的平台 在支撑该品牌的正面声量。
> **💡 计算口径说明**：当前“引用率”基于“**已产生引用链接的对话**”计算。未来将考虑新增以“品牌总提及对话数”为分母的全局指标。

### 数据计算逻辑

```sql
SELECT
    brand,
    COUNT(DISTINCT qr.domain) AS citation_source_count,
    COALESCE(
        (
            SELECT AVG(has_published_link)
            FROM (
                SELECT
                    conversation_id,
                    MAX(is_published_link) AS has_published_link
                FROM qa_reference
                WHERE 
                    tenant_key = <tenant_key>
                    AND job_id = <job_id>
                    AND brand = <brand>
                    AND created_at >= CURDATE() - INTERVAL <timeframe> DAY
                    AND created_at <= CURDATE()
                GROUP BY conversation_id
            ) AS conv_stats
        ),
        0
    ) AS citation_rate_by_post
FROM qa_reference qr
WHERE
    qr.tenant_key = <tenant_key>
    AND qr.job_id = <job_id>
    AND qr.brand = <brand>
    AND qr.created_at >= CURDATE() - INTERVAL <timeframe> DAY
    AND qr.created_at <= CURDATE()
GROUP BY brand;
```
---------------------

### 接口信息
- **路径**: `/api/v1/dashboard/domain-citation-rate`
- **方法**: `GET`
- **描述**: 获取品牌参考引用信息，基于`qa_reference`表计算

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 是 | 任务ID |
| brand | string | 是 | 品牌名称 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days`, `specific_day` |
| start_date | string | 否 | 起始日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |
| end_date | string | 否 | 结束日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/domain-citation-rate?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=30days"
```

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/domain-citation-rate?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=specific_day&start_date=20260102&end_date=20260131"
```

### 响应格式

```json
{
  "status": "success",
  "domain_distribution": [
    {
      "domain": "www.baidu.com",
      "domain-citation-rate": 8.96
    },
    {
      "domain": "www.google.com",
      "domain-citation-rate": 3.73
    },
    {
      "domain": "www.zhihu.com",
      "domain-citation-rate": 2.34
    },
    ......
  ],
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_456",
    "timeframe": "30days",
    "start_date": "20260102",
    "end_date": "20260131",
    "calculation_method": "domain_citation_rate",
    "row_count": 5
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| domain_distribution | array | 域名引用率分布 |
| domain_distribution.domain | string | 域名 |
| domain_distribution.domain-citation-rate | float | 域名引用率 |
| metadata | object | 元数据 |
| metadata.tenant_key | string | 租户标识 tenant_key |
| metadata.job_id | string | 任务ID |
| metadata.timeframe | string | 时间范围 |
| metadata.start_date | string | 起始日期 |
| metadata.end_date | string | 结束日期 |
| metadata.calculation_method | string | 计算方法 |
| metadata.row_count | int | 数据行数 |

> **💡 计算口径说明**：当前“域名引用率”计算均基于“**已产生引用链接的对话**”作为分母。

### 数据计算逻辑

```sql
SELECT 
    domain,
    ROUND(
        COUNT(*) * 100.0 / (
            SELECT COUNT(*)
            FROM qa_reference
            WHERE 
              tenant_key = <tenant_key>
              AND job_id = <job_id>
              AND brand = <brand>
              AND domain IS NOT NULL
              AND `date` BETWEEN :start_date AND :end_date
        ),
        2
    ) AS percentage
FROM qa_reference
WHERE
    tenant_key = <tenant_key>
    AND job_id = <job_id>
    AND brand = <brand>
    AND domain IS NOT NULL
    AND `date` BETWEEN :start_date AND :end_date
GROUP BY domain
ORDER BY percentage DESC;
```
---------------------------

## 📊 品牌总提及率 API

### 接口信息
- **路径**: `/api/v1/dashboard/brand-mention-rate`
- **方法**: `GET`
- **描述**: 获取品牌总提及率数据，基于`qa_brand_summary`表计算
- **实现状态**: ✅ 已完成

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 是 | 任务ID |
| brand | string | 是 | 品牌名称 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days`, `specific_day` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/brand-mention-rate?tenant_key=tn_xxx&job_id=job_456&brand=Apple&timeframe=7days"
```

### 响应格式

```json
{
  "status": "success",
  "data": {
    "mention_rate": 0.5,
    "rank": 1,
    "change": 5.2,
    "question_count": 12,
    "mention_count": 6,
    "first_mention_count": 3,
    "analysis_date": "2025-11-28",
    "last_updated": "2025-12-08T20:02:15.198791"
  },
  "metadata": {
    "timeframe": "7days",
    "calculation_method": "mention_count_ratio"
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| mention_rate | float | 品牌总提及率（百分比） |
| rank | int | 品牌排名 |
| change | float | 与上一周期对比的变化（百分比） |
| question_count | int | 问题总数 |
| mention_count | int | 品牌提及数量 |
| first_mention_count | int | 首次提及品牌数量 |
| analysis_date | string | 分析日期 |
| last_updated | string | 最后更新时间 |
| metadata | object | 元数据，包含 timeframe 和 calculation_method |

### 使用示例

```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/brand-mention-rate?tenant_key=tn_xxx&job_id=job_456&brand=Apple&timeframe=7days" \
  -H "accept: application/json"
```

### 数据计算逻辑

基于代码实际执行的 SQL（参数以 SQLAlchemy 命名参数形式展示）：

```sql
SELECT 1
FROM qa_brand_summary
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND brand = :brand
LIMIT 1
```

```sql
SELECT
    SUM(question_count) as total_questions,
    SUM(mention_count) as total_mentions,
    SUM(first_mention_count) as total_first_mentions,
    MAX(date) as latest_date,
    AVG(mention_rate) as avg_mention_rate
FROM qa_brand_summary
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND brand = :brand
  AND date BETWEEN :start_date AND :end_date
```

```sql
SELECT COUNT(*) + 1
FROM (
    SELECT brand, AVG(mention_rate) as rate
    FROM qa_brand_summary
    WHERE tenant_key = :tenant_key
      AND job_id = :job_id
      AND date BETWEEN :start_date AND :end_date
    GROUP BY brand
    HAVING rate > :my_rate
) as ranks
```

```sql
SELECT AVG(mention_rate)
FROM qa_brand_summary
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND brand = :brand
  AND date BETWEEN :prev_start AND :prev_end
```

---

## 📈 各平台品牌提及率对比 API

### 接口信息
- **路径**: `/api/v1/dashboard/platform-mention-rates`
- **方法**: `GET`
- **描述**: 获取单个品牌在各平台的提及率对比数据，基于`qa_brand_state`表计算
- **实现状态**: ✅ 已完成

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 是 | 任务ID |
| category | string | 是 | 商品大类 |
| brand | string | 是 | 品牌名称 |
| keyword | string | 是 | 品牌关键词，或"全部" |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days`, `specific_day` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/platform-mention-rates?tenant_key=tn_xxx&job_id=job_456&category=手机&brand=Apple&keyword=iPhone&timeframe=7days"
```

### 响应格式

```json
{
  "status": "success",
  "data": [
    {
      "name": "DeepSeek",
      "mention_rate": 45.0,
      "first_mention_rate": 30.0,
      "color": "#06b6d4"
    },
    {
      "name": "Claude",
      "mention_rate": 35.0,
      "first_mention_rate": 25.0,
      "color": "#f59e0b"
    },
    {
      "name": "ChatGPT",
      "mention_rate": 28.5,
      "first_mention_rate": 20.0,
      "color": "#10b981"
    }
  ],
  "metadata": {
    "category": "手机",
    "brand": "Apple",
    "keyword": "iPhone",
    "timeframe": "7days",
    "date": "20250115",
    "calculation_method": "platform_mention_rate",
    "platform_count": 3,
    "queries": 1500
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| data | array | 各平台提及率数据列表 |
| name | string | 平台名称（如：DeepSeek、Claude、ChatGPT 等） |
| mention_rate | float | 该平台上的品牌提及率（百分比） |
| first_mention_rate | float | 该平台上的品牌首位提及率（百分比） |
| color | string | 平台颜色编码（用于前端图表展示） |
| metadata | object | 元数据 |
| metadata.category | string | 请求的商品大类 |
| metadata.brand | string | 请求的品牌名称 |
| metadata.keyword | string | 请求的品牌关键词 |
| metadata.timeframe | string | 请求的时间范围 |
| metadata.date | string | 请求的日期 |
| metadata.calculation_method | string | 计算方式说明 |
| metadata.platform_count | int | 平台数量 |
| metadata.queries | int | 总查询次数 |

### 平台颜色映射

| 平台名称 | 颜色编码 |
|----------|----------|
| DeepSeek | `#06b6d4` |
| Claude   | `#f59e0b` |
| ChatGPT  | `#10b981` |
| Gemini   | `#3b82f6` |
| 豆包      | `#8b5cf6` |
| 通义千问   | `#ef4444` |

### 数据计算逻辑

基于代码实际执行的 SQL（参数以 SQLAlchemy 命名参数形式展示）：

```sql
SELECT
    platform,
    COUNT(DISTINCT conversation_id) AS query_count,
    COUNT(
        DISTINCT CASE WHEN is_mentioned = 1 THEN conversation_id END
    ) AS mention_count,
    COUNT(
        DISTINCT CASE WHEN is_first_mentioned = 1 THEN conversation_id END
    ) AS first_mention_count
FROM qa_brand_state
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND brand = :brand
  AND date BETWEEN :start_date AND :end_date
  AND category = :category
  AND keyword = :keyword -- 仅在 keyword != "全部" 时添加此过滤条件
GROUP BY platform
ORDER BY mention_rate DESC; -- 在代码中进行排序
```

- **mention_rate**: `(mention_count / query_count) * 100`
- **first_mention_rate**: `(first_mention_count / query_count) * 100`

---

## 📉 品牌提及率趋势 API（平台 + 关键词）

### 接口信息
- **路径**: `/api/v1/dashboard/brand-mention-trend`
- **方法**: `GET`
- **描述**: 获取指定品牌在指定平台、指定关键词下的“按日提及率”趋势数据（仅返回日期范围内实际有数据的日期点位）
- **实现状态**: ✅ 已完成

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 是 | 任务ID |
| brand | string | 是 | 品牌名称 |
| platform | string | 是 | 平台名称（如 deepseek） |
| keyword | string | 是 | 关键词 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days`, `specific_day` |
| start_date | string | 否 | 起始日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |
| end_date | string | 否 | 结束日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/brand-mention-trend?tenant_key=tn_xxx&job_id=job_456&brand=哈基桃电竞&platform=deepseek&keyword=三角洲陪玩&timeframe=30days"
```

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/brand-mention-trend?tenant_key=tn_xxx&job_id=job_456&brand=哈基桃电竞&platform=deepseek&keyword=三角洲陪玩&start_date=20260102&end_date=20260131"
```

### 响应格式

```json
{
  "status": "success",
  "data": [
    {
      "date": "20260101",
      "brand": "哈基桃电竞",
      "platform": "deepseek",
      "keyword": "三角洲陪玩",
      "mention_rate": 0.2000
    },
    {
      "date": "20260103",
      "brand": "哈基桃电竞",
      "platform": "deepseek",
      "keyword": "三角洲陪玩",
      "mention_rate": 0.5000
    }
  ],
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_456",
    "timeframe": "30days",
    "start_date": "20260102",
    "end_date": "20260131",
    "calculation_method": "mention_rate_by_day",
    "row_count": 2
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| data | array | 趋势数据列表（按日） |
| data.date | string | 日期（YYYYMMDD） |
| data.brand | string | 品牌名称 |
| data.platform | string | 平台名称 |
| data.keyword | string | 关键词 |
| data.mention_rate | float | 提及率（比例，0~1） |
| metadata | object | 元数据 |
| metadata.tenant_key | string | 租户标识 tenant_key |
| metadata.job_id | string | 任务ID |
| metadata.timeframe | string | 时间范围 |
| metadata.start_date | string | 开始日期，格式: `YYYYMMDD` |
| metadata.end_date | string | 结束日期，格式: `YYYYMMDD` |
| metadata.calculation_method | string | 计算方式说明 |
| metadata.row_count | int | 返回点位数量（等于 data 长度） |

### 数据计算逻辑

基于代码实际执行的 SQL（参数以 SQLAlchemy 命名参数形式展示）：

```sql
SELECT
    date,
    brand,
    platform,
    keyword,
    ROUND(SUM(is_mentioned) * 1.0 / COUNT(DISTINCT conversation_id), 4) AS mention_rate
FROM qa_brand_state
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND brand = :brand
  AND platform = :platform
  AND keyword = :keyword
  AND date BETWEEN :start_date AND :end_date
GROUP BY date, platform, brand, keyword
ORDER BY date ASC
```

日期返回规则：
- 不做缺失日期补齐，仅返回 `[start_date, end_date]` 范围内实际有数据的日期点位。

---

## 关键词-平台-品牌提及率明细 API

### 接口信息
- **路径**: `/api/v1/dashboard/keyword-platform-brand-rates`
- **方法**: `GET`
- **描述**: 获取指定时间范围内按 `keyword + platform + brand` 聚合的提及率与首位提及率数据，基于`qa_brand_state`表计算
- **实现状态**: ✅ 已完成

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 是 | 任务ID |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days`, `specific_day` |
| start_date | string | 否 | 起始日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |
| end_date | string | 否 | 结束日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/keyword-platform-brand-rates?tenant_key=tn_xxx&job_id=job_456&timeframe=30days"
```

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/keyword-platform-brand-rates?tenant_key=tn_xxx&job_id=job_456&timeframe=specific_day&start_date=20260131&end_date=20260131"
```

### 响应格式

```json
{
  "status": "success",
  "data": [
    {
      "keyword": "三角洲陪玩",
      "platform": "deepseek",
      "brand": "五九电竞",
      "mention_rate": 0.6935,
      "first_mention_rate": 0.0323,
      "top3_mention_rate": 0.1545
    }
  ],
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_456",
    "timeframe": "30days",
    "start_date": "20260102",
    "end_date": "20260131",
    "calculation_method": "distinct_conversation_ratio",
    "rate_unit": "ratio_0_1",
    "row_count": 1
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| data | array | 数据列表 |
| data.keyword | string | 关键词 |
| data.platform | string | 平台 |
| data.brand | string | 品牌 |
| data.mention_rate | float | 提及率（比例，0~1） |
| data.first_mention_rate | float | 首位提及率（比例，0~1） |
| data.top3_mention_rate | float | 前3位提及率（比例，0~1） |
| metadata | object | 元数据 |
| metadata.tenant_key | string | 租户标识 |
| metadata.job_id | string | 任务ID |
| metadata.timeframe | string | 时间范围 |
| metadata.start_date | string | 起始日期（`YYYYMMDD`） |
| metadata.end_date | string | 结束日期（`YYYYMMDD`） |
| metadata.calculation_method | string | 计算方式说明 |
| metadata.rate_unit | string | rate 单位说明 |
| metadata.row_count | int | 返回行数 |

### 数据计算逻辑

基于代码实际执行的 SQL（参数以 SQLAlchemy 命名参数形式展示）：

```sql
SELECT
    keyword,
    platform,
    brand,
    ROUND(SUM(is_mentioned) * 1.0 / COUNT(DISTINCT conversation_id), 4) AS mention_rate,
    ROUND(SUM(is_first_mentioned) * 1.0 / COUNT(DISTINCT conversation_id), 4) AS first_mention_rate,
    ROUND(SUM(is_top3_mentioned) * 1.0 / COUNT(DISTINCT conversation_id), 4) AS top3_mention_rate
FROM qa_brand_state
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND date BETWEEN :start_date AND :end_date
GROUP BY keyword, platform, brand
ORDER BY keyword ASC, platform ASC, mention_rate DESC;
```

---

## �� 引用统计 API

### 全局引用URL统计

### 接口信息
- **路径**: `/api/v1/dashboard/reference-url-stats`
- **方法**: `GET`
- **描述**: 获取全局引用 URL 的统计数据，包括各站点的引用次数和引用率。
- **实现状态**: ✅ 已完成

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 是 | 任务ID |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days`, `specific_day` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/reference-url-stats?tenant_key=tn_xxx&job_id=job_456&timeframe=7days"
```

### 响应格式

```json
{
  "status": "success",
  "data": [
    {
      "answer_reference_url": "https://www.zhihu.com/question/xxx",
      "reference_count": 15,
      "total_questions": 100,
      "chinese_name": "知乎",
      "reference_rate": 15.0
    },
    ...
  ],
  "metadata": {
    "timeframe": "7days",
    "calculation_method": "reference_url_count",
    "url_count": 10
  }
}
```

### 数据计算逻辑

基于代码实际执行的 SQL（参数以 SQLAlchemy 命名参数形式展示）：

```sql
-- 1. 获取引用 URL 统计数据
SELECT 
    url, 
    COUNT(*) AS reference_count 
FROM qa_reference 
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND url IS NOT NULL 
  AND date BETWEEN :start_date AND :end_date 
GROUP BY url 
ORDER BY reference_count DESC;

-- 2. 获取总提问数（用于计算引用率）
SELECT COUNT(DISTINCT conversation_id) AS total_questions 
FROM qa_reference 
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND date BETWEEN :start_date AND :end_date;
```

- **reference_rate**: `(reference_count / total_questions) * 100`

---------------------

### 仪表盘可用日期 API

### 接口信息
- **路径**: `/api/v1/dashboard/available-dates`
- **方法**: `GET`
- **描述**: 获取仪表盘中有数据的所有日期列表

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 否 | 任务ID |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/available-dates?tenant_key=tn_xxx&job_id=job_123"
```

### 响应格式

```json
{
  "status": "success",
  "data": [
    "2026-02-01",
    "2026-01-31"
  ],
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_123",
    "count": 2
  }
}
```

### 数据计算逻辑

```sql
SELECT DISTINCT date 
FROM qa_brand_state 
WHERE tenant_key = :tenant_key 
  AND job_id = :job_id -- 可选
ORDER BY date DESC;
```
-------------

### 任务筛选元数据接口

### 接口信息
- **路径**: `/api/v1/dashboard/filter-metadata`
- **方法**: `GET`
- **描述**: 获取指定任务下所有可用的平台和关键词，用于前端渲染筛选标签。

### 请求参数 (Query & Path)

| 参数名 | 类型 | 必填 | 位置 | 描述 |
|--------|------|------|------|------|
| job_id | string | 是 | Path | 任务唯一标识 |
| tenant_key | string | 是 | Query | 租户标识（安全校验） |
| start_date | string | 否 | Query | 开始日期 (YYYYMMDD) |
| end_date | string | 否 | Query | 结束日期 (YYYYMMDD) |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/filter-metadata?tenant_key=tn_1b02b3ef4fbd&job_id=job_20260127_...&start_date=20260101&end_date=20260131"
```

### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "platforms": ["ChatGPT", "Deepseek", "Qwen"],
    "keywords": ["手机", "笔记本", "智能家居", "海尔冰箱"],
    "combinations": [
      { "platform": "Qwen", "keyword": "手机" },
      { "platform": "Qwen", "keyword": "笔记本" },
      { "platform": "Deepseek", "keyword": "手机" }
    ]
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| code | int | 状态码 |
| message | string | 状态信息 |
| data.platforms | array | 平台列表（去重） |
| data.keywords | array | 关键词列表（去重） |
| data.combinations | array | 有效的平台与关键词组合列表，用于联动筛选 |

### 数据计算逻辑

```sql
SELECT DISTINCT platform, keyword
FROM qa_brand_state 
WHERE tenant_key = :tenant_key  
  AND job_id = :job_id 
  AND date BETWEEN :start_date AND :end_date
ORDER BY platform ASC, keyword ASC;
```

------

## 🧠 品牌策略与分析 API (LLM)

### 品牌定位关键词生成

### 接口信息
- **路径**: `/api/v1/analysis/positioning-keywords`
- **方法**: `POST`
- **描述**: 基于行业和品牌名称，利用 LLM 生成品牌定位关键词。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 Key |
| job_id | string | 是 | 任务 ID |
| industry | string | 是 | 行业名称（如：教育、汽车） |
| brand | string | 是 | 品牌名称（如：学而思、蔚来） |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/analysis/positioning-keywords" \
     -H "Content-Type: application/json" \
     -d '{
  "tenant_key": "tn_xxx",
  "job_id": "job_456",
  "industry": "教育",
  "brand": "学而思"
}'
```

### 响应格式

```json
[
  "关键词1",
  "关键词2",
  "关键词3"
]
```

### 实现逻辑 (LLM)
该接口目前直接调用 LLM 生成，不涉及 SQL 数据库查询。

**Prompt 模板**:
```text
你是一个品牌策略顾问。请基于品牌或产品的公开信息，直接输出一个包含5个标准化定位关键词的 JSON 数组。

要求检索品牌或产品的典型产品特征、用户评价和市场定位（可以通过搜索互联网信息进行检索），从检索结果中提取5个最核心的产品关键词
确保这些关键词：
- 精准反映产品核心优势
- 与竞品形成差异化
- 直接关联用户真实需求
- 适用于品牌营销和定位
- 仅输出 JSON 数组，不要任何解释、标注、注释或额外文本；
- 使用双引号，符合标准 JSON 格式。

现在为以下品牌或产品输出定位关键词：
{brand}
```

---

### 消费者常见问题生成

### 接口信息
- **路径**: `/api/v1/analysis/consumer-questions`
- **方法**: `POST`
- **描述**: 基于行业、品牌和核心关键词，生成消费者可能会问的问题。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 Key |
| job_id | string | 是 | 任务 ID |
| industry | string | 是 | 行业名称 |
| brand | string | 是 | 品牌名称 |
| keywords | array | 是 | 关键词列表 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/analysis/consumer-questions" \
     -H "Content-Type: application/json" \
     -d '{
  "tenant_key": "tn_xxx",
  "job_id": "job_456",
  "industry": "教育",
  "brand": "学而思",
  "keywords": ["奥数", "网课", "培优"]
}'
```

### 响应格式

```json
{
  "关键词1": ["问题1", "问题2"],
  "关键词2": ["问题3", "问题4"]
}
```

### 实现逻辑 (LLM)
该接口目前直接调用 LLM 生成，不涉及 SQL 数据库查询。

**Prompt 模板**:
```text
请根据{industry}行业{brand}的以下5个关键词，为每个关键词生成3个消费者在购买前可能提出的问题。

要求：
1. 每个关键词对应3个问题；
2. 每个问题应从不同角度切入（例如价格、质量、售后服务、使用体验、环保性、兼容性、安全性、品牌信誉等）；
3. 同一关键词下的3个问题之间应尽量避免内容重叠或逻辑关联；
4. 问题需贴近真实消费者的语言习惯，具有实际参考价值。

输出格式：
- 严格使用 JSON 格式，键为关键词，值为包含3个问题的数组；
- 不包含任何额外说明、注释或解释性文字。

关键词列表：
{keywords}
```

---

## 🏢 平台租户管理 API

### 平台操作员创建租户

### 接口信息
- **路径**: `/api/v1/platform/tenants`
- **方法**: `POST`
- **描述**: 平台操作员创建租户并生成管理员账号与邀请码。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenantName | string | 是 | 租户显示名称 |
| companyLegalName | string | 是 | 企业法定名称 |
| registrationNo | string | 否 | 企业注册号/统一社会信用代码 |
| industry | string | 是 | 行业 |
| companyType | string | 否 | 企业类型 |
| adminName | string | 是 | 管理员姓名 |
| adminEmail | string | 是 | 管理员邮箱 |
| adminPhone | string | 否 | 管理员电话 |
| planType | string | 否 | 订阅计划类型 |
| billingCycle | string | 否 | 计费周期（monthly/yearly） |
| contractStartDate | string | 否 | 合同开始日期（YYYY-MM-DD） |
| contractEndDate | string | 否 | 合同结束日期（YYYY-MM-DD） |
| maxUsers | integer | 否 | 最大用户数 |
| preferredSubdomain | string | 否 | 首选子域名 |
| salesPersonId | string | 否 | 销售负责人ID |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/platform/tenants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <platform-admin-token>" \
  -d '{
    "tenantName": "阿里巴巴集团",
    "companyLegalName": "阿里巴巴（中国）网络技术有限公司",
    "registrationNo": "91330000748833471G",
    "industry": "互联网/电子商务",
    "companyType": "有限责任公司",
    "adminName": "张三",
    "adminEmail": "zhangsan@alibaba.com",
    "adminPhone": "13800138000",
    "planType": "enterprise",
    "billingCycle": "yearly",
    "contractStartDate": "2025-01-20",
    "contractEndDate": "2026-01-19",
    "maxUsers": 200,
    "preferredSubdomain": "alibaba",
    "salesPersonId": "SALES_001"
  }'
```

### 响应格式

```json
{
  "success": true,
  "message": "租户创建成功",
  "data": {
    "tenantId": 100,
    "tenantKey": "tn_a8f3k9m2x7p1",
    "tenantName": "阿里巴巴集团",
    "adminUserKey": "usr_b9g4l0n3y8q2",
    "inviteCode": "AB3K9M",
    "activationUrl": "https://alibaba.yourplatform.com/activate?token=eyJ..."
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | boolean | 是否创建成功 |
| message | string | 提示消息 |
| data.tenantId | integer | 租户ID |
| data.tenantKey | string | 租户标识 Key |
| data.tenantName | string | 租户名称 |
| data.adminUserKey | string | 管理员用户标识 |
| data.inviteCode | string | 企业邀请码 |
| data.activationUrl | string | 管理员激活链接 |

---

## 📥 数据加载 API

### LLM查询任务加载接口

### 接口信息
- **路径**: `/api/v1/query-jobs/load`
- **方法**: `POST`
- **描述**: 接收原始 JSON 数据并批量加载到 `llm_query_jobs` 数据库表中。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 Key |
| job_id | string | 是 | 任务 ID |
| effective_from | string | 是 | 生效开始时间 (ISO 8601 格式) |
| effective_to | string | 否 | 生效结束时间 (ISO 8601 格式) |
| executor_id | string | 是 | 执行器 ID |
| total_runs | integer | 是 | 总执行次数 (默认: 15) |
| executed_runs | integer | 否 | 已执行次数 (默认: 0) |
| last_executed_date | string | 是 | 最近执行日期 (YYYY-MM-DD，默认: 当前日期) |
| data | object | 是 | 任务相关的查询配置数据对象 |

#### data 对象结构

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| category | string | 是 | 分类名称 |
| brand | string | 是 | 品牌名称 |
| competitor | array | 是 | 竞品名称列表 |
| content | array | 是 | 内容列表，包含关键词和查询内容 |

#### content 数组项结构

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| keyword | string | 是 | 关键词 |
| query_content | array | 是 | 查询内容（Query）列表 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/query-jobs/load" \
     -H "Content-Type: application/json" \
     -d '{
  "tenant_key": "tn_1b02b3ef4fbd",
  "job_id": "job_20260123_172515_f38024e2",
  "effective_from": "2026-01-23T00:00:00",
  "effective_to": "2026-02-01T00:00:00",
  "executor_id": "exec_bbda021a",
  "total_runs": 10,
  "executed_runs": 0,
  "last_executed_date": "2026-01-23",
  "data": {
    "category": "游戏",
    "brand": "哈基桃电竞",
    "competitor": [
        "河马电竞俱乐部",
        "五九电竞俱乐部",
        "知悦电竞俱乐部",
        "黛玉电竞俱乐部"
    ],
    "content": [
        {
            "keyword": "三角洲陪玩",
            "query_content":  [
                "三角洲陪玩有什么推荐？",
                "三角洲陪玩哪家好？",
                "三角洲陪玩哪家靠谱？",
                "三角洲陪玩哪家专业？",
                "三角洲陪玩哪家服务好？",
                "三角洲陪玩哪家口碑好？",
                "三角洲陪玩哪家性价比高？",
                "三角洲陪玩哪家打手实力强？"
            ]
        },
        {
            "keyword": "三角洲陪玩俱乐部",
            "query_content":  [
                "三角洲陪玩俱乐部有什么推荐？",
                "三角洲陪玩俱乐部哪家好？",
                "三角洲陪玩俱乐部哪家靠谱？",
                "三角洲陪玩俱乐部哪家专业？",
                "三角洲陪玩俱乐部哪家服务好？",
                "三角洲陪玩俱乐部哪家口碑好？",
                "三角洲陪玩俱乐部哪家性价比高？",
                "三角洲陪玩俱乐部售后服务好？"
            ]
        }
    ]
  }
}'
```

### 响应格式

```json
{
  "success": true,
  "inserted_rows": 2,
  "message": "LLM查询任务加载成功"
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | boolean | 是否处理成功 |
| inserted_rows | int | 实际插入数据库的行数 |
| message | string | 提示消息 |

---

### LLM查询任务获取接口

### 接口信息
- **路径**: `/api/v1/query-jobs/fetch`
- **方法**: `GET`
- **描述**: 执行器获取待执行任务。采用 Round-Robin 策略：优先选取已执行次数最少的任务，且按物理顺序排列。

### 请求参数 (Query & Header)

| 参数名 | 类型 | 必填 | 位置 | 描述 |
|--------|------|------|------|------|
| executor_id | string | 是 | Query | 执行器唯一 ID |
| X-Executor-Key | string | 是 | Header | 执行器 API Key |
| tenant_key | string | 否 | Query | 租户标识 Key (可选，用于过滤) |
| job_id | string | 否 | Query | 任务 ID (可选，用于过滤) |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/query-jobs/fetch?executor_id=exec_bbda021a&tenant_key=tn_xxx" \
     -H "X-Executor-Key: sk-xxxx-your-api-key"
```

### 响应示例

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
        "competitor": [
            "河马电竞俱乐部",
            "五九电竞俱乐部",
            "知悦电竞俱乐部",
            "黛玉电竞俱乐部"
        ],
        "keyword": "三角洲陪玩",
        "query_content": "三角洲陪玩有什么推荐？"
    }
}
```

---

### LLM查询任务状态查询接口

### 接口信息
- **路径**: `/api/v1/query-jobs/status`
- **方法**: `GET`
- **描述**: 追踪 LLM 查询 query 的执行与生效情况。该接口允许租户管理员或系统监控人员查看query的当前状态、生效生命周期（开始/结束时间）以及对应的查询内容。支持通过任务状态码识别任务是处于“等待中”、“执行中”还是“已完成/失效”状态。

### 请求参数 (Query)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 Key |
| job_id | string | 否 | 任务 ID |
| include_deleted | boolean | 否 | 是否包含已删除任务（默认 false） |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/query-jobs/status?tenant_key=tn_1b02b3ef4fbd&job_id=job_456&include_deleted=false"
```

### 响应示例

```json
{
  "success": true,
  "count": 2,
  "jobs": [
    {
        "tenant_key": "tn_1b02b3ef4fbd",
        "job_id": "job_20260201_171229_34974f3a",
        "brand": "宝马",
        "competitor": [
            "奔驰",
            "蔚来"
        ],
        "query_content": "宝马汽车的驾驶乐趣有哪些？",
        "query_status": 1,
        "effective_from": "2026-02-01T00:00:00",
        "effective_to": "2026-02-03T00:00:00"
    },
    {
        "tenant_key": "tn_1b02b3ef4fbd",
        "job_id": "job_20260127_223236_989cc4db",
        "brand": "哈基桃电竞",
        "competitor": [
            "河马电竞",
            "五九电竞",
            "知悦电竞",
            "黛玉电竞"
        ],
        "query_content": "三角洲陪玩俱乐部售后服务好？",
        "query_status": 3,
        "effective_from": "2026-01-26T16:00:00",
        "effective_to": "2026-01-31T16:00:00"
    }
  ]
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | boolean | 是否成功 |
| count | int | 任务数量 |
| jobs | array | 任务状态列表 |
| jobs.tenant_key | string | 租户标识 Key |
| jobs.job_id | string | 任务 ID |
| jobs.brand | string | 品牌名称 |
| jobs.competitor | array | 竞品名称列表 |
| jobs.query_content | string | 查询内容 |
| jobs.query_status | int | 问题生效状态：<br>0: **未生效** (等待开始或手动禁用)<br>1: **生效中** (执行器正在抓取)<br>2: **已完成** (已达总执行次数)<br>3: **已失效** (超过生效结束时间) |
| jobs.effective_from | string | 生效开始时间 (ISO 8601 格式) |
| jobs.effective_to | string | 生效结束时间 (ISO 8601 格式，可为空) |

---

### LLM查询任务上报接口

### 接口信息
- **路径**: `/api/v1/query-jobs/report`
- **方法**: `POST`
- **描述**: 执行器上报任务执行结果，系统将增加该任务的已执行次数，并更新最近执行日期。

### 请求参数 (Query, Header & Body)

| 参数名 | 类型 | 必填 | 位置 | 描述 |
|--------|------|------|------|------|
| executor_id | string | 是 | Query | 执行器唯一 ID |
| X-Executor-Key | string | 是 | Header | 执行器 API Key |
| id | integer | 是 | Body (JSON) | 任务记录唯一主键 ID |

### 请求示例

```bash
curl -X POST "http://localhost:8000/api/v1/query-jobs/report?executor_id=exec_bbda021a" \
     -H "X-Executor-Key: ek_d7c2a651c2b40a3f97f3642cb628844c" \
     -H "Content-Type: application/json" \
     -d "{\"id\": 1}"
```

### 响应示例

```json
{
  "success": true,
  "message": "上报成功"
}
```

---

### LLM对话入库接口

### 接口信息
- **路径**: `/api/v1/conversation/load`
- **方法**: `POST`
- **描述**: 执行器批量上报对话与引用数据，写入 `llm_conversations` 与 `llm_conversation_references` 表。

### 请求参数 (Query, Header & Body)

| 参数名 | 类型 | 必填 | 位置 | 描述 |
|--------|------|------|------|------|
| executor_id | string | 是 | Query | 执行器唯一 ID |
| X-Executor-Key | string | 是 | Header | 执行器 API Key |
| tenant_key | string | 是 | Body (JSON) | 租户标识 Key |
| job_id | string | 是 | Body (JSON) | 任务 ID |
| platform | string | 是 | Body (JSON) | 平台名称 |
| items | array | 是 | Body (JSON) | 对话批量数据 |

#### items 数组项结构

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| conversation_id | string | 是 | 对话 ID（幂等主键） |
| keyword | string | 是 | 关键词 |
| brand | string | 否 | 品牌名称 |
| category | string | 是 | 商品大类 |
| query_content | string | 是 | 用户提问内容 |
| answer_content | string | 是 | 平台回复内容 |
| extracted_at | string | 否 | 抽取时间 (ISO 8601) |
| references | array | 否 | 引用列表 |

#### references 数组项结构

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| url | string | 是 | 引用链接 |
| site_name | string | 否 | 站点名称 |
| cite_index | integer | 否 | 引用序号 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/conversation/load?executor_id=exec_3f2a1b9c" \
     -H "X-Executor-Key: sk-xxxx-your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
  "tenant_key": "tn_1b02b3ef4fbd",
  "job_id": "job_20260123_172515_f38024e2",
  "platform": "deepseek",
  "items": [
    {
      "conversation_id": "conversation_9f3c1a7b",
      "keyword": "三角洲陪玩",
      "brand": "哈基桃电竞",
      "category": "游戏",
      "query_content": "三角洲陪玩有什么推荐？",
      "answer_content": "……",
      "extracted_at": "2026-01-25T12:34:56Z",
      "references": [
        {
          "url": "https://www.zhihu.com/question/xxx",
          "site_name": "知乎",
          "cite_index": 1
        }
      ]
    }
  ]
}'
```

### 响应格式

```json
{
  "success": true,
  "inserted_conversations": 1,
  "inserted_references": 1,
  "message": "对话入库成功"
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | boolean | 是否处理成功 |
| inserted_conversations | int | 新增对话数 |
| inserted_references | int | 新增引用数 |
| message | string | 提示消息 |

---

### LLM对话获取接口

### 接口信息
- **路径**: `/api/v1/conversation/fetch`
- **方法**: `GET`
- **描述**: 获取对话与引用列表，支持分页。

### 请求参数 (Query & Header)

| 参数名 | 类型 | 必填 | 位置 | 描述 |
|--------|------|------|------|------|
| executor_id | string | 是 | Query | 执行器唯一 ID |
| X-Executor-Key | string | 是 | Header | 执行器 API Key |
| tenant_key | string | 是 | Query | 租户标识 Key |
| job_id | string | 是 | Query | 任务 ID |
| platform | string | 否 | Query | 平台名称 |
| limit | integer | 否 | Query | 返回条数，默认 50 |
| cursor | string | 否 | Query | 分页游标 |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/conversation/fetch?executor_id=exec_3f2a1b9c&tenant_key=tn_xxx&job_id=job_456&platform=deepseek&limit=10" \
     -H "X-Executor-Key: sk-xxxx-your-api-key"
```

### 响应示例

```json
{
  "success": true,
  "count": 1,
  "items": [
    {
      "conversation_id": "conversation_9f3c1a7b",
      "tenant_key": "tn_1b02b3ef4fbd",
      "job_id": "job_20260123_172515_f38024e2",
      "platform": "deepseek",
      "keyword": "三角洲陪玩",
      "brand": "哈基桃电竞",
      "category": "游戏",
      "query_content": "三角洲陪玩有什么推荐？",
      "answer_content": "……",
      "extracted_at": "2026-01-25T12:34:56Z",
      "references": [
        {
          "url": "https://www.zhihu.com/question/xxx",
          "domain": "zhihu.com",
          "site_name": "知乎",
          "cite_index": 1,
          "content_type": "ugc"
        }
      ]
    }
  ],
  "next_cursor": "eyJpZCI6MTIzfQ=="
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | boolean | 是否处理成功 |
| count | int | 返回对话数量 |
| items | array | 对话数据列表 |
| next_cursor | string | 下一页游标 |

---

## 🛠️ 执行器管理 API (Executors)

系统采用 **"先预设 IP，后注册取回凭据"** 的安全流程：
1. **预设**: 管理员在系统中手动创建执行器记录，并指定其固定的 `ip_address`。
2. **注册**: 执行器从预设的 IP 发起请求，通过 `/register` 接口取回自己的 `executor_id` 和 `api_key`。
3. **调用**: 执行器使用取回的凭据调用数据加载等业务接口。

### 1. 预设执行器 (Admin: Create Executor)

**接口地址**: `POST /api/v1/executors/`

**请求参数 (JSON Body)**:

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| name | string | 是 | 执行器名称（全局唯一，注册时使用） |
| ip_address | string | 是 | 执行器的固定 IP 地址 |
| type | string | 否 | 执行器类型（如: `crawler`） |

**请求示例**:
```bash
curl -X POST "http://your-api.com/api/v1/executors/" \
     -H "Content-Type: application/json" \
     -d '{
  "name": "laptop PC-query01",
  "ip_address": "192.168.31.112",
  "type": "crawler"
}'
```

**响应示例**:
```json
{
  "executor_id": "exec_3f2a1b9c",
  "name": "laptop PC-query01",
  "ip_address": "192.168.31.112",
  "type": "crawler",
  "status": "active",
  "created_at": "2024-01-23T10:00:00"
}
```

### 2. 执行器注册 (Executor: Register)

**接口地址**: `POST /api/v1/executors/register`

**描述**: 执行器启动时调用此接口。身份验证完全基于请求的 **来源 IP**。

**请求参数**: 无。

**请求示例**:
```bash
# 执行器只需发起一个空 Body 的 POST 请求
curl -X POST "http://your-api.com/api/v1/executors/register" \
     -H "Content-Type: application/json" \
     -d "{}"
```

**响应示例**:
```json
{
  "executor_id": "exec_3f2a1b9c",
  "api_key": "ek_7d9e2f4a5b6c8d9e0f1a2b3c4d5e6f7a"
}
```

### 3. 获取执行器列表 (List)

**接口地址**: `GET /api/v1/executors/`

**描述**: 获取系统中所有执行器的列表。出于安全考虑，该接口不返回 `api_key`。

**请求示例**:

```bash
curl -X GET "http://your-api.com/api/v1/executors/"
```

**响应示例**:

```json
[
  {
    "executor_id": "exec_3f2a1b9c",
    "name": "爬虫集群-A",
    "type": "crawler",
    "status": "active",
    "created_at": "2024-01-23T10:00:00"
  }
]
```

### 4. 禁用执行器 (Deactivate Executor)

**接口地址**: `DELETE /api/v1/executors/{executor_id}`

**描述**: 将指定执行器的状态设置为 `inactive`，禁用其访问权限。

**请求示例**:

```bash
curl -X DELETE "http://your-api.com/api/v1/executors/exec_3f2a1b9c"
```

**响应示例**:

```json
{
  "success": true,
  "message": "执行器 exec_3f2a1b9c 已禁用"
}
```

---

## 🏗️ 代码架构

### 主要文件结构

```
api/
├── main.py                    # FastAPI应用主文件
├── routes/
│   ├── dashboard.py          # Dashboard API路由实现
│   ├── analysis.py           # 分析相关API
│   ├── brand_strategy.py     # 品牌策略API
│   ├── config.py             # 配置相关API
│   └── query_jobs.py         # LLM查询任务相关API
├── repositories/
│   └── database.py           # 数据库查询函数
├── models/
│   └── schemas.py            # 数据模型定义
├── services/
│   └── llm_client.py         # LLM客户端服务
├── utils/
│   ├── llm_client.py         # LLM客户端工具
│   ├── llm_adapters.py       # LLM适配器
│   ├── llm_operator.py       # LLM操作器
│   └── url_domain_resolver.py # URL域名解析工具
└── database/
    ├── schema.sql            # 数据库表结构
    └── README.md             # 数据库文档
```

### 核心查询函数（位于 `repositories/database.py`）

#### `query_brand_mention_data(tenant_key, job_id, brand, timeframe, specific_date)`
- **功能**: 查询品牌提及率数据
- **参数**:
  - `tenant_key`: 租户标识
  - `job_id`: 任务ID
  - `brand`: 品牌名称
  - `timeframe`: 时间范围（yesterday, 7days, 30days, specific_day）
  - `specific_date`: 指定日期（可选，格式: YYYYMMDD）
- **返回**: 包含提及率数据的字典

#### `query_brand_platform_mention_data(tenant_key, job_id, brand, timeframe, specific_date)`
- **功能**: 查询品牌在各平台的提及率数据
- **参数**:
  - `tenant_key`: 租户标识
  - `job_id`: 任务ID
  - `brand`: 品牌名称
  - `timeframe`: 时间范围
  - `specific_date`: 指定日期（可选）
- **返回**: 包含各平台提及率数据的列表

#### `query_reference_url_stats(tenant_key, job_id, timeframe, specific_date)`
- **功能**: 查询引用URL统计数据
- **参数**:
  - `tenant_key`: 租户标识
  - `job_id`: 任务ID
  - `timeframe`: 时间范围
  - `specific_date`: 指定日期（可选）
- **返回**: 包含引用URL统计数据的列表

### 辅助函数

#### `get_date_range(timeframe, specific_date)`
- **功能**: 根据时间范围计算日期区间
- **参数**:
  - `timeframe`: 时间范围
  - `specific_date`: 指定日期（可选）
- **返回**: (start_date, end_date) 元组

#### `get_previous_date_range(timeframe, specific_date)`
- **功能**: 计算上一期日期区间（用于同比分析）
- **参数**:
  - `timeframe`: 时间范围
  - `specific_date`: 指定日期（可选）
- **返回**: (prev_start_date, prev_end_date) 元组

---

## 📊 数据库表对应关系

| API接口 | 主要数据表 | 查询函数 | 实现状态 |
|---------|------------|----------|----------|
| 品牌总提及率 | `qa_brand_summary` | `query_brand_mention_data` | ✅ 已完成 |
| 各平台提及率 | `qa_brand_summary` | `query_brand_platform_mention_data` | ✅ 已完成 |
| 引用URL统计 | `qa_reference` | `query_reference_url_stats` | ✅ 已完成（全局统计） |
| 可用日期列表 | `qa_brand_state` | `get_available_dates` | ✅ 已完成 |
| LLM查询记录加载 | `llm_query_jobs` | N/A (Direct Insert) | ✅ 已完成 |
