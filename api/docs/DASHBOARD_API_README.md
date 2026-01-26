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
| user_id | string | 是 | 用户ID |
| job_id | string | 是 | 任务ID |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |
| brand | string | 否 | 品牌名称 |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/brand-metrics?user_id=usr_123&job_id=job_456&timeframe=7days"
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
      "citation_rate_by_post": 0,
      "prompt_count": 15,
      "citation_source_count": 0,
      "keyword_coverage": 3
    },
    {
      "brand": "新东方",
      "mention_rate": 0.2667,
      "first_mention_rate": 0.1333,
      "citation_rate_by_post": 0,
      "prompt_count": 15,
      "citation_source_count": 0,
      "keyword_coverage": 2
    },
    {
      "brand": "作业帮",
      "mention_rate": 0.2000,
      "first_mention_rate": 0.0000,
      "citation_rate_by_post": 0,
      "prompt_count": 15,
      "citation_source_count": 0,
      "keyword_coverage": 3
    },
    ......
  ],
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
| brand | string | 品牌名称 |
| mention_rate | float | 品牌总提及率（百分比） |
| first_mention_rate | float | 首次提及 brand 率（百分比） |
| citation_rate_by_post | float | 发文引用率（发文的引用次数占总引用次数的比例） |
| prompt_count | int | 问题总数 |
| citation_source_count | int | 引用来源数量 |
| keyword_coverage | int | 问题的答案提及品牌时，问题所属关键词的个数 |

### 数据计算逻辑

当请求参数不带brand='xxx'时，返回所有品牌的指标：
```sql
SELECT 
    brand,
    COUNT(DISTINCT conversation_id) AS prompt_count,
    SUM(is_mentioned) / COUNT(DISTINCT conversation_id) AS mention_rate,
    SUM(is_first_mention) / COUNT(DISTINCT conversation_id) AS first_mention_rate,
    0 AS citation_rate_by_post,
    0 AS citation_source_count,
    COUNT(DISTINCT CASE WHEN is_mentioned = 1 THEN keyword END) AS keyword_coverage
FROM qa_brand_state
WHERE 
    user_id = <user_id>
    AND job_id = <job_id>
    AND `date` >= CURDATE() - INTERVAL <timeframe> DAY
    AND `date` <= CURDATE()
GROUP BY brand
ORDER BY mention_rate DESC, brand ASC;
```

当请求参数带brand='xxx'时，返回指定品牌的指标：
```sql
SELECT 
    brand,
    COUNT(DISTINCT conversation_id) AS prompt_count,
    SUM(is_mentioned) / COUNT(DISTINCT conversation_id) AS mention_rate,
    SUM(is_first_mention) / COUNT(DISTINCT conversation_id) AS first_mention_rate,
    0 AS citation_rate_by_post,
    0 AS citation_source_count,
    COUNT(DISTINCT CASE WHEN is_mentioned = 1 THEN keyword END) AS keyword_coverage
FROM qa_brand_state
WHERE 
    user_id = <user_id>
    AND job_id = <job_id>
    AND brand = <brand>
    AND `date` >= CURDATE() - INTERVAL <timeframe> DAY
    AND `date` <= CURDATE();
```

--------------------------

### 接口信息
- **路径**: `/api/v1/dashboard/platform-metrics-by-brand`
- **方法**: `GET`
- **描述**: 获取平台指标，基于`qa_brand_state`表计算

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| user_id | string | 是 | 用户ID |
| job_id | string | 是 | 任务ID |
| brand | string | 是 | 品牌名称 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/platform-metrics-by-brand?user_id=usr_123&job_id=job_456&brand=学而思&timeframe=7days"
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
    "timeframe": "7days",
    "calculation_method": "platform_metrics_by_brand"
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| brand | string | 品牌名称 |
| platforms | array | 平台指标列表 |
| platform | string | 平台名称 |
| mention_rate | float | 平台提及率（百分比） |

### 数据计算逻辑

```sql
SELECT 
    platform,
    SUM(is_mentioned) / COUNT(*) AS mention_rate
FROM qa_brand_state
WHERE 
    user_id = <user_id>
    AND job_id = <job_id>
    AND brand = <brand>
    AND date >= CURDATE() - INTERVAL <timeframe> DAY
    AND date <= CURDATE()
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
| user_id | string | 是 | 用户ID |
| job_id | string | 是 | 任务ID |
| brand | string | 是 | 品牌名称 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/post-citation-rate?user_id=usr_123&job_id=job_456&brand=学而思&timeframe=7days"
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
| citation_source_count | int | 引用来源数量 |
| citation_rate_by_post | float | 发文引用率（发文的引用次数占总引用次数的比例） |

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
                    user_id = <user_id>
                    AND job_id = <job_id>
                    AND brand = <brand>
                    AND date >= CURDATE() - INTERVAL <timeframe> DAY
                    AND date <= CURDATE()
                GROUP BY conversation_id
            ) AS conv_stats
        ),
        0
    ) AS citation_rate_by_post
FROM qa_reference qr
WHERE
    qr.user_id = <user_id>
    AND qr.job_id = <job_id>
    AND qr.brand = <brand>
    AND qr.date >= CURDATE() - INTERVAL <timeframe> DAY
    AND qr.date <= CURDATE()
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
| user_id | string | 是 | 用户ID |
| job_id | string | 是 | 任务ID |
| brand | string | 是 | 品牌名称 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/domain-citation-rate?user_id=usr_123&job_id=job_456&brand=学而思&timeframe=7days"
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
    "timeframe": "7days",
    "calculation_method": "domain_citation_rate"
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| domain_distribution | array | 域名引用率分布 |
| domain | string | 域名 |
| domain-citation-rate | float | 域名引用率 |
| metadata | object | 元数据 |
| timeframe | string | 时间范围 |
| calculation_method | string | 计算方法 |

### 数据计算逻辑

```sql
SELECT 
    domain,
    ROUND(
        COUNT(*) * 100.0 / (
            SELECT COUNT(*)
            FROM qa_reference
            WHERE 
              user_id = <user_id>
              AND job_id = <job_id>
              AND brand = <brand>
              AND domain IS NOT NULL
              AND date >= CURDATE() - INTERVAL <timeframe> DAY
        ),
        2
    ) AS percentage
FROM qa_reference
WHERE
    user_id = <user_id>
    AND job_id = <job_id>
    AND brand = <brand>
    AND domain IS NOT NULL
    AND date >= CURDATE() - INTERVAL <timeframe> DAY
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
| brand | string | 是 | 品牌名称 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/platform-mention-rates?category=手机&brand=Apple&keyword=iPhone&timeframe=7days"
```

### 响应格式

```json
{
  "status": "success",
  "data": {
    "mention_rate": 50.0,
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
curl -X GET "http://localhost:8000/api/v1/dashboard/brand-mention-rate?brand=Apple&timeframe=7days" \
  -H "accept: application/json"
```

### 数据计算逻辑

基于`qa_brand_summary`表的字段计算：
- **mention_rate**: `AVG(mention_rate)` 在指定时间范围内的平均值
- **change**: 当前周期与上一周期提及率的百分比变化

---

## 📈 各平台品牌提及率对比 API

### 接口信息
- **路径**: `/api/v1/dashboard/platform-mention-rates`
- **方法**: `GET`
- **描述**: 获取单个品牌在各平台的提及率对比数据，基于`qa_brand_summary`表计算
- **实现状态**: ✅ 已完成

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| category | string | 是 | 商品大类 |
| brand | string | 是 | 品牌名称 |
| keyword | string | 是 | 品牌关键词，或"全部" |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/dashboard/reference-url-stats?timeframe=7days"
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
| 豆包      | `#3b82f6` |
| 千问      | `#8b5cf6` |

---

## 🔗 引用统计 API

### 全局引用URL统计

### 接口信息
- **路径**: `/api/v1/dashboard/reference-url-stats`
- **方法**: `GET`
- **描述**: 获取全局引用 URL 的统计数据，包括各站点的引用次数和引用率。
- **实现状态**: ✅ 已完成

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

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

---

## 🧠 品牌策略与分析 API (LLM)

### 品牌定位关键词生成

### 接口信息
- **路径**: `/api/v1/analysis/positioning-keywords`
- **方法**: `POST`
- **描述**: 基于行业和品牌名称，利用 LLM 生成品牌定位关键词。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| industry | string | 是 | 行业名称（如：教育、汽车） |
| brand | string | 是 | 品牌名称（如：学而思、蔚来） |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/analysis/positioning-keywords" \
     -H "Content-Type: application/json" \
     -d '{
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

---

### 消费者常见问题生成

### 接口信息
- **路径**: `/api/v1/analysis/consumer-questions`
- **方法**: `POST`
- **描述**: 基于行业、品牌和核心关键词，生成消费者可能会问的问题。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| industry | string | 是 | 行业名称 |
| brand | string | 是 | 品牌名称 |
| keywords | array | 是 | 关键词列表 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/analysis/consumer-questions" \
     -H "Content-Type: application/json" \
     -d '{
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
| brand | string | 否 | 品牌名称 |
| competitor | array | 否 | 竞品名称列表 |
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

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/query-jobs/fetch?executor_id=exec_bbda021a" \
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
| tenant_key | string | 否 | Query | 租户标识 Key |
| job_id | string | 否 | Query | 任务 ID |
| platform | string | 否 | Query | 平台名称 |
| limit | integer | 否 | Query | 返回条数，默认 50 |
| cursor | string | 否 | Query | 分页游标 |

### 请求示例

```bash
curl -X GET "http://your-api.com/api/v1/conversation/fetch?executor_id=exec_3f2a1b9c&platform=deepseek&limit=10" \
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
      "model_name": "deepseek-chat",
      "token_usage": 1234,
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

#### `query_brand_mention_data(brand, timeframe, specific_date)`
- **功能**: 查询品牌提及率数据
- **参数**:
  - `brand`: 品牌名称
  - `timeframe`: 时间范围（yesterday, 7days, 30days）
  - `specific_date`: 指定日期（可选，格式: YYYYMMDD）
- **返回**: 包含提及率数据的字典

#### `query_brand_platform_mention_data(brand, timeframe, specific_date)`
- **功能**: 查询品牌在各平台的提及率数据
- **参数**:
  - `brand`: 品牌名称
  - `timeframe`: 时间范围
  - `specific_date`: 指定日期（可选）
- **返回**: 包含各平台提及率数据的列表

#### `query_reference_url_stats(timeframe, specific_date)`
- **功能**: 查询引用URL统计数据
- **参数**:
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
| LLM查询记录加载 | `llm_query_record` | N/A (Direct Insert) | ✅ 已完成 |
