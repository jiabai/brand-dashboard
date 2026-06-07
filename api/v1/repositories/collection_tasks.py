from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

_CLAIMABLE_TASK_CONDITION = """
(
    status = 'pending'
    OR (status = 'failed' AND attempt_count < max_attempts)
    OR (status = 'reserved' AND (lease_until IS NULL OR lease_until <= :now))
)
"""


def _select_collection_task_by_id(db: Session, task_pk: int):
    return db.execute(
        text(
            """
            SELECT
              id,
              tenant_key,
              collection_task_id,
              collection_job_id,
              project_id,
              prompt_set_id,
              prompt_item_id,
              platform,
              query_content,
              run_index,
              status,
              lease_owner,
              lease_until,
              attempt_count,
              max_attempts
            FROM collection_tasks
            WHERE id = :id
            """
        ),
        {"id": task_pk},
    ).first()


def fetch_next_collection_task(
    db: Session,
    *,
    executor_id: str,
    tenant_key: str,
    now: datetime,
    lease_until: datetime,
    collection_job_id: Optional[str] = None,
    max_claim_attempts: int = 3,
):
    params: Dict[str, Any] = {
        "tenant_key": tenant_key,
        "executor_id": executor_id,
        "now": now,
        "lease_until": lease_until,
    }
    where_clauses = [
        "tenant_key = :tenant_key",
        _CLAIMABLE_TASK_CONDITION,
    ]

    if collection_job_id is not None:
        where_clauses.append("collection_job_id = :collection_job_id")
        params["collection_job_id"] = collection_job_id

    for _ in range(max_claim_attempts):
        candidate = db.execute(
            text(
                f"""
                SELECT id
                FROM collection_tasks
                WHERE {" AND ".join(where_clauses)}
                ORDER BY id ASC
                LIMIT 1
                """
            ),
            params,
        ).first()

        if candidate is None:
            return None

        claim_result = db.execute(
            text(
                f"""
                UPDATE collection_tasks
                SET
                  status = 'reserved',
                  lease_owner = :executor_id,
                  lease_until = :lease_until,
                  reserved_at = :now,
                  updated_at = :now
                WHERE id = :id
                  AND tenant_key = :tenant_key
                  AND {_CLAIMABLE_TASK_CONDITION}
                """
            ),
            {
                **params,
                "id": candidate.id,
            },
        )

        if claim_result.rowcount == 1:
            return _select_collection_task_by_id(db, candidate.id)

    return None
