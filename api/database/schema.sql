-- ==========================================================
-- Brand Dashboard Full Database Schema
-- Combined Schema (Auth + Business + Initialization)
-- ==========================================================

-- ---------------------------------------------------------
-- PART 1: Tenants and Users (Auth & Infrastructure)
-- Source: schema_tenants_and_users.sql
-- ---------------------------------------------------------

-- 1. 租户表（tenants）
CREATE TABLE IF NOT EXISTS tenants (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '租户ID',
    tenant_key VARCHAR(255) NOT NULL UNIQUE COMMENT '租户唯一字符串标识，用于路由/API/隔离',
    tenant_name VARCHAR(255) NOT NULL UNIQUE COMMENT '租户显示名称',
    subdomain VARCHAR(100) UNIQUE COMMENT '租户子域名',
    company_legal_name VARCHAR(255) COMMENT '企业法定名称',
    company_type VARCHAR(100) COMMENT '企业类型',
    registration_no VARCHAR(100) COMMENT '企业注册号/统一社会信用代码',
    industry VARCHAR(100) COMMENT '行业',
    contact_name VARCHAR(100) COMMENT '联系人姓名',
    contact_email VARCHAR(255) COMMENT '联系人邮箱',
    contact_phone VARCHAR(50) COMMENT '联系人电话',
    status ENUM('active', 'inactive', 'suspended') NOT NULL DEFAULT 'active' COMMENT '租户状态',
    plan_type VARCHAR(50) COMMENT '订阅计划类型',
    max_users INT DEFAULT 10 COMMENT '最大用户数',
    billing_cycle VARCHAR(50) COMMENT '计费周期（monthly/yearly）',
    contract_start_date DATE COMMENT '合同开始日期',
    contract_end_date DATE COMMENT '合同结束日期',
    created_by VARCHAR(36) COMMENT '创建人user_key（平台操作员）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_tenant_key (tenant_key),
    INDEX idx_subdomain (subdomain)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 用户表（users）
CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    user_key VARCHAR(36) NOT NULL UNIQUE COMMENT '用户全局唯一字符串ID（如 UUID/ULID）',
    email VARCHAR(255) NOT NULL UNIQUE COMMENT '登录邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    first_name VARCHAR(100) COMMENT '名',
    last_name VARCHAR(100) COMMENT '姓',
    phone_number VARCHAR(50) COMMENT '手机号',
    is_verified BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已验证',
    status ENUM('pending_activation', 'active', 'inactive', 'suspended') NOT NULL DEFAULT 'active' COMMENT '用户状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 用户-租户关系表（核心多租户关联）
CREATE TABLE IF NOT EXISTS user_tenants (
    user_id BIGINT NOT NULL COMMENT '关联 users.id',
    tenant_id BIGINT NOT NULL COMMENT '关联 tenants.id',
    role VARCHAR(50) NOT NULL DEFAULT 'member' COMMENT '租户内角色：admin, member, viewer 等',
    status ENUM('active', 'inactive') NOT NULL DEFAULT 'active' COMMENT '在该租户下的状态',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    PRIMARY KEY (user_id, tenant_id),
    INDEX idx_tenant_user (tenant_id, user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 租户配置表（tenant_configs）
CREATE TABLE IF NOT EXISTS tenant_configs (
    tenant_id BIGINT PRIMARY KEY COMMENT '关联 tenants.id',
    theme_color VARCHAR(20) DEFAULT '#3498db' COMMENT '主题色',
    logo_url VARCHAR(512) COMMENT 'Logo 地址',
    custom_domain VARCHAR(255) COMMENT '自定义域名，如 app.acmecorp.com',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 邀请码表
CREATE TABLE IF NOT EXISTS invitation_codes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '邀请码ID',
    tenant_id BIGINT NOT NULL COMMENT '所属租户ID',
    code VARCHAR(20) NOT NULL UNIQUE COMMENT '邀请码（6位）',
    
    status ENUM('active', 'inactive', 'expired') NOT NULL DEFAULT 'active' COMMENT '邀请码状态',
    max_uses INT NULL COMMENT '最大使用次数（NULL=无限制）',
    usage_count INT DEFAULT 0 COMMENT '已使用次数',
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    
    created_by BIGINT COMMENT '创建人user_id',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_tenant_id (tenant_id),
    INDEX idx_code (code),
    INDEX idx_status (status),
    
    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ---------------------------------------------------------
-- PART 2: Business Logic (Conversations, Jobs, Analytics)
-- Source: database_schema.sql
-- ---------------------------------------------------------

-- 6. LLM 对话内容主表
CREATE TABLE IF NOT EXISTS `llm_conversations` (
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
  `generated_date` date DEFAULT NULL COMMENT '对话生成的日期（YYYY-MM-DD），用于按日期分析计算',
  `extracted_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '文件生成时间（来自文件的Generated at），原始文件创建时间，保持数据时序一致性',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '数据库记录创建时间，数据入库时间，用于数据管理',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间，记录最后修改时间，支持数据审计',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_conversation` (`tenant_key`,`conversation_id`),
  KEY `idx_tenant_user_job` (`tenant_key`,`job_id`),
  KEY `idx_tenant_generated_date` (`tenant_key`,`generated_date`),
  KEY `idx_platform` (`platform`),
  KEY `idx_brand` (`brand`),
  KEY `idx_category` (`category`),
  KEY `idx_keyword` (`keyword`),
  CONSTRAINT `llm_conversations_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储LLM对话内容的主表';

-- 7. 对话引用链接关联表
CREATE TABLE IF NOT EXISTS `llm_conversation_references` (
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
  `generated_date` date DEFAULT NULL COMMENT '对话生成的日期（YYYY-MM-DD），用于按日期分析计算',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间，记录引用链接入库时间，用于数据管理',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间，记录引用信息最后修改时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_conversation_url` (`tenant_key`,`conversation_id`,`url`(191)),
  KEY `idx_tenant_job` (`tenant_key`,`job_id`),
  KEY `idx_tenant_generated_date` (`tenant_key`,`generated_date`),
  KEY `idx_platform` (`platform`),
  KEY `idx_brand` (`brand`),
  KEY `idx_category` (`category`),
  KEY `idx_keyword` (`keyword`),
  KEY `idx_domain` (`domain`),
  KEY `idx_content_type` (`content_type`),
  CONSTRAINT `llm_conversation_references_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE,
  CONSTRAINT `llm_conversation_references_ibfk_conversation` FOREIGN KEY (`tenant_key`,`conversation_id`) REFERENCES `llm_conversations` (`tenant_key`,`conversation_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='存储对话中引用链接的关联表';

-- 8. 执行器信息表
CREATE TABLE IF NOT EXISTS `executors` (
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

-- 9. 用户监测任务记录表
CREATE TABLE IF NOT EXISTS `llm_query_jobs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '任务记录唯一主键ID，自增',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `job_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '作业ID',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品大类（比如“汽车”）',
  `brand` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '目标品牌（如“蔚来”，可为NULL表示未指定具体品牌）',
  `competitor` json DEFAULT NULL COMMENT '竞品品牌（如“小鹏”“理想”，可为NULL表示未指定竞品）',
  `keyword` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '核心关键词（如“换电补能”“高端豪华”）',
  `query_content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户具体咨询问题内容',
  `query_status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '问题生效状态：0: 未生效 (等待开始或手动禁用), 1: 生效中 (执行器正在抓取), 2: 已完成 (已达总执行次数), 3: 已失效 (超过生效结束时间)',
  `executor_id` varchar(128) DEFAULT NULL COMMENT '执行器唯一标识',
  `total_runs` int(11) NOT NULL DEFAULT '15' COMMENT '总执行次数',
  `executed_runs` int(11) NOT NULL DEFAULT '0' COMMENT '已发生过的 attempt 数（成功 + 失败）',
  `last_executed_date` date DEFAULT NULL COMMENT '最近一次执行日期，配合 <= 逻辑支持单日多次领取直至跑满 total_runs',
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

-- 10. 每日品牌情感和提及统计汇总表
CREATE TABLE IF NOT EXISTS `qa_brand_summary` ( 
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT 'Auto-increment ID', 
  `tenant_key` VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `job_id` VARCHAR(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '作业ID',
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

-- 11. 品牌在问答中的具体状态记录表
CREATE TABLE IF NOT EXISTS `qa_brand_state` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Auto-increment primary key',
  `job_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务唯一标识（llm_query_jobs.job_id）',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `date` date NOT NULL COMMENT 'Date of the record',
  `conversation_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对话唯一标识，通常是文件名中的唯一标识符，确保每个对话的唯一性',
  `brand` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Brand name mentioned',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品大类',
  `platform` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Platform where the question was posted (e.g., Qwen, Deepseek, etc.)',
  `keyword` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '生成question的关键词，用户提交job时系统会根据关键词生成question',
  `is_mentioned` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Whether the brand is mentioned in the answer (0 = no, 1 = yes)',
  `is_first_mentioned` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Whether the brand is the first mentioned in the answer',
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

-- 12. 问答引用详情表
CREATE TABLE IF NOT EXISTS `qa_reference` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，数据库自增，唯一标识每条引用记录',
  `job_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务唯一标识（llm_query_jobs.job_id）',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `date` date NOT NULL COMMENT 'Date of the record',
  `conversation_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对话ID，标识单次AI对话的唯一ID，一个conversation_id对应一条对话的引用链接',
  `platform` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '平台名称',
  `brand` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '品牌，例如：阿里巴巴、腾讯、字节跳动等',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品大类',
  `keyword` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '生成question的关键词，用户提交job时系统会根据关键词生成question',
  `query_content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户查询内容，完整的用户提问内容',
  `url` varchar(1024) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '引用链接URL，完整的引用链接地址，用于追溯信息来源',
  `is_published_link` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否为发稿链接：0-否（默认），1-是；标识该URL是否为自媒体发布的稿件链接，若AI平台读取的链接与发稿链接一致则标记为1',
  `domain` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '域名，从URL中提取的域名，如news.cn, zol.com.cn，用于域名分析和统计',
  `content_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '内容类型：news, tech_review, gov_report等，标识链接内容的性质 and 可信度',
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


-- ---------------------------------------------------------
-- PART 3: Initialization & Events
-- Source: schema_init.sql
-- ---------------------------------------------------------

-- 开启事件调度器（可能需要 SUPER 权限）
SET GLOBAL event_scheduler = ON;

-- 每日执行跨日重置（硬性满足有效期范围）
DROP EVENT IF EXISTS ev_reset_query_jobs_daily;
CREATE EVENT ev_reset_query_jobs_daily
ON SCHEDULE EVERY 1 DAY
STARTS TIMESTAMP(CURDATE() + INTERVAL 1 DAY)
DO
  UPDATE llm_query_jobs
  SET executed_runs = 0
  WHERE query_status = 1
    AND is_deleted = 0
    AND executed_runs = total_runs
    AND last_executed_date < CURDATE()
    AND NOW() >= effective_from
    AND (effective_to IS NULL OR NOW() <= effective_to);

-- 索引补充（若表中未包含）
-- CREATE INDEX idx_jobs_fetch ON llm_query_jobs (executor_id, query_status, is_deleted, executed_runs, id);
-- CREATE INDEX idx_jobs_reset ON llm_query_jobs (executor_id, query_status, is_deleted, last_executed_date, executed_runs);

-- ==========================================================
-- Full Schema Creation Completed
-- ==========================================================
