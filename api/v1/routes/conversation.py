from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.v1.models.schemas import ConversationLoadRequest, ConversationLoadResponse
from api.v1.repositories.database import get_db
from api.v1.routes.query_jobs import verify_executor
from api.v1.utils.url_domain_resolver import extract_domain_from_url, infer_content_type

router = APIRouter()

@router.post("/load", response_model=ConversationLoadResponse)
async def load_conversations(
    request: ConversationLoadRequest,
    executor_id: str = Depends(verify_executor),
    db: Session = Depends(get_db),
):
    tenant_check = db.execute(
        text("SELECT 1 FROM tenants WHERE tenant_key = :tenant_key"),
        {"tenant_key": request.tenant_key},
    ).first()
    if not tenant_check:
        raise HTTPException(status_code=400, detail=f"租户不存在: {request.tenant_key}")

    inserted_conversations = 0
    inserted_references = 0
    now = datetime.now(timezone.utc)

    try:
        for item in request.items:
            extracted_at = item.extracted_at or now
            existing = db.execute(
                text(
                    """
                    SELECT 1
                    FROM llm_conversations
                    WHERE tenant_key = :tenant_key
                      AND conversation_id = :conversation_id
                    """
                ),
                {
                    "tenant_key": request.tenant_key,
                    "conversation_id": item.conversation_id,
                },
            ).first()

            if not existing:
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
                        "tenant_key": request.tenant_key,
                        "job_id": request.job_id,
                        "conversation_id": item.conversation_id,
                        "platform": request.platform,
                        "keyword": item.keyword,
                        "brand": item.brand,
                        "category": item.category,
                        "query_content": item.query_content,
                        "answer_content": item.answer_content,
                        "generated_date": extracted_at.date(),
                        "extracted_at": extracted_at,
                    },
                )
                inserted_conversations += 1

            if item.references:
                for ref in item.references:
                    if not ref.url:
                        continue
                    ref_exists = db.execute(
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
                            "tenant_key": request.tenant_key,
                            "conversation_id": item.conversation_id,
                            "url": ref.url,
                        },
                    ).first()

                    domain = extract_domain_from_url(ref.url)
                    content_type = infer_content_type(domain, ref.url)

                    if not ref_exists:
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
                                "tenant_key": request.tenant_key,
                                "job_id": request.job_id,
                                "conversation_id": item.conversation_id,
                                "platform": request.platform,
                                "brand": item.brand,
                                "category": item.category,
                                "keyword": item.keyword,
                                "query_content": item.query_content,
                                "url": ref.url,
                                "domain": domain,
                                "cite_index": ref.cite_index,
                                "site_name": ref.site_name,
                                "content_type": content_type,
                                "generated_date": extracted_at.date(),
                            },
                        )
                        inserted_references += 1

        db.commit()
        return ConversationLoadResponse(
            success=True,
            inserted_conversations=inserted_conversations,
            inserted_references=inserted_references,
            message="对话入库成功",
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"对话入库失败: {str(exc)}") from exc
