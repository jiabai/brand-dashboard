"""分析相关API路由."""

from datetime import UTC, datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from api.v1.models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    BrandRecognitionRequest,
    BrandRecognitionResponse,
)

try:
    from brand_analysis import BrandAnalyzer, LLMBrandRecognizer

    _BrandAnalyzer: Optional[type] = BrandAnalyzer
    _LLMBrandRecognizer: Optional[type] = LLMBrandRecognizer
    HAS_BRAND_ANALYSIS = True
except ImportError:
    _BrandAnalyzer = None
    _LLMBrandRecognizer = None
    HAS_BRAND_ANALYSIS = False

router = APIRouter()


def _require_brand_analysis():
    if not HAS_BRAND_ANALYSIS:
        raise HTTPException(
            status_code=501,
            detail=(
                "brand_analysis 模块未在容器中安装，"
                "无法执行分析，请在 API 镜像中安装该依赖或提供相应模块。"
            ),
        )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_brand(request: AnalysisRequest):
    """执行品牌分析."""
    try:
        _require_brand_analysis()
        analyzer = _BrandAnalyzer()
        result = analyzer.analyze(
            brand_name=request.brand_name,
            analysis_type=request.analysis_type,
            params=request.params,
        )

        return AnalysisResponse(
            success=True,
            data=result,
            message="分析完成",
            timestamp=datetime.now(UTC),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}") from e


@router.post("/recognize-brand", response_model=BrandRecognitionResponse)
async def recognize_brand(request: BrandRecognitionRequest):
    """品牌识别."""
    try:
        _require_brand_analysis()
        recognizer = _LLMBrandRecognizer()
        result = recognizer.recognize_brand(
            text=request.text,
            context=request.context,
        )

        return BrandRecognitionResponse(
            success=True,
            data=result,
            message="品牌识别完成",
            timestamp=datetime.now(UTC),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"品牌识别失败: {str(e)}")


@router.get("/results/{result_id}", response_model=AnalysisResponse)
async def get_analysis_result(result_id: str):
    """获取分析结果."""
    raise HTTPException(
        status_code=501,
        detail="分析结果持久化尚未实现，结果仅在内存中可用。",
    )


@router.get("/history", response_model=Dict[str, Any])
async def get_analysis_history(limit: int = 10, offset: int = 0):
    """获取分析历史记录."""
    raise HTTPException(
        status_code=501,
        detail="分析历史记录功能尚未实现。",
    )
