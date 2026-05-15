"""应用层定时任务：替代 MySQL 事件调度器

将 schema_init.sql 中的 ev_reset_query_jobs_daily 事件迁移为 Python 定时任务。
使用 FastAPI lifespan 启动后台线程，每日凌晨自动重置 llm_query_jobs。
"""
import logging
import threading
import time
from datetime import datetime

from sqlalchemy import text

from api.v1.repositories.connection import engine, get_dialect

logger = logging.getLogger(__name__)


def reset_query_jobs_daily():
    """每日重置已跑满的 query_jobs 的 executed_runs 计数器。

    等价于 MySQL 事件:
    UPDATE llm_query_jobs
    SET executed_runs = 0
    WHERE query_status = 1
      AND is_deleted = 0
      AND executed_runs = total_runs
      AND last_executed_date < CURDATE()
      AND NOW() >= effective_from
      AND (effective_to IS NULL OR NOW() <= effective_to);
    """
    try:
        with engine.begin() as conn:
            result = conn.execute(text("""
                UPDATE llm_query_jobs
                SET executed_runs = 0
                WHERE query_status = 1
                  AND is_deleted = 0
                  AND executed_runs = total_runs
                  AND last_executed_date < DATE('now')
                  AND CURRENT_TIMESTAMP >= effective_from
                  AND (effective_to IS NULL OR CURRENT_TIMESTAMP <= effective_to)
            """))
            logger.info("每日重置 query_jobs 完成，影响行数: %d", result.rowcount)
    except Exception as e:
        logger.error("每日重置 query_jobs 失败: %s", str(e))


def _run_scheduler(interval_seconds: int = 3600):
    """后台线程：每隔 interval_seconds 检查是否需要执行重置。"""
    last_reset_date = None
    while True:
        try:
            now = datetime.now()
            # 每天凌晨（0-1点之间）执行一次
            if now.hour == 0 and last_reset_date != now.date():
                reset_query_jobs_daily()
                last_reset_date = now.date()
        except Exception as e:
            logger.error("定时任务线程异常: %s", str(e))
        time.sleep(interval_seconds)


def start_scheduler():
    """启动后台定时任务线程（daemon 模式，随主进程退出）。"""
    # 仅在需要时启动（SQLite 不支持 MySQL 事件，MySQL 由自身事件调度器处理）
    if get_dialect() == "sqlite":
        t = threading.Thread(target=_run_scheduler, daemon=True)
        t.start()
        logger.info("SQLite 定时任务调度器已启动（每日凌晨重置 query_jobs）")
    else:
        logger.info("MySQL 模式，跳过应用层定时任务（由 MySQL 事件调度器处理）")
