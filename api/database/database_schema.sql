-- MySQL Database Schema for LLM Conversation Storage
-- 用于存储LLM对话和引用链接的数据库表结构
-- 
-- 数据库设计说明：
-- 本数据库用于存储从AI平台抓取的QA对话内容，支持多平台、多任务、多对话的管理
-- 采用两表设计：主表存储对话内容，关联表存储引用链接

CREATE TABLE `llm_conversations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，数据库自增，唯一标识每条对话记录',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）', 
  `job_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务ID，标识生成QA对抓取AI平台内容的任务，一个job_id对应一批对话',
  `conversation_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对话唯一标识，通常是文件名中的唯一标识符，确保每个对话的唯一性',
  `platform` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台名称：deepseek, doubao, qianwen, kimi, yuanbao',
  `brand` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品牌，例如：阿里巴巴、腾讯、字节跳动等',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品大类',
  `keyword` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '生成question的关键词，用户提交job时系统会根据关键词生成question',
  `query_content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户查询内容，完整的用户提问内容',
  `answer_content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'AI回答内容，AI生成的完整回答',
  `extracted_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '文件生成时间（来自文件的Generated at），原始文件创建时间，保持数据时序一致性',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '数据库记录创建时间，数据入库时间，用于数据管理',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间，记录最后修改时间，支持数据审计',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_conversation` (`tenant_key`,`conversation_id`),
  KEY `idx_tenant_user_job` (`tenant_key`,`job_id`),
  KEY `idx_platform` (`platform`),
  KEY `idx_brand` (`brand`),
  KEY `idx_category` (`category`),
  KEY `idx_keyword` (`keyword`),
  CONSTRAINT `llm_conversations_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储LLM对话内容的主表';

CREATE TABLE `llm_conversation_references` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，数据库自增，唯一标识每条引用记录',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `job_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务ID，标识生成QA对抓取AI平台内容的任务，一个job_id对应一批对话',
  `conversation_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对话ID（外键），关联到llm_conversations表的conversation_id，建立一对多关系',
  `platform` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台名称：deepseek, doubao, qianwen, kimi, yuanbao',
  `brand` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品牌，例如：阿里巴巴、腾讯、字节跳动等',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品大类',
  `keyword` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '生成question的关键词，用户提交job时系统会根据关键词生成question',
  `query_content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户查询内容，完整的用户提问内容',
  `url` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '引用链接URL，完整的引用链接地址，用于追溯信息来源',
  `domain` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '域名，从URL中提取的域名，如news.cn, zol.com.cn，用于域名分析和统计',
  `cite_index` int(10) unsigned DEFAULT NULL COMMENT '引用序号，表示该引用在当前对话中出现的顺序（从1开始）',
  `site_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '站点名称，从引用页面提取的网站标题或名称，用于展示',
  `content_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '内容类型：news, tech_review, gov_report等，标识链接内容的性质和可信度',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间，记录引用链接入库时间，用于数据管理',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间，记录引用信息最后修改时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_conversation_url` (`tenant_key`,`conversation_id`,`url`(255)),
  KEY `idx_tenant_job` (`tenant_key`,`job_id`),
  KEY `idx_platform` (`platform`),
  KEY `idx_brand` (`brand`),
  KEY `idx_category` (`category`),
  KEY `idx_keyword` (`keyword`),
  KEY `idx_domain` (`domain`),
  KEY `idx_content_type` (`content_type`),
  CONSTRAINT `llm_conversation_references_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE,
  CONSTRAINT `llm_conversation_references_ibfk_conversation` FOREIGN KEY (`tenant_key`,`conversation_id`) REFERENCES `llm_conversations` (`tenant_key`,`conversation_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储对话中引用链接的关联表';

-- 执行器信息表
CREATE TABLE `executors` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '执行器内部主键ID，自增',
  `executor_id` varchar(128) NOT NULL COMMENT '执行器唯一字符串标识',
  `name` varchar(255) NOT NULL COMMENT '执行器名称',
  `type` varchar(64) DEFAULT NULL COMMENT '执行器类型',
  `status` varchar(20) DEFAULT 'active' COMMENT '执行器状态',
  `ip_address` varchar(45) NOT NULL COMMENT '预设的执行器IP地址，用于注册验证',
  `api_key` varchar(255) DEFAULT NULL COMMENT '执行器身份验证密钥',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_executor_id` (`executor_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='执行器信息表';

CREATE TABLE `llm_query_jobs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '任务记录唯一主键ID，自增',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `job_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '作业ID',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品大类（比如“汽车”）',
  `brand` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标品牌（如“蔚来”，可为NULL表示未指定具体品牌）',
  `competitor` json DEFAULT NULL COMMENT '竞品品牌（如“小鹏”“理想”，可为NULL表示未指定竞品）',
  `keyword` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '核心关键词（如“换电补能”“高端豪华”）',
  `query_content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户具体咨询问题内容',
  `query_status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '问题生效状态：0-失效，1-生效（关键字段，标记问题是否处于使用状态）',
  `executor_id` varchar(128) DEFAULT NULL COMMENT '执行器唯一标识',
  `total_runs` int(11) NOT NULL DEFAULT '15' COMMENT '总执行次数',
  `executed_runs` int(11) NOT NULL DEFAULT '0' COMMENT '已发生过的 attempt 数（成功 + 失败）',
  `last_executed_date` date DEFAULT NULL COMMENT '最近一次执行日期（仅记录年月日）',
  `effective_from` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生效开始时间（所属JOB生命周期起点）',
  `effective_to` timestamp NULL DEFAULT NULL COMMENT '生效结束时间（所属JOB生命周期终点，NULL表示未结束）',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '任务记录创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录最后更新时间，自动同步修改时间',
  `is_deleted` tinyint(4) NOT NULL DEFAULT '0' COMMENT '软删除标识：0-未删除，1-已删除',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_job` (`tenant_key`,`job_id`),
  KEY `idx_brand` (`brand`),
  KEY `idx_category` (`category`),
  KEY `idx_keyword` (`keyword`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_executor_fetch_v2` (`executor_id`, `query_status`, `is_deleted`, `executed_runs`, `id`),
  KEY `idx_jobs_daily_reset` (`query_status`, `is_deleted`, `last_executed_date`, `executed_runs`),
  KEY `idx_executor_fetch_date` (`executor_id`, `query_status`, `is_deleted`, `last_executed_date`, `id`),
  CONSTRAINT `llm_query_jobs_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE,
  CONSTRAINT `fk_tasks_executor` FOREIGN KEY (`executor_id`) REFERENCES `executors` (`executor_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户监测任务记录表';

-- 
-- 品牌分析相关表结构
-- 

-- 每日品牌情感和提及统计汇总表
CREATE TABLE `qa_brand_summary` ( 
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'Auto-increment ID', 
  `tenant_key` VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `date` DATE NOT NULL COMMENT 'Summary date, means analysis_date', 
  `brand` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Brand name', 
  `product` VARCHAR(255) COLLATE utf8mb4_unicode_ci COMMENT 'Product name (optional)', 
  `platform` VARCHAR(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Platform (e.g., Qwen, Deepseek)', 
  `question_count` INT NOT NULL COMMENT 'Total number of questions, means total_files', 
  `mention_count` INT NOT NULL COMMENT 'Total mentions of the brand, means mentioned_files', 
  `first_mention_count` INT NOT NULL COMMENT 'Number of first-time mentions, means first_mention_files', 
  `mention_rate` DECIMAL(5,2) NOT NULL COMMENT 'Mention rate (e.g., 0.85 for 85%)', 
  `first_mention_rate` DECIMAL(5,2) NOT NULL COMMENT 'First mention rate (e.g., 0.30 for 30%)', 
  `positive_count` INT NOT NULL COMMENT 'Number of positive sentiment questions', 
  `negative_count` INT NOT NULL COMMENT 'Number of negative sentiment questions', 
  `positive_ratio` DECIMAL(5,2) NOT NULL COMMENT 'Positive sentiment ratio (e.g., 0.70 for 70%)', 
  `negative_ratio` DECIMAL(5,2) NOT NULL COMMENT 'Negative sentiment ratio (e.g., 0.25 for 25%)', 
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  KEY `idx_tenant_date_brand` (`tenant_key`, `date`, `brand`), 
  KEY `idx_tenant_platform` (`tenant_key`, `platform`), 
  KEY `idx_tenant_brand_product` (`tenant_key`, `brand`, `product`),
  CONSTRAINT `qa_brand_summary_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Daily brand sentiment and mention statistics summary'; 

-- 品牌在问答中的具体状态记录表
CREATE TABLE `qa_brand_state` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Auto-increment primary key',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `date` date NOT NULL COMMENT 'Date of the record',
  `conversation_id` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对话唯一标识，通常是文件名中的唯一标识符，确保每个对话的唯一性',
  `brand` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Brand name mentioned',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品大类',
  `platform` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Platform where the question was posted (e.g., Qwen, Deepseek, etc.)',
  `keyword` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '生成question的关键词，用户提交job时系统会根据关键词生成question',
  `is_mentioned` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Whether the brand is mentioned in the answer (0 = no, 1 = yes)',
  `is_first_mention` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Whether the brand is the first mentioned in the answer',
  `sentiment_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Sentiment/emotion status (e.g., positive, negative, neutral)',
  `brands_found` json DEFAULT NULL COMMENT 'All brands found in the text (e.g., ["海尔 (Haier)", ...])',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_tenant_date` (`tenant_key`,`date`),
  KEY `idx_tenant_brand` (`tenant_key`,`brand`),
  KEY `idx_tenant_platform` (`tenant_key`,`platform`),
  KEY `idx_tenant_sentiment_status` (`tenant_key`,`sentiment_status`),
  KEY `idx_tenant_conversation_id` (`tenant_key`,`conversation_id`),
  CONSTRAINT `qa_brand_state_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Records of brand status in Q&A'; 

-- 问答引用详情表
CREATE TABLE `qa_reference` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，数据库自增，唯一标识每条引用记录',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `date` date NOT NULL COMMENT 'Date of the record',
  `conversation_id` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对话ID，标识单次AI对话的唯一ID，一个conversation_id对应一条对话的引用链接',
  `platform` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台名称',
  `brand` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品牌，例如：阿里巴巴、腾讯、字节跳动等',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品大类',
  `keyword` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '生成question的关键词，用户提交job时系统会根据关键词生成question',
  `query_content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户查询内容，完整的用户提问内容',
  `url` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '引用链接URL，完整的引用链接地址，用于追溯信息来源',
  `is_published_link` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否为发稿链接：0-否（默认），1-是；标识该URL是否为自媒体发布的稿件链接，若AI平台读取的链接与发稿链接一致则标记为1',
  `domain` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '域名，从URL中提取的域名，如news.cn, zol.com.cn，用于域名分析和统计',
  `content_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '内容类型：news, tech_review, gov_report等，标识链接内容的性质和可信度',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间，记录引用链接入库时间，用于数据管理',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间，记录引用信息最后修改时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_conversation_url` (`tenant_key`,`conversation_id`,`url`(191)),
  KEY `idx_platform` (`platform`),
  KEY `idx_brand` (`brand`),
  KEY `idx_category` (`category`),
  KEY `idx_keyword` (`keyword`),
  KEY `idx_domain` (`domain`),
  KEY `idx_content_type` (`content_type`),
  KEY `idx_is_published_link` (`is_published_link`),
  CONSTRAINT `qa_reference_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='存储对话中引用链接的关联表';

-- 数据库设计总结：
-- 1. 基础对话存储：llm_conversations 和 llm_conversation_references 存储原始抓取对话及引用
-- 2. 品牌分析统计：qa_brand_summary 存储每日品牌提及和情感分析统计
-- 3. 品牌状态详情：qa_brand_state 存储每个问题中品牌的具体表现（提及、首位、情感）
-- 4. 引用详情：qa_reference 存储问题相关的引用链接详情
-- 5. 时间字段：extracted_at使用文件原始时间，created_at/updated_at使用数据库时间
-- 6. 索引优化：针对常用查询场景设计，支持用户、任务、平台、关键词、品牌、日期等多维度查询
-- 7. 字符集：使用utf8mb4支持完整的Unicode字符
