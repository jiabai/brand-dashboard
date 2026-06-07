from __future__ import annotations

import datetime
import json
import uuid
from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from api.v1.models.schemas import GeneratedReportItem, GenerateProjectReportRequest
from api.v1.repositories import reports as report_repo


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def _new_report_id() -> str:
    return f"report_{uuid.uuid4().hex[:16]}"


def _json_dumps(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _json_loads(value: Any, default: dict[str, Any]) -> dict[str, Any]:
    if value is None:
        return default
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return default
        return parsed if isinstance(parsed, dict) else default
    return default


def _float_value(value: Any) -> float:
    if value is None:
        return 0.0
    return round(float(value), 6)


def _int_value(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def _date_string(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _datetime_string(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _build_core_metrics(rows: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    metric_sums: dict[tuple[str, str, str], dict[str, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    metric_weights: dict[tuple[str, str, str], dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    dimension_weights: dict[tuple[str, str, str], dict[tuple[Any, ...], int]] = defaultdict(dict)

    for row in rows:
        key = (
            str(row.get("brand_id") or ""),
            str(row.get("brand_name") or ""),
            str(row.get("metric_definition_version") or "brand_metrics_v1"),
        )
        groups.setdefault(
            key,
            {
                "brand_id": key[0],
                "brand_name": key[1] or None,
                "metric_definition_version": key[2],
            },
        )

        metric_name = str(row.get("metric_name") or "")
        if metric_name not in report_repo.CORE_REPORT_METRICS:
            continue
        weight = _int_value(row.get("analyzed_answer_count")) or 1
        metric_sums[key][metric_name] += _float_value(row.get("metric_value")) * weight
        metric_weights[key][metric_name] += weight

        dimension_key = (
            row.get("metric_date"),
            row.get("brand_id") or "",
            row.get("platform") or "",
            row.get("keyword") or "",
            row.get("metric_definition_version") or "brand_metrics_v1",
        )
        dimension_weights[key][dimension_key] = max(
            dimension_weights[key].get(dimension_key, 0),
            _int_value(row.get("analyzed_answer_count")),
        )

    results: list[dict[str, Any]] = []
    for key, base in groups.items():
        item = dict(base)
        item["analyzed_answer_count"] = sum(dimension_weights[key].values())
        for metric_name in report_repo.CORE_REPORT_METRICS:
            weight = metric_weights[key].get(metric_name, 0)
            if weight:
                item[metric_name] = round(metric_sums[key][metric_name] / weight, 6)
        results.append(item)

    return sorted(
        results,
        key=lambda item: (
            str(item.get("brand_name") or ""),
            str(item.get("brand_id") or ""),
        ),
    )


def _build_alert_snapshot(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    severity_counts: dict[str, int] = {}
    open_event_count = 0

    for row in rows:
        severity = str(row.get("severity") or "warning")
        event_status = str(row.get("event_status") or "open")
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        if event_status == "open":
            open_event_count += 1
        events.append(
            {
                "alert_event_id": row.get("alert_event_id"),
                "alert_rule_id": row.get("alert_rule_id"),
                "analysis_run_id": row.get("analysis_run_id"),
                "collection_job_id": row.get("collection_job_id"),
                "metric_date": _date_string(row.get("metric_date")),
                "metric_name": row.get("metric_name"),
                "metric_definition_version": row.get("metric_definition_version"),
                "brand_id": row.get("brand_id") or "",
                "brand_name": row.get("brand_name"),
                "platform": row.get("platform") or "",
                "keyword": row.get("keyword") or "",
                "previous_metric_date": _date_string(row.get("previous_metric_date")),
                "previous_value": (
                    _float_value(row.get("previous_value"))
                    if row.get("previous_value") is not None
                    else None
                ),
                "current_value": _float_value(row.get("current_value")),
                "delta_value": _float_value(row.get("delta_value")),
                "threshold_value": _float_value(row.get("threshold_value")),
                "severity": severity,
                "event_status": event_status,
                "title": row.get("title"),
                "message": row.get("message"),
                "triggered_at": _datetime_string(row.get("triggered_at")),
            }
        )

    return {
        "event_count": len(events),
        "open_event_count": open_event_count,
        "severity_counts": severity_counts,
        "events": events,
    }


def _report_item(row: Mapping[str, Any]) -> GeneratedReportItem:
    data = dict(row)
    data["summary"] = _json_loads(data.pop("summary_json", None), {})
    data["metrics"] = _json_loads(data.pop("metrics_json", None), {})
    data["alerts"] = _json_loads(data.pop("alerts_json", None), {})
    return GeneratedReportItem(**data)


def generate_project_report(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    generated_by: int | None,
    request: GenerateProjectReportRequest,
) -> GeneratedReportItem:
    if request.start_date > request.end_date:
        raise ValueError("start_date must be before or equal to end_date")

    generated_at = _now()
    report_id = request.report_id or _new_report_id()
    title = request.title or (
        f"Project report {request.start_date.isoformat()} to {request.end_date.isoformat()}"
    )
    metric_rows = report_repo.list_core_metric_rows(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    alert_rows = report_repo.list_alert_events_for_window(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )
    core_metrics = _build_core_metrics(metric_rows)
    alert_snapshot = _build_alert_snapshot(alert_rows)
    metrics_snapshot = {
        "metric_names": list(report_repo.CORE_REPORT_METRICS),
        "core_metrics": core_metrics,
    }
    summary = {
        "project_id": project_id,
        "report_type": request.report_type,
        "timeframe": request.timeframe,
        "data_window": {
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
        },
        "metric_count": len(metric_rows),
        "brand_count": len(core_metrics),
        "alert_event_count": alert_snapshot["event_count"],
        "generated_at": generated_at.isoformat(),
    }

    report_repo.insert_generated_report(
        db,
        tenant_key=tenant_key,
        report_id=report_id,
        project_id=project_id,
        report_type=request.report_type,
        title=title,
        timeframe=request.timeframe,
        start_date=request.start_date,
        end_date=request.end_date,
        status="generated",
        summary_json=_json_dumps(summary),
        metrics_json=_json_dumps(metrics_snapshot),
        alerts_json=_json_dumps(alert_snapshot),
        generated_by=generated_by,
        generated_at=generated_at,
    )
    row = report_repo.get_generated_report(
        db,
        tenant_key=tenant_key,
        report_id=report_id,
    )
    if row is None:
        raise RuntimeError("generated report could not be loaded")
    return _report_item(row)


def list_project_reports(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    limit: int = 50,
) -> list[GeneratedReportItem]:
    rows = report_repo.list_project_reports(
        db,
        tenant_key=tenant_key,
        project_id=project_id,
        limit=limit,
    )
    return [_report_item(row) for row in rows]
