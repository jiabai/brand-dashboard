from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import text

SENTIMENT_STATUSES = ("positive", "negative", "neutral", "unknown")


def _serialize_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _base_params(
    *,
    tenant_key: str,
    job_id: str,
    start_date: date,
    end_date: date,
    brand: str | None,
    platform: str | None,
    keyword: str | None,
) -> dict[str, Any]:
    return {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "start_date": start_date,
        "end_date": end_date,
        "brand": brand,
        "platform": platform,
        "keyword": keyword,
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
            "data_source": "analysis_fact",
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
            "metric_definition_version": "brand_metrics_v1",
            "sample_count": 0,
            "row_count": 0,
        },
    }
