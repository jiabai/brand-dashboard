from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

METRIC_SNAPSHOT_COLUMNS = [
    "tenant_key",
    "snapshot_id",
    "project_id",
    "analysis_run_id",
    "metric_date",
    "brand_id",
    "brand_name",
    "platform",
    "keyword",
    "metric_name",
    "metric_value",
    "metric_unit",
    "metric_definition_version",
    "expected_task_count",
    "succeeded_task_count",
    "failed_task_count",
    "analyzed_answer_count",
    "coverage_rate",
    "source_watermark",
    "dimension_hash",
    "generated_at",
]

METRIC_SNAPSHOT_IDENTITY_COLUMNS = [
    "tenant_key",
    "project_id",
    "metric_date",
    "metric_name",
    "metric_definition_version",
    "analysis_run_id",
    "dimension_hash",
]


def _dialect_name(db: Session) -> str:
    bind = db.get_bind()
    return getattr(bind.dialect, "name", "")


def _upsert_sql(db: Session) -> str:
    columns = ", ".join(METRIC_SNAPSHOT_COLUMNS)
    values = ", ".join(f":{column}" for column in METRIC_SNAPSHOT_COLUMNS)
    update_columns = [
        column
        for column in METRIC_SNAPSHOT_COLUMNS
        if column not in METRIC_SNAPSHOT_IDENTITY_COLUMNS
    ]

    if _dialect_name(db) == "mysql":
        updates = ", ".join(f"{column} = VALUES({column})" for column in update_columns)
        return (
            f"INSERT INTO metric_snapshots ({columns}) VALUES ({values}) "
            f"ON DUPLICATE KEY UPDATE {updates}"
        )

    conflict_columns = ", ".join(METRIC_SNAPSHOT_IDENTITY_COLUMNS)
    updates = ", ".join(f"{column} = excluded.{column}" for column in update_columns)
    return (
        f"INSERT INTO metric_snapshots ({columns}) VALUES ({values}) "
        f"ON CONFLICT({conflict_columns}) DO UPDATE SET {updates}"
    )


def upsert_metric_snapshots(
    db: Session,
    snapshots: Sequence[Mapping[str, Any]],
) -> int:
    if not snapshots:
        return 0

    db.execute(text(_upsert_sql(db)), [dict(snapshot) for snapshot in snapshots])
    return len(snapshots)


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
          )
        ORDER BY ar.finished_at DESC, ar.updated_at DESC, ar.id DESC
        LIMIT 1
    )
    """


def query_snapshot_brand_metrics(
    engine,
    *,
    tenant_key: str,
    job_id: str,
    start_date: date,
    end_date: date,
    brand: str | None = None,
    platform: str | None = None,
    metric_definition_version: str = "brand_metrics_v1",
) -> list[dict[str, Any]]:
    query = (
        _latest_run_cte()
        + """
        , metric_rows AS (
            SELECT
              ms.brand_name,
              ms.metric_date,
              ms.platform,
              ms.keyword,
              ms.metric_name,
              ms.metric_value,
              ms.analyzed_answer_count
            FROM metric_snapshots ms
            JOIN latest_run lr
              ON lr.analysis_run_id = ms.analysis_run_id
            WHERE ms.tenant_key = :tenant_key
              AND ms.metric_definition_version = :metric_definition_version
              AND ms.metric_date BETWEEN :start_date AND :end_date
              AND ms.metric_name IN (
                'mention_rate',
                'first_mention_rate',
                'top3_mention_rate'
              )
              AND (:brand IS NULL OR ms.brand_name = :brand)
              AND (:platform IS NULL OR ms.platform = :platform)
        ),
        dimension_rows AS (
            SELECT
              brand_name AS brand,
              metric_date,
              platform,
              keyword,
              MAX(analyzed_answer_count) AS analyzed_answer_count,
              MAX(CASE WHEN metric_name = 'mention_rate' THEN metric_value END)
                AS mention_rate,
              MAX(CASE WHEN metric_name = 'first_mention_rate' THEN metric_value END)
                AS first_mention_rate,
              MAX(CASE WHEN metric_name = 'top3_mention_rate' THEN metric_value END)
                AS top3_mention_rate
            FROM metric_rows
            GROUP BY brand_name, metric_date, platform, keyword
        )
        SELECT
          brand,
          SUM(COALESCE(mention_rate, 0) * analyzed_answer_count)
            / NULLIF(SUM(analyzed_answer_count), 0) AS mention_rate,
          SUM(COALESCE(first_mention_rate, 0) * analyzed_answer_count)
            / NULLIF(SUM(analyzed_answer_count), 0) AS first_mention_rate,
          SUM(COALESCE(top3_mention_rate, 0) * analyzed_answer_count)
            / NULLIF(SUM(analyzed_answer_count), 0) AS top3_mention_rate,
          SUM(analyzed_answer_count) AS prompt_count,
          COUNT(DISTINCT CASE
            WHEN COALESCE(mention_rate, 0) > 0 THEN keyword
          END) AS keyword_coverage
        FROM dimension_rows
        GROUP BY brand
        ORDER BY mention_rate DESC, brand ASC
        """
    )
    params = {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "start_date": start_date,
        "end_date": end_date,
        "brand": brand,
        "platform": platform,
        "metric_definition_version": metric_definition_version,
    }

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return [
        {
            "brand": row[0],
            "mention_rate": round(float(row[1]), 4) if row[1] is not None else 0.0,
            "first_mention_rate": (
                round(float(row[2]), 4) if row[2] is not None else 0.0
            ),
            "top3_mention_rate": (
                round(float(row[3]), 4) if row[3] is not None else 0.0
            ),
            "prompt_count": int(row[4]) if row[4] else 0,
            "keyword_coverage": int(row[5]) if row[5] else 0,
        }
        for row in rows
    ]


def query_snapshot_daily_mention_rates(
    engine,
    *,
    tenant_key: str,
    job_id: str,
    brand: str,
    platform: str,
    keyword: str,
    start_date: date,
    end_date: date,
    metric_definition_version: str = "brand_metrics_v1",
) -> list[dict[str, Any]]:
    query = (
        _latest_run_cte()
        + """
        SELECT
          ms.metric_date,
          ms.brand_name,
          ms.platform,
          ms.keyword,
          ms.metric_value
        FROM metric_snapshots ms
        JOIN latest_run lr
          ON lr.analysis_run_id = ms.analysis_run_id
        WHERE ms.tenant_key = :tenant_key
          AND ms.metric_definition_version = :metric_definition_version
          AND ms.metric_name = 'mention_rate'
          AND ms.brand_name = :brand
          AND ms.platform = :platform
          AND ms.keyword = :keyword
          AND ms.metric_date BETWEEN :start_date AND :end_date
        ORDER BY ms.metric_date ASC
        """
    )
    params = {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "brand": brand,
        "platform": platform,
        "keyword": keyword,
        "start_date": start_date,
        "end_date": end_date,
        "metric_definition_version": metric_definition_version,
    }

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return [
        {
            "date": row[0],
            "brand": row[1],
            "platform": row[2],
            "keyword": row[3],
            "mention_rate": float(row[4]) if row[4] is not None else 0.0,
        }
        for row in rows
    ]


def query_snapshot_platform_metrics_by_brand(
    engine,
    *,
    tenant_key: str,
    job_id: str,
    brand: str,
    start_date: date,
    end_date: date,
    metric_definition_version: str = "brand_metrics_v1",
) -> list[dict[str, Any]]:
    query = (
        _latest_run_cte()
        + """
        SELECT
          ms.platform,
          SUM(ms.metric_value * ms.analyzed_answer_count)
            / NULLIF(SUM(ms.analyzed_answer_count), 0) AS mention_rate
        FROM metric_snapshots ms
        JOIN latest_run lr
          ON lr.analysis_run_id = ms.analysis_run_id
        WHERE ms.tenant_key = :tenant_key
          AND ms.metric_definition_version = :metric_definition_version
          AND ms.metric_name = 'mention_rate'
          AND ms.brand_name = :brand
          AND ms.metric_date BETWEEN :start_date AND :end_date
        GROUP BY ms.platform
        ORDER BY ms.platform ASC
        """
    )
    params = {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "brand": brand,
        "start_date": start_date,
        "end_date": end_date,
        "metric_definition_version": metric_definition_version,
    }

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return [
        {
            "platform": row[0],
            "mention_rate": round(float(row[1]), 4) if row[1] is not None else 0.0,
        }
        for row in rows
    ]


def query_snapshot_keyword_platform_brand_rates(
    engine,
    *,
    tenant_key: str,
    job_id: str,
    start_date: date,
    end_date: date,
    metric_definition_version: str = "brand_metrics_v1",
) -> list[dict[str, Any]]:
    query = (
        _latest_run_cte()
        + """
        SELECT
          ms.keyword,
          ms.platform,
          ms.brand_name,
          MAX(CASE WHEN ms.metric_name = 'mention_rate' THEN ms.metric_value END)
            AS mention_rate,
          MAX(CASE WHEN ms.metric_name = 'first_mention_rate' THEN ms.metric_value END)
            AS first_mention_rate,
          MAX(CASE WHEN ms.metric_name = 'top3_mention_rate' THEN ms.metric_value END)
            AS top3_mention_rate
        FROM metric_snapshots ms
        JOIN latest_run lr
          ON lr.analysis_run_id = ms.analysis_run_id
        WHERE ms.tenant_key = :tenant_key
          AND ms.metric_definition_version = :metric_definition_version
          AND ms.metric_name IN (
            'mention_rate',
            'first_mention_rate',
            'top3_mention_rate'
          )
          AND ms.metric_date BETWEEN :start_date AND :end_date
        GROUP BY ms.keyword, ms.platform, ms.brand_name
        HAVING MAX(CASE WHEN ms.metric_name = 'mention_rate' THEN ms.metric_value END)
          IS NOT NULL
        ORDER BY ms.keyword ASC, ms.platform ASC, mention_rate DESC
        """
    )
    params = {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "start_date": start_date,
        "end_date": end_date,
        "metric_definition_version": metric_definition_version,
    }

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    return [
        {
            "keyword": row[0],
            "platform": row[1],
            "brand": row[2],
            "mention_rate": float(row[3]) if row[3] is not None else 0.0,
            "first_mention_rate": float(row[4]) if row[4] is not None else 0.0,
            "top3_mention_rate": float(row[5]) if row[5] is not None else 0.0,
        }
        for row in rows
    ]
