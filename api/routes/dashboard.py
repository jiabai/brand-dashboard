from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.repositories.database import (
    query_brand_mention_data,
    query_brand_metrics,
    query_brand_platform_mention_data,
    query_platform_metrics_by_brand,
    query_post_citation_rate,
    query_reference_url_stats,
)
from api.utils.url_domain_resolver import resolve_url_domain

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
    mention_rate: float = Field(..., description="该平台上的品牌提及率(百分比)")
    first_mention_rate: float = Field(..., description="该平台上的品牌首次提及率(百分比)")
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


class BrandMetricsItem(BaseModel):
    brand: str = Field(..., description="品牌名称")
    platform: str = Field(..., description="平台名称")
    mention_rate: float = Field(..., description="品牌总提及率")
    first_mention_rate: float = Field(..., description="首次提及品牌率")
    citation_rate_by_post: float = Field(..., description="引用率")
    prompt_count: int = Field(..., description="问题总数")
    citation_source_count: int = Field(..., description="引用来源数量")
    keyword_coverage: int = Field(..., description="关键词覆盖数")


class BrandMetricsResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[BrandMetricsItem] = Field(..., description="品牌总指标列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class PlatformMetricsByBrandItem(BaseModel):
    platform: str = Field(..., description="平台名称")
    mention_rate: float = Field(..., description="平台提及率")


class PlatformMetricsByBrandData(BaseModel):
    brand: str = Field(..., description="品牌名称")
    platforms: List[PlatformMetricsByBrandItem] = Field(..., description="平台指标列表")


class PlatformMetricsByBrandResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: PlatformMetricsByBrandData = Field(..., description="品牌平台指标数据")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class PostCitationRateData(BaseModel):
    brand: str = Field(..., description="品牌名称")
    citation_source_count: int = Field(..., description="引用来源数量")
    citation_rate_by_post: float = Field(..., description="发文引用率")


class PostCitationRateResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[PostCitationRateData] = Field(..., description="数据列表")
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
    category: str = Query(..., description="商品大类"),
    brand: str = Query(..., description="品牌名称"),
    keyword: str = Query(..., description='品牌关键词，或"全部"'),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)")
):
    """获取品牌在各平台的提及率数据."""
    try:
        # 从数据库查询各平台数据
        platform_data_list = query_brand_platform_mention_data(
            brand=brand,
            category=category,
            keyword=keyword,
            timeframe=timeframe.value,
            specific_date=date
        )

        platform_colors = {
            "ChatGPT": "#10b981",
            "Gemini": "#3b82f6",
            "Claude": "#f59e0b",
            "通义千问": "#ef4444",
            "Qwen": "#ef4444",
            "豆包": "#8b5cf6",
            "DeepSeek": "#06b6d4",
            "Deepseek": "#06b6d4",
            "Kimi": "#a855f7",
            "元宝": "#f97316",
            "夸克": "#ec4899",
            "文心一言": "#6b7280",
        }

        # 转换数据格式以匹配响应模型
        response_data = []
        for platform_data in platform_data_list:
            platform_name = platform_data["platform"]
            response_data.append(
                PlatformMentionRateData(
                    name=platform_name,
                    mention_rate=platform_data["mention_rate"],
                    first_mention_rate=platform_data["first_mention_rate"],
                    color=platform_colors.get(platform_name, "#6b7280"),
                )
            )

        meta_date = date or datetime.now().strftime("%Y%m%d")
        total_queries = sum((p["query_count"] for p in platform_data_list), start=0)

        return PlatformMentionRateResponse(
            status="success",
            data=response_data,
            metadata={
                "category": category,
                "brand": brand,
                "keyword": keyword,
                "timeframe": timeframe.value,
                "date": meta_date,
                "calculation_method": "platform_mention_rate",
                "platform_count": len(response_data),
                "queries": total_queries,
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
            reference_count = reference_data["reference_count"]
            total_questions = reference_data["total_questions"]
            # 解析URL获取中文名称
            domain_info = resolve_url_domain(reference_data["answer_reference_url"])
            chinese_name = domain_info["chinese_name"]
            
            # 计算引用率
            reference_rate = (
                round(reference_count / total_questions * 100, 2)
                if total_questions > 0
                else 0.0
            )
            
            response_data.append(ReferenceUrlData(
                answer_reference_url=reference_data["answer_reference_url"],
                reference_count=reference_count,
                total_questions=total_questions,
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


@router.get("/brand-metrics", response_model=BrandMetricsResponse)
async def get_brand_metrics(
    user_id: str = Query(..., description="用户ID"),
    job_id: str = Query(..., description="任务ID"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)"),
    brand: Optional[str] = Query(None, description="品牌名称"),
):
    try:
        metrics = query_brand_metrics(
            user_id=user_id,
            job_id=job_id,
            timeframe=timeframe.value,
            specific_date=date,
            brand=brand,
        )

        data = [
            BrandMetricsItem(
                brand=item["brand"],
                platform=item["platform"],
                mention_rate=item["mention_rate"],
                first_mention_rate=item["first_mention_rate"],
                citation_rate_by_post=item["citation_rate_by_post"],
                prompt_count=item["prompt_count"],
                citation_source_count=item["citation_source_count"],
                keyword_coverage=item["keyword_coverage"],
            )
            for item in metrics
        ]

        return BrandMetricsResponse(
            status="success",
            data=data,
            metadata={
                "timeframe": timeframe.value,
                "calculation_method": "mention_count_ratio",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取品牌总指标失败: {str(e)}") from e


@router.get("/platform-metrics-by-brand", response_model=PlatformMetricsByBrandResponse)
async def get_platform_metrics_by_brand(
    user_id: str = Query(..., description="用户ID"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)"),
):
    try:
        platforms = query_platform_metrics_by_brand(
            user_id=user_id,
            job_id=job_id,
            brand=brand,
            timeframe=timeframe.value,
            specific_date=date,
        )

        return PlatformMetricsByBrandResponse(
            status="success",
            data=PlatformMetricsByBrandData(
                brand=brand,
                platforms=[
                    PlatformMetricsByBrandItem(
                        platform=item["platform"],
                        mention_rate=item["mention_rate"],
                    )
                    for item in platforms
                ],
            ),
            metadata={
                "timeframe": timeframe.value,
                "calculation_method": "platform_metrics_by_brand",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取平台指标失败: {str(e)}") from e


@router.get("/post-citation-rate", response_model=PostCitationRateResponse)
async def get_post_citation_rate(
    user_id: str = Query(..., description="用户ID"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)")
):
    """获取品牌发文引用率信息."""
    try:
        data = query_post_citation_rate(
            user_id=user_id,
            job_id=job_id,
            brand=brand,
            timeframe=timeframe.value,
            specific_date=date
        )

        return PostCitationRateResponse(
            status="success",
            data=[PostCitationRateData(**data)],
            metadata={
                "timeframe": timeframe.value,
                "calculation_method": "post_citation_rate"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取品牌发文引用率失败: {str(e)}") from e
