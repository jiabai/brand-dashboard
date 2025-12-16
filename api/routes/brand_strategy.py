from typing import List, Dict

from fastapi import APIRouter, HTTPException

from api.models.schemas import PositioningRequest, ConsumerQuestionsRequest
from api.services.llm_client import generate_positioning_keywords, generate_consumer_questions

router = APIRouter()

@router.post("/positioning-keywords", response_model=List[str])
async def positioning_keywords(req: PositioningRequest) -> List[str]:
    """Generate positioning keywords for a brand within a given industry.

    Args:
        req: A PositioningRequest containing the industry and brand name.

    Returns:
        A list of suggested positioning keywords.
    """
    try:
        return await generate_positioning_keywords(req.industry, req.brand)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/consumer-questions", response_model=Dict[str, List[str]])
async def consumer_questions(req: ConsumerQuestionsRequest) -> Dict[str, List[str]]:
    """Generate consumer questions for brand keywords.

    Args:
        req: A ConsumerQuestionsRequest containing the industry, brand name and keywords.

    Returns:
        A dictionary mapping keywords to lists of consumer questions.
    """
    try:
        return await generate_consumer_questions(req.industry, req.brand, req.keywords)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
