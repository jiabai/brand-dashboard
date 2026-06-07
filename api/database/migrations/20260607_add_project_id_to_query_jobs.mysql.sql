-- Phase 3.4: link legacy llm_query_jobs rows to monitoring projects.
-- The column is nullable so existing job_id-based dashboard rows remain valid.

ALTER TABLE `llm_query_jobs`
  ADD COLUMN `project_id` varchar(128) COLLATE utf8mb4_unicode_ci NULL
    COMMENT '关联监测项目ID，兼容期可为空'
    AFTER `job_id`,
  ADD INDEX `idx_lqj_project` (`tenant_key`, `project_id`);
