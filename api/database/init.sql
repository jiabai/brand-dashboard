-- 1) 开启事件调度器（只需执行一次）
SET GLOBAL event_scheduler = ON;

-- 2) 每日执行跨日重置（硬性满足有效期范围）
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

-- 3) fetch 查询索引（保证过滤+排序高效）
CREATE INDEX idx_jobs_fetch
  ON llm_query_jobs (executor_id, query_status, is_deleted, executed_runs, id);

-- 4) 重置筛选索引（帮助事件 UPDATE 过滤）
CREATE INDEX idx_jobs_reset
  ON llm_query_jobs (executor_id, query_status, is_deleted, last_executed_date, executed_runs);