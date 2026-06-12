-- MySQL Database Schema for LLM Business Logic (Sub-schema)
-- 用于存储LLM对话和指标的业务表结构
-- 
-- ⚠️ 注意：本文件是业务表子集，依赖 tenants 表（定义在 schema_auth.sql 中）。
-- 建议直接执行 schema.sql 以获得完整的数据库结构。
-- 
-- 数据库设计说明：
-- 本数据库用于存储从AI平台抓取的QA对话内容，支持多平台、多任务、多对话的管理
-- 采用两表设计：主表存储对话内容，关联表存储引用链接

CREATE TABLE IF NOT EXISTS `monitoring_projects` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Tenant key',
  `project_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable project id',
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Project name',
  `industry` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Industry',
  `category` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Category',
  `status` enum('draft','active','paused','archived') NOT NULL DEFAULT 'draft' COMMENT 'Project status',
  `created_by` bigint(20) DEFAULT NULL COMMENT 'Creator user id',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_project` (`tenant_key`,`project_id`),
  KEY `idx_monitoring_projects_tenant_status` (`tenant_key`,`status`),
  KEY `idx_monitoring_projects_tenant_category` (`tenant_key`,`category`),
  CONSTRAINT `monitoring_projects_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Monitoring projects';

CREATE TABLE IF NOT EXISTS `project_brands` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Tenant key',
  `project_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable project id',
  `brand_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable brand id',
  `brand_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Display brand name',
  `role` enum('target','competitor','watch_only') NOT NULL DEFAULT 'competitor' COMMENT 'Brand role',
  `aliases` json DEFAULT NULL COMMENT 'Brand aliases',
  `status` enum('active','inactive') NOT NULL DEFAULT 'active' COMMENT 'Brand config status',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_project_brand_role` (`tenant_key`,`project_id`,`brand_id`,`role`),
  KEY `idx_project_brands_project_role` (`tenant_key`,`project_id`,`role`),
  KEY `idx_project_brands_brand` (`tenant_key`,`brand_id`),
  CONSTRAINT `project_brands_ibfk_project` FOREIGN KEY (`tenant_key`,`project_id`) REFERENCES `monitoring_projects` (`tenant_key`,`project_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Project brand configuration';

CREATE TABLE IF NOT EXISTS `prompt_sets` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Tenant key',
  `project_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable project id',
  `prompt_set_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable prompt set id',
  `version` int(11) NOT NULL DEFAULT '1' COMMENT 'Prompt set version',
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Prompt set name',
  `status` enum('draft','active','archived') NOT NULL DEFAULT 'draft' COMMENT 'Prompt set status',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_prompt_set` (`tenant_key`,`prompt_set_id`),
  UNIQUE KEY `uk_tenant_project_prompt_version` (`tenant_key`,`project_id`,`version`),
  KEY `idx_prompt_sets_project_status` (`tenant_key`,`project_id`,`status`),
  CONSTRAINT `prompt_sets_ibfk_project` FOREIGN KEY (`tenant_key`,`project_id`) REFERENCES `monitoring_projects` (`tenant_key`,`project_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Project prompt sets';

CREATE TABLE IF NOT EXISTS `prompt_items` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Tenant key',
  `prompt_set_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable prompt set id',
  `prompt_item_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable prompt item id',
  `keyword` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Prompt keyword',
  `query_content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Prompt content',
  `status` enum('active','inactive') NOT NULL DEFAULT 'active' COMMENT 'Prompt item status',
  `sort_order` int(11) NOT NULL DEFAULT '0' COMMENT 'Sort order',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_prompt_item` (`tenant_key`,`prompt_set_id`,`prompt_item_id`),
  KEY `idx_prompt_items_prompt_set_status` (`tenant_key`,`prompt_set_id`,`status`),
  KEY `idx_prompt_items_keyword` (`tenant_key`,`keyword`),
  CONSTRAINT `prompt_items_ibfk_prompt_set` FOREIGN KEY (`tenant_key`,`prompt_set_id`) REFERENCES `prompt_sets` (`tenant_key`,`prompt_set_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Prompt items';

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

CREATE TABLE IF NOT EXISTS `collection_jobs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Tenant key',
  `collection_job_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable collection job id',
  `project_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Monitoring project id',
  `prompt_set_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Prompt set id used by this run',
  `source_job_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Legacy llm_query_jobs job_id during compatibility period',
  `status` enum('pending','running','succeeded','failed','expired','cancelled') NOT NULL DEFAULT 'pending' COMMENT 'Collection job status',
  `window_start` timestamp NULL DEFAULT NULL COMMENT 'Collection window start',
  `window_end` timestamp NULL DEFAULT NULL COMMENT 'Collection window end',
  `expected_task_count` int(11) NOT NULL DEFAULT '0' COMMENT 'Expected task count',
  `succeeded_task_count` int(11) NOT NULL DEFAULT '0' COMMENT 'Succeeded task count',
  `failed_task_count` int(11) NOT NULL DEFAULT '0' COMMENT 'Failed task count',
  `created_by` bigint(20) DEFAULT NULL COMMENT 'Creator user id',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_collection_job` (`tenant_key`,`collection_job_id`),
  KEY `idx_collection_jobs_tenant_project_status` (`tenant_key`,`project_id`,`status`),
  KEY `idx_collection_jobs_prompt_set` (`tenant_key`,`prompt_set_id`),
  KEY `idx_collection_jobs_source_job` (`tenant_key`,`source_job_id`),
  CONSTRAINT `collection_jobs_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE,
  CONSTRAINT `collection_jobs_ibfk_project` FOREIGN KEY (`tenant_key`,`project_id`) REFERENCES `monitoring_projects` (`tenant_key`,`project_id`),
  CONSTRAINT `collection_jobs_ibfk_prompt_set` FOREIGN KEY (`tenant_key`,`prompt_set_id`) REFERENCES `prompt_sets` (`tenant_key`,`prompt_set_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Collection job batches';

CREATE TABLE IF NOT EXISTS `collection_tasks` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Tenant key',
  `collection_task_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable collection task id',
  `collection_job_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Collection job id',
  `project_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Monitoring project id',
  `prompt_set_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Prompt set id',
  `prompt_item_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Prompt item id',
  `platform` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'AI platform',
  `query_content` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Prompt content',
  `run_index` int(11) NOT NULL DEFAULT '1' COMMENT 'Run index inside the collection job',
  `status` enum('pending','reserved','running','succeeded','failed','expired','cancelled') NOT NULL DEFAULT 'pending' COMMENT 'Collection task status',
  `lease_owner` varchar(128) DEFAULT NULL COMMENT 'Executor holding the current lease',
  `lease_until` timestamp NULL DEFAULT NULL COMMENT 'Lease expiry time',
  `reserved_at` timestamp NULL DEFAULT NULL COMMENT 'Reserved time',
  `started_at` timestamp NULL DEFAULT NULL COMMENT 'Started time',
  `finished_at` timestamp NULL DEFAULT NULL COMMENT 'Finished time',
  `attempt_count` int(11) NOT NULL DEFAULT '0' COMMENT 'Attempt count',
  `max_attempts` int(11) NOT NULL DEFAULT '3' COMMENT 'Max attempts before terminal failure',
  `last_error_code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Last error code',
  `last_error_message` text COLLATE utf8mb4_unicode_ci COMMENT 'Last error message',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_collection_task` (`tenant_key`,`collection_task_id`),
  KEY `idx_collection_tasks_fetch` (`tenant_key`,`status`,`lease_until`,`id`),
  KEY `idx_collection_tasks_job_status` (`tenant_key`,`collection_job_id`,`status`),
  KEY `idx_collection_tasks_project` (`tenant_key`,`project_id`,`status`),
  KEY `idx_collection_tasks_prompt` (`tenant_key`,`prompt_set_id`,`prompt_item_id`),
  KEY `idx_collection_tasks_lease_owner` (`lease_owner`,`status`,`tenant_key`),
  CONSTRAINT `collection_tasks_ibfk_job` FOREIGN KEY (`tenant_key`,`collection_job_id`) REFERENCES `collection_jobs` (`tenant_key`,`collection_job_id`) ON DELETE CASCADE,
  CONSTRAINT `collection_tasks_ibfk_project` FOREIGN KEY (`tenant_key`,`project_id`) REFERENCES `monitoring_projects` (`tenant_key`,`project_id`),
  CONSTRAINT `collection_tasks_ibfk_prompt_item` FOREIGN KEY (`tenant_key`,`prompt_set_id`,`prompt_item_id`) REFERENCES `prompt_items` (`tenant_key`,`prompt_set_id`,`prompt_item_id`),
  CONSTRAINT `collection_tasks_ibfk_executor` FOREIGN KEY (`lease_owner`) REFERENCES `executors` (`executor_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Collection tasks';

CREATE TABLE IF NOT EXISTS `collection_attempts` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Tenant key',
  `attempt_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable attempt id',
  `collection_task_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Collection task id',
  `executor_id` varchar(128) DEFAULT NULL COMMENT 'Executor id',
  `status` enum('running','succeeded','failed','timeout','cancelled') NOT NULL DEFAULT 'running' COMMENT 'Attempt status',
  `started_at` timestamp NULL DEFAULT NULL COMMENT 'Started time',
  `finished_at` timestamp NULL DEFAULT NULL COMMENT 'Finished time',
  `error_code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Error code',
  `error_message` text COLLATE utf8mb4_unicode_ci COMMENT 'Error message',
  `raw_response_id` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Raw response id or external artifact id',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_collection_attempt` (`tenant_key`,`attempt_id`),
  KEY `idx_collection_attempts_task` (`tenant_key`,`collection_task_id`),
  KEY `idx_collection_attempts_executor_status` (`tenant_key`,`executor_id`,`status`),
  KEY `idx_collection_attempts_executor_fk` (`executor_id`),
  CONSTRAINT `collection_attempts_ibfk_task` FOREIGN KEY (`tenant_key`,`collection_task_id`) REFERENCES `collection_tasks` (`tenant_key`,`collection_task_id`) ON DELETE CASCADE,
  CONSTRAINT `collection_attempts_ibfk_executor` FOREIGN KEY (`executor_id`) REFERENCES `executors` (`executor_id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Collection execution attempts';

-- Analysis run lifecycle model
CREATE TABLE IF NOT EXISTS `analysis_runs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Tenant key',
  `analysis_run_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable analysis run id',
  `project_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Monitoring project id',
  `collection_job_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Source collection job id',
  `status` enum('pending','running','succeeded','failed','stale') NOT NULL DEFAULT 'pending' COMMENT 'Analysis run status',
  `plugin_versions` json DEFAULT NULL COMMENT 'Analysis plugin versions',
  `model_config_hash` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Model/config hash for reproducibility',
  `input_watermark` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Input data watermark',
  `started_at` timestamp NULL DEFAULT NULL COMMENT 'Started time',
  `finished_at` timestamp NULL DEFAULT NULL COMMENT 'Finished time',
  `stale_at` timestamp NULL DEFAULT NULL COMMENT 'Time when upstream data or config made this run stale',
  `error_code` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Failure error code',
  `error_message` text COLLATE utf8mb4_unicode_ci COMMENT 'Failure or stale reason',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_analysis_run` (`tenant_key`,`analysis_run_id`),
  KEY `idx_analysis_runs_tenant_project_status` (`tenant_key`,`project_id`,`status`),
  KEY `idx_analysis_runs_collection_job` (`tenant_key`,`collection_job_id`),
  KEY `idx_analysis_runs_status_updated` (`tenant_key`,`status`,`updated_at`),
  CONSTRAINT `analysis_runs_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE,
  CONSTRAINT `analysis_runs_ibfk_project` FOREIGN KEY (`tenant_key`,`project_id`) REFERENCES `monitoring_projects` (`tenant_key`,`project_id`),
  CONSTRAINT `analysis_runs_ibfk_collection_job` FOREIGN KEY (`tenant_key`,`collection_job_id`) REFERENCES `collection_jobs` (`tenant_key`,`collection_job_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Analysis run lifecycle records';

CREATE TABLE `llm_query_jobs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '任务记录唯一主键ID，自增',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `job_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '作业ID',
  `project_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '关联监测项目ID，兼容期可为空',
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
  KEY `idx_lqj_project` (`tenant_key`,`project_id`),
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

-- 品牌在问答中的具体状态记录表
CREATE TABLE `qa_brand_state` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Auto-increment primary key',
  `job_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务唯一标识（llm_query_jobs.job_id）',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `analysis_run_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '生成该事实的分析运行ID',
  `date` date NOT NULL COMMENT 'Date of the record',
  `conversation_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '对话唯一标识，通常是文件名中的唯一标识符，确保每个对话的唯一性',
  `brand` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Brand name mentioned',
  `category` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '商品大类',
  `platform` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Platform where the question was posted (e.g., Qwen, Deepseek, etc.)',
  `keyword` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '生成question的关键词，用户提交job时系统会根据关键词生成question',
  `is_mentioned` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Whether the brand is mentioned in the answer (0 = no, 1 = yes)',
  `is_first_mentioned` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Whether the brand is the first mentioned in the answer',
  `is_top3_mentioned` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Whether the brand is among the first three mentioned in the answer',
  `sentiment_status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'unknown' COMMENT 'Sentiment status (positive, negative, neutral, unknown)',
  `brands_found` json DEFAULT NULL COMMENT 'All brands found in the text (e.g., ["海尔 (Haier)", ...])',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_job_conv_brand` (`tenant_key`(191),`job_id`(191),`conversation_id`(191),`brand`),
  KEY `idx_tenant_date` (`tenant_key`,`date`),
  KEY `idx_tenant_brand` (`tenant_key`,`brand`),
  KEY `idx_tenant_platform` (`tenant_key`,`platform`),
  KEY `idx_tenant_sentiment_status` (`tenant_key`,`sentiment_status`),
  KEY `idx_tenant_conversation_id` (`tenant_key`,`conversation_id`),
  KEY `idx_qbrs_analysis_run` (`tenant_key`,`analysis_run_id`),
  CONSTRAINT `qa_brand_state_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE,
  CONSTRAINT `qa_brand_state_ibfk_analysis_run` FOREIGN KEY (`tenant_key`,`analysis_run_id`) REFERENCES `analysis_runs` (`tenant_key`,`analysis_run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Records of brand status in Q&A'; 

-- 问答引用详情表
CREATE TABLE `qa_reference` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，数据库自增，唯一标识每条引用记录',
  `job_id` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务唯一标识（llm_query_jobs.job_id）',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '租户唯一字符串标识（tenants.tenant_key）',
  `analysis_run_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '生成该事实的分析运行ID',
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
  KEY `idx_qr_analysis_run` (`tenant_key`,`analysis_run_id`),
  CONSTRAINT `qa_reference_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE,
  CONSTRAINT `qa_reference_ibfk_analysis_run` FOREIGN KEY (`tenant_key`,`analysis_run_id`) REFERENCES `analysis_runs` (`tenant_key`,`analysis_run_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC COMMENT='存储对话中引用链接的关联表';

-- 数据库设计总结：
-- 1. 基础对话存储：llm_conversations 和 llm_conversation_references 存储原始抓取对话及引用
-- 2. 品牌状态详情：qa_brand_state 存储每个问题中品牌的具体表现（提及、首位、情感）
-- 3. 引用详情：qa_reference 存储问题相关的引用链接详情
-- 4. 时间字段：extracted_at使用文件原始时间，created_at/updated_at使用数据库时间
-- 5. 索引优化：针对常用查询场景设计，支持用户、任务、平台、关键词、品牌、日期等多维度查询
-- 6. 字符集：使用utf8mb4支持完整的Unicode字符
