-- Phase 5.1: add analysis run lifecycle model.
-- Depends on Phase 4.1 collection lifecycle tables.
-- Safe to rerun: the table uses CREATE TABLE IF NOT EXISTS.

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
