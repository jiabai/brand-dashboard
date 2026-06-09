from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def list_failed_collection_tasks(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    limit: int = 100,
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              ct.collection_task_id,
              ct.collection_job_id,
              ct.platform,
              pi.keyword,
              ct.query_content,
              ct.status,
              ct.attempt_count,
              ct.max_attempts,
              CASE
                WHEN ct.status = 'failed' AND ct.attempt_count < ct.max_attempts
                THEN 1 ELSE 0
              END AS can_retry,
              ct.last_error_code,
              ct.last_error_message,
              ct.lease_owner,
              ct.updated_at
            FROM collection_tasks ct
            LEFT JOIN prompt_items pi
              ON pi.tenant_key = ct.tenant_key
             AND pi.prompt_set_id = ct.prompt_set_id
             AND pi.prompt_item_id = ct.prompt_item_id
            WHERE ct.tenant_key = :tenant_key
              AND ct.project_id = :project_id
              AND ct.status = 'failed'
            ORDER BY ct.updated_at DESC, ct.id DESC
            LIMIT :limit
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "limit": limit,
        },
    ).mappings().all()


def list_stale_analysis_runs(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    limit: int = 100,
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              analysis_run_id,
              collection_job_id,
              status,
              stale_at,
              error_code,
              error_message
            FROM analysis_runs
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
              AND status = 'stale'
            ORDER BY stale_at DESC, updated_at DESC, id DESC
            LIMIT :limit
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "limit": limit,
        },
    ).mappings().all()


def list_analysis_fact_quality_rows(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              ar.analysis_run_id,
              ar.collection_job_id,
              ar.finished_at,
              cj.expected_task_count,
              cj.succeeded_task_count,
              cj.failed_task_count,
              bs.date AS fact_date,
              bs.brand,
              bs.platform,
              bs.keyword,
              COUNT(DISTINCT bs.conversation_id) AS analyzed_answer_count
            FROM analysis_runs ar
            JOIN collection_jobs cj
              ON cj.tenant_key = ar.tenant_key
             AND cj.collection_job_id = ar.collection_job_id
            LEFT JOIN qa_brand_state bs
              ON bs.tenant_key = ar.tenant_key
             AND bs.analysis_run_id = ar.analysis_run_id
            WHERE ar.tenant_key = :tenant_key
              AND ar.project_id = :project_id
              AND ar.status = 'succeeded'
            GROUP BY
              ar.analysis_run_id,
              ar.collection_job_id,
              ar.finished_at,
              cj.expected_task_count,
              cj.succeeded_task_count,
              cj.failed_task_count,
              bs.date,
              bs.brand,
              bs.platform,
              bs.keyword
            ORDER BY ar.finished_at DESC, ar.id DESC
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
        },
    ).mappings().all()
