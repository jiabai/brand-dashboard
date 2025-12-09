"""Dashboard相关API路由."""

import sys
import os
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from brand_analysis_api.repositories.database import (
    query_brand_mention_data,
    query_brand_platform_mention_data,
    query_reference_url_stats
)
from brand_analysis_api.utils.url_domain_resolver import resolve_url_domain

router = APIRouter()

class TimeFrame(str, Enum):
    """时间范围枚举."""
    YESTERDAY = "yesterday"
    DAYS_7 = "7days"
    DAYS_30 = "30days"

class BrandMentionRateData(BaseModel):
    """品牌总提及率数据模型."""
    mention_rate: float = Field(..., description="品牌总提及率(百分比)")
    rank: int = Field(..., description="品牌排名")
    change: float = Field(..., description="与上一周期对比的变化(百分比)")
    question_count: int = Field(..., description="问题总数")
    mention_count: int = Field(..., description="品牌提及数量")
    first_mention_count: int = Field(..., description="首次提及品牌数量")
    analysis_date: str = Field(..., description="分析日期")
    last_updated: datetime = Field(..., description="最后更新时间")

class BrandMentionRateResponse(BaseModel):
    """品牌总提及率响应模型."""
    status: str = Field(..., description="响应状态")
    data: BrandMentionRateData = Field(..., description="品牌总提及率数据")
    metadata: Dict[str, Any] = Field(..., description="元数据")

class PlatformMentionRateData(BaseModel):
    """各平台提及率数据模型."""
    name: str = Field(..., description="平台名称")
    rate: float = Field(..., description="提及率")
    color: str = Field(..., description="颜色")

class PlatformMentionRateResponse(BaseModel):
    """各平台提及率响应模型."""
    status: str = Field(..., description="响应状态")
    data: List[PlatformMentionRateData] = Field(..., description="各平台提及率数据列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class ReferenceUrlData(BaseModel):
    """引用URL统计数据模型."""
    answer_reference_url: str = Field(..., description="引用URL")
    reference_count: int = Field(..., description="引用次数")
    total_questions: int = Field(..., description="总提问数")
    chinese_name: str = Field(..., description="中文名称")
    reference_rate: float = Field(..., description="引用率(引用次数/总提问数)")


class ReferenceUrlResponse(BaseModel):
    """引用URL统计响应模型."""
    status: str = Field(..., description="响应状态")
    data: List[ReferenceUrlData] = Field(..., description="引用URL统计数据列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")

@router.get("/brand-mention-rate", response_model=BrandMentionRateResponse)
async def get_brand_mention_rate(
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)")
):
    """获取品牌总提及率数据."""
    try:
        # 从数据库查询真实数据
        db_data = query_brand_mention_data(
            brand=brand,
            timeframe=timeframe.value,
            specific_date=date
        )

        # 转换数据格式以匹配响应模型
        response_data = {
            "mention_rate": db_data["mention_rate"],
            "rank": db_data["rank"],
            "change": db_data["change"],
            "question_count": db_data["question_count"],
            "mention_count": db_data["mention_count"],
            "first_mention_count": db_data["first_mention_count"],
            "analysis_date": db_data["analysis_date"],
            "last_updated": datetime.fromisoformat(db_data["last_updated"])
        }

        return BrandMentionRateResponse(
            status="success",
            data=BrandMentionRateData(**response_data),
            metadata={
                "timeframe": timeframe.value,
                "calculation_method": "mention_count_ratio"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取品牌总提及率失败: {str(e)}") from e

@router.get("/platform-mention-rates", response_model=PlatformMentionRateResponse)
async def get_platform_mention_rates(
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)")
):
    """获取品牌在各平台的提及率数据."""
    try:
        # 从数据库查询各平台数据
        platform_data_list = query_brand_platform_mention_data(
            brand=brand,
            timeframe=timeframe.value,
            specific_date=date
        )
        # 转换数据格式以匹配响应模型
        response_data = []
        for platform_data in platform_data_list:
            # 为不同平台分配颜色
            platform_colors = {
                "ChatGPT": "#10b981",
                "Gemini": "#3b82f6", 
                "Claude": "#f59e0b",
                "通义千问": "#ef4444",
                "豆包": "#8b5cf6",
                "DeepSeek": "#06b6d4",
                "Kimi": "#a855f7",
                "元宝": "#f97316",
                "夸克": "#ec4899",
                "文心一言": "#6b7280"
            }

            response_data.append(PlatformMentionRateData(
                name=platform_data["platform"],
                rate=platform_data["mention_rate"],
                color=platform_colors.get(platform_data["platform"], "#6b7280")
            ))
        return PlatformMentionRateResponse(
            status="success",
            data=response_data,
            metadata={
                "timeframe": timeframe.value,
                "calculation_method": "platform_mention_rate",
                "platform_count": len(response_data)
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取品牌平台提及率失败: {str(e)}") from e

@router.get("/reference-url-stats", response_model=ReferenceUrlResponse)
async def get_reference_url_stats(
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)")
):
    """获取引用URL统计数据."""
    try:
        # 从数据库查询引用URL统计数据
        reference_data_list = query_reference_url_stats(
            timeframe=timeframe.value,
            specific_date=date
        )

        # 转换数据格式以匹配响应模型
        response_data = []
        for reference_data in reference_data_list:
            # 解析URL获取中文名称
            domain_info = resolve_url_domain(reference_data["answer_reference_url"])
            chinese_name = domain_info["chinese_name"]
            
            # 计算引用率
            reference_rate = round(reference_data["reference_count"] / reference_data["total_questions"] * 100, 2) if reference_data["total_questions"] > 0 else 0.0
            
            response_data.append(ReferenceUrlData(
                answer_reference_url=reference_data["answer_reference_url"],
                reference_count=reference_data["reference_count"],
                total_questions=reference_data["total_questions"],
                chinese_name=chinese_name,
                reference_rate=reference_rate
            ))

        return ReferenceUrlResponse(
            status="success",
            data=response_data,
            metadata={
                "timeframe": timeframe.value,
                "calculation_method": "reference_url_count",
                "url_count": len(response_data)
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取引用URL统计数据失败: {str(e)}") from e
