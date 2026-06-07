from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.v1.models.schemas import CollectionTaskDetail, FetchCollectionTaskResponse
from api.v1.repositories.collection_tasks import fetch_next_collection_task
from api.v1.repositories.connection import get_db
from api.v1.routes.query_jobs import verify_executor

router = APIRouter()


@router.get("/fetch", response_model=FetchCollectionTaskResponse)
async def fetch_collection_task(
    tenant_key: str = Query(..., min_length=1, description="租户Key"),
    collection_job_id: Optional[str] = Query(None, description="可选：仅拉取指定采集批次"),
    lease_seconds: int = Query(300, ge=1, le=3600, description="租约有效秒数"),
    executor_id: str = Depends(verify_executor),
    db: Session = Depends(get_db),
):
    normalized_tenant_key = tenant_key.strip()
    if not normalized_tenant_key:
        raise HTTPException(status_code=400, detail="tenant_key 不能为空")

    normalized_collection_job_id = collection_job_id.strip() if collection_job_id else None
    if not normalized_collection_job_id:
        normalized_collection_job_id = None

    now = datetime.now(UTC)
    lease_until = now + timedelta(seconds=lease_seconds)

    try:
        result = fetch_next_collection_task(
            db,
            executor_id=executor_id,
            tenant_key=normalized_tenant_key,
            collection_job_id=normalized_collection_job_id,
            now=now,
            lease_until=lease_until,
        )

        if result is None:
            return FetchCollectionTaskResponse(success=True, count=0, task=None)

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"领取采集任务失败: {exc}") from exc

    return FetchCollectionTaskResponse(
        success=True,
        count=1,
        task=CollectionTaskDetail(
            id=result.id,
            tenant_key=result.tenant_key,
            collection_task_id=result.collection_task_id,
            collection_job_id=result.collection_job_id,
            project_id=result.project_id,
            prompt_set_id=result.prompt_set_id,
            prompt_item_id=result.prompt_item_id,
            platform=result.platform,
            query_content=result.query_content,
            run_index=result.run_index,
            status=result.status,
            lease_owner=result.lease_owner,
            lease_until=result.lease_until,
            attempt_count=result.attempt_count,
            max_attempts=result.max_attempts,
        ),
    )
