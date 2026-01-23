# 品牌分析API数据库架构

本目录包含品牌分析API的数据库架构文件和相关文档。

## 📁 文件说明

- **`database_schema.sql`** - 核心业务表结构定义（对话、指标、统计）
- **`schema_tenants_and_users.sql`** - 租户与用户管理表结构
- **`migrations/`** - 数据库迁移脚本（待创建）
- **`seeds/`** - 测试数据种子文件（待创建）

## 🗂️ 核心表结构

### 1. llm_conversations - LLM 对话内容主表
存储从 AI 平台抓取的原始对话内容。

**主要字段：**
- `tenant_key` - 租户唯一标识
- `job_id` - 任务 ID
- `conversation_id` - 对话唯一标识
- `platform` - 平台（deepseek, doubao 等）
- `brand` - 品牌名称
- `category` - 商品大类
- `keyword` - 核心关键词
- `query_content` - 用户提问内容
- `answer_content` - AI 回答内容
- `extracted_at` - 文件原始生成时间

### 2. llm_conversation_references - 对话引用链接表
存储对话中提到的参考链接和元数据。

**主要字段：**
- `url` - 引用链接 URL
- `domain` - 提取的域名
- `site_name` - 站点名称
- `content_type` - 内容类型（news, tech_review 等）

### 3. llm_query_jobs - 用户咨询任务记录表
存储用户提交的任务配置和待查询问题模板。

**主要字段：**
- `category` - 商品大类
- `brand` - 目标品牌
- `competitor` - 竞品品牌 (JSON)
- `keyword` - 核心关键词
- `query_content` - 具体咨询内容
- `query_status` - 生效状态
- `total_runs` - 总执行次数
- `executed_runs` - 已执行次数

### 4. qa_brand_state - 品牌问答状态详情表
记录品牌在每个问答中的具体表现。

**主要字段：**
- `is_mentioned` - 是否提及
- `is_first_mention` - 是否首位提及
- `sentiment_status` - 情感状态
- `brands_found` - 发现的所有品牌 (JSON)

### 5. qa_brand_summary - 品牌汇总统计表
存储按日、按品牌、按平台的统计摘要。

**主要字段：**
- `mention_rate` - 提及率
- `first_mention_rate` - 首位提及率
- `positive_ratio` - 正面情感比例

### 6. qa_reference - 问答引用详情表（分析用）
专门用于分析的引用链接表，包含发稿链接校验。

**主要字段：**
- `is_published_link` - 是否为发稿链接

## 👥 租户与用户管理

- **`tenants`**: 存储租户（企业/客户）基本信息、订阅计划及状态。
- **`users`**: 存储用户信息及登录凭证。
- **`user_tenants`**: 管理用户与租户的多对多关系及角色（admin/member）。
- **`invitation_codes`**: 租户邀请码管理。

## 🔧 数据库初始化

### 创建数据库
```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS geo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 执行建表语句
```bash
# 1. 基础架构（租户与用户）
mysql -u root -p geo < schema_tenants_and_users.sql

# 2. 业务表（对话与指标）
mysql -u root -p geo < database_schema.sql
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