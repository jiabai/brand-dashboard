from datetime import date, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


def conversation_exists(db: Session, *, tenant_key: str, conversation_id: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM llm_conversations
            WHERE tenant_key = :tenant_key
              AND conversation_id = :conversation_id
            """
        ),
        {
            "tenant_key": tenant_key,
            "conversation_id": conversation_id,
        },
    ).first()
    return row is not None


def insert_conversation(
    db: Session,
    *,
    tenant_key: str,
    job_id: str,
    conversation_id: str,
    platform: str,
    keyword: str,
    brand: str | None,
    category: str,
    query_content: str,
    answer_content: str,
    generated_date: date,
    extracted_at: datetime,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO llm_conversations
              (tenant_key, job_id, conversation_id, platform, keyword, brand, category,
               query_content, answer_content, generated_date, extracted_at)
            VALUES
              (
                :tenant_key,
                :job_id,
                :conversation_id,
                :platform,
                :keyword,
                :brand,
                :category,
                :query_content,
                :answer_content,
                :generated_date,
                :extracted_at
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "job_id": job_id,
            "conversation_id": conversation_id,
            "platform": platform,
            "keyword": keyword,
            "brand": brand,
            "category": category,
            "query_content": query_content,
            "answer_content": answer_content,
            "generated_date": generated_date,
            "extracted_at": extracted_at,
        },
    )


def reference_exists(db: Session, *, tenant_key: str, conversation_id: str, url: str) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM llm_conversation_references
            WHERE tenant_key = :tenant_key
              AND conversation_id = :conversation_id
              AND url = :url
            """
        ),
        {
            "tenant_key": tenant_key,
            "conversation_id": conversation_id,
            "url": url,
        },
    ).first()
    return row is not None


def insert_reference(
    db: Session,
    *,
    tenant_key: str,
    job_id: str,
    conversation_id: str,
    platform: str,
    brand: str | None,
    category: str,
    keyword: str,
    query_content: str,
    url: str,
    domain: str,
    cite_index: int | None,
    site_name: str | None,
    content_type: str,
    generated_date: date,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO llm_conversation_references
              (
                tenant_key,
                job_id,
                conversation_id,
                platform,
                brand,
                category,
                keyword,
                query_content,
                url,
                domain,
                cite_index,
                site_name,
                content_type,
                generated_date
              )
            VALUES
              (
                :tenant_key,
                :job_id,
                :conversation_id,
                :platform,
                :brand,
                :category,
                :keyword,
                :query_content,
                :url,
                :domain,
                :cite_index,
                :site_name,
                :content_type,
                :generated_date
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "job_id": job_id,
            "conversation_id": conversation_id,
            "platform": platform,
            "brand": brand,
            "category": category,
            "keyword": keyword,
            "query_content": query_content,
            "url": url,
            "domain": domain,
            "cite_index": cite_index,
            "site_name": site_name,
            "content_type": content_type,
            "generated_date": generated_date,
        },
    )

