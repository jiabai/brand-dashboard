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


def list_metric_snapshot_quality_rows(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              analysis_run_id,
              metric_date,
              metric_definition_version,
              generated_at,
              coverage_rate,
              expected_task_count,
              succeeded_task_count,
              failed_task_count,
              analyzed_answer_count,
              dimension_hash
            FROM metric_snapshots
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
            ORDER BY generated_at DESC, id DESC
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
        },
    ).mappings().all()
