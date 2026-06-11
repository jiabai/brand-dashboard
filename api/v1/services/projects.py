import datetime
import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from api.v1.models.schemas import (
    AlertEventItem,
    AlertRuleItem,
    GeneratedReportItem,
    GenerateProjectReportRequest,
    MonitoringProjectCreate,
    MonitoringProjectDetail,
    MonitoringProjectSummary,
    ProjectAlertsResponse,
    ProjectBrandConfigRequest,
    ProjectBrandResponse,
    ProjectDataQualityResponse,
    ProjectReportListResponse,
    PromptItemResponse,
    PromptSetConfigRequest,
    PromptSetResponse,
)
from api.v1.repositories import alerts as alert_repo
from api.v1.repositories import projects as project_repo
from api.v1.services import data_quality as data_quality_service
from api.v1.services import reports as report_service


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def _new_project_id() -> str:
    return f"proj_{uuid.uuid4().hex[:16]}"


def _aliases_from_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    return []


def _project_summary(row: Any) -> MonitoringProjectSummary:
    return MonitoringProjectSummary(**dict(row))


def _brand_response(row: Any) -> ProjectBrandResponse:
    data = dict(row)
    data["aliases"] = _aliases_from_value(data.get("aliases"))
    return ProjectBrandResponse(**data)


def _prompt_item_response(row: Any) -> PromptItemResponse:
    return PromptItemResponse(**dict(row))


def _prompt_set_response(
    db: Session,
    *,
    tenant_key: str,
    row: Any,
) -> PromptSetResponse:
    data = dict(row)
    items = project_repo.list_prompt_items(
        db,
        tenant_key=tenant_key,
        prompt_set_id=data["prompt_set_id"],
    )
    data["items"] = [_prompt_item_response(item) for item in items]
    return PromptSetResponse(**data)


def list_project_summaries(
    db: Session,
    *,
    tenant_key: str,
) -> list[MonitoringProjectSummary]:
    rows = project_repo.list_projects(db, tenant_key=tenant_key)
    return [_project_summary(row) for row in rows]


def get_project_detail(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
) -> MonitoringProjectDetail | None:
    project = project_repo.get_project(db, tenant_key=tenant_key, project_id=project_id)
    if not project:
        return None

    project_data = dict(project)
    brands = project_repo.list_project_brands(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
    )
    prompt_sets = project_repo.list_prompt_sets(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
    )
    project_data["brands"] = [_brand_response(row) for row in brands]
    project_data["prompt_sets"] = [
        _prompt_set_response(db, tenant_key=tenant_key, row=row)
        for row in prompt_sets
    ]
    return MonitoringProjectDetail(**project_data)


def create_project(
    db: Session,
    *,
    tenant_key: str,
    created_by: int,
    request: MonitoringProjectCreate,
) -> MonitoringProjectDetail:
    project_id = request.project_id or _new_project_id()
    project_repo.create_project(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        name=request.name,
        industry=request.industry,
        category=request.category,
        status=request.status,
        created_by=created_by,
        now=_now(),
    )
    detail = get_project_detail(db, tenant_key=tenant_key, project_id=project_id)
    if detail is None:
        raise RuntimeError("created project could not be loaded")
    return detail


def configure_project_brand(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    request: ProjectBrandConfigRequest,
) -> ProjectBrandResponse | None:
    if not project_repo.get_project(db, tenant_key=tenant_key, project_id=project_id):
        return None
    project_repo.upsert_project_brand(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        brand_id=request.brand_id,
        brand_name=request.brand_name,
        role=request.role,
        aliases=request.aliases,
        status=request.status,
        now=_now(),
    )
    row = project_repo.get_project_brand(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        brand_id=request.brand_id,
        role=request.role,
    )
    if row is None:
        raise RuntimeError("project brand could not be loaded")
    return _brand_response(row)


def configure_prompt_set(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    request: PromptSetConfigRequest,
) -> PromptSetResponse | None:
    if not project_repo.get_project(db, tenant_key=tenant_key, project_id=project_id):
        return None

    now = _now()
    project_repo.upsert_prompt_set(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        prompt_set_id=request.prompt_set_id,
        version=request.version,
        name=request.name,
        status=request.status,
        now=now,
    )
    for item in request.items:
        project_repo.upsert_prompt_item(
            db,
            tenant_key=tenant_key,
            prompt_set_id=request.prompt_set_id,
            prompt_item_id=item.prompt_item_id,
            keyword=item.keyword,
            query_content=item.query_content,
            status=item.status,
            sort_order=item.sort_order,
            now=now,
        )

    row = project_repo.get_prompt_set(
        db,
        tenant_key=tenant_key,
        prompt_set_id=request.prompt_set_id,
    )
    if row is None:
        raise RuntimeError("prompt set could not be loaded")
    return _prompt_set_response(db, tenant_key=tenant_key, row=row)


def get_project_alerts(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    event_limit: int = 100,
) -> ProjectAlertsResponse | None:
    if project_repo.get_project(db, tenant_key=tenant_key, project_id=project_id) is None:
        return None

    rule_rows = alert_repo.list_project_rules(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
    )
    event_rows = alert_repo.list_project_events(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        limit=event_limit,
    )
    rules = [AlertRuleItem(**dict(row)) for row in rule_rows]
    events = [AlertEventItem(**dict(row)) for row in event_rows]
    return ProjectAlertsResponse(
        success=True,
        project_id=project_id,
        rule_count=len(rules),
        event_count=len(events),
        rules=rules,
        events=events,
    )


def get_project_data_quality(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
) -> ProjectDataQualityResponse | None:
    if project_repo.get_project(db, tenant_key=tenant_key, project_id=project_id) is None:
        return None
    return data_quality_service.get_project_data_quality(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
    )


def generate_project_report(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    generated_by: int | None,
    request: GenerateProjectReportRequest,
) -> GeneratedReportItem | None:
    if project_repo.get_project(db, tenant_key=tenant_key, project_id=project_id) is None:
        return None
    return report_service.generate_project_report(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        generated_by=generated_by,
        request=request,
    )


def list_project_reports(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    limit: int = 50,
) -> ProjectReportListResponse | None:
    if project_repo.get_project(db, tenant_key=tenant_key, project_id=project_id) is None:
        return None
    reports = report_service.list_project_reports(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        limit=limit,
    )
    return ProjectReportListResponse(
        success=True,
        project_id=project_id,
        count=len(reports),
        reports=reports,
    )


def list_project_collection_job_entries(
    db: Session, *, tenant_key: str, project_id: str
) -> dict[str, Any]:
    rows = project_repo.list_project_collection_jobs(
        db, tenant_key=tenant_key, project_id=project_id
    )
    target_brand = project_repo.get_project_target_brand(
        db, tenant_key=tenant_key, project_id=project_id
    )
    collection_jobs = [
        {
            "collection_job_id": row["collection_job_id"],
            "source_job_id": row["source_job_id"],
            "status": row["status"],
            "window_start": str(row["window_start"]) if row["window_start"] is not None else None,
            "window_end": str(row["window_end"]) if row["window_end"] is not None else None,
            "expected_task_count": row["expected_task_count"] or 0,
            "succeeded_task_count": row["succeeded_task_count"] or 0,
            "failed_task_count": row["failed_task_count"] or 0,
        }
        for row in rows
    ]
    return {"target_brand": target_brand, "collection_jobs": collection_jobs}
