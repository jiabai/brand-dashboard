from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import date
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

CORE_FACT_METRICS = (
    "mention_rate",
    "first_mention_rate",
    "top3_mention_rate",
    "sentiment_negative_ratio",
    "reference_rate",
)


def _stable_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _dimension_hash(row: Mapping[str, Any]) -> str:
    return _stable_hash(
        {
            "brand_id": row.get("brand_id") or "",
            "brand_name": row.get("brand_name") or "",
            "platform": row.get("platform") or "",
            "keyword": row.get("keyword") or "",
        }
    )


def _float_metric(value: Any) -> float:
    if value is None:
        return 0.0
    return round(float(value), 6)


def list_project_fact_metric_rows(
    db: Session,
    *,
    tenant_key: str,
    project_id: str,
    start_date: date,
    end_date: date,
    analysis_run_id: str | None = None,
    metric_definition_version: str = "brand_metrics_v1",
) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            WITH brand_lookup AS (
              SELECT
                tenant_key,
                project_id,
                brand_name,
                MIN(brand_id) AS brand_id
              FROM project_brands
              WHERE tenant_key = :tenant_key
                AND project_id = :project_id
              GROUP BY tenant_key, project_id, brand_name
            ),
            base AS (
              SELECT
                bs.tenant_key,
                ar.project_id,
                ar.analysis_run_id,
                ar.collection_job_id,
                bs.date AS metric_date,
                COALESCE(bl.brand_id, '') AS brand_id,
                bs.brand AS brand_name,
                bs.platform,
                bs.keyword,
                COUNT(DISTINCT bs.conversation_id) AS analyzed_answer_count,
                COUNT(DISTINCT CASE WHEN bs.is_mentioned = 1
                  THEN bs.conversation_id END) AS mention_count,
                COUNT(DISTINCT CASE WHEN bs.is_first_mentioned = 1
                  THEN bs.conversation_id END) AS first_mention_count,
                COUNT(DISTINCT CASE WHEN bs.is_top3_mentioned = 1
                  THEN bs.conversation_id END) AS top3_mention_count,
                COUNT(DISTINCT CASE
                  WHEN LOWER(COALESCE(bs.sentiment_status, '')) = 'negative'
                  THEN bs.conversation_id END) AS negative_sentiment_count,
                COUNT(DISTINCT CASE
                  WHEN COALESCE(bs.sentiment_status, '') != ''
                  THEN bs.conversation_id END) AS sentiment_answer_count
              FROM qa_brand_state bs
              JOIN analysis_runs ar
                ON ar.tenant_key = bs.tenant_key
               AND ar.analysis_run_id = bs.analysis_run_id
               AND ar.status = 'succeeded'
              LEFT JOIN brand_lookup bl
                ON bl.tenant_key = ar.tenant_key
               AND bl.project_id = ar.project_id
               AND bl.brand_name = bs.brand
              WHERE bs.tenant_key = :tenant_key
                AND ar.project_id = :project_id
                AND bs.date BETWEEN :start_date AND :end_date
                AND (:analysis_run_id IS NULL OR ar.analysis_run_id = :analysis_run_id)
              GROUP BY
                bs.tenant_key,
                ar.project_id,
                ar.analysis_run_id,
                ar.collection_job_id,
                bs.date,
                COALESCE(bl.brand_id, ''),
                bs.brand,
                bs.platform,
                bs.keyword
            ),
            reference_counts AS (
              SELECT
                qr.tenant_key,
                ar.project_id,
                ar.analysis_run_id,
                qr.date AS metric_date,
                COALESCE(qr.brand, '') AS brand_name,
                qr.platform,
                qr.keyword,
                COUNT(DISTINCT qr.conversation_id) AS reference_count
              FROM qa_reference qr
              JOIN analysis_runs ar
                ON ar.tenant_key = qr.tenant_key
               AND ar.analysis_run_id = qr.analysis_run_id
               AND ar.status = 'succeeded'
              WHERE qr.tenant_key = :tenant_key
                AND ar.project_id = :project_id
                AND qr.date BETWEEN :start_date AND :end_date
                AND (:analysis_run_id IS NULL OR ar.analysis_run_id = :analysis_run_id)
              GROUP BY
                qr.tenant_key,
                ar.project_id,
                ar.analysis_run_id,
                qr.date,
                COALESCE(qr.brand, ''),
                qr.platform,
                qr.keyword
            )
            SELECT
              b.tenant_key,
              b.project_id,
              b.analysis_run_id,
              b.collection_job_id,
              b.metric_date,
              b.brand_id,
              b.brand_name,
              b.platform,
              b.keyword,
              'mention_rate' AS metric_name,
              CASE WHEN b.analyzed_answer_count = 0 THEN 0
                ELSE b.mention_count * 1.0 / b.analyzed_answer_count END AS metric_value,
              :metric_definition_version AS metric_definition_version,
              b.analyzed_answer_count
            FROM base b
            UNION ALL
            SELECT
              b.tenant_key,
              b.project_id,
              b.analysis_run_id,
              b.collection_job_id,
              b.metric_date,
              b.brand_id,
              b.brand_name,
              b.platform,
              b.keyword,
              'first_mention_rate' AS metric_name,
              CASE WHEN b.analyzed_answer_count = 0 THEN 0
                ELSE b.first_mention_count * 1.0 / b.analyzed_answer_count END AS metric_value,
              :metric_definition_version AS metric_definition_version,
              b.analyzed_answer_count
            FROM base b
            UNION ALL
            SELECT
              b.tenant_key,
              b.project_id,
              b.analysis_run_id,
              b.collection_job_id,
              b.metric_date,
              b.brand_id,
              b.brand_name,
              b.platform,
              b.keyword,
              'top3_mention_rate' AS metric_name,
              CASE WHEN b.analyzed_answer_count = 0 THEN 0
                ELSE b.top3_mention_count * 1.0 / b.analyzed_answer_count END AS metric_value,
              :metric_definition_version AS metric_definition_version,
              b.analyzed_answer_count
            FROM base b
            UNION ALL
            SELECT
              b.tenant_key,
              b.project_id,
              b.analysis_run_id,
              b.collection_job_id,
              b.metric_date,
              b.brand_id,
              b.brand_name,
              b.platform,
              b.keyword,
              'sentiment_negative_ratio' AS metric_name,
              CASE WHEN b.sentiment_answer_count = 0 THEN 0
                ELSE b.negative_sentiment_count * 1.0 / b.sentiment_answer_count END
                AS metric_value,
              :metric_definition_version AS metric_definition_version,
              b.sentiment_answer_count AS analyzed_answer_count
            FROM base b
            UNION ALL
            SELECT
              b.tenant_key,
              b.project_id,
              b.analysis_run_id,
              b.collection_job_id,
              b.metric_date,
              b.brand_id,
              b.brand_name,
              b.platform,
              b.keyword,
              'reference_rate' AS metric_name,
              CASE WHEN b.analyzed_answer_count = 0 THEN 0
                ELSE COALESCE(rc.reference_count, 0) * 1.0 / b.analyzed_answer_count END
                AS metric_value,
              :metric_definition_version AS metric_definition_version,
              b.analyzed_answer_count
            FROM base b
            LEFT JOIN reference_counts rc
              ON rc.tenant_key = b.tenant_key
             AND rc.project_id = b.project_id
             AND rc.analysis_run_id = b.analysis_run_id
             AND rc.metric_date = b.metric_date
             AND rc.brand_name = b.brand_name
             AND rc.platform = b.platform
             AND rc.keyword = b.keyword
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "start_date": start_date,
            "end_date": end_date,
            "analysis_run_id": analysis_run_id,
            "metric_definition_version": metric_definition_version,
        },
    ).mappings().all()

    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["metric_value"] = _float_metric(item.get("metric_value"))
        item["analyzed_answer_count"] = int(item.get("analyzed_answer_count") or 0)
        item["dimension_hash"] = _dimension_hash(item)
        result.append(item)

    return sorted(
        result,
        key=lambda item: (
            str(item.get("brand_name") or ""),
            str(item.get("brand_id") or ""),
            str(item.get("metric_definition_version") or ""),
            str(item.get("metric_date") or ""),
            str(item.get("platform") or ""),
            str(item.get("keyword") or ""),
            str(item.get("metric_name") or ""),
        ),
    )
