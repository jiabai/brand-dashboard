from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import bindparam, text


def _format_date_key(value: Any) -> str:
    if value is None:
        return ""
    if hasattr(value, "strftime"):
        return value.strftime("%Y%m%d")
    return str(value).replace("-", "")[:8]


def _reference_filter(has_reference: bool | None) -> str:
    if has_reference is True:
        return "COALESCE(ref.reference_count, 0) > 0"
    if has_reference is False:
        return "COALESCE(ref.reference_count, 0) = 0"
    return ""


def _build_where_clauses(
    *,
    brand: str | None,
    platform: str | None,
    keyword: str | None,
    sentiment: str | None,
    has_reference: bool | None,
) -> list[str]:
    clauses = [
        "c.tenant_key = :tenant_key",
        "c.job_id = :job_id",
        "c.generated_date BETWEEN :start_date AND :end_date",
    ]
    if brand:
        clauses.append("bs.brand = :brand")
    if platform:
        clauses.append("c.platform = :platform")
    if keyword:
        clauses.append("c.keyword = :keyword")
    if sentiment:
        clauses.append("bs.sentiment_status = :sentiment")

    reference_clause = _reference_filter(has_reference)
    if reference_clause:
        clauses.append(reference_clause)

    return clauses


def _base_params(
    *,
    tenant_key: str,
    job_id: str,
    start_date: date,
    end_date: date,
    brand: str | None,
    platform: str | None,
    keyword: str | None,
    sentiment: str | None,
) -> dict[str, Any]:
    return {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "start_date": start_date,
        "end_date": end_date,
        "brand": brand,
        "platform": platform,
        "keyword": keyword,
        "sentiment": sentiment,
    }


def _query_references(
    conn,
    *,
    tenant_key: str,
    job_id: str,
    start_date: date,
    end_date: date,
    brand: str | None,
    conversation_ids: list[str],
) -> dict[str, list[dict[str, Any]]]:
    if not conversation_ids:
        return {}

    brand_clause = "AND (:brand IS NULL OR qr.brand = :brand)"
    statement = text(
        f"""
        SELECT
          qr.conversation_id,
          qr.url,
          qr.domain,
          qr.content_type,
          MAX(qr.is_published_link) AS is_published_link
        FROM qa_reference qr
        WHERE qr.tenant_key = :tenant_key
          AND qr.job_id = :job_id
          AND qr.date BETWEEN :start_date AND :end_date
          {brand_clause}
          AND qr.conversation_id IN :conversation_ids
        GROUP BY qr.conversation_id, qr.url, qr.domain, qr.content_type
        ORDER BY qr.conversation_id ASC, is_published_link DESC, qr.domain ASC, qr.url ASC
        """
    ).bindparams(bindparam("conversation_ids", expanding=True))
    rows = conn.execute(
        statement,
        {
            "tenant_key": tenant_key,
            "job_id": job_id,
            "start_date": start_date,
            "end_date": end_date,
            "brand": brand,
            "conversation_ids": conversation_ids,
        },
    ).fetchall()

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row[0], []).append(
            {
                "url": row[1],
                "domain": row[2],
                "content_type": row[3],
                "is_published_link": bool(row[4]),
            }
        )
    return grouped


def query_answer_snapshots(
    engine,
    *,
    tenant_key: str,
    job_id: str,
    start_date: date,
    end_date: date,
    brand: str | None = None,
    platform: str | None = None,
    keyword: str | None = None,
    sentiment: str | None = None,
    has_reference: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    where_sql = " AND ".join(
        _build_where_clauses(
            brand=brand,
            platform=platform,
            keyword=keyword,
            sentiment=sentiment,
            has_reference=has_reference,
        )
    )
    params = _base_params(
        tenant_key=tenant_key,
        job_id=job_id,
        start_date=start_date,
        end_date=end_date,
        brand=brand,
        platform=platform,
        keyword=keyword,
        sentiment=sentiment,
    )
    params.update({"limit": limit, "offset": offset})

    reference_summary = """
      SELECT
        qr.conversation_id,
        COUNT(DISTINCT qr.url) AS reference_count
      FROM qa_reference qr
      WHERE qr.tenant_key = :tenant_key
        AND qr.job_id = :job_id
        AND qr.date BETWEEN :start_date AND :end_date
        AND (:brand IS NULL OR qr.brand = :brand)
      GROUP BY qr.conversation_id
    """

    from_and_join = f"""
      FROM llm_conversations c
      LEFT JOIN qa_brand_state bs
        ON bs.tenant_key = c.tenant_key
       AND bs.job_id = c.job_id
       AND bs.conversation_id = c.conversation_id
       AND bs.date BETWEEN :start_date AND :end_date
      LEFT JOIN ({reference_summary}) ref
        ON ref.conversation_id = c.conversation_id
      WHERE {where_sql}
    """

    group_sql = """
      GROUP BY
        c.id,
        c.conversation_id,
        c.generated_date,
        c.platform,
        c.brand,
        c.keyword,
        c.query_content,
        c.answer_content,
        c.extracted_at,
        ref.reference_count
    """

    data_query = f"""
    SELECT
      c.conversation_id,
      c.generated_date,
      c.platform,
      COALESCE(:brand, c.brand, MAX(bs.brand), '') AS brand,
      c.keyword,
      c.query_content,
      c.answer_content,
      COALESCE(MAX(bs.sentiment_status), 'unknown') AS sentiment_status,
      COALESCE(MAX(bs.is_mentioned), 0) AS is_mentioned,
      COALESCE(ref.reference_count, 0) AS reference_count
    {from_and_join}
    {group_sql}
    ORDER BY c.generated_date DESC, c.extracted_at DESC, c.id DESC
    LIMIT :limit OFFSET :offset
    """

    count_query = f"""
    SELECT COUNT(*)
    FROM (
      SELECT c.conversation_id
      {from_and_join}
      {group_sql}
    ) filtered_answer_snapshots
    """

    with engine.connect() as conn:
        rows = conn.execute(text(data_query), params).fetchall()
        total_count = int(conn.execute(text(count_query), params).scalar() or 0)
        references_by_conversation = _query_references(
            conn,
            tenant_key=tenant_key,
            job_id=job_id,
            start_date=start_date,
            end_date=end_date,
            brand=brand,
            conversation_ids=[row[0] for row in rows],
        )

    items: list[dict[str, Any]] = []
    for row in rows:
        conversation_id = row[0]
        references = references_by_conversation.get(conversation_id, [])
        reference_count = int(row[9]) if row[9] else 0
        items.append(
            {
                "conversation_id": conversation_id,
                "date": _format_date_key(row[1]),
                "platform": row[2],
                "brand": row[3],
                "keyword": row[4],
                "query_content": row[5],
                "answer_content": row[6],
                "sentiment_status": row[7],
                "is_mentioned": bool(row[8]),
                "has_reference": reference_count > 0,
                "reference_count": reference_count,
                "references": references,
            }
        )

    return items, total_count
