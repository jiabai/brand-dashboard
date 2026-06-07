from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text

SENTIMENT_STATUSES = ("positive", "negative", "neutral", "unknown")
SENTIMENT_METRIC_NAMES = {
    "positive": "sentiment_positive_ratio",
    "negative": "sentiment_negative_ratio",
    "neutral": "sentiment_neutral_ratio",
    "unknown": "sentiment_unknown_ratio",
}


def _serialize_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _latest_run_cte() -> str:
    return """
    WITH latest_run AS (
        SELECT ar.analysis_run_id
        FROM analysis_runs ar
        JOIN collection_jobs cj
          ON cj.tenant_key = ar.tenant_key
         AND cj.collection_job_id = ar.collection_job_id
        WHERE ar.tenant_key = :tenant_key
          AND ar.status = 'succeeded'
          AND (
            ar.collection_job_id = :job_id
            OR cj.source_job_id = :job_id
          )
          AND EXISTS (
            SELECT 1
            FROM metric_snapshots ms_exists
            WHERE ms_exists.tenant_key = ar.tenant_key
              AND ms_exists.analysis_run_id = ar.analysis_run_id
              AND ms_exists.metric_definition_version = :metric_definition_version
              AND ms_exists.metric_name IN (
                'sentiment_positive_ratio',
                'sentiment_negative_ratio',
                'sentiment_neutral_ratio',
                'sentiment_unknown_ratio'
              )
          )
        ORDER BY ar.finished_at DESC, ar.updated_at DESC, ar.id DESC
        LIMIT 1
    )
    """


def _base_params(
    *,
    tenant_key: str,
    job_id: str,
    start_date: date,
    end_date: date,
    brand: str | None,
    platform: str | None,
    keyword: str | None,
    metric_definition_version: str = "brand_metrics_v1",
) -> dict[str, Any]:
    return {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "start_date": start_date,
        "end_date": end_date,
        "brand": brand,
        "platform": platform,
        "keyword": keyword,
        "metric_definition_version": metric_definition_version,
    }


def _build_distribution(
    *,
    counts: dict[str, int],
    sample_count: int,
) -> list[dict[str, Any]]:
    if sample_count <= 0:
        return []

    distribution = []
    for status in SENTIMENT_STATUSES:
        answer_count = counts.get(status, 0)
        if answer_count <= 0:
            continue
        distribution.append(
            {
                "sentiment_status": status,
                "answer_count": answer_count,
                "ratio": round(answer_count / sample_count, 4),
            }
        )
    return distribution


def _keyword_rows_with_ratios(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    aggregated_rows: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        key = (
            row["brand"],
            row["platform"],
            row["keyword"],
            row["sentiment_status"],
        )
        if key not in aggregated_rows:
            aggregated_rows[key] = {**row}
        else:
            aggregated_rows[key]["answer_count"] += row["answer_count"]

    rows = list(aggregated_rows.values())
    dimension_totals: dict[tuple[str, str, str], int] = {}
    for row in rows:
        key = (row["brand"], row["platform"], row["keyword"])
        dimension_totals[key] = dimension_totals.get(key, 0) + row["answer_count"]

    enriched = []
    for row in rows:
        total = dimension_totals[(row["brand"], row["platform"], row["keyword"])]
        enriched.append(
            {
                **row,
                "ratio": round(row["answer_count"] / total, 4) if total else 0.0,
            }
        )

    return sorted(
        enriched,
        key=lambda item: (
            -item["answer_count"],
            item["keyword"],
            item["platform"],
            item["brand"],
            item["sentiment_status"],
        ),
    )


def query_snapshot_sentiment_analysis(
    engine,
    *,
    tenant_key: str,
    job_id: str,
    start_date: date,
    end_date: date,
    brand: str | None = None,
    platform: str | None = None,
    keyword: str | None = None,
    metric_definition_version: str = "brand_metrics_v1",
) -> dict[str, Any] | None:
    query = (
        _latest_run_cte()
        + """
        SELECT
          ms.brand_name,
          ms.platform,
          ms.keyword,
          ms.metric_date,
          ms.dimension_hash,
          MAX(ms.analyzed_answer_count) AS analyzed_answer_count,
          MAX(ms.generated_at) AS metric_generated_at,
          MIN(ms.coverage_rate) AS metric_coverage_rate,
          MAX(ms.expected_task_count) AS metric_expected_task_count,
          MAX(ms.succeeded_task_count) AS metric_succeeded_task_count,
          MAX(ms.failed_task_count) AS metric_failed_task_count,
          MAX(CASE WHEN ms.metric_name = 'sentiment_positive_ratio'
            THEN ms.metric_value END) AS positive_ratio,
          MAX(CASE WHEN ms.metric_name = 'sentiment_negative_ratio'
            THEN ms.metric_value END) AS negative_ratio,
          MAX(CASE WHEN ms.metric_name = 'sentiment_neutral_ratio'
            THEN ms.metric_value END) AS neutral_ratio,
          MAX(CASE WHEN ms.metric_name = 'sentiment_unknown_ratio'
            THEN ms.metric_value END) AS unknown_ratio
        FROM metric_snapshots ms
        JOIN latest_run lr
          ON lr.analysis_run_id = ms.analysis_run_id
        WHERE ms.tenant_key = :tenant_key
          AND ms.metric_definition_version = :metric_definition_version
          AND ms.metric_name IN (
            'sentiment_positive_ratio',
            'sentiment_negative_ratio',
            'sentiment_neutral_ratio',
            'sentiment_unknown_ratio'
          )
          AND ms.metric_date BETWEEN :start_date AND :end_date
          AND (:brand IS NULL OR ms.brand_name = :brand)
          AND (:platform IS NULL OR ms.platform = :platform)
          AND (:keyword IS NULL OR ms.keyword = :keyword)
        GROUP BY ms.brand_name, ms.platform, ms.keyword, ms.metric_date, ms.dimension_hash
        ORDER BY ms.metric_date ASC, ms.brand_name ASC, ms.platform ASC, ms.keyword ASC
        """
    )
    params = _base_params(
        tenant_key=tenant_key,
        job_id=job_id,
        start_date=start_date,
        end_date=end_date,
        brand=brand,
        platform=platform,
        keyword=keyword,
        metric_definition_version=metric_definition_version,
    )

    with engine.connect() as conn:
        raw_rows = conn.execute(text(query), params).mappings().all()

    if not raw_rows:
        return None

    counts = {status: 0 for status in SENTIMENT_STATUSES}
    keyword_rows: list[dict[str, Any]] = []
    sample_count = 0
    metadata = {
        "data_source": "metric_snapshot",
        "snapshot_status": "available",
        "metric_definition_version": metric_definition_version,
        "metric_generated_at": None,
        "metric_coverage_rate": None,
        "metric_expected_task_count": None,
        "metric_succeeded_task_count": None,
        "metric_failed_task_count": None,
    }

    for row in raw_rows:
        analyzed_answer_count = int(row["analyzed_answer_count"] or 0)
        if analyzed_answer_count <= 0:
            continue
        sample_count += analyzed_answer_count
        metadata["metric_generated_at"] = _serialize_timestamp(row["metric_generated_at"])
        metadata["metric_coverage_rate"] = (
            round(float(row["metric_coverage_rate"]), 6)
            if row["metric_coverage_rate"] is not None
            else None
        )
        metadata["metric_expected_task_count"] = int(row["metric_expected_task_count"] or 0)
        metadata["metric_succeeded_task_count"] = int(row["metric_succeeded_task_count"] or 0)
        metadata["metric_failed_task_count"] = int(row["metric_failed_task_count"] or 0)

        ratios = {
            "positive": row["positive_ratio"],
            "negative": row["negative_ratio"],
            "neutral": row["neutral_ratio"],
            "unknown": row["unknown_ratio"],
        }
        for status, ratio in ratios.items():
            answer_count = int(round(float(ratio or 0) * analyzed_answer_count))
            counts[status] += answer_count
            if answer_count <= 0:
                continue
            keyword_rows.append(
                {
                    "keyword": row["keyword"] or "",
                    "platform": row["platform"] or "",
                    "brand": row["brand_name"] or "",
                    "sentiment_status": status,
                    "answer_count": answer_count,
                }
            )

    if sample_count <= 0:
        return None

    return {
        "distribution": _build_distribution(counts=counts, sample_count=sample_count),
        "keywords": _keyword_rows_with_ratios(keyword_rows),
        "metadata": {
            **metadata,
            "sample_count": sample_count,
            "row_count": len(keyword_rows),
        },
    }


def query_legacy_sentiment_analysis(
    engine,
    *,
    tenant_key: str,
    job_id: str,
    start_date: date,
    end_date: date,
    brand: str | None = None,
    platform: str | None = None,
    keyword: str | None = None,
) -> dict[str, Any] | None:
    query = """
    SELECT
      brand,
      platform,
      keyword,
      CASE
        WHEN LOWER(COALESCE(sentiment_status, '')) IN ('positive', 'negative', 'neutral')
          THEN LOWER(sentiment_status)
        ELSE 'unknown'
      END AS sentiment_status,
      COUNT(DISTINCT conversation_id) AS answer_count
    FROM qa_brand_state
    WHERE tenant_key = :tenant_key
      AND job_id = :job_id
      AND date BETWEEN :start_date AND :end_date
      AND (:brand IS NULL OR brand = :brand)
      AND (:platform IS NULL OR platform = :platform)
      AND (:keyword IS NULL OR keyword = :keyword)
    GROUP BY brand, platform, keyword, sentiment_status
    ORDER BY answer_count DESC, keyword ASC, platform ASC, brand ASC, sentiment_status ASC
    """
    params = _base_params(
        tenant_key=tenant_key,
        job_id=job_id,
        start_date=start_date,
        end_date=end_date,
        brand=brand,
        platform=platform,
        keyword=keyword,
    )

    with engine.connect() as conn:
        raw_rows = conn.execute(text(query), params).mappings().all()

    if not raw_rows:
        return None

    counts = {status: 0 for status in SENTIMENT_STATUSES}
    keyword_rows: list[dict[str, Any]] = []
    for row in raw_rows:
        status = row["sentiment_status"] or "unknown"
        answer_count = int(row["answer_count"] or 0)
        if answer_count <= 0:
            continue
        counts[status] = counts.get(status, 0) + answer_count
        keyword_rows.append(
            {
                "keyword": row["keyword"] or "",
                "platform": row["platform"] or "",
                "brand": row["brand"] or "",
                "sentiment_status": status,
                "answer_count": answer_count,
            }
        )

    sample_count = sum(counts.values())
    if sample_count <= 0:
        return None

    return {
        "distribution": _build_distribution(counts=counts, sample_count=sample_count),
        "keywords": _keyword_rows_with_ratios(keyword_rows),
        "metadata": {
            "data_source": "legacy_fact",
            "snapshot_status": "missing",
            "metric_definition_version": "brand_metrics_v1",
            "sample_count": sample_count,
            "row_count": len(keyword_rows),
        },
    }


def query_sentiment_analysis(
    engine,
    *,
    tenant_key: str,
    job_id: str,
    start_date: date,
    end_date: date,
    brand: str | None = None,
    platform: str | None = None,
    keyword: str | None = None,
) -> dict[str, Any]:
    snapshot_result = query_snapshot_sentiment_analysis(
        engine,
        tenant_key=tenant_key,
        job_id=job_id,
        start_date=start_date,
        end_date=end_date,
        brand=brand,
        platform=platform,
        keyword=keyword,
    )
    if snapshot_result:
        return snapshot_result

    legacy_result = query_legacy_sentiment_analysis(
        engine,
        tenant_key=tenant_key,
        job_id=job_id,
        start_date=start_date,
        end_date=end_date,
        brand=brand,
        platform=platform,
        keyword=keyword,
    )
    if legacy_result:
        return legacy_result

    return {
        "distribution": [],
        "keywords": [],
        "metadata": {
            "data_source": "empty",
            "snapshot_status": "missing",
            "metric_definition_version": "brand_metrics_v1",
            "sample_count": 0,
            "row_count": 0,
        },
    }
