from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from api.v1.models.schemas import (
    ProjectDataQualityResponse,
    ProjectDataQualitySummary,
    ProjectFailedCollectionTaskItem,
    ProjectMetricCoverageData,
    ProjectRecomputeAction,
    ProjectStaleAnalysisRunItem,
)
from api.v1.repositories import data_quality as data_quality_repo


def _int_value(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def _bool_value(value: Any) -> bool:
    return bool(_int_value(value))


def _recompute_endpoint(analysis_run_id: str) -> str:
    return f"/api/v1/analysis-runs/{analysis_run_id}/retry"


def _build_metric_coverage(
    rows: list[Mapping[str, Any]],
) -> ProjectMetricCoverageData:
    if not rows:
        return ProjectMetricCoverageData(
            data_source="empty",
            snapshot_status="missing",
            metric_definition_version="brand_metrics_v1",
            metric_snapshot_count=0,
            metric_dimension_count=0,
        )

    latest = rows[0]
    dimensions: dict[tuple[Any, Any], int] = {}
    coverage_values = [
        float(row["coverage_rate"])
        for row in rows
        if row.get("coverage_rate") is not None
    ]
    for row in rows:
        dimension_key = (row.get("metric_date"), row.get("dimension_hash"))
        dimensions[dimension_key] = max(
            dimensions.get(dimension_key, 0),
            _int_value(row.get("analyzed_answer_count")),
        )

    return ProjectMetricCoverageData(
        data_source="metric_snapshot",
        snapshot_status="available",
        metric_definition_version=latest.get("metric_definition_version") or "brand_metrics_v1",
        analysis_run_id=latest.get("analysis_run_id"),
        metric_generated_at=latest.get("generated_at"),
        metric_coverage_rate=round(min(coverage_values), 6) if coverage_values else None,
        metric_expected_task_count=max(_int_value(row.get("expected_task_count")) for row in rows),
        metric_succeeded_task_count=max(
            _int_value(row.get("succeeded_task_count")) for row in rows
        ),
        metric_failed_task_count=max(_int_value(row.get("failed_task_count")) for row in rows),
        metric_analyzed_answer_count=sum(dimensions.values()),
        metric_snapshot_count=len(rows),
        metric_dimension_count=len(dimensions),
    )


def get_project_data_quality(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    failed_task_limit: int = 100,
    stale_run_limit: int = 100,
) -> ProjectDataQualityResponse:
    failed_rows = data_quality_repo.list_failed_collection_tasks(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        limit=failed_task_limit,
    )
    stale_rows = data_quality_repo.list_stale_analysis_runs(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        limit=stale_run_limit,
    )
    metric_rows = data_quality_repo.list_metric_snapshot_quality_rows(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
    )

    failed_tasks = [
        ProjectFailedCollectionTaskItem(
            collection_task_id=row["collection_task_id"],
            collection_job_id=row["collection_job_id"],
            platform=row["platform"],
            keyword=row.get("keyword"),
            query_content=row["query_content"],
            status=row["status"],
            attempt_count=_int_value(row.get("attempt_count")),
            max_attempts=_int_value(row.get("max_attempts")),
            can_retry=_bool_value(row.get("can_retry")),
            last_error_code=row.get("last_error_code"),
            last_error_message=row.get("last_error_message"),
            lease_owner=row.get("lease_owner"),
            updated_at=row["updated_at"],
        )
        for row in failed_rows
    ]
    stale_runs = [
        ProjectStaleAnalysisRunItem(
            analysis_run_id=row["analysis_run_id"],
            collection_job_id=row["collection_job_id"],
            status=row["status"],
            stale_at=row.get("stale_at"),
            error_code=row.get("error_code"),
            error_message=row.get("error_message"),
            can_recompute=True,
            recompute_endpoint=_recompute_endpoint(row["analysis_run_id"]),
        )
        for row in stale_rows
    ]
    recompute_actions = [
        ProjectRecomputeAction(
            action_type="retry_analysis_run",
            analysis_run_id=row["analysis_run_id"],
            label=f"Retry analysis run {row['analysis_run_id']}",
            method="POST",
            endpoint=_recompute_endpoint(row["analysis_run_id"]),
            enabled=True,
        )
        for row in stale_rows
    ]
    metric_coverage = _build_metric_coverage(metric_rows)
    summary = ProjectDataQualitySummary(
        failed_collection_task_count=len(failed_tasks),
        retryable_failed_collection_task_count=sum(1 for item in failed_tasks if item.can_retry),
        stale_analysis_run_count=len(stale_runs),
        recomputable_analysis_run_count=sum(1 for item in stale_runs if item.can_recompute),
        metric_snapshot_count=metric_coverage.metric_snapshot_count,
        metric_dimension_count=metric_coverage.metric_dimension_count,
        metric_coverage_rate=metric_coverage.metric_coverage_rate,
    )

    return ProjectDataQualityResponse(
        success=True,
        project_id=project_id,
        summary=summary,
        failed_collection_tasks=failed_tasks,
        stale_analysis_runs=stale_runs,
        metric_coverage=metric_coverage,
        recompute_actions=recompute_actions,
    )
