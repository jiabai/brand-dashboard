from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.v1.dependencies.auth import (
    CurrentTenantContext,
    get_current_tenant,
    require_current_tenant,
)
from api.v1.models.schemas import (
    AnalysisRunDetail,
    AnalysisRunResponse,
    RetryAnalysisRunRequest,
    RetryAnalysisRunResponse,
)
from api.v1.repositories import analysis_runs as analysis_run_repository
from api.v1.repositories.connection import get_db
from api.v1.services import analysis_runner

router = APIRouter()


def _can_retry(row) -> bool:
    return row.status in {"failed", "stale"}


def _to_analysis_run_detail(row) -> AnalysisRunDetail:
    return AnalysisRunDetail(
        id=row.id,
        tenant_key=row.tenant_key,
        analysis_run_id=row.analysis_run_id,
        project_id=row.project_id,
        collection_job_id=row.collection_job_id,
        status=row.status,
        plugin_versions=row.plugin_versions,
        model_config_hash=row.model_config_hash,
        input_watermark=row.input_watermark,
        started_at=row.started_at,
        finished_at=row.finished_at,
        stale_at=row.stale_at,
        error_code=row.error_code,
        error_message=row.error_message,
        can_retry=_can_retry(row),
    )


def _raise_operation_error(status_code: int, message: str) -> None:
    raise HTTPException(status_code=status_code, detail=message)


@router.get("/{analysis_run_id}", response_model=AnalysisRunResponse)
async def get_analysis_run(
    analysis_run_id: str,
    tenant: CurrentTenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    analysis_run = analysis_run_repository.get_analysis_run(
        db,
        tenant_key=tenant.tenant_key,
        analysis_run_id=analysis_run_id,
    )
    if analysis_run is None:
        raise HTTPException(status_code=404, detail="analysis run 不存在")

    return AnalysisRunResponse(
        success=True,
        analysis_run=_to_analysis_run_detail(analysis_run),
    )


@router.post("/{analysis_run_id}/retry", response_model=RetryAnalysisRunResponse)
async def retry_analysis_run(
    analysis_run_id: str,
    request: RetryAnalysisRunRequest | None = None,
    tenant: CurrentTenantContext = Depends(require_current_tenant("admin")),
    db: Session = Depends(get_db),
):
    try:
        result = analysis_runner.retry_analysis_run(
            db,
            tenant_key=tenant.tenant_key,
            analysis_run_id=analysis_run_id,
            retry_analysis_run_id=request.analysis_run_id if request else None,
            now=datetime.now(UTC),
        )
        if result.status_code != 200:
            _raise_operation_error(result.status_code, result.message)
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重试 analysis run 失败: {exc}") from exc

    return RetryAnalysisRunResponse(
        success=True,
        retried_from_analysis_run_id=result.retried_from_analysis_run_id
        or analysis_run_id,
        analysis_run=_to_analysis_run_detail(result.analysis_run),
    )
