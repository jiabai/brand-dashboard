from typing import List
from fastapi import APIRouter, HTTPException

from brand_analysis_api.models.schemas import PositioningRequest
from brand_analysis_api.utils.llm_client import generate_positioning_keywords

router = APIRouter()

@router.post("/positioning-keywords", response_model=List[str])
async def positioning_keywords(req: PositioningRequest) -> List[str]:
    try:
        return await generate_positioning_keywords(req.industry, req.brand)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
