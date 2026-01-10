# Dashboard API 文档

## 品牌总指标 API

---------------------

### 接口信息
- **路径**: `/api/dashboard/brand-metrics`
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
      "platform": "deepseek",
      "mention_rate": 0.3333,
      "first_mention_rate": 0.0000,
      "citation_rate_by_post": 0,
      "prompt_count": 15,
      "citation_source_count": 0,
      "keyword_coverage": 3
    },
    {
      "brand": "新东方",
      "platform": "deepseek",
      "mention_rate": 0.2667,
      "first_mention_rate": 0.1333,
      "citation_rate_by_post": 0,
      "prompt_count": 15,
      "citation_source_count": 0,
      "keyword_coverage": 2
    },
    {
      "brand": "作业帮",
      "platform": "deepseek",
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
| platform | string | 平台名称（如：DeepSeek、豆包、千问 等） |
| mention_rate | float | 品牌总提及率（百分比） |
| first_mention_rate | float | 首次提及品牌率（百分比） |
| citation_rate_by_post | float | 引用率（每个帖子的引用次数占总引用次数的比例） |
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
    AND date >= CURDATE() - INTERVAL 6 DAY   -- 过去7天（含今天）
    AND date <= CURDATE()
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
    AND date >= CURDATE() - INTERVAL 6 DAY   -- 过去7天（含今天）
    AND date <= CURDATE();
```
`

--------------------------

### 接口信息
- **路径**: `/api/dashboard/platform-metrics-by-brand`
- **方法**: `GET`
- **描述**: 获取品牌总指标，基于`qa_brand_state`表计算

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
    AND date >= CURDATE() - INTERVAL 6 DAY
    AND date <= CURDATE()
GROUP BY platform
ORDER BY platform ASC;
```

---------------------

### 接口信息
- **路径**: `/api/dashboard/post-citation-rate`
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
    COUNT(DISTINCT qr.domain) AS 引用信源数值,
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
                    AND date >= CURDATE() - INTERVAL 6 DAY
                    AND date <= CURDATE()
                GROUP BY conversation_id
            ) AS conv_stats
        ),
        0
    ) AS 发文引用率
FROM qa_reference qr
WHERE
    qr.user_id = <user_id>
    AND qr.job_id = <job_id>
    AND qr.brand = <brand>
    AND qr.date >= CURDATE() - INTERVAL 6 DAY
    AND qr.date <= CURDATE()
GROUP BY brand;
```
---------------------

### 接口信息
- **路径**: `/api/dashboard/domain-citation-rate`
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
            WHERE brand = <brand>
              AND domain IS NOT NULL
              AND date >= CURDATE() - INTERVAL 6 DAY
        ),
        2
    ) AS percentage
FROM qa_reference
WHERE
    user_id = <user_id>
    AND job_id = <job_id>
    AND brand = <brand>
    AND domain IS NOT NULL
    AND date >= CURDATE() - INTERVAL 6 DAY
GROUP BY domain
ORDER BY percentage DESC;
```

---------------------------

## 📊 品牌总提及率 API

### 接口信息
- **路径**: `/api/dashboard/brand-mention-rate`
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
curl -X GET "http://localhost:8000/api/dashboard/brand-mention-rate?brand=Apple&timeframe=7days" \
  -H "accept: application/json"
```

### 数据计算逻辑

基于`qa_brand_summary`表的字段计算：
- **mention_rate**: `AVG(mention_rate)` 在指定时间范围内的平均值
- **change**: 当前周期与上一周期提及率的百分比变化

---

## 📈 各平台品牌提及率对比 API

### 接口信息
- **路径**: `/api/dashboard/platform-mention-rates`
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
| first_mention_rate | float | 该平台上的品牌首次提及率（百分比） |
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
| ChatGPT | #10b981 |
| Gemini | #3b82f6 |
| Claude | #f59e0b |
| 通义千问/Qwen | #ef4444 |
| 豆包 | #8b5cf6 |
| DeepSeek/Deepseek | #06b6d4 |
| Kimi | #a855f7 |
| 元宝 | #f97316 |
| 夸克 | #ec4899 |
| 文心一言 | #6b7280 |
| 其他平台 | #6b7280 |

### 使用示例

```bash
curl -X GET "http://localhost:8000/api/dashboard/platform-mention-rates?category=手机&brand=Apple&keyword=iPhone&timeframe=7days" \
  -H "accept: application/json"
```

---

## 🔗 引用URL统计 API

### 接口信息
- **路径**: `/api/dashboard/reference-url-stats`
- **方法**: `GET`
- **描述**: 获取全局引用URL统计数据，基于`qa_reference`表查询
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
      "answer_reference_url": "https://item.taobao.com/item.htm?id=12345",
      "reference_count": 25,
      "total_questions": 100,
      "chinese_name": "淘宝",
      "reference_rate": 25.0
    },
    {
      "answer_reference_url": "https://item.jd.com/item.html?sku=67890",
      "reference_count": 18,
      "total_questions": 100,
      "chinese_name": "京东",
      "reference_rate": 18.0
    }
  ],
  "metadata": {
    "timeframe": "7days",
    "calculation_method": "reference_url_count",
    "url_count": 10
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| data | array | 引用URL统计数据列表 |
| answer_reference_url | string | 被引用的URL地址 |
| reference_count | int | 该URL被引用的次数 |
| total_questions | int | 总提问数（用于计算引用率） |
| chinese_name | string | URL域名对应的中文名称（如：淘宝、京东等） |
| reference_rate | float | 引用率（引用次数/总提问数 * 100） |
| metadata | object | 元数据 |
| metadata.timeframe | string | 请求的时间范围 |
| metadata.calculation_method | string | 计算方式说明 |
| metadata.url_count | int | 返回的URL数量 |

### 使用示例

```bash
curl -X GET "http://localhost:8000/api/dashboard/reference-url-stats?timeframe=7days" \
  -H "accept: application/json"
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
│   └── config.py             # 配置相关API
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

---

## ⚡ 错误处理

### 通用错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### 参数验证错误

当 timeframe 参数值无效时，返回 HTTP 400 错误：

```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["query", "timeframe"],
      "msg": "Input should be 'yesterday', '7days' or '30days'",
      "input": "invalid",
      "ctx": {
        "expected": "'yesterday', '7days' or '30days'"
      }
    }
  ]
}
```

### 日期格式错误

当 date 参数格式错误时，返回 HTTP 400 错误：

```json
{
  "detail": "日期格式错误，应为YYYYMMDD"
}
```

### 服务器内部错误

当数据库查询失败时，返回 HTTP 500 错误：

```json
{
  "detail": "获取品牌总提及率失败: 数据库查询失败"
}
```

---

## 🧪 测试文件

### 测试命令

```bash
# 运行所有测试
pytest tests/

# 运行Dashboard相关测试
pytest tests/test_dashboard_*.py

# 运行特定测试函数
pytest tests/test_dashboard_api.py::test_brand_mention_rate
```

---

## 📝 更新记录

- **2025-01-15**: 修正各平台提及率API文档，参数改为单个brand，响应格式改为扁平列表
- **2025-01-15**: 修正引用URL统计API响应格式，添加status、metadata包装字段
- **2025-01-15**: 更新字段说明，添加 chinese_name、reference_rate、color 等字段
- **2025-01-15**: 移除品牌情感分析API文档（代码中未实现）
- **2025-01-15**: 更新平台颜色映射表
