-- Phase 5.2: bind analysis fact rows to analysis_runs.
-- Historical rows keep NULL analysis_run_id during compatibility period.

ALTER TABLE `qa_brand_state`
  ADD COLUMN `analysis_run_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '生成该事实的分析运行ID' AFTER `tenant_key`,
  ADD KEY `idx_qbrs_analysis_run` (`tenant_key`,`analysis_run_id`),
  ADD CONSTRAINT `qa_brand_state_ibfk_analysis_run`
    FOREIGN KEY (`tenant_key`,`analysis_run_id`)
    REFERENCES `analysis_runs` (`tenant_key`,`analysis_run_id`);

ALTER TABLE `qa_reference`
  ADD COLUMN `analysis_run_id` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '生成该事实的分析运行ID' AFTER `tenant_key`,
  ADD KEY `idx_qr_analysis_run` (`tenant_key`,`analysis_run_id`),
  ADD CONSTRAINT `qa_reference_ibfk_analysis_run`
    FOREIGN KEY (`tenant_key`,`analysis_run_id`)
    REFERENCES `analysis_runs` (`tenant_key`,`analysis_run_id`);
