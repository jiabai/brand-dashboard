from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.v1.models.schemas import (
    CollectionAttemptDetail,
    CollectionAttemptResponse,
    CompleteCollectionAttemptRequest,
    StartCollectionAttemptRequest,
)
from api.v1.repositories.collection_attempts import (
    complete_collection_attempt,
    start_collection_attempt,
)
from api.v1.repositories.connection import get_db
from api.v1.routes.query_jobs import verify_executor

router = APIRouter()


def _to_attempt_detail(row) -> CollectionAttemptDetail:
    return CollectionAttemptDetail(
        id=row.id,
        tenant_key=row.tenant_key,
        attempt_id=row.attempt_id,
        collection_task_id=row.collection_task_id,
        executor_id=row.executor_id,
        status=row.status,
        started_at=row.started_at,
        finished_at=row.finished_at,
        error_code=row.error_code,
        error_message=row.error_message,
        raw_response_id=row.raw_response_id,
    )


def _raise_operation_error(status_code: int, message: str) -> None:
    raise HTTPException(status_code=status_code, detail=message)


@router.post("/{attempt_id}/start", response_model=CollectionAttemptResponse)
async def start_attempt(
    attempt_id: str,
    request: StartCollectionAttemptRequest,
    executor_id: str = Depends(verify_executor),
    db: Session = Depends(get_db),
):
    now = datetime.now(UTC)
    try:
        result = start_collection_attempt(
            db,
            tenant_key=request.tenant_key,
            collection_task_id=request.collection_task_id,
            attempt_id=attempt_id,
            executor_id=executor_id,
            now=now,
        )
        if result.status_code != 200:
            db.rollback()
            _raise_operation_error(result.status_code, result.message)

        db.commit()
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"启动 attempt 失败: {exc}") from exc

    return CollectionAttemptResponse(
        success=True,
        attempt=_to_attempt_detail(result.attempt),
    )


@router.post("/{attempt_id}/complete", response_model=CollectionAttemptResponse)
async def complete_attempt(
    attempt_id: str,
    request: CompleteCollectionAttemptRequest,
    executor_id: str = Depends(verify_executor),
    db: Session = Depends(get_db),
):
    now = datetime.now(UTC)
    try:
        result = complete_collection_attempt(
            db,
            tenant_key=request.tenant_key,
            attempt_id=attempt_id,
            executor_id=executor_id,
            status=request.status,
            error_code=request.error_code,
            error_message=request.error_message,
            raw_response_id=request.raw_response_id,
            now=now,
        )
        if result.status_code != 200:
            db.rollback()
            _raise_operation_error(result.status_code, result.message)

        db.commit()
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"完成 attempt 失败: {exc}") from exc

    return CollectionAttemptResponse(
        success=True,
        attempt=_to_attempt_detail(result.attempt),
    )
