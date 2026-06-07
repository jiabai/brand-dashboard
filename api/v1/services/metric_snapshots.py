from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from api.v1.repositories import analysis_runs
from api.v1.repositories import metric_snapshots as metric_snapshot_repo

DEFAULT_METRIC_DEFINITION_VERSION = "brand_metrics_v1"
METRIC_UNIT_RATIO = "ratio"
SIX_PLACES = Decimal("0.000001")


@dataclass(frozen=True)
class MetricSnapshotGenerationResult:
    status_code: int
    message: str
    analysis_run: object | None = None
    snapshot_count: int = 0
    metric_names: list[str] = field(default_factory=list)


def _now() -> datetime:
    return datetime.now(UTC)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    value = Decimal(numerator) / Decimal(denominator)
    return float(value.quantize(SIX_PLACES, rounding=ROUND_HALF_UP))


def _coverage_rate(succeeded: int, expected: int) -> float | None:
    if expected <= 0:
        return None
    return _ratio(succeeded, expected)


def _metric_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _dimension_hash(*, brand_id: str, platform: str, keyword: str) -> str:
    return _stable_hash(
        {
            "brand_id": brand_id,
            "keyword": keyword,
            "platform": platform,
        }
    )


def _snapshot_id(
    *,
    tenant_key: str,
    project_id: str,
    analysis_run_id: str,
    metric_date: str,
    metric_name: str,
    metric_definition_version: str,
    dimension_hash: str,
) -> str:
    digest = _stable_hash(
        {
            "analysis_run_id": analysis_run_id,
            "dimension_hash": dimension_hash,
            "metric_date": metric_date,
            "metric_definition_version": metric_definition_version,
            "metric_name": metric_name,
            "project_id": project_id,
            "tenant_key": tenant_key,
        }
    )
    return f"metric_snapshot_{digest[:32]}"


def _collection_job(db: Session, *, tenant_key: str, collection_job_id: str):
    return db.execute(
        text(
            """
            SELECT
              tenant_key,
              collection_job_id,
              project_id,
              expected_task_count,
              succeeded_task_count,
              failed_task_count
            FROM collection_jobs
            WHERE tenant_key = :tenant_key
              AND collection_job_id = :collection_job_id
            LIMIT 1
            """
        ),
        {
            "tenant_key": tenant_key,
            "collection_job_id": collection_job_id,
        },
    ).mappings().first()


def _project_brand_ids(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
) -> dict[str, str]:
    rows = db.execute(
        text(
            """
            SELECT brand_id, brand_name
            FROM project_brands
            WHERE tenant_key = :tenant_key
              AND project_id = :project_id
              AND status = 'active'
            ORDER BY id ASC
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
        },
    ).mappings().all()
    return {
        str(row["brand_name"]).strip(): str(row["brand_id"]).strip()
        for row in rows
        if str(row["brand_name"] or "").strip()
    }


def _brand_fact_dimensions(
    db: Session,
    *,
    tenant_key: str,
    analysis_run_id: str,
) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
              date AS metric_date,
              brand AS brand_name,
              platform,
              keyword,
              COUNT(DISTINCT conversation_id) AS analyzed_answer_count,
              COUNT(DISTINCT CASE WHEN is_mentioned = 1 THEN conversation_id END)
                AS mention_count,
              COUNT(DISTINCT CASE WHEN is_first_mentioned = 1 THEN conversation_id END)
                AS first_mention_count,
              COUNT(DISTINCT CASE WHEN is_top3_mentioned = 1 THEN conversation_id END)
                AS top3_mention_count,
              COUNT(DISTINCT CASE
                WHEN LOWER(sentiment_status) = 'positive' THEN conversation_id
              END) AS positive_count,
              COUNT(DISTINCT CASE
                WHEN LOWER(sentiment_status) = 'negative' THEN conversation_id
              END) AS negative_count,
              COUNT(DISTINCT CASE
                WHEN LOWER(sentiment_status) = 'neutral' THEN conversation_id
              END) AS neutral_count,
              COUNT(DISTINCT CASE
                WHEN LOWER(sentiment_status) NOT IN ('positive', 'negative', 'neutral')
                  THEN conversation_id
              END) AS unknown_count
            FROM qa_brand_state
            WHERE tenant_key = :tenant_key
              AND analysis_run_id = :analysis_run_id
            GROUP BY date, brand, platform, keyword
            ORDER BY date ASC, brand ASC, platform ASC, keyword ASC
            """
        ),
        {
            "tenant_key": tenant_key,
            "analysis_run_id": analysis_run_id,
        },
    ).mappings().all()
    return [dict(row) for row in rows]


def _reference_counts_by_dimension(
    db: Session,
    *,
    tenant_key: str,
    analysis_run_id: str,
) -> dict[tuple[str, str, str, str], int]:
    rows = db.execute(
        text(
            """
            SELECT
              date AS metric_date,
              brand AS brand_name,
              platform,
              keyword,
              COUNT(DISTINCT conversation_id) AS reference_answer_count
            FROM qa_reference
            WHERE tenant_key = :tenant_key
              AND analysis_run_id = :analysis_run_id
            GROUP BY date, brand, platform, keyword
            """
        ),
        {
            "tenant_key": tenant_key,
            "analysis_run_id": analysis_run_id,
        },
    ).mappings().all()
    return {
        (
            _metric_date(row["metric_date"]),
            str(row["brand_name"] or ""),
            str(row["platform"] or ""),
            str(row["keyword"] or ""),
        ): int(row["reference_answer_count"] or 0)
        for row in rows
    }


def _metric_rows_for_dimension(
    *,
    tenant_key: str,
    project_id: str,
    analysis_run_id: str,
    metric_definition_version: str,
    generated_at: datetime,
    collection_job: Any,
    analysis_run: Any,
    brand_id: str,
    brand_name: str,
    metric_date: str,
    platform: str,
    keyword: str,
    analyzed_answer_count: int,
    reference_answer_count: int,
    counts: dict[str, int],
) -> list[dict[str, Any]]:
    expected_task_count = int(collection_job["expected_task_count"] or 0)
    succeeded_task_count = int(collection_job["succeeded_task_count"] or 0)
    failed_task_count = int(collection_job["failed_task_count"] or 0)
    coverage_rate = _coverage_rate(succeeded_task_count, expected_task_count)
    dimension_hash = _dimension_hash(
        brand_id=brand_id,
        platform=platform,
        keyword=keyword,
    )
    metrics = {
        "mention_rate": _ratio(counts["mention_count"], analyzed_answer_count),
        "first_mention_rate": _ratio(
            counts["first_mention_count"],
            analyzed_answer_count,
        ),
        "top3_mention_rate": _ratio(
            counts["top3_mention_count"],
            analyzed_answer_count,
        ),
        "sentiment_positive_ratio": _ratio(
            counts["positive_count"],
            analyzed_answer_count,
        ),
        "sentiment_negative_ratio": _ratio(
            counts["negative_count"],
            analyzed_answer_count,
        ),
        "sentiment_neutral_ratio": _ratio(
            counts["neutral_count"],
            analyzed_answer_count,
        ),
        "sentiment_unknown_ratio": _ratio(
            counts["unknown_count"],
            analyzed_answer_count,
        ),
        "reference_rate": _ratio(reference_answer_count, analyzed_answer_count),
    }

    return [
        {
            "tenant_key": tenant_key,
            "snapshot_id": _snapshot_id(
                tenant_key=tenant_key,
                project_id=project_id,
                analysis_run_id=analysis_run_id,
                metric_date=metric_date,
                metric_name=metric_name,
                metric_definition_version=metric_definition_version,
                dimension_hash=dimension_hash,
            ),
            "project_id": project_id,
            "analysis_run_id": analysis_run_id,
            "metric_date": metric_date,
            "brand_id": brand_id,
            "brand_name": brand_name,
            "platform": platform,
            "keyword": keyword,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "metric_unit": METRIC_UNIT_RATIO,
            "metric_definition_version": metric_definition_version,
            "expected_task_count": expected_task_count,
            "succeeded_task_count": succeeded_task_count,
            "failed_task_count": failed_task_count,
            "analyzed_answer_count": analyzed_answer_count,
            "coverage_rate": coverage_rate,
            "source_watermark": analysis_run.input_watermark,
            "dimension_hash": dimension_hash,
            "generated_at": generated_at,
        }
        for metric_name, metric_value in metrics.items()
    ]


def generate_metric_snapshots_for_analysis_run(
    db: Session,
    *,
    tenant_key: str,
    analysis_run_id: str,
    metric_definition_version: str = DEFAULT_METRIC_DEFINITION_VERSION,
    generated_at: datetime | None = None,
) -> MetricSnapshotGenerationResult:
    run = analysis_runs.get_analysis_run(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    )
    if run is None:
        return MetricSnapshotGenerationResult(404, "analysis run 不存在")
    if run.status != "succeeded":
        return MetricSnapshotGenerationResult(
            409,
            "只有 succeeded analysis run 可以生成指标快照",
            analysis_run=run,
        )

    collection_job = _collection_job(
        db,
        tenant_key=tenant_key,
        collection_job_id=run.collection_job_id,
    )
    if collection_job is None:
        return MetricSnapshotGenerationResult(
            404,
            "analysis run 对应的采集批次不存在",
            analysis_run=run,
        )

    fact_dimensions = _brand_fact_dimensions(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    )
    if not fact_dimensions:
        return MetricSnapshotGenerationResult(
            422,
            "analysis run 没有可生成快照的品牌事实",
            analysis_run=run,
        )

    brand_ids = _project_brand_ids(
        db,
        tenant_key=tenant_key,
        project_id=run.project_id,
    )
    reference_counts = _reference_counts_by_dimension(
        db,
        tenant_key=tenant_key,
        analysis_run_id=analysis_run_id,
    )
    snapshot_rows: list[dict[str, Any]] = []
    snapshot_generated_at = generated_at or _now()

    for dimension in fact_dimensions:
        analyzed_answer_count = int(dimension["analyzed_answer_count"] or 0)
        if analyzed_answer_count <= 0:
            continue

        metric_date = _metric_date(dimension["metric_date"])
        brand_name = str(dimension["brand_name"] or "")
        platform = str(dimension["platform"] or "")
        keyword = str(dimension["keyword"] or "")
        reference_answer_count = reference_counts.get(
            (metric_date, brand_name, platform, keyword),
            0,
        )
        brand_id = brand_ids.get(brand_name, brand_name)
        counts = {
            "mention_count": int(dimension["mention_count"] or 0),
            "first_mention_count": int(dimension["first_mention_count"] or 0),
            "top3_mention_count": int(dimension["top3_mention_count"] or 0),
            "positive_count": int(dimension["positive_count"] or 0),
            "negative_count": int(dimension["negative_count"] or 0),
            "neutral_count": int(dimension["neutral_count"] or 0),
            "unknown_count": int(dimension["unknown_count"] or 0),
        }
        snapshot_rows.extend(
            _metric_rows_for_dimension(
                tenant_key=tenant_key,
                project_id=run.project_id,
                analysis_run_id=analysis_run_id,
                metric_definition_version=metric_definition_version,
                generated_at=snapshot_generated_at,
                collection_job=collection_job,
                analysis_run=run,
                brand_id=brand_id,
                brand_name=brand_name,
                metric_date=metric_date,
                platform=platform,
                keyword=keyword,
                analyzed_answer_count=analyzed_answer_count,
                reference_answer_count=reference_answer_count,
                counts=counts,
            )
        )

    inserted_count = metric_snapshot_repo.upsert_metric_snapshots(db, snapshot_rows)
    db.commit()

    return MetricSnapshotGenerationResult(
        200,
        "指标快照已生成",
        analysis_run=run,
        snapshot_count=inserted_count,
        metric_names=sorted({row["metric_name"] for row in snapshot_rows}),
    )
