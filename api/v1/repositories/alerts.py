from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


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
    return db.execute(
        text(
            """
            SELECT
              ms.tenant_key,
              ms.project_id,
              ms.analysis_run_id,
              ar.collection_job_id,
              ms.metric_date,
              ms.metric_name,
              ms.metric_definition_version,
              ms.metric_value,
              ms.brand_id,
              ms.brand_name,
              ms.platform,
              ms.keyword,
              ms.dimension_hash
            FROM metric_snapshots ms
            JOIN analysis_runs ar
              ON ar.tenant_key = ms.tenant_key
             AND ar.analysis_run_id = ms.analysis_run_id
            WHERE ms.tenant_key = :tenant_key
              AND ms.analysis_run_id = :analysis_run_id
            ORDER BY ms.metric_date ASC, ms.metric_name ASC, ms.id ASC
            """
        ),
        {"tenant_key": tenant_key, "analysis_run_id": analysis_run_id},
    ).mappings().all()


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
    return db.execute(
        text(
            """
            SELECT
              ms.metric_date,
              ms.metric_value,
              ms.analysis_run_id
            FROM metric_snapshots ms
            WHERE ms.tenant_key = :tenant_key
              AND ms.project_id = :project_id
              AND ms.metric_name = :metric_name
              AND ms.metric_definition_version = :metric_definition_version
              AND ms.dimension_hash = :dimension_hash
              AND ms.analysis_run_id != :analysis_run_id
              AND ms.metric_date < :metric_date
            ORDER BY ms.metric_date DESC, ms.generated_at DESC, ms.id DESC
            LIMIT 1
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "metric_name": metric_name,
            "metric_definition_version": metric_definition_version,
            "dimension_hash": dimension_hash,
            "metric_date": metric_date,
            "analysis_run_id": analysis_run_id,
        },
    ).mappings().first()


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
