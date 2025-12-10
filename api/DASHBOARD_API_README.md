# Dashboard API 文档

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
    "mention_rate": 50.0,           // 品牌总提及率(百分比)
    "rank": 1,                      // 品牌排名
    "change": 5.2,                  // 与上一周期对比的变化(百分比)
    "question_count": 12,           // 问题总数
    "mention_count": 6,             // 品牌提及数量
    "first_mention_count": 3,       // 首次提及品牌数量
    "analysis_date": "2025-11-28",  // 分析日期
    "last_updated": "2025-12-08T20:02:15.198791"   // 最后更新时间
  },
  "metadata": {
    "timeframe": "7days",           // 请求的时间范围
    "calculation_method": "mention_count_ratio",    // 计算方式说明
    "data_source": "qa_brand_summary"             // 数据来源表
  }
}
```

### 使用示例

#### 获取7天数据
```bash
curl -X GET "http://localhost:8000/api/dashboard/brand-mention-rate?brand=Apple&timeframe=7days" \
  -H "accept: application/json"
```



#### 获取昨天数据并指定日期
```bash
curl -X GET "http://localhost:8000/api/dashboard/brand-mention-rate?brand=Apple&timeframe=yesterday&date=20251128" \
  -H "accept: application/json"
```

### 数据计算逻辑

基于`qa_brand_summary`表的字段计算：
- **mention_rate**: `mention_count / question_count * 100`
- **change**: 与上一周期对比的百分比变化

### 错误处理

#### 参数验证错误
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

#### 数据不存在错误
```json
{
  "status": "error",
  "message": "No data found for brand 'Apple' in the specified timeframe",
  "data": null
}
```

#### 数据库错误处理
```python
try:
    result = query_brand_mention_data(brand, timeframe, specific_date)
except Exception as e:
    logger.error(f"数据库查询失败: {str(e)}")
    return {"error": "数据查询失败，请稍后重试"}
```

---

## 📈 各平台品牌提及率对比 API

### 接口信息
- **路径**: `/api/dashboard/platform-mention-rates`
- **方法**: `GET`
- **描述**: 获取多个品牌在各平台的提及率对比数据，基于`qa_brand_summary`表计算
- **实现状态**: ✅ 已完成

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| brands | string | 是 | 品牌名称列表（逗号分隔） |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |

### 响应格式

```json
{
  "status": "success",
  "data": {
    "timeframe": "7days",
    "platforms": ["qwen", "deepseek"],
    "brands": ["Apple", "Huawei"],
    "platform_data": {
      "qwen": {
        "Apple": {
          "mention_rate": 45.0,
          "mention_count": 9,
          "question_count": 20,
          "rank": 1
        },
        "Huawei": {
          "mention_rate": 35.0,
          "mention_count": 7,
          "question_count": 20,
          "rank": 2
        }
      },
      "deepseek": {
        "Apple": {
          "mention_rate": 60.0,
          "mention_count": 6,
          "question_count": 10,
          "rank": 1
        },
        "Huawei": {
          "mention_rate": 40.0,
          "mention_count": 4,
          "question_count": 10,
          "rank": 2
        }
      }
    }
  },
  "metadata": {
    "total_brands": 2,
    "total_platforms": 2,
    "data_source": "qa_brand_summary"
  }
}
```

### 使用示例

```bash
# 比较Apple和华为在各平台的提及率
curl -X GET "http://localhost:8000/api/dashboard/platform-mention-rates?brands=Apple,Huawei&timeframe=7days" \
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
| limit | integer | 否 | 返回结果数量限制，默认50 |

### 响应格式

```json
[
  {
    "answer_reference_url": "https://item.taobao.com/12345.htm",
    "reference_count": 25,
    "total_questions": 100
  },
  {
    "answer_reference_url": "https://item.jd.com/67890.htm", 
    "reference_count": 15,
    "total_questions": 100
  }
]
```

### 使用示例

```bash
# 获取引用URL统计
curl -X GET "http://localhost:8000/api/dashboard/reference-url-stats?timeframe=7days" \
  -H "accept: application/json"

# 获取指定日期的引用统计
curl -X GET "http://localhost:8000/api/dashboard/reference-url-stats?timeframe=yesterday&date=20251128&limit=10" \
  -H "accept: application/json"
```

---

## 📈 品牌情感分析 API

### 接口信息
- **路径**: `/api/dashboard/brand-sentiment`
- **方法**: `GET`
- **描述**: 获取品牌情感分析数据，基于`qa_brand_state`表计算
- **实现状态**: 🔄 开发中

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| brand | string | 是 | 品牌名称 |
| timeframe | string | 是 | 时间范围，可选值: `yesterday`, `7days`, `30days` |
| date | string | 否 | 具体日期，格式: `YYYYMMDD` |
| sentiment | string | 否 | 情感类型筛选，`positive`、`negative`、`neutral` |

### 响应格式

```json
{
  "status": "success",
  "data": {
    "brand": "Apple",
    "timeframe": "7days",
    "sentiment_distribution": {
      "positive": 45,
      "negative": 15,
      "neutral": 40
    },
    "sentiment_ratios": {
      "positive_ratio": 0.45,
      "negative_ratio": 0.15,
      "neutral_ratio": 0.40
    },
    "total_mentions": 100,
    "analysis_date": "2025-11-28",
    "last_updated": "2025-12-08T20:02:15.198791",
    "top_positive_questions": [
      {
        "question_id": "q123",
        "question": "Apple的产品质量如何？",
        "answer": "Apple的产品质量一直很优秀...",
        "platform": "qwen",
        "date": "2025-11-27"
      }
    ],
    "top_negative_questions": [
      {
        "question_id": "q456",
        "question": "Apple的价格是否合理？",
        "answer": "Apple的价格相对较高...",
        "platform": "deepseek",
        "date": "2025-11-26"
      }
    ]
  },
  "metadata": {
    "data_source": "qa_brand_state",
    "sentiment_fields": ["positive", "negative", "neutral"],
    "calculation_method": "sentiment_status_count"
  }
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
│   └── config.py             # 配置相关API
├── repositories/
│   └── database.py           # 数据库查询函数
├── models/
│   └── schemas.py            # 数据模型定义
└── database/
    ├── schema.sql            # 数据库表结构
    └── README.md             # 数据库文档
```

### 核心查询函数（位于 `repositories/database.py`）

#### `query_brand_mention_data(brand, timeframe, specific_date)`
- **功能**: 查询品牌提及数据
- **参数**: 
  - `brand`: 品牌名称
  - `timeframe`: 时间范围
  - `specific_date`: 指定日期（可选）
- **返回**: 提及数据和趋势

#### `query_reference_url_stats(timeframe, specific_date, limit)`
- **功能**: 查询引用URL统计数据
- **参数**:
  - `timeframe`: 时间范围
  - `specific_date`: 指定日期（可选）
  - `limit`: 返回数量限制
- **返回**: URL统计和分布数据

#### `query_brand_platform_mention_data(brand, timeframe, specific_date)`
- **功能**: 查询品牌在各平台的提及数据
- **参数**:
  - `brand`: 品牌名称
  - `timeframe`: 时间范围
  - `specific_date`: 指定日期（可选）
- **返回**: 平台提及率对比数据

### 辅助函数

#### `get_date_range(timeframe)`
- **功能**: 根据时间范围计算日期区间
- **返回**: 开始日期和结束日期

#### `get_previous_date_range(timeframe)`
- **功能**: 计算上一期日期区间（用于同比分析）
- **返回**: 上一期的开始日期和结束日期

---

## 📊 数据库表对应关系

| API接口 | 主要数据表 | 查询函数 | 实现状态 |
|---------|------------|----------|----------|
| 品牌总提及率 | `qa_brand_summary` | `query_brand_mention_data` | ✅ 已完成 |
| 各平台提及率 | `qa_brand_summary` | `query_brand_platform_mention_data` | ✅ 已完成 |
| 引用URL统计 | `qa_reference` | `query_reference_url_stats` | ✅ 已完成（全局统计） |
| 品牌情感分析 | `qa_brand_state` | 待实现 | 🔄 开发中 |

---

## 🧪 测试文件

### 测试文件位置
- `tests/test_dashboard_api.py` - API接口测试
- `tests/test_dashboard_service.py` - 服务层测试
- `tests/test_database.py` - 数据库查询测试

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

## ⚡ 性能优化建议

### 1. 数据库优化
- 使用索引字段进行过滤（date, brand, platform）
- 合理使用聚合函数减少数据量
- 考虑添加复合索引提升查询性能

### 2. 缓存策略
- 对热门查询结果添加Redis缓存
- 设置合理的缓存过期时间（5-15分钟）
- 实现缓存预热机制

### 3. 查询优化
- 限制返回数据量（分页、时间范围）
- 使用预计算字段存储聚合结果
- 考虑使用物化视图优化复杂查询

---

## 🔧 开发建议

### 1. 数据查询优化
- 利用表的索引字段进行高效查询
- 使用`qa_brand_summary`进行汇总统计，避免实时计算
- 引用URL统计为全局统计，不按品牌筛选
- 合理设计查询语句，减少数据库压力

### 2. 错误处理
- 参数验证：品牌名称不能为空（品牌相关API）
- 时间范围验证：支持预定义的时间范围
- 异常处理：数据库连接错误、查询超时等

### 3. 代码规范
- 遵循RESTful API设计原则
- 使用类型提示提高代码可读性
- 添加充分的注释和文档

---

## 📋 实现状态总结

| API接口 | 实现状态 | 数据表 | 备注 |
|---------|----------|--------|------|
| 品牌总提及率 | ✅ 已完成 | `qa_brand_summary` | 全功能实现 |
| 各平台提及率 | ✅ 已完成 | `qa_brand_summary` | 单品牌多平台对比 |
| 引用URL统计 | ✅ 已完成 | `qa_reference` | 全局URL引用统计 |
| 品牌情感分析 | 🔄 开发中 | `qa_brand_state` | 待实现 |

---

## 📝 更新记录

- **2024-01-15**: 创建API文档
- **2024-01-15**: 添加品牌情感分析和参考链接API
- **2024-01-15**: 更新已实现API状态和数据模型说明
- **2024-01-15**: 完善代码架构和查询函数文档
- **2024-01-15**: 修正文档错误：删除未实现的platform参数和platform_breakdown字段
- **2024-01-15**: 更新引用URL统计API为全局统计，不按品牌筛选
