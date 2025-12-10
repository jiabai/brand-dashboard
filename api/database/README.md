# 品牌分析API数据库架构

本目录包含品牌分析API的数据库架构文件和相关文档。

## 📁 文件说明

- **`schema.sql`** - 核心数据库表结构定义
- **`migrations/`** - 数据库迁移脚本（待创建）
- **`seeds/`** - 测试数据种子文件（待创建）

## 🗂️ 核心表结构

### 1. qa_brand_state - Q&A品牌状态记录表
记录品牌在问答平台上的提及情况和情感分析结果。

**主要字段：**
- `id` - 自增主键
- `date` - 记录日期
- `question_id` - 问题唯一标识
- `brand` - 品牌名称
- `product` - 产品名称（可选）
- `platform` - 问答平台（如Qwen、Deepseek等）
- `question` - 用户原始问题
- `answer` - 提供的答案
- `is_mentioned` - 品牌是否在答案中被提及
- `is_first_mention` - 品牌是否为答案中首次提及
- `sentiment_status` - 情感状态（positive/negative/neutral）
- `brands_found` - JSON格式存储的所有发现品牌

**索引：**
- `idx_date` - 日期索引
- `idx_question_id` - 问题ID索引
- `idx_brand` - 品牌索引
- `idx_platform` - 平台索引
- `idx_sentiment_status` - 情感状态索引

### 2. qa_brand_summary - Q&A品牌汇总统计表
存储品牌情感和提及统计的每日摘要数据。

**主要字段：**
- `id` - 自增主键
- `date` - 汇总日期
- `brand` - 品牌名称
- `product` - 产品名称（可选）
- `platform` - 平台名称
- `question_count` - 问题总数
- `mention_count` - 品牌提及总数
- `first_mention_count` - 首次提及数量
- `mention_rate` - 提及率（百分比）
- `first_mention_rate` - 首次提及率
- `positive_count` - 正面情感问题数
- `negative_count` - 负面情感问题数
- `positive_ratio` - 正面情感比例
- `negative_ratio` - 负面情感比例

**索引：**
- `idx_date_brand` - 日期+品牌组合索引
- `idx_platform` - 平台索引
- `idx_brand_product` - 品牌+产品组合索引

### 3. qa_reference - Q&A参考链接表
存储问答中的参考链接和相关元数据。

**主要字段：**
- `id` - 自增主键
- `date` - 问题日期
- `question_id` - 问题唯一标识
- `brand` - 品牌名称
- `product` - 产品名称或描述
- `platform` - 平台（如淘宝、京东等）
- `answer_reference_url` - 答案中引用的URL
- `search_url` - 用于获取问题的原始搜索URL

**索引：**
- `idx_date` - 日期索引
- `idx_question_id` - 问题ID索引
- `idx_brand` - 品牌索引
- `idx_platform` - 平台索引

## 🔧 数据库初始化

### 创建数据库
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS geo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 执行建表语句
```bash
mysql -u root -p geo < schema.sql
```

### 验证表结构
```bash
mysql -u root -p geo -e "SHOW TABLES;"
```

## 📊 使用场景

1. **qa_brand_state** - 适用于实时记录和分析Q&A平台上的品牌提及情况
2. **qa_brand_summary** - 适用于生成品牌分析报表和趋势分析
3. **qa_reference** - 适用于跟踪答案中的参考链接来源和商品链接分析

## ⚙️ 技术规范

- **字符集**: `utf8mb4` - 支持完整的Unicode字符，包括emoji
- **存储引擎**: `InnoDB` - 支持事务和外键约束
- **时间格式**: 使用`date`类型存储日期信息
- **JSON字段**: 使用MySQL原生JSON类型存储结构化数据
- **索引策略**: 基于查询模式优化，支持多维度数据分析

## 🚀 性能优化建议

1. **分区策略**: 考虑按日期对大数据表进行分区
2. **复合索引**: 根据实际查询模式调整索引组合
3. **数据归档**: 定期归档历史数据以保持查询性能
4. **缓存策略**: 对汇总数据实施合理的缓存机制