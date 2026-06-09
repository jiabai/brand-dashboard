from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from api.v1.repositories import alerts as alert_repo


@dataclass(frozen=True)
class AlertEvaluationResult:
    status_code: int
    message: str
    analysis_run_id: str | None = None
    matched_rule_count: int = 0
    created_event_count: int = 0


def _now() -> datetime:
    return datetime.now(UTC)


def _stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _event_id(
    *,
    tenant_key: str,
    alert_rule_id: str,
    analysis_run_id: str,
    metric_date: Any,
    dimension_hash: str,
) -> str:
    digest = _stable_hash(
        {
            "alert_rule_id": alert_rule_id,
            "analysis_run_id": analysis_run_id,
            "dimension_hash": dimension_hash,
            "metric_date": metric_date,
            "tenant_key": tenant_key,
        }
    )
    return f"alert_event_{digest[:32]}"


def _decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value or 0))


def _matches_dimension(rule: Any, metric: Any) -> bool:
    return (
        str(rule["metric_name"]) == str(metric["metric_name"])
        and str(rule["metric_definition_version"])
        == str(metric["metric_definition_version"])
        and str(rule["brand_id"] or "") == str(metric["brand_id"] or "")
        and str(rule["platform"] or "") == str(metric["platform"] or "")
        and str(rule["keyword"] or "") == str(metric["keyword"] or "")
    )


def _delta_for_rule(rule_type: str, previous_value: Decimal, current_value: Decimal):
    if rule_type == "metric_drop":
        return previous_value - current_value
    if rule_type == "metric_rise":
        return current_value - previous_value
    if rule_type == "metric_change":
        return abs(current_value - previous_value)
    return Decimal("0")


def _metric_label(metric_name: str) -> str:
    labels = {
        "mention_rate": "提及率",
        "sentiment_negative_ratio": "负面情绪占比",
        "reference_rate": "信源引用率",
    }
    return labels.get(metric_name, metric_name)


def _rule_action_label(rule_type: str) -> str:
    labels = {
        "metric_drop": "下降",
        "metric_rise": "上升",
        "metric_change": "变化",
    }
    return labels.get(rule_type, "变化")


def _event_title(rule: Any, metric: Any) -> str:
    brand_name = str(metric["brand_name"] or rule["brand_name"] or "全部品牌")
    metric_label = _metric_label(str(rule["metric_name"]))
    action_label = _rule_action_label(str(rule["rule_type"]))
    return f"{brand_name}{metric_label}{action_label}"


def _event_message(rule: Any, metric: Any, previous: Any, delta: Decimal) -> str:
    current_value = _decimal(metric["metric_value"])
    previous_value = _decimal(previous["metric_value"])
    return (
        f"{_metric_label(str(rule['metric_name']))}从 {previous_value:.4f} "
        f"变为 {current_value:.4f}，变化幅度 {delta:.4f}，"
        f"已达到阈值 {_decimal(rule['threshold_value']):.4f}。"
    )


def evaluate_alert_rules_for_analysis_run(
    db: Session,
    *,
    tenant_key: str,
    analysis_run_id: str,
    triggered_at: datetime | None = None,
) -> AlertEvaluationResult:
    run = alert_repo.get_analysis_run_context(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    )
    if run is None:
        return AlertEvaluationResult(
            status_code=404,
            message="analysis run 不存在",
            analysis_run_id=analysis_run_id,
        )
    if run["status"] != "succeeded":
        return AlertEvaluationResult(
            status_code=409,
            message="只有 succeeded analysis run 可以触发告警评估",
            analysis_run_id=analysis_run_id,
        )

    metric_rows = alert_repo.list_current_metric_rows(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    )
    if not metric_rows:
        return AlertEvaluationResult(
            status_code=422,
            message="analysis run 没有可评估的事实指标",
            analysis_run_id=analysis_run_id,
        )

    rules = alert_repo.list_active_rules_for_project(
        db,
        tenant_key=tenant_key,
        project_id=run["project_id"],
    )
    matched_rule_count = 0
    created_event_count = 0
    event_time = triggered_at or _now()

    for rule in rules:
        for metric in metric_rows:
            if not _matches_dimension(rule, metric):
                continue
            previous = alert_repo.get_previous_metric_row(
                db,
                tenant_key=tenant_key,
                project_id=metric["project_id"],
                metric_name=metric["metric_name"],
                metric_definition_version=metric["metric_definition_version"],
                dimension_hash=metric["dimension_hash"],
                metric_date=metric["metric_date"],
                analysis_run_id=analysis_run_id,
            )
            if previous is None:
                continue

            matched_rule_count += 1
            delta = _delta_for_rule(
                str(rule["rule_type"]),
                _decimal(previous["metric_value"]),
                _decimal(metric["metric_value"]),
            )
            threshold = _decimal(rule["threshold_value"])
            if delta < threshold:
                continue
            if alert_repo.alert_event_exists(
                db,
                tenant_key=tenant_key,
                alert_rule_id=rule["alert_rule_id"],
                analysis_run_id=analysis_run_id,
                metric_date=metric["metric_date"],
                dimension_hash=metric["dimension_hash"],
            ):
                continue

            alert_repo.insert_alert_event(
                db,
                {
                    "tenant_key": tenant_key,
                    "alert_event_id": _event_id(
                        tenant_key=tenant_key,
                        alert_rule_id=rule["alert_rule_id"],
                        analysis_run_id=analysis_run_id,
                        metric_date=metric["metric_date"],
                        dimension_hash=metric["dimension_hash"],
                    ),
                    "alert_rule_id": rule["alert_rule_id"],
                    "project_id": metric["project_id"],
                    "analysis_run_id": analysis_run_id,
                    "collection_job_id": metric["collection_job_id"],
                    "metric_date": metric["metric_date"],
                    "metric_name": metric["metric_name"],
                    "metric_definition_version": metric["metric_definition_version"],
                    "brand_id": metric["brand_id"] or "",
                    "brand_name": metric["brand_name"],
                    "platform": metric["platform"] or "",
                    "keyword": metric["keyword"] or "",
                    "dimension_hash": metric["dimension_hash"],
                    "previous_metric_date": previous["metric_date"],
                    "previous_value": previous["metric_value"],
                    "current_value": metric["metric_value"],
                    "delta_value": float(delta),
                    "threshold_value": float(threshold),
                    "severity": rule["severity"],
                    "event_status": "open",
                    "title": _event_title(rule, metric),
                    "message": _event_message(rule, metric, previous, delta),
                    "triggered_at": event_time,
                },
            )
            created_event_count += 1

    db.commit()
    return AlertEvaluationResult(
        status_code=200,
        message="告警规则评估完成",
        analysis_run_id=analysis_run_id,
        matched_rule_count=matched_rule_count,
        created_event_count=created_event_count,
    )
