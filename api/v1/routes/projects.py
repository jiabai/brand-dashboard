from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.v1.dependencies.auth import (
    CurrentTenantContext,
    CurrentUser,
    get_current_tenant,
    get_current_user,
    require_current_tenant,
)
from api.v1.models.schemas import (
    MonitoringProjectCreate,
    ProjectBrandConfigRequest,
    ProjectBrandConfigResponse,
    ProjectListResponse,
    ProjectResponse,
    PromptSetConfigRequest,
    PromptSetConfigResponse,
)
from api.v1.repositories.connection import get_db
from api.v1.services import projects as project_service

router = APIRouter()


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    tenant: CurrentTenantContext = Depends(get_current_tenant),
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
    tenant: CurrentTenantContext = Depends(get_current_tenant),
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
