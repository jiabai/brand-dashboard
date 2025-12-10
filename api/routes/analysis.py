"""分析相关API路由."""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from api.models.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    BrandRecognitionRequest,
    BrandRecognitionResponse,
)

try:
    from brand_analysis import BrandAnalyzer, LLMBrandRecognizer
    HAS_BRAND_ANALYSIS = True
except ImportError:
    BrandAnalyzer = None  # type: ignore[assignment]
    LLMBrandRecognizer = None  # type: ignore[assignment]
    HAS_BRAND_ANALYSIS = False

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_brand(request: AnalysisRequest):
    """执行品牌分析."""
    try:
        if not HAS_BRAND_ANALYSIS:
            raise HTTPException(
                status_code=501,
                detail=(
                    "brand_analysis 模块未在容器中安装，"
                    "无法执行分析，请在 API 镜像中安装该依赖或提供相应模块。"
                ),
            )
        # 初始化分析器
        analyzer = BrandAnalyzer()
        # 执行分析
        result = analyzer.analyze(
            brand_name=request.brand_name,
            analysis_type=request.analysis_type,
            params=request.params
        )

        return AnalysisResponse(
            success=True,
            data=result,
            message="分析完成",
            timestamp=datetime.now()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}") from e


@router.post("/recognize-brand", response_model=BrandRecognitionResponse)
async def recognize_brand(request: BrandRecognitionRequest):
    """品牌识别."""
    try:
        if not HAS_BRAND_ANALYSIS:
            raise HTTPException(
                status_code=501,
                detail=(
                    "brand_analysis 模块未在容器中安装，"
                    "无法执行品牌识别，请在 API 镜像中安装该依赖或提供相应模块。"
                ),
            )
        # 初始化品牌识别器
        recognizer = LLMBrandRecognizer()
        
        # 执行识别
        result = recognizer.recognize_brand(
            text=request.text,
            context=request.context
        )
        
        return BrandRecognitionResponse(
            success=True,
            data=result,
            message="品牌识别完成",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"品牌识别失败: {str(e)}")


@router.get("/results/{result_id}", response_model=AnalysisResponse)
async def get_analysis_result(result_id: str):
    """获取分析结果."""
    try:
        # 这里可以实现结果缓存或数据库查询
        # 目前返回模拟数据
        return AnalysisResponse(
            success=True,
            data={"result_id": result_id, "status": "completed"},
            message="获取结果成功",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取结果失败: {str(e)}")


@router.get("/history", response_model=Dict[str, Any])
async def get_analysis_history(limit: int = 10, offset: int = 0):
    """获取分析历史记录."""
    try:
        # 这里可以实现历史记录查询
        # 目前返回模拟数据
        return {
            "success": True,
            "data": {
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            },
            "message": "获取历史记录成功",
            "timestamp": datetime.now()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史记录失败: {str(e)}") from e
