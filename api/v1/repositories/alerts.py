from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from api.v1.repositories.fact_metrics import list_project_fact_metric_rows


def get_analysis_run_context(
    db: Session,
    *,
    tenant_key: str,
    analysis_run_id: str,
):
    return db.execute(
        text(
            """
            SELECT
              ar.analysis_run_id,
              ar.project_id,
              ar.collection_job_id,
              ar.status,
              ar.finished_at
            FROM analysis_runs ar
            WHERE ar.tenant_key = :tenant_key
              AND ar.analysis_run_id = :analysis_run_id
            LIMIT 1
            """
        ),
        {"tenant_key": tenant_key, "analysis_run_id": analysis_run_id},
    ).mappings().first()


def list_current_metric_rows(
    db: Session,
    *,
    tenant_key: str,
    analysis_run_id: str,
) -> list[Mapping[str, Any]]:
    run = get_analysis_run_context(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    )
    if run is None:
        return []

    date_range = db.execute(
        text(
            """
            SELECT
              MIN(date) AS start_date,
              MAX(date) AS end_date
            FROM qa_brand_state
            WHERE tenant_key = :tenant_key
              AND analysis_run_id = :analysis_run_id
            """
        ),
        {"tenant_key": tenant_key, "analysis_run_id": analysis_run_id},
    ).mappings().one()
    if date_range["start_date"] is None or date_range["end_date"] is None:
        return []

    return list_project_fact_metric_rows(
        db,
        tenant_key=tenant_key,
        project_id=run["project_id"],
        start_date=date_range["start_date"],
        end_date=date_range["end_date"],
        analysis_run_id=analysis_run_id,
    )


def list_active_rules_for_project(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              tenant_key,
              alert_rule_id,
              project_id,
              name,
              rule_type,
              metric_name,
              metric_definition_version,
              brand_id,
              brand_name,
              platform,
              keyword,
              threshold_value,
              severity,
              status,
              created_at,
              updated_at
            FROM alert_rules
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
              AND status = 'active'
            ORDER BY id ASC
            """
        ),
        {"tenant_key": tenant_key, "project_id": project_id},
    ).mappings().all()


def get_previous_metric_row(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    metric_name: str,
    metric_definition_version: str,
    dimension_hash: str,
    metric_date: Any,
    analysis_run_id: str,
):
    rows = list_project_fact_metric_rows(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        start_date=date(1900, 1, 1),
        end_date=metric_date,
    )
    candidates = [
        row
        for row in rows
        if row["metric_name"] == metric_name
        and row["metric_definition_version"] == metric_definition_version
        and row["dimension_hash"] == dimension_hash
        and row["analysis_run_id"] != analysis_run_id
        and str(row["metric_date"]) < str(metric_date)
    ]
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda row: (str(row["metric_date"]), str(row["analysis_run_id"])),
        reverse=True,
    )[0]


def alert_event_exists(
    db: Session,
    *,
    tenant_key: str,
    alert_rule_id: str,
    analysis_run_id: str,
    metric_date: Any,
    dimension_hash: str,
) -> bool:
    value = db.execute(
        text(
            """
            SELECT 1
            FROM alert_events
            WHERE tenant_key = :tenant_key
              AND alert_rule_id = :alert_rule_id
              AND analysis_run_id = :analysis_run_id
              AND metric_date = :metric_date
              AND dimension_hash = :dimension_hash
            LIMIT 1
            """
        ),
        {
            "tenant_key": tenant_key,
            "alert_rule_id": alert_rule_id,
            "analysis_run_id": analysis_run_id,
            "metric_date": metric_date,
            "dimension_hash": dimension_hash,
        },
    ).scalar_one_or_none()
    return value is not None


def insert_alert_event(db: Session, event: Mapping[str, Any]) -> None:
    db.execute(
        text(
            """
            INSERT INTO alert_events
              (
                tenant_key,
                alert_event_id,
                alert_rule_id,
                project_id,
                analysis_run_id,
                collection_job_id,
                metric_date,
                metric_name,
                metric_definition_version,
                brand_id,
                brand_name,
                platform,
                keyword,
                dimension_hash,
                previous_metric_date,
                previous_value,
                current_value,
                delta_value,
                threshold_value,
                severity,
                event_status,
                title,
                message,
                triggered_at,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                :alert_event_id,
                :alert_rule_id,
                :project_id,
                :analysis_run_id,
                :collection_job_id,
                :metric_date,
                :metric_name,
                :metric_definition_version,
                :brand_id,
                :brand_name,
                :platform,
                :keyword,
                :dimension_hash,
                :previous_metric_date,
                :previous_value,
                :current_value,
                :delta_value,
                :threshold_value,
                :severity,
                :event_status,
                :title,
                :message,
                :triggered_at,
                :triggered_at,
                :triggered_at
              )
            """
        ),
        dict(event),
    )


def list_project_rules(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              tenant_key,
              alert_rule_id,
              project_id,
              name,
              rule_type,
              metric_name,
              metric_definition_version,
              brand_id,
              brand_name,
              platform,
              keyword,
              threshold_value,
              severity,
              status,
              created_at,
              updated_at
            FROM alert_rules
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
            ORDER BY
              CASE status WHEN 'active' THEN 1 ELSE 2 END,
              id ASC
            """
        ),
        {"tenant_key": tenant_key, "project_id": project_id},
    ).mappings().all()


def list_project_events(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    limit: int = 100,
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              tenant_key,
              alert_event_id,
              alert_rule_id,
              project_id,
              analysis_run_id,
              collection_job_id,
              metric_date,
              metric_name,
              metric_definition_version,
              brand_id,
              brand_name,
              platform,
              keyword,
              dimension_hash,
              previous_metric_date,
              previous_value,
              current_value,
              delta_value,
              threshold_value,
              severity,
              event_status,
              title,
              message,
              triggered_at,
              created_at,
              updated_at
            FROM alert_events
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
            ORDER BY triggered_at DESC, id DESC
            LIMIT :limit
            """
        ),
        {"tenant_key": tenant_key, "project_id": project_id, "limit": limit},
    ).mappings().all()
