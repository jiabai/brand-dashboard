from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_platform_collection_health(
    db: Session,
    *,
    now: datetime,
    failed_task_limit: int = 20,
):
    summary = db.execute(
        text(
            """
            SELECT
                (SELECT COUNT(*) FROM executors) AS executor_count,
                (
                    SELECT COUNT(*)
                    FROM executors
                    WHERE status = 'active'
                ) AS active_executor_count,
                (
                    SELECT COUNT(*)
                    FROM executors
                    WHERE status != 'active'
                ) AS inactive_executor_count,
                (
                    SELECT COUNT(*)
                    FROM collection_tasks
                    WHERE status = 'pending'
                ) AS pending_task_count,
                (
                    SELECT COUNT(*)
                    FROM collection_tasks
                    WHERE status = 'reserved'
                ) AS reserved_task_count,
                (
                    SELECT COUNT(*)
                    FROM collection_tasks
                    WHERE status = 'running'
                ) AS running_task_count,
                (
                    SELECT COUNT(*)
                    FROM collection_tasks
                    WHERE status = 'failed'
                ) AS failed_task_count,
                (
                    SELECT COUNT(*)
                    FROM collection_tasks
                    WHERE status = 'failed'
                      AND attempt_count < max_attempts
                ) AS retryable_failed_task_count,
                (
                    SELECT COUNT(*)
                    FROM collection_tasks
                    WHERE status IN ('reserved', 'running')
                      AND lease_until IS NOT NULL
                      AND lease_until < :now
                ) AS expired_lease_task_count
            """
        ),
        {"now": now},
    ).one()

    executors = db.execute(
        text(
            """
            SELECT
                e.executor_id,
                e.name,
                e.type,
                e.status,
                e.ip_address,
                e.created_at,
                e.updated_at,
                (
                    SELECT COUNT(*)
                    FROM collection_tasks active_tasks
                    WHERE active_tasks.lease_owner = e.executor_id
                      AND active_tasks.status IN ('reserved', 'running')
                      AND active_tasks.lease_until IS NOT NULL
                      AND active_tasks.lease_until > :now
                ) AS active_lease_count,
                (
                    SELECT COUNT(*)
                    FROM collection_attempts running_attempts
                    WHERE running_attempts.executor_id = e.executor_id
                      AND running_attempts.status = 'running'
                ) AS running_attempt_count,
                (
                    SELECT COUNT(*)
                    FROM collection_attempts failed_attempts
                    WHERE failed_attempts.executor_id = e.executor_id
                      AND failed_attempts.status IN ('failed', 'timeout')
                ) AS failed_attempt_count,
                (
                    SELECT MAX(all_attempts.updated_at)
                    FROM collection_attempts all_attempts
                    WHERE all_attempts.executor_id = e.executor_id
                ) AS latest_attempt_at
            FROM executors e
            ORDER BY e.status ASC, e.executor_id ASC
            """
        ),
        {"now": now},
    ).fetchall()

    queues = db.execute(
        text(
            """
            SELECT
                ct.tenant_key,
                t.tenant_name,
                ct.project_id,
                mp.name AS project_name,
                ct.collection_job_id,
                cj.status AS collection_job_status,
                COUNT(*) AS total_task_count,
                SUM(CASE WHEN ct.status = 'pending' THEN 1 ELSE 0 END) AS pending_task_count,
                SUM(CASE WHEN ct.status = 'reserved' THEN 1 ELSE 0 END) AS reserved_task_count,
                SUM(CASE WHEN ct.status = 'running' THEN 1 ELSE 0 END) AS running_task_count,
                SUM(CASE WHEN ct.status = 'succeeded' THEN 1 ELSE 0 END) AS succeeded_task_count,
                SUM(CASE WHEN ct.status = 'failed' THEN 1 ELSE 0 END) AS failed_task_count,
                SUM(
                    CASE
                        WHEN ct.status = 'failed' AND ct.attempt_count < ct.max_attempts
                        THEN 1 ELSE 0
                    END
                ) AS retryable_failed_task_count,
                SUM(
                    CASE
                        WHEN ct.status IN ('reserved', 'running')
                         AND ct.lease_until IS NOT NULL
                         AND ct.lease_until < :now
                        THEN 1 ELSE 0
                    END
                ) AS expired_lease_task_count
            FROM collection_tasks ct
            JOIN collection_jobs cj
              ON cj.tenant_key = ct.tenant_key
             AND cj.collection_job_id = ct.collection_job_id
            LEFT JOIN tenants t ON t.tenant_key = ct.tenant_key
            LEFT JOIN monitoring_projects mp
              ON mp.tenant_key = ct.tenant_key
             AND mp.project_id = ct.project_id
            GROUP BY
                ct.tenant_key,
                t.tenant_name,
                ct.project_id,
                mp.name,
                ct.collection_job_id,
                cj.status
            ORDER BY failed_task_count DESC, pending_task_count DESC, ct.tenant_key ASC
            """
        ),
        {"now": now},
    ).fetchall()

    failed_tasks = db.execute(
        text(
            """
            SELECT
                ct.tenant_key,
                t.tenant_name,
                ct.project_id,
                mp.name AS project_name,
                ct.collection_job_id,
                ct.collection_task_id,
                ct.platform,
                pi.keyword,
                ct.query_content,
                ct.attempt_count,
                ct.max_attempts,
                ct.last_error_code,
                ct.last_error_message,
                ct.lease_owner,
                ct.updated_at
            FROM collection_tasks ct
            LEFT JOIN tenants t ON t.tenant_key = ct.tenant_key
            LEFT JOIN monitoring_projects mp
              ON mp.tenant_key = ct.tenant_key
             AND mp.project_id = ct.project_id
            LEFT JOIN prompt_items pi
              ON pi.tenant_key = ct.tenant_key
             AND pi.prompt_set_id = ct.prompt_set_id
             AND pi.prompt_item_id = ct.prompt_item_id
            WHERE ct.status = 'failed'
            ORDER BY ct.updated_at DESC, ct.id DESC
            LIMIT :limit
            """
        ),
        {"limit": failed_task_limit},
    ).fetchall()

    return {
        "summary": summary,
        "executors": executors,
        "queues": queues,
        "failed_tasks": failed_tasks,
    }
