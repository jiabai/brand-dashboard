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
- **应用场景**: 用于分析不同平台对品牌的提及率，位置在首页"各平台提及率"卡片

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
| start_date | string | 否 | 起始日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |
| end_date | string | 否 | 结束日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/post-citation-rate?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=30days"
```

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/post-citation-rate?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=specific_day&start_date=20260102&end_date=20260131"
```

### 响应格式

```json
{
  "status": "success",
  "data": [
    {
      "brand": "学而思",
      "citation_source_count": 104,
      "citation_rate_by_post": 0.0
    }
  ],
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_456",
    "timeframe": "30days",
    "start_date": "20260102",
    "end_date": "20260131",
    "calculation_method": "post_citation_rate",
    "row_count": 1
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| brand | string | 品牌名称 |
| citation_source_count | int | 引用信源数量 |
| citation_rate_by_post | float | 发文引用率（有发文引用的对话占总对话的比例） |

> 指标名为"引用信源数量"，代表信源多样性。在互联网分析中，一个"信源"通常指一个独立的发布平台（如知乎、小红书、新浪新闻）。使用域名去重可以准确反映： 有多少个不同的平台 在支撑该品牌的正面声量。
> **💡 计算口径说明**：当前"引用率"基于"**已产生引用链接的对话**"计算。未来将考虑新增以"品牌总提及对话数"为分母的全局指标。

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
                    AND `date` BETWEEN :start_date AND :end_date
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
    AND qr.date BETWEEN :start_date AND :end_date
GROUP BY brand;
```
---------------------

### 接口信息
- **路径**: `/api/v1/dashboard/citation-domain-stats`
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
| keyword | string | 否 | 关键词，用于筛选引用信源 |
| platform | string | 否 | 中国大模型平台，可选值: `deepseek`, `千问`, `豆包`, `元宝`|

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/citation-domain-stats?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=30days"
```

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/citation-domain-stats?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=specific_day&start_date=20260102&end_date=20260131&platform=deepseek"
```

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/citation-domain-stats?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=30days&keyword=数学培训"
```

### 响应格式

```json
{
  "status": "success",
  "domain_distribution": [
    {
      "domain": "www.baidu.com",
      "chinese_name": "百度",
      "keywords": "数学培训,奥数",
      "content_types": "新闻,论坛",
      "platforms": "deepseek,千问",
      "domain_citation_rate": 8.96
    },
    {
      "domain": "www.google.com",
      "chinese_name": "谷歌",
      "keywords": "数学培训",
      "content_types": "新闻",
      "platforms": "deepseek",
      "domain_citation_rate": 3.73
    },
    {
      "domain": "www.zhihu.com",
      "chinese_name": "知乎",
      "keywords": "数学培训",
      "content_types": "新闻",
      "platforms": "deepseek",
      "domain_citation_rate": 2.34
    },
    ......
  ],
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_456",
    "keyword": "数学培训",
    "platform": "deepseek",
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
| domain_distribution.chinese_name | string | 域名中文名称 |
| domain_distribution.keywords | string | 关键词（多个以逗号分隔） |
| domain_distribution.content_types | string | 内容类型（多个以逗号分隔） |
| domain_distribution.platforms | string | 中国大模型平台（多个以逗号分隔） |
| domain_distribution.domain_citation_rate | float | 域名引用率 |
| metadata | object | 元数据 |
| metadata.tenant_key | string | 租户标识 tenant_key |
| metadata.job_id | string | 任务ID |
| metadata.keyword | string | 关键词 |
| metadata.timeframe | string | 时间范围 |
| metadata.start_date | string | 起始日期 |
| metadata.end_date | string | 结束日期 |
| metadata.calculation_method | string | 计算方法 |
| metadata.row_count | int | 数据行数 |

> **💡 计算口径说明**：
> - **域名引用率**：计算各域名在指定范围内的引用占比。
> - **分母说明**：
>     - 基础分母为指定品牌、时间范围内的总引用记录数。
>     - 当筛选 `platform` 时，分母同步缩小为该平台内的总引用数。
>     - 当筛选 `keyword` 时，**分母保持不变**（即保持在平台层级或品牌层级），以反映该关键词对整体/平台的**贡献度（Contribution）**，而非该关键词细分市场内的占比。

### 数据计算逻辑

当没有 keyword 和 platform 筛选时，计算逻辑（体现品牌/时间范围内的整体域名引用率）
```sql
SELECT 
    domain, 
    GROUP_CONCAT(DISTINCT keyword) AS keywords,
    GROUP_CONCAT(DISTINCT content_type) AS content_types, 
    GROUP_CONCAT(DISTINCT platform) AS platforms,
    ROUND(
        COUNT(*) * 100.0 / NULLIF((
            SELECT COUNT(*)
            FROM qa_reference
            WHERE 
              tenant_key = <tenant_key>
              AND job_id = <job_id>
              AND brand = <brand>
              AND domain IS NOT NULL
              AND `date` BETWEEN :start_date AND :end_date
        ), 0),
        2
    ) AS domain_citation_rate
FROM qa_reference
WHERE
    tenant_key = <tenant_key>
    AND job_id = <job_id>
    AND brand = <brand>
    AND domain IS NOT NULL
    AND `date` BETWEEN :start_date AND :end_date
GROUP BY domain
ORDER BY domain_citation_rate DESC;
```

当有单独的 keyword 筛选时，计算逻辑（体现关键词对品牌的贡献度）
```sql
SELECT 
    domain, 
    GROUP_CONCAT(DISTINCT keyword) AS keywords,
    GROUP_CONCAT(DISTINCT content_type) AS content_types, 
    GROUP_CONCAT(DISTINCT platform) AS platforms,
    ROUND(
        COUNT(*) * 100.0 / NULLIF((
            SELECT COUNT(*)
            FROM qa_reference
            WHERE 
              tenant_key = <tenant_key>
              AND job_id = <job_id>
              AND brand = <brand>
              AND domain IS NOT NULL
              AND `date` BETWEEN :start_date AND :end_date
        ), 0),
        2
    ) AS domain_citation_rate
FROM qa_reference
WHERE
    tenant_key = <tenant_key>
    AND job_id = <job_id>
    AND brand = <brand>
    AND keyword = :keyword
    AND domain IS NOT NULL
    AND `date` BETWEEN :start_date AND :end_date
GROUP BY domain
ORDER BY domain_citation_rate DESC;
```

当有 keyword 和 platform 筛选时的计算逻辑（体现关键词对平台的贡献度）
```sql
SELECT 
    domain, 
    GROUP_CONCAT(DISTINCT keyword) AS keywords,
    GROUP_CONCAT(DISTINCT content_type) AS content_types, 
    GROUP_CONCAT(DISTINCT platform) AS platforms,
    ROUND(
        COUNT(*) * 100.0 / (
            SELECT COUNT(*)
            FROM qa_reference
            WHERE 
              tenant_key = <tenant_key>
              AND job_id = <job_id>
              AND brand = <brand>
              -- 分母不受 keyword 影响，仅受 platform 影响 (实现平台内贡献度)
              AND platform = :platform
              AND domain IS NOT NULL
              AND `date` BETWEEN :start_date AND :end_date
        ),
        2
    ) AS domain_citation_rate
FROM qa_reference
WHERE
    tenant_key = <tenant_key>
    AND job_id = <job_id>
    AND brand = <brand>
    -- 分子受 keyword 和 platform 共同筛选
    AND keyword = :keyword
    AND platform = :platform
    AND domain IS NOT NULL
    AND `date` BETWEEN :start_date AND :end_date
GROUP BY domain
ORDER BY domain_citation_rate DESC;
```
---------------------------

### 接口信息
- **路径**: `/api/v1/dashboard/citation-domain-summary`
- **方法**: `GET`
- **描述**: 获取域名维度的引用率汇总，按域名聚合，适配前端 `ReferencesTable` 组件

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
curl -X GET "http://your-api.com/api/v1/dashboard/citation-domain-summary?tenant_key=tn_xxx&job_id=job_456&brand=学而思&timeframe=30days"
```

### 响应格式

```json
{
  "status": "success",
  "domain_distribution": [
    {
      "domain": "www.baidu.com",
      "chinese_name": "百度",
      "citation_count": 10,
      "keyword_coverage": 1,
      "platform_coverage": 1,
      "domain-citation-rate": 15.42
    },
    {
      "domain": "www.google.com",
      "chinese_name": "谷歌",
      "citation_count": 50,
      "keyword_coverage": 1,
      "platform_coverage": 1,
      "domain-citation-rate": 5.21
    }
  ],
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_456",
    "brand": "学而思",
    "timeframe": "30days",
    "start_date": "20260102",
    "end_date": "20260131",
    "calculation_method": "domain_citation_summary",
    "row_count": 2
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| domain_distribution | array | 域名引用率汇总分布 |
| domain_distribution.domain | string | 域名 |
| domain_distribution.chinese_name | string | 域名中文名称 |
| domain_distribution.citation_count | int | 域名引用次数 |
| domain_distribution.keyword_coverage | int | 域名关键词覆盖数 |
| domain_distribution.platform_coverage | int | 域名平台覆盖数 |
| domain_distribution.domain-citation-rate | float | 域名总引用率 |
| metadata | object | 元数据 |

### 数据计算逻辑

```sql
SELECT 
    domain,
    COUNT(*) AS citation_count,
    COUNT(DISTINCT keyword) AS keyword_coverage,
    COUNT(DISTINCT platform) AS platform_coverage,
    ROUND(
        COUNT(*) * 100.0 / NULLIF((
            SELECT COUNT(*)
            FROM qa_reference
            WHERE 
              tenant_key = <tenant_key>
              AND job_id = <job_id>
              AND brand = <brand>
              AND domain IS NOT NULL
              AND `date` BETWEEN :start_date AND :end_date
        ), 0),
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
> **注**：`chinese_name` 的映射由 API 后端代码根据 `domain` 完成，不涉及数据库聚合操作。
---------------------------

## 📊 引用类型占比统计 API

### 接口信息
- **路径**: `/api/v1/dashboard/citation-type-stats`
- **方法**: `GET`
- **描述**: 获取引用类型占比统计，返回总条数、去重对话数及各引用类型占比，基于`qa_reference`表计算

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
curl -X GET "http://your-api.com/api/v1/dashboard/citation-type-stats?tenant_key=tn_xxx&job_id=job_456&timeframe=30days"
```

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/citation-type-stats?tenant_key=tn_xxx&job_id=job_456&timeframe=specific_day&start_date=20260102&end_date=20260131"
```

### 响应格式

```json
{
  "status": "success",
  "summary": {
    "total_rows": 1240,
    "conversations": 356
  },
  "citation_type_stats": [
    {
      "content_type": "news",
      "type_pct": 42.35
    },
    {
      "content_type": "tech_review",
      "type_pct": 28.19
    },
    {
      "content_type": "gov_report",
      "type_pct": 12.58
    }
  ],
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_456",
    "timeframe": "30days",
    "start_date": "20260102",
    "end_date": "20260131",
    "calculation_method": "content_type_pct",
    "row_count": 3
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| summary | object | 汇总信息 |
| summary.total_rows | int | 总条数 |
| summary.conversations | int | 去重对话数 |
| citation_type_stats | array | 引用类型占比列表 |
| citation_type_stats.content_type | string | 引用类型 |
| citation_type_stats.type_pct | float | 引用类型占比（百分比） |
| metadata | object | 元数据 |
| metadata.tenant_key | string | 租户标识 tenant_key |
| metadata.job_id | string | 任务ID |
| metadata.timeframe | string | 时间范围 |
| metadata.start_date | string | 起始日期 |
| metadata.end_date | string | 结束日期 |
| metadata.calculation_method | string | 计算方法 |
| metadata.row_count | int | 引用类型条目数 |

### 数据计算逻辑

```sql
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT conversation_id) AS conversations
FROM qa_reference
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND `date` BETWEEN :start_date AND :end_date;
```

```sql
SELECT
    content_type,
    ROUND(
        COUNT(*) * 100.0 / NULLIF((
            SELECT COUNT(*)
            FROM qa_reference
            WHERE tenant_key = :tenant_key
              AND job_id = :job_id
              AND `date` BETWEEN :start_date AND :end_date
        ), 0),
        2
    ) AS type_pct
FROM qa_reference
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND `date` BETWEEN :start_date AND :end_date
GROUP BY content_type
ORDER BY type_pct DESC;
```
---------------------------

## 📊 品牌总提及率 API [未使用]

### 接口信息
- **路径**: `/api/v1/dashboard/brand-mention-rate` [未使用]
- **方法**: `GET`
- **描述**: 获取品牌总提及率数据，基于`qa_brand_summary`表计算

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

## 📉 各平台品牌提及率对比 API [未使用]

### 接口信息
- **路径**: `/api/v1/dashboard/platform-mention-rates` [未使用]
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
- **描述**: 获取指定品牌在指定平台、指定关键词下的"按日提及率"趋势数据（仅返回日期范围内实际有数据的日期点位）

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

## 📊 引用统计 API

### 全局引用URL统计 [未使用]

### 接口信息
- **路径**: `/api/v1/dashboard/citation-url-stats`
- **方法**: `GET`
- **描述**: 获取全局引用 URL 的统计数据，包括各站点的引用次数和引用率。基于`qa_reference`表计算。
- **实现状态**: ✅ 已完成

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 tenant_key |
| job_id | string | 是 | 任务ID |
| keyword | string | 是 | 关键词 |
| domain | string | 是 | 域名 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days`, `specific_day` |
| start_date | string | 否 | 起始日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |
| end_date | string | 否 | 结束日期，格式: `YYYYMMDD`（当 `timeframe=specific_day` 时必填） |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/citation-url-stats?tenant_key=tn_xxx&job_id=job_456&keyword=三角洲陪玩&domain=zhihu.com&timeframe=7days"
```

### 响应格式

```json
{
  "status": "success",
  "data": [
    {
      "answer_reference_url": "https://www.zhihu.com/question/xxx",
      "citation_count": 15,
      "total_questions": 100,
      "chinese_name": "知乎",
      "citation_rate": 15.0
    },
    ...
  ],
  "metadata": {
    "tenant_key": "tn_xxx",
    "job_id": "job_456",
    "keyword": "数学培训",
    "domain": "zhihu.com",
    "timeframe": "7days",
    "start_date": "20260102",
    "end_date": "20260131",
    "calculation_method": "citation_url_count",
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
    COUNT(*) AS citation_count 
FROM qa_reference 
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND keyword = :keyword      -- 过滤：特定关键词
  AND domain = :domain        -- 过滤：特定域名
  AND url IS NOT NULL 
  AND date BETWEEN :start_date AND :end_date 
GROUP BY url 
ORDER BY citation_count DESC;

-- 2. 获取总提问数（用于计算引用率）
SELECT COUNT(DISTINCT conversation_id) AS total_questions 
FROM qa_reference 
WHERE tenant_key = :tenant_key
  AND job_id = :job_id
  AND date BETWEEN :start_date AND :end_date;
```

- **citation_rate**: `(citation_count / total_questions) * 100`

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
