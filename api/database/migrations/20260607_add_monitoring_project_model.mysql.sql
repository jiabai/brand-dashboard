-- Phase 3.1: add monitoring project configuration model.
-- Safe to rerun: every table uses CREATE TABLE IF NOT EXISTS.

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
