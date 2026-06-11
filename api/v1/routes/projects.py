from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.v1.dependencies.auth import (
    CurrentTenantContext,
    CurrentUser,
    get_current_tenant,
    get_current_tenant_for_read,
    get_current_user,
    require_current_tenant,
)
from api.v1.models.schemas import (
    GenerateProjectReportRequest,
    MonitoringProjectCreate,
    ProjectAlertsResponse,
    ProjectBrandConfigRequest,
    ProjectBrandConfigResponse,
    ProjectCollectionJobsResponse,
    ProjectDataQualityResponse,
    ProjectListResponse,
    ProjectReportListResponse,
    ProjectReportResponse,
    ProjectResponse,
    PromptSetConfigRequest,
    PromptSetConfigResponse,
)
from api.v1.repositories.connection import get_db
from api.v1.services import projects as project_service

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    tenant: CurrentTenantContext = Depends(get_current_tenant_for_read),
    db: Session = Depends(get_db),
):
    projects = project_service.list_project_summaries(
        db,
        tenant_key=tenant.tenant_key,
    )
    return ProjectListResponse(success=True, count=len(projects), projects=projects)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    request: MonitoringProjectCreate,
    tenant: CurrentTenantContext = Depends(require_current_tenant("admin")),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        project = project_service.create_project(
            db,
            tenant_key=tenant.tenant_key,
            created_by=current_user.user_id,
            request=request,
        )
        db.commit()
        return ProjectResponse(success=True, project=project)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Project already exists or conflicts") from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create project: {exc}") from exc


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    tenant: CurrentTenantContext = Depends(get_current_tenant_for_read),
    db: Session = Depends(get_db),
):
    project = project_service.get_project_detail(
        db,
        tenant_key=tenant.tenant_key,
        project_id=project_id,
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(success=True, project=project)


@router.get("/{project_id}/data-quality", response_model=ProjectDataQualityResponse)
async def get_project_data_quality(
    project_id: str,
    tenant: CurrentTenantContext = Depends(get_current_tenant_for_read),
    db: Session = Depends(get_db),
):
    quality = project_service.get_project_data_quality(
        db,
        tenant_key=tenant.tenant_key,
        project_id=project_id,
    )
    if quality is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return quality


@router.get("/{project_id}/collection-jobs", response_model=ProjectCollectionJobsResponse)
async def list_project_collection_jobs(
    project_id: str,
    tenant: CurrentTenantContext = Depends(get_current_tenant_for_read),
    db: Session = Depends(get_db),
):
    result = project_service.list_project_collection_job_entries(
        db,
        tenant_key=tenant.tenant_key,
        project_id=project_id,
    )
    return ProjectCollectionJobsResponse(
        success=True,
        target_brand=result["target_brand"],
        collection_jobs=result["collection_jobs"],
    )


@router.get("/{project_id}/reports", response_model=ProjectReportListResponse)
async def list_project_reports(
    project_id: str,
    limit: int = Query(50, ge=1, le=200),
    tenant: CurrentTenantContext = Depends(get_current_tenant_for_read),
    db: Session = Depends(get_db),
):
    reports = project_service.list_project_reports(
        db,
        tenant_key=tenant.tenant_key,
        project_id=project_id,
        limit=limit,
    )
    if reports is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return reports


@router.post(
    "/{project_id}/reports",
    response_model=ProjectReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_project_report(
    project_id: str,
    request: GenerateProjectReportRequest,
    tenant: CurrentTenantContext = Depends(get_current_tenant),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        report = project_service.generate_project_report(
            db,
            tenant_key=tenant.tenant_key,
            project_id=project_id,
            generated_by=current_user.user_id,
            request=request,
        )
        if report is None:
            raise HTTPException(status_code=404, detail="Project not found")
        db.commit()
        return ProjectReportResponse(success=True, report=report)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Project report conflicts") from exc
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {exc}") from exc


@router.get("/{project_id}/alerts", response_model=ProjectAlertsResponse)
async def get_project_alerts(
    project_id: str,
    event_limit: int = Query(100, ge=1, le=500),
    tenant: CurrentTenantContext = Depends(get_current_tenant_for_read),
    db: Session = Depends(get_db),
):
    alerts = project_service.get_project_alerts(
        db,
        tenant_key=tenant.tenant_key,
        project_id=project_id,
        event_limit=event_limit,
    )
    if alerts is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return alerts


@router.post("/{project_id}/brands", response_model=ProjectBrandConfigResponse)
async def configure_project_brand(
    project_id: str,
    request: ProjectBrandConfigRequest,
    tenant: CurrentTenantContext = Depends(require_current_tenant("admin")),
    db: Session = Depends(get_db),
):
    try:
        brand = project_service.configure_project_brand(
            db,
            tenant_key=tenant.tenant_key,
            project_id=project_id,
            request=request,
        )
        if brand is None:
            raise HTTPException(status_code=404, detail="Project not found")
        db.commit()
        return ProjectBrandConfigResponse(success=True, brand=brand)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Project brand conflicts") from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure project brand: {exc}",
        ) from exc


@router.post("/{project_id}/prompt-sets", response_model=PromptSetConfigResponse)
async def configure_prompt_set(
    project_id: str,
    request: PromptSetConfigRequest,
    tenant: CurrentTenantContext = Depends(require_current_tenant("admin")),
    db: Session = Depends(get_db),
):
    try:
        prompt_set = project_service.configure_prompt_set(
            db,
            tenant_key=tenant.tenant_key,
            project_id=project_id,
            request=request,
        )
        if prompt_set is None:
            raise HTTPException(status_code=404, detail="Project not found")
        db.commit()
        return PromptSetConfigResponse(success=True, prompt_set=prompt_set)
    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Prompt set conflicts") from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to configure prompt set: {exc}",
        ) from exc
