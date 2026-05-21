from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.v1.models.schemas import ConversationLoadRequest, ConversationLoadResponse
from api.v1.repositories.connection import get_db
from api.v1.repositories.conversation import (
    conversation_exists,
    insert_conversation,
    insert_reference,
    reference_exists,
)
from api.v1.repositories.tenants import tenant_exists
from api.v1.routes.query_jobs import verify_executor, verify_executor_job_scope
from api.v1.utils.url_domain_resolver import extract_domain_from_url, infer_content_type

router = APIRouter()

@router.post("/load", response_model=ConversationLoadResponse)
async def load_conversations(
    request: ConversationLoadRequest,
    executor_id: str = Depends(verify_executor),
    db: Session = Depends(get_db),
):
    if not tenant_exists(db, request.tenant_key):
        raise HTTPException(status_code=400, detail=f"租户不存在: {request.tenant_key}")

    verify_executor_job_scope(
        db,
        executor_id=executor_id,
        tenant_key=request.tenant_key,
        job_id=request.job_id,
    )

    inserted_conversations = 0
    inserted_references = 0
    now = datetime.now(timezone.utc)

    try:
        for item in request.items:
            extracted_at = item.extracted_at or now
            existing = conversation_exists(
                db,
                tenant_key=request.tenant_key,
                conversation_id=item.conversation_id,
            )

            if not existing:
                insert_conversation(
                    db,
                    tenant_key=request.tenant_key,
                    job_id=request.job_id,
                    conversation_id=item.conversation_id,
                    platform=request.platform,
                    keyword=item.keyword,
                    brand=item.brand,
                    category=item.category,
                    query_content=item.query_content,
                    answer_content=item.answer_content,
                    generated_date=extracted_at.date(),
                    extracted_at=extracted_at,
                )
                inserted_conversations += 1

            if item.references:
                for ref in item.references:
                    if not ref.url:
                        continue
                    ref_exists = reference_exists(
                        db,
                        tenant_key=request.tenant_key,
                        conversation_id=item.conversation_id,
                        url=ref.url,
                    )

                    domain = extract_domain_from_url(ref.url)
                    content_type = infer_content_type(domain, ref.url)

                    if not ref_exists:
                        insert_reference(
                            db,
                            tenant_key=request.tenant_key,
                            job_id=request.job_id,
                            conversation_id=item.conversation_id,
                            platform=request.platform,
                            brand=item.brand,
                            category=item.category,
                            keyword=item.keyword,
                            query_content=item.query_content,
                            url=ref.url,
                            domain=domain,
                            cite_index=ref.cite_index,
                            site_name=ref.site_name,
                            content_type=content_type,
                            generated_date=extracted_at.date(),
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
