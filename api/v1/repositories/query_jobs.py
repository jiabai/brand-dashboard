import datetime
from typing import Any, Dict, Iterable, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def sync_query_jobs_status(db: Session, now: datetime.datetime) -> int:
    result = db.execute(
        text(
            """
            UPDATE llm_query_jobs
            SET query_status = CASE
                WHEN query_status = 0 AND effective_from <= :now THEN 1
                WHEN query_status = 1 AND effective_to IS NOT NULL
                     AND effective_to < :now THEN 3
                ELSE query_status
            END,
            updated_at = :now
            WHERE (query_status = 0 AND effective_from <= :now)
               OR (query_status = 1 AND effective_to IS NOT NULL AND effective_to < :now)
            """
        ),
        {"now": now},
    )
    return result.rowcount


def fetch_next_query_job(
    db: Session,
    *,
    executor_id: str,
    tenant_key: Optional[str] = None,
    job_id: Optional[str] = None,
):
    params: Dict[str, Any] = {"executor_id": executor_id}
    where_clauses = ["executor_id = :executor_id"]

    if tenant_key is not None:
        where_clauses.append("tenant_key = :tenant_key")
        params["tenant_key"] = tenant_key

    if job_id is not None:
        where_clauses.append("job_id = :job_id")
        params["job_id"] = job_id

    where_clauses.extend(
        [
            "query_status = 1",
            "is_deleted = 0",
            "executed_runs < total_runs",
            "CURRENT_TIMESTAMP >= effective_from",
            "(effective_to IS NULL OR CURRENT_TIMESTAMP <= effective_to)",
            "(last_executed_date IS NULL OR last_executed_date <= CURRENT_DATE)",
        ]
    )

    return db.execute(
        text(
            f"""
            SELECT
              id, job_id, tenant_key, category, brand, competitor, keyword, query_content
            FROM llm_query_jobs
            WHERE {" AND ".join(where_clauses)}
            ORDER BY
              executed_runs ASC,
              id ASC
            LIMIT 1
            """
        ),
        params,
    ).first()


def get_query_job_runs(db: Session, *, record_id: int, executor_id: str):
    return db.execute(
        text(
            """
            SELECT executed_runs, total_runs
            FROM llm_query_jobs
            WHERE id = :id AND executor_id = :executor_id
            """
        ),
        {"id": record_id, "executor_id": executor_id},
    ).first()


def executor_has_job_scope(
    db: Session,
    *,
    executor_id: str,
    tenant_key: str,
    job_id: str,
) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM llm_query_jobs
            WHERE executor_id = :executor_id
              AND tenant_key = :tenant_key
              AND job_id = :job_id
              AND is_deleted = 0
            LIMIT 1
            """
        ),
        {
            "executor_id": executor_id,
            "tenant_key": tenant_key,
            "job_id": job_id,
        },
    ).first()
    return row is not None


def increment_query_job_runs(
    db: Session,
    *,
    record_id: int,
    executor_id: str,
    today: datetime.date,
    now: datetime.datetime,
) -> int:
    result = db.execute(
        text(
            """
            UPDATE llm_query_jobs
            SET executed_runs = executed_runs + 1,
                query_status = CASE
                    WHEN executed_runs + 1 >= total_runs THEN 2
                    ELSE query_status
                END,
                last_executed_date = :today,
                updated_at = :now
            WHERE id = :id
              AND executor_id = :executor_id
              AND executed_runs < total_runs
            """
        ),
        {
            "today": today,
            "now": now,
            "id": record_id,
            "executor_id": executor_id,
        },
    )
    return result.rowcount


def list_query_jobs_status(
    db: Session,
    *,
    tenant_key: str,
    job_id: Optional[str] = None,
    include_deleted: bool = False,
):
    params: Dict[str, Any] = {"tenant_key": tenant_key}
    where_clauses = ["tenant_key = :tenant_key"]

    if job_id is not None:
        where_clauses.append("job_id = :job_id")
        params["job_id"] = job_id

    if not include_deleted:
        where_clauses.append("is_deleted = 0")

    return db.execute(
        text(
            f"""
            SELECT
              tenant_key,
              job_id,
              brand,
              competitor,
              query_content,
              query_status,
              effective_from,
              effective_to
            FROM llm_query_jobs
            WHERE {" AND ".join(where_clauses)}
            ORDER BY id DESC
            """
        ),
        params,
    ).fetchall()


def insert_query_jobs(db: Session, rows: Iterable[Dict[str, Any]]) -> int:
    result = db.execute(
        text(
            """
            INSERT INTO llm_query_jobs (
              tenant_key,
              job_id,
              category,
              brand,
              competitor,
              keyword,
              query_content,
              query_status,
              executor_id,
              total_runs,
              executed_runs,
              last_executed_date,
              effective_from,
              effective_to,
              created_at,
              updated_at
            )
            VALUES (
              :tenant_key,
              :job_id,
              :category,
              :brand,
              :competitor,
              :keyword,
              :query_content,
              :query_status,
              :executor_id,
              :total_runs,
              :executed_runs,
              :last_executed_date,
              :effective_from,
              :effective_to,
              :created_at,
              :updated_at
            )
            """
        ),
        rows,
    )
    return result.rowcount
