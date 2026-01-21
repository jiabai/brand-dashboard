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
- **路径**: `/api/analysis/positioning-keywords`
- **方法**: `POST`
- **描述**: 基于行业和品牌名称，利用 LLM 生成品牌定位关键词。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| industry | string | 是 | 行业名称（如：教育、汽车） |
| brand | string | 是 | 品牌名称（如：学而思、蔚来） |

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
- **路径**: `/api/analysis/consumer-questions`
- **方法**: `POST`
- **描述**: 基于行业、品牌和核心关键词，生成消费者可能会问的问题。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| industry | string | 是 | 行业名称 |
| brand | string | 是 | 品牌名称 |
| keywords | array | 是 | 关键词列表 |

### 响应格式

```json
{
  "关键词1": ["问题1", "问题2"],
  "关键词2": ["问题3", "问题4"]
}
```

---

## 📥 数据加载 API

### LLM查询记录加载接口

### 接口信息
- **路径**: `/api/query-records/load`
- **方法**: `POST`
- **描述**: 接收原始 JSON 数据并批量加载到 `llm_query_record` 数据库表中。

### 请求参数 (JSON Body)

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenant_key | string | 是 | 租户标识 Key |
| job_id | string | 是 | 任务 ID |
| data | object | 是 | 查询记录数据对象 |

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

```json
{
  "tenant_key": "test_tenant",
  "job_id": "job_123456",
  "data": {
    "category": "教育",
    "brand": "学而思",
    "competitor": ["新东方", "作业帮"],
    "content": [
      {
        "keyword": "数学网课",
        "query_content": [
          "推荐几个好的数学网课",
          "学而思的数学网课怎么样"
        ]
      }
    ]
  }
}
```

### 响应格式

```json
{
  "success": true,
  "inserted_rows": 2,
  "message": "LLM查询记录加载成功"
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| success | boolean | 是否处理成功 |
| inserted_rows | int | 实际插入数据库的行数 |
| message | string | 提示消息 |

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
│   └── query_records.py      # LLM查询记录相关API
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
