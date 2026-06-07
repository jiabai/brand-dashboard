from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

CORE_REPORT_METRICS = (
    "mention_rate",
    "first_mention_rate",
    "top3_mention_rate",
    "sentiment_negative_ratio",
    "reference_rate",
)


def list_core_metric_rows(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    start_date: date,
    end_date: date,
    metric_definition_version: str = "brand_metrics_v1",
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              metric_date,
              brand_id,
              brand_name,
              platform,
              keyword,
              metric_name,
              metric_value,
              metric_definition_version,
              analyzed_answer_count
            FROM metric_snapshots
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
              AND metric_definition_version = :metric_definition_version
              AND metric_date BETWEEN :start_date AND :end_date
              AND metric_name IN (
                'mention_rate',
                'first_mention_rate',
                'top3_mention_rate',
                'sentiment_negative_ratio',
                'reference_rate'
              )
            ORDER BY
              brand_name ASC,
              brand_id ASC,
              metric_definition_version ASC,
              metric_date ASC,
              platform ASC,
              keyword ASC,
              metric_name ASC,
              id ASC
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "start_date": start_date,
            "end_date": end_date,
            "metric_definition_version": metric_definition_version,
        },
    ).mappings().all()


def list_alert_events_for_window(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    start_date: date,
    end_date: date,
    limit: int = 50,
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              alert_event_id,
              alert_rule_id,
              analysis_run_id,
              collection_job_id,
              metric_date,
              metric_name,
              metric_definition_version,
              brand_id,
              brand_name,
              platform,
              keyword,
              previous_metric_date,
              previous_value,
              current_value,
              delta_value,
              threshold_value,
              severity,
              event_status,
              title,
              message,
              triggered_at
            FROM alert_events
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
              AND metric_date BETWEEN :start_date AND :end_date
            ORDER BY triggered_at DESC, id DESC
            LIMIT :limit
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
        },
    ).mappings().all()


def insert_generated_report(
    db: Session,
    *,
    tenant_key: str,
    report_id: str,
    project_id: str,
    report_type: str,
    title: str,
    timeframe: str,
    start_date: date,
    end_date: date,
    status: str,
    summary_json: str,
    metrics_json: str,
    alerts_json: str,
    generated_by: int | None,
    generated_at: datetime,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO generated_reports
              (
                tenant_key,
                report_id,
                project_id,
                report_type,
                title,
                timeframe,
                start_date,
                end_date,
                status,
                summary_json,
                metrics_json,
                alerts_json,
                generated_by,
                generated_at,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                :report_id,
                :project_id,
                :report_type,
                :title,
                :timeframe,
                :start_date,
                :end_date,
                :status,
                :summary_json,
                :metrics_json,
                :alerts_json,
                :generated_by,
                :generated_at,
                :generated_at,
                :generated_at
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "report_id": report_id,
            "project_id": project_id,
            "report_type": report_type,
            "title": title,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "summary_json": summary_json,
            "metrics_json": metrics_json,
            "alerts_json": alerts_json,
            "generated_by": generated_by,
            "generated_at": generated_at,
        },
    )


def get_generated_report(
    db: Session,
    *,
    tenant_key: str,
    report_id: str,
):
    return db.execute(
        text(
            """
            SELECT
              tenant_key,
              report_id,
              project_id,
              report_type,
              title,
              timeframe,
              start_date,
              end_date,
              status,
              summary_json,
              metrics_json,
              alerts_json,
              generated_by,
              generated_at,
              created_at,
              updated_at
            FROM generated_reports
            WHERE tenant_key = :tenant_key
              AND report_id = :report_id
            LIMIT 1
            """
        ),
        {"tenant_key": tenant_key, "report_id": report_id},
    ).mappings().first()


def list_project_reports(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    limit: int = 50,
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              tenant_key,
              report_id,
              project_id,
              report_type,
              title,
              timeframe,
              start_date,
              end_date,
              status,
              summary_json,
              metrics_json,
              alerts_json,
              generated_by,
              generated_at,
              created_at,
              updated_at
            FROM generated_reports
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
            ORDER BY generated_at DESC, id DESC
            LIMIT :limit
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "limit": limit,
        },
    ).mappings().all()
