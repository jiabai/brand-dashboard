from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class AttemptOperationResult:
    status_code: int
    message: str
    attempt: object | None = None


def _select_attempt(db: Session, *, tenant_key: str, attempt_id: str):
    return db.execute(
        text(
            """
            SELECT
              id,
              tenant_key,
              attempt_id,
              collection_task_id,
              executor_id,
              status,
              started_at,
              finished_at,
              error_code,
              error_message,
              raw_response_id
            FROM collection_attempts
            WHERE tenant_key = :tenant_key
              AND attempt_id = :attempt_id
            """
        ),
        {"tenant_key": tenant_key, "attempt_id": attempt_id},
    ).first()


def _attempt_exists(db: Session, *, tenant_key: str, attempt_id: str) -> bool:
    return (
        db.execute(
            text(
                """
                SELECT 1
                FROM collection_attempts
                WHERE tenant_key = :tenant_key
                  AND attempt_id = :attempt_id
                LIMIT 1
                """
            ),
            {"tenant_key": tenant_key, "attempt_id": attempt_id},
        ).first()
        is not None
    )


def _select_task_for_attempt(db: Session, *, tenant_key: str, collection_task_id: str):
    return db.execute(
        text(
            """
            SELECT
              collection_task_id,
              status,
              lease_owner,
              lease_until,
              attempt_count,
              max_attempts
            FROM collection_tasks
            WHERE tenant_key = :tenant_key
              AND collection_task_id = :collection_task_id
            """
        ),
        {"tenant_key": tenant_key, "collection_task_id": collection_task_id},
    ).first()


def _normalize_datetime(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def start_collection_attempt(
    db: Session,
    *,
    tenant_key: str,
    collection_task_id: str,
    attempt_id: str,
    executor_id: str,
    now: datetime,
) -> AttemptOperationResult:
    task = _select_task_for_attempt(
        db,
        tenant_key=tenant_key,
        collection_task_id=collection_task_id,
    )

    if task is None:
        return AttemptOperationResult(404, "采集任务不存在")

    lease_until = _normalize_datetime(task.lease_until)
    if (
        task.status != "reserved"
        or task.lease_owner != executor_id
        or lease_until is None
        or lease_until <= now
    ):
        return AttemptOperationResult(403, "执行器无权启动该采集任务 attempt")

    if task.attempt_count >= task.max_attempts:
        return AttemptOperationResult(409, "任务重试次数已达上限")

    if _attempt_exists(db, tenant_key=tenant_key, attempt_id=attempt_id):
        return AttemptOperationResult(409, "attempt_id 已存在")

    db.execute(
        text(
            """
            INSERT INTO collection_attempts
              (
                tenant_key,
                attempt_id,
                collection_task_id,
                executor_id,
                status,
                started_at,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                :attempt_id,
                :collection_task_id,
                :executor_id,
                'running',
                :now,
                :now,
                :now
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "attempt_id": attempt_id,
            "collection_task_id": collection_task_id,
            "executor_id": executor_id,
            "now": now,
        },
    )
    db.execute(
        text(
            """
            UPDATE collection_tasks
            SET
              status = 'running',
              started_at = :now,
              attempt_count = attempt_count + 1,
              updated_at = :now
            WHERE tenant_key = :tenant_key
              AND collection_task_id = :collection_task_id
            """
        ),
        {
            "tenant_key": tenant_key,
            "collection_task_id": collection_task_id,
            "now": now,
        },
    )

    return AttemptOperationResult(
        200,
        "attempt 已启动",
        _select_attempt(db, tenant_key=tenant_key, attempt_id=attempt_id),
    )


def complete_collection_attempt(
    db: Session,
    *,
    tenant_key: str,
    attempt_id: str,
    executor_id: str,
    status: str,
    now: datetime,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    raw_response_id: Optional[str] = None,
) -> AttemptOperationResult:
    attempt = _select_attempt(db, tenant_key=tenant_key, attempt_id=attempt_id)
    if attempt is None:
        return AttemptOperationResult(404, "attempt 不存在")

    if attempt.executor_id != executor_id:
        return AttemptOperationResult(403, "执行器无权完成该 attempt")

    if attempt.status != "running":
        return AttemptOperationResult(409, "attempt 不处于 running 状态")

    task = _select_task_for_attempt(
        db,
        tenant_key=tenant_key,
        collection_task_id=attempt.collection_task_id,
    )
    if task is None:
        return AttemptOperationResult(404, "采集任务不存在")

    if status == "succeeded":
        task_status = "succeeded"
        last_error_code = None
        last_error_message = None
    elif status == "cancelled":
        task_status = "cancelled"
        last_error_code = error_code
        last_error_message = error_message
    else:
        task_status = "failed"
        last_error_code = error_code
        last_error_message = error_message

    db.execute(
        text(
            """
            UPDATE collection_attempts
            SET
              status = :status,
              finished_at = :now,
              error_code = :error_code,
              error_message = :error_message,
              raw_response_id = :raw_response_id,
              updated_at = :now
            WHERE tenant_key = :tenant_key
              AND attempt_id = :attempt_id
              AND status = 'running'
            """
        ),
        {
            "tenant_key": tenant_key,
            "attempt_id": attempt_id,
            "status": status,
            "error_code": error_code,
            "error_message": error_message,
            "raw_response_id": raw_response_id,
            "now": now,
        },
    )
    db.execute(
        text(
            """
            UPDATE collection_tasks
            SET
              status = :task_status,
              lease_owner = NULL,
              lease_until = NULL,
              finished_at = :now,
              last_error_code = :last_error_code,
              last_error_message = :last_error_message,
              updated_at = :now
            WHERE tenant_key = :tenant_key
              AND collection_task_id = :collection_task_id
            """
        ),
        {
            "tenant_key": tenant_key,
            "collection_task_id": attempt.collection_task_id,
            "task_status": task_status,
            "last_error_code": last_error_code,
            "last_error_message": last_error_message,
            "now": now,
        },
    )

    return AttemptOperationResult(
        200,
        "attempt 已完成",
        _select_attempt(db, tenant_key=tenant_key, attempt_id=attempt_id),
    )
