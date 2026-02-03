from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from api.v1.repositories.database import (
    get_available_dates,
    query_brand_mention_data,
    query_brand_metrics,
    query_brand_platform_keyword_daily_mention_rates,
    query_brand_platform_mention_data,
    query_domain_citation_rate,
    query_filter_metadata,
    query_keyword_platform_brand_rates,
    query_platform_metrics_by_brand,
    query_post_citation_rate,
    query_reference_url_stats,
)
from api.v1.utils.url_domain_resolver import resolve_url_domain

router = APIRouter()

class TimeFrame(str, Enum):
    """时间范围枚举."""
    YESTERDAY = "yesterday"
    DAYS_7 = "7days"
    DAYS_30 = "30days"
    SPECIFIC_DAY = "specific_day"

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
    first_mention_rate: float = Field(..., description="该平台上的品牌首位提及率(百分比)")
    color: str = Field(..., description="颜色")

class PlatformMentionRateResponse(BaseModel):
    """各平台提及率响应模型."""
    status: str = Field(..., description="响应状态")
    data: List[PlatformMentionRateData] = Field(..., description="各平台提及率数据列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class KeywordPlatformBrandRateItem(BaseModel):
    keyword: str = Field(..., description="关键词")
    platform: str = Field(..., description="平台")
    brand: str = Field(..., description="品牌")
    mention_rate: float = Field(..., description="提及率(比例，0~1)")
    first_mention_rate: float = Field(..., description="首位提及率(比例，0~1)")


class KeywordPlatformBrandRatesResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[KeywordPlatformBrandRateItem] = Field(..., description="数据列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class BrandMentionTrendItem(BaseModel):
    date: str = Field(..., description="日期")
    brand: str = Field(..., description="品牌")
    platform: str = Field(..., description="平台")
    keyword: str = Field(..., description="关键词")
    mention_rate: float = Field(..., description="提及率(比例，0~1)")


class BrandMentionTrendResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[BrandMentionTrendItem] = Field(..., description="趋势数据列表")
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


class AvailableDatesResponse(BaseModel):
    """有数据日期响应模型."""
    status: str = Field(..., description="响应状态")
    data: List[str] = Field(..., description="日期列表 (YYYY-MM-DD)")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class FilterMetadataCombination(BaseModel):
    platform: str = Field(..., description="平台名称")
    keyword: str = Field(..., description="关键词")


class FilterMetadataData(BaseModel):
    platforms: List[str] = Field(..., description="平台列表（去重）")
    keywords: List[str] = Field(..., description="关键词列表（去重）")
    combinations: List[FilterMetadataCombination] = Field(
        ...,
        description="有效的平台与关键词组合列表",
    )


class FilterMetadataResponse(BaseModel):
    code: int = Field(..., description="状态码")
    message: str = Field(..., description="状态信息")
    data: FilterMetadataData = Field(..., description="筛选元数据")


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


class DomainCitationRateItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    domain: str = Field(..., description="域名")
    domain_citation_rate: float = Field(
        ...,
        alias="domain-citation-rate",
        description="域名引用率",
    )


class DomainCitationRateResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    domain_distribution: List[DomainCitationRateItem] = Field(..., description="域名引用率分布")
    metadata: Dict[str, Any] = Field(..., description="元数据")


class PostCitationRateData(BaseModel):
    brand: str = Field(..., description="品牌名称")
    citation_source_count: int = Field(..., description="引用来源数量")
    citation_rate_by_post: float = Field(..., description="发文引用率（有发文引用的对话占比）")


class PostCitationRateResponse(BaseModel):
    status: str = Field(..., description="响应状态")
    data: List[PostCitationRateData] = Field(..., description="数据列表")
    metadata: Dict[str, Any] = Field(..., description="元数据")

@router.get("/brand-mention-rate", response_model=BrandMentionRateResponse)
async def get_brand_mention_rate(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)")
):
    """获取品牌总提及率数据."""
    try:
        # 从数据库查询真实数据
        db_data = query_brand_mention_data(
            tenant_key=tenant_key,
            job_id=job_id,
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
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
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
            tenant_key=tenant_key,
            job_id=job_id,
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

@router.get("/brand-mention-trend", response_model=BrandMentionTrendResponse)
async def get_brand_mention_trend(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    platform: str = Query(..., description="平台名称"),
    keyword: str = Query(..., description="关键词"),
    start_date: str = Query(..., description="开始日期(格式: YYYYMMDD)"),
    end_date: str = Query(..., description="结束日期(格式: YYYYMMDD)"),
):
    try:
        start_value = datetime.strptime(start_date, "%Y%m%d").date()
        end_value = datetime.strptime(end_date, "%Y%m%d").date()

        if start_value > end_value:
            raise ValueError("开始日期不能晚于结束日期")

        rows = query_brand_platform_keyword_daily_mention_rates(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            platform=platform,
            keyword=keyword,
            start_date=start_value,
            end_date=end_value,
        )

        data: List[BrandMentionTrendItem] = []
        for row in rows:
            row_date = row["date"]
            if hasattr(row_date, "strftime"):
                date_key = row_date.strftime("%Y%m%d")
            else:
                date_key = str(row_date).replace("-", "")

            mention_rate = float(row["mention_rate"]) if row["mention_rate"] is not None else 0.0
            data.append(
                BrandMentionTrendItem(
                    date=date_key,
                    brand=brand,
                    platform=platform,
                    keyword=keyword,
                    mention_rate=mention_rate,
                )
            )

        return BrandMentionTrendResponse(
            status="success",
            data=data,
            metadata={
                "brand": brand,
                "platform": platform,
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
                "calculation_method": "mention_rate_by_day",
                "points": len(data),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取品牌提及率趋势失败: {str(e)}") from e

@router.get("/reference-url-stats", response_model=ReferenceUrlResponse)
async def get_reference_url_stats(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)")
):
    """获取引用URL统计数据."""
    try:
        # 从数据库查询引用URL统计数据
        reference_data_list = query_reference_url_stats(
            tenant_key=tenant_key,
            job_id=job_id,
            timeframe=timeframe.value,
            specific_date=date
        )

        # 转换数据格式以匹配响应模型
        response_data = []
        for reference_data in reference_data_list:
            reference_count = reference_data["reference_count"]
            total_questions = reference_data["total_questions"]
            # 解析URL获取中文名称
            domain_info = resolve_url_domain(reference_data["url"])
            chinese_name = domain_info["chinese_name"]

            # 计算引用率
            reference_rate = (
                round(reference_count / total_questions * 100, 2)
                if total_questions > 0
                else 0.0
            )

            response_data.append(ReferenceUrlData(
                answer_reference_url=reference_data["url"],
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


@router.get("/filter-metadata", response_model=FilterMetadataResponse)
async def get_filter_metadata(
    tenant_key: str = Query(..., description="租户标识（安全校验）"),
    job_id: str = Query(..., description="任务唯一标识"),
    start_date: Optional[str] = Query(None, description="开始日期(格式: YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(格式: YYYYMMDD)"),
):
    try:
        rows = query_filter_metadata(
            tenant_key=tenant_key,
            job_id=job_id,
            start_date=start_date,
            end_date=end_date,
        )

        platforms: List[str] = []
        keywords: List[str] = []
        combinations: List[FilterMetadataCombination] = []
        seen_platforms = set()
        seen_keywords = set()

        for row in rows:
            platform = row["platform"]
            keyword = row["keyword"]
            if platform not in seen_platforms:
                platforms.append(platform)
                seen_platforms.add(platform)
            if keyword not in seen_keywords:
                keywords.append(keyword)
                seen_keywords.add(keyword)
            combinations.append(
                FilterMetadataCombination(platform=platform, keyword=keyword)
            )

        return FilterMetadataResponse(
            code=200,
            message="success",
            data=FilterMetadataData(
                platforms=platforms,
                keywords=keywords,
                combinations=combinations,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取筛选元数据失败: {str(e)}") from e


@router.get("/available-dates", response_model=AvailableDatesResponse)
async def get_dashboard_available_dates(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: Optional[str] = Query(None, description="任务ID")
):
    """获取仪表盘有数据的日期列表."""
    try:
        dates = get_available_dates(tenant_key, job_id)
        return AvailableDatesResponse(
            status="success",
            data=dates,
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "count": len(dates)
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取可用日期失败: {str(e)}") from e


@router.get("/brand-metrics", response_model=BrandMetricsResponse)
async def get_brand_metrics(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)"),
    brand: Optional[str] = Query(None, description="品牌名称"),
    platform: Optional[str] = Query(None, description="平台名称"),
):
    try:
        metrics = query_brand_metrics(
            tenant_key=tenant_key,
            job_id=job_id,
            timeframe=timeframe.value,
            specific_date=date,
            brand=brand,
            platform=platform,
        )

        data = [
            BrandMetricsItem(
                brand=item["brand"],
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
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)"),
):
    try:
        platforms = query_platform_metrics_by_brand(
            tenant_key=tenant_key,
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


@router.get("/domain-citation-rate", response_model=DomainCitationRateResponse)
async def get_domain_citation_rate(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)"),
):
    try:
        domain_distribution = query_domain_citation_rate(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            timeframe=timeframe.value,
            specific_date=date,
        )

        return DomainCitationRateResponse(
            status="success",
            domain_distribution=[
                DomainCitationRateItem(
                    domain=item["domain"],
                    domain_citation_rate=item["domain_citation_rate"],
                )
                for item in domain_distribution
            ],
            metadata={
                "timeframe": timeframe.value,
                "calculation_method": "domain_citation_rate",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取域名引用率失败: {str(e)}") from e


@router.get("/post-citation-rate", response_model=PostCitationRateResponse)
async def get_post_citation_rate(
    tenant_key: str = Query(..., description="租户唯一字符串标识"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)")
):
    """获取品牌发文引用率信息."""
    try:
        data = query_post_citation_rate(
            tenant_key=tenant_key,
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


@router.get(
    "/keyword-platform-brand-rates",
    response_model=KeywordPlatformBrandRatesResponse,
)
async def get_keyword_platform_brand_rates(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)"),
):
    if timeframe == TimeFrame.SPECIFIC_DAY and not date:
        raise HTTPException(
            status_code=400,
            detail="timeframe=specific_day 时必须提供 date(YYYYMMDD)",
        )

    try:
        rows = query_keyword_platform_brand_rates(
            tenant_key=tenant_key,
            job_id=job_id,
            timeframe=timeframe.value,
            specific_date=date,
        )

        data = [
            KeywordPlatformBrandRateItem(
                keyword=item["keyword"],
                platform=item["platform"],
                brand=item["brand"],
                mention_rate=item["mention_rate"],
                first_mention_rate=item["first_mention_rate"],
            )
            for item in rows
        ]

        return KeywordPlatformBrandRatesResponse(
            status="success",
            data=data,
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "timeframe": timeframe.value,
                "date": date,
                "calculation_method": "distinct_conversation_ratio",
                "rate_unit": "ratio_0_1",
                "row_count": len(data),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取 keyword-platform-brand rates 失败: {str(e)}",
        ) from e
