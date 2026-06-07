-- Phase 7.4: generated reports read model
-- Adds persistent project report snapshots for brand monitoring reports.

CREATE TABLE IF NOT EXISTS `generated_reports` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `tenant_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Tenant key',
  `report_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Stable generated report id',
  `project_id` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Monitoring project id',
  `report_type` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'project_summary' COMMENT 'Report type',
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Report title',
  `timeframe` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'custom' COMMENT 'Report timeframe',
  `start_date` date NOT NULL COMMENT 'Report window start date',
  `end_date` date NOT NULL COMMENT 'Report window end date',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'generated' COMMENT 'Report status',
  `summary_json` json NOT NULL COMMENT 'Report summary snapshot',
  `metrics_json` json NOT NULL COMMENT 'Core metrics snapshot',
  `alerts_json` json DEFAULT NULL COMMENT 'Alert event snapshot',
  `generated_by` bigint(20) DEFAULT NULL COMMENT 'User id that generated the report',
  `generated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Report generated time',
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Created time',
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Updated time',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_tenant_generated_report` (`tenant_key`,`report_id`),
  KEY `idx_generated_reports_project_generated` (`tenant_key`(128),`project_id`,`generated_at`),
  KEY `idx_generated_reports_project_window` (`tenant_key`(128),`project_id`,`start_date`,`end_date`),
  CONSTRAINT `generated_reports_ibfk_tenant` FOREIGN KEY (`tenant_key`) REFERENCES `tenants` (`tenant_key`) ON DELETE CASCADE,
  CONSTRAINT `generated_reports_ibfk_project` FOREIGN KEY (`tenant_key`,`project_id`) REFERENCES `monitoring_projects` (`tenant_key`,`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Generated brand monitoring reports';
