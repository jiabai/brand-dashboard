from fastapi import APIRouter, HTTPException

from api.v1.models.schemas import (
    ConsumerQuestionsRequest,
    ConsumerQuestionsResponse,
    PositioningKeywordsResponse,
    PositioningRequest,
)
from api.v1.services.llm_client import generate_consumer_questions, generate_positioning_keywords

router = APIRouter()


@router.post("/positioning-keywords", response_model=PositioningKeywordsResponse)
async def positioning_keywords(req: PositioningRequest) -> PositioningKeywordsResponse:
    try:
        keywords, source = await generate_positioning_keywords(req.industry, req.brand)
        return PositioningKeywordsResponse(keywords=keywords, source=source)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/consumer-questions", response_model=ConsumerQuestionsResponse)
async def consumer_questions(req: ConsumerQuestionsRequest) -> ConsumerQuestionsResponse:
    try:
        questions, source = await generate_consumer_questions(
            req.industry, req.brand, req.keywords,
        )
        return ConsumerQuestionsResponse(questions=questions, source=source)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e