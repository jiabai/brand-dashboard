from datetime import UTC, datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.v1.models.schemas import (
    AvailableDatesResponse,
    BrandMentionRateData,
    BrandMentionRateResponse,
    BrandMentionTrendItem,
    BrandMentionTrendResponse,
    BrandMetricsItem,
    BrandMetricsResponse,
    CitationTypeStatsItem,
    CitationTypeStatsResponse,
    CitationTypeStatsSummary,
    CitationUrlData,
    CitationUrlResponse,
    DomainCitationRateItem,
    DomainCitationRateResponse,
    DomainCitationSummaryItem,
    DomainCitationSummaryResponse,
    FilterMetadataCombination,
    FilterMetadataData,
    FilterMetadataResponse,
    KeywordPlatformBrandRateItem,
    KeywordPlatformBrandRatesResponse,
    PlatformMentionRateData,
    PlatformMentionRateResponse,
    PlatformMetricsByBrandData,
    PlatformMetricsByBrandItem,
    PlatformMetricsByBrandResponse,
    PostCitationRateData,
    PostCitationRateResponse,
    TimeFrame,
)
from api.v1.repositories.database import (
    get_available_dates,
    get_date_range,
    query_brand_mention_data,
    query_brand_metrics,
    query_brand_platform_keyword_daily_mention_rates,
    query_brand_platform_mention_data,
    query_citation_type_stats,
    query_citation_url_stats,
    query_domain_citation_rate,
    query_domain_citation_summary,
    query_filter_metadata,
    query_keyword_platform_brand_rates,
    query_platform_metrics_by_brand,
    query_post_citation_rate,
)
from api.v1.utils.url_domain_resolver import resolve_url_domain

router = APIRouter()


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

        meta_date = date or datetime.now(UTC).strftime("%Y%m%d")
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
    timeframe: TimeFrame = Query(..., description="时间范围"),
    start_date: str = Query(..., description="开始日期(格式: YYYYMMDD)"),
    end_date: str = Query(..., description="结束日期(格式: YYYYMMDD)"),
):
    if timeframe == TimeFrame.SPECIFIC_DAY and (not start_date or not end_date):
        raise HTTPException(
            status_code=400,
            detail="timeframe=specific_day 时必须提供 start_date 和 end_date(YYYYMMDD)",
        )

    try:
        if timeframe == TimeFrame.SPECIFIC_DAY:
            query_start_date = datetime.strptime(start_date, "%Y%m%d").date()
            query_end_date = datetime.strptime(end_date, "%Y%m%d").date()
        else:
            query_start_date, query_end_date = get_date_range(timeframe.value)

        if query_start_date > query_end_date:
            raise ValueError("开始日期不能晚于结束日期")

        rows = query_brand_platform_keyword_daily_mention_rates(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            platform=platform,
            keyword=keyword,
            start_date=query_start_date,
            end_date=query_end_date,
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
                "tenant_key": tenant_key,
                "job_id": job_id,
                "timeframe": timeframe.value,
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
                "calculation_method": "mention_rate_by_day",
                "points": len(data),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取品牌提及率趋势失败: {str(e)}") from e

@router.get("/citation-url-stats", response_model=CitationUrlResponse)
async def get_citation_url_stats(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    keyword: str = Query(..., description="关键词"),
    domain: str = Query(..., description="域名"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    start_date: Optional[str] = Query(None, description="开始日期(格式: YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(格式: YYYYMMDD)"),
):
    """获取引用URL统计数据."""
    if timeframe == TimeFrame.SPECIFIC_DAY and (not start_date or not end_date):
        raise HTTPException(
            status_code=400,
            detail="timeframe=specific_day 时必须提供 start_date 和 end_date(YYYYMMDD)",
        )
    if timeframe == TimeFrame.SPECIFIC_DAY:
        query_start_date = datetime.strptime(start_date, "%Y%m%d").date()
        query_end_date = datetime.strptime(end_date, "%Y%m%d").date()
    else:
        query_start_date, query_end_date = get_date_range(timeframe.value)

    try:
        if query_start_date > query_end_date:
            raise ValueError("开始日期不能晚于结束日期")

        # 从数据库查询引用URL统计数据
        citation_data_list = query_citation_url_stats(
            tenant_key=tenant_key,
            job_id=job_id,
            keyword=keyword,
            domain=domain,
            start_date=query_start_date,
            end_date=query_end_date,
        )

        # 转换数据格式以匹配响应模型
        response_data = []
        for citation_data in citation_data_list:
            citation_count = citation_data["citation_count"]
            total_questions = citation_data["total_questions"]
            # 解析URL获取中文名称
            domain_info = resolve_url_domain(citation_data["url"])
            chinese_name = domain_info["chinese_name"]

            # 计算引用率
            citation_rate = (
                round(citation_count / total_questions * 100, 2)
                if total_questions > 0
                else 0.0
            )

            response_data.append(CitationUrlData(
                answer_reference_url=citation_data["url"],
                citation_count=citation_count,
                total_questions=total_questions,
                chinese_name=chinese_name,
                citation_rate=citation_rate
            ))

        return CitationUrlResponse(
            status="success",
            data=response_data,
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "keyword": keyword,
                "domain": domain,
                "timeframe": timeframe.value,
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
                "calculation_method": "citation_url_count",
                "url_count": len(response_data)
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取引用URL统计数据失败: {str(e)}") from e


@router.get("/citation-type-stats", response_model=CitationTypeStatsResponse)
async def get_citation_type_stats(
    tenant_key: str = Query(..., description="租户标识 tenant_key"),
    job_id: str = Query(..., description="任务ID"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    start_date: Optional[str] = Query(None, description="起始日期(格式: YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(格式: YYYYMMDD)"),
):
    if timeframe == TimeFrame.SPECIFIC_DAY and (not start_date or not end_date):
        raise HTTPException(
            status_code=400,
            detail="timeframe=specific_day 时必须提供 start_date 和 end_date(YYYYMMDD)",
        )

    try:
        if timeframe == TimeFrame.SPECIFIC_DAY:
            query_start_date = datetime.strptime(start_date, "%Y%m%d").date()
            query_end_date = datetime.strptime(end_date, "%Y%m%d").date()
        else:
            query_start_date, query_end_date = get_date_range(timeframe.value)

        if query_start_date > query_end_date:
            raise ValueError("开始日期不能晚于结束日期")

        summary, stats = query_citation_type_stats(
            tenant_key=tenant_key,
            job_id=job_id,
            start_date=query_start_date,
            end_date=query_end_date,
        )

        return CitationTypeStatsResponse(
            status="success",
            summary=CitationTypeStatsSummary(**summary),
            citation_type_stats=[
                CitationTypeStatsItem(**item) for item in stats
            ],
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "timeframe": timeframe.value,
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
                "calculation_method": "content_type_pct",
                "row_count": len(stats),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取引用类型占比统计失败: {str(e)}") from e


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
    start_date: Optional[str] = Query(None, description="起始日期(格式: YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(格式: YYYYMMDD)"),
    brand: Optional[str] = Query(None, description="品牌名称"),
    platform: Optional[str] = Query(None, description="平台名称"),
):
    if timeframe == TimeFrame.SPECIFIC_DAY and (not start_date or not end_date):
        raise HTTPException(
            status_code=400,
            detail="timeframe=specific_day 时必须提供 start_date 和 end_date(YYYYMMDD)",
        )

    try:
        if timeframe == TimeFrame.SPECIFIC_DAY:
            query_start_date = datetime.strptime(start_date, "%Y%m%d").date()
            query_end_date = datetime.strptime(end_date, "%Y%m%d").date()
        else:
            query_start_date, query_end_date = get_date_range(timeframe.value)

        if query_start_date > query_end_date:
            raise ValueError("开始日期不能晚于结束日期")

        metrics = query_brand_metrics(
            tenant_key=tenant_key,
            job_id=job_id,
            start_date=query_start_date,
            end_date=query_end_date,
            brand=brand,
            platform=platform,
        )

        data = [
            BrandMetricsItem(
                brand=item["brand"],
                mention_rate=item["mention_rate"],
                first_mention_rate=item["first_mention_rate"],
                top3_mention_rate=item["top3_mention_rate"],
                prompt_count=item["prompt_count"],
                keyword_coverage=item["keyword_coverage"],
            )
            for item in metrics
        ]

        return BrandMetricsResponse(
            status="success",
            data=data,
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "timeframe": timeframe.value,
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
                "calculation_method": "mention_count_ratio",
                "row_count": len(data),
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
    start_date: Optional[str] = Query(None, description="起始日期(格式: YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(格式: YYYYMMDD)"),
):
    if timeframe == TimeFrame.SPECIFIC_DAY and (not start_date or not end_date):
        raise HTTPException(
            status_code=400,
            detail="timeframe=specific_day 时必须提供 start_date 和 end_date(YYYYMMDD)",
        )

    try:
        if timeframe == TimeFrame.SPECIFIC_DAY:
            query_start_date = datetime.strptime(start_date, "%Y%m%d").date()
            query_end_date = datetime.strptime(end_date, "%Y%m%d").date()
        else:
            query_start_date, query_end_date = get_date_range(timeframe.value)

        if query_start_date > query_end_date:
            raise ValueError("开始日期不能晚于结束日期")

        platforms = query_platform_metrics_by_brand(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            start_date=query_start_date,
            end_date=query_end_date,
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
                "tenant_key": tenant_key,
                "job_id": job_id,
                "timeframe": timeframe.value,
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
                "calculation_method": "platform_metrics_by_brand",
                "row_count": len(platforms),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取平台指标失败: {str(e)}") from e

@router.get("/citation-domain-stats", response_model=DomainCitationRateResponse)
async def get_domain_citation_rate(
    tenant_key: str = Query(..., description="租户标识 tenant_key"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(
        ...,
        description="时间范围，可选值: yesterday, 7days, 30days, specific_day",
    ),
    start_date: Optional[str] = Query(
        None,
        description="起始日期，格式: YYYYMMDD（当 timeframe=specific_day 时必填）",
    ),
    end_date: Optional[str] = Query(
        None,
        description="结束日期，格式: YYYYMMDD（当 timeframe=specific_day 时必填）",
    ),
    keyword: Optional[str] = Query(
        None,
        description="关键词，用于筛选引用信源",
    ),
    platform: Optional[str] = Query(
        None,
        description="中国大模型平台，可选值: deepseek, 千问, 豆包, 元宝",
    ),
):
    if timeframe == TimeFrame.SPECIFIC_DAY and (not start_date or not end_date):
        raise HTTPException(
            status_code=400,
            detail="timeframe=specific_day 时必须提供 start_date 和 end_date(YYYYMMDD)",
        )

    try:
        if timeframe == TimeFrame.SPECIFIC_DAY:
            query_start_date = datetime.strptime(start_date, "%Y%m%d").date()
            query_end_date = datetime.strptime(end_date, "%Y%m%d").date()
        else:
            query_start_date, query_end_date = get_date_range(timeframe.value)

        if query_start_date > query_end_date:
            raise ValueError("开始日期不能晚于结束日期")

        domain_distribution = query_domain_citation_rate(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            start_date=query_start_date,
            end_date=query_end_date,
            keyword=keyword,
            platform=platform
        )

        return DomainCitationRateResponse(
            status="success",
            domain_distribution=[
                DomainCitationRateItem(
                    domain=item["domain"],
                    chinese_name=item["chinese_name"],
                    keywords=item["keywords"],
                    content_types=item["content_types"],
                    platforms=item["platforms"],
                    domain_citation_rate=item["domain_citation_rate"],
                )
                for item in domain_distribution
            ],
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "keyword": keyword,
                "platform": platform,
                "timeframe": timeframe.value,
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
                "calculation_method": "domain_citation_rate",
                "row_count": len(domain_distribution),
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取域名引用率失败: {str(e)}") from e


@router.get("/citation-domain-summary", response_model=DomainCitationSummaryResponse)
async def get_domain_citation_summary(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    start_date: Optional[str] = Query(None, description="起始日期(格式: YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(格式: YYYYMMDD)"),
):
    """获取域名维度的引用率汇总，按域名聚合，适配前端 ReferencesTable 组件."""
    if timeframe == TimeFrame.SPECIFIC_DAY and (not start_date or not end_date):
        raise HTTPException(
            status_code=400,
            detail="timeframe=specific_day 时必须提供 start_date 和 end_date(YYYYMMDD)",
        )

    try:
        if timeframe == TimeFrame.SPECIFIC_DAY:
            query_start_date = datetime.strptime(start_date, "%Y%m%d").date()
            query_end_date = datetime.strptime(end_date, "%Y%m%d").date()
        else:
            query_start_date, query_end_date = get_date_range(timeframe.value)

        if query_start_date > query_end_date:
            raise ValueError("开始日期不能晚于结束日期")

        domain_distribution = query_domain_citation_summary(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            start_date=query_start_date,
            end_date=query_end_date,
        )

        return DomainCitationSummaryResponse(
            status="success",
            domain_distribution=[
                DomainCitationSummaryItem(
                    domain=item["domain"],
                    chinese_name=item["chinese_name"],
                    citation_count=item["citation_count"],
                    keyword_coverage=item["keyword_coverage"],
                    platform_coverage=item["platform_coverage"],
                    domain_citation_rate=item["domain_citation_rate"],
                )
                for item in domain_distribution
            ],
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "brand": brand,
                "timeframe": timeframe.value,
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
                "calculation_method": "domain_citation_summary",
                "row_count": len(domain_distribution),
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取域名引用率汇总失败: {str(e)}") from e


@router.get("/post-citation-rate", response_model=PostCitationRateResponse)
async def get_post_citation_rate(
    tenant_key: str = Query(..., description="租户唯一字符串标识"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    start_date: Optional[str] = Query(None, description="起始日期(格式: YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(格式: YYYYMMDD)"),
):
    """获取品牌发文引用率信息."""
    if timeframe == TimeFrame.SPECIFIC_DAY and (not start_date or not end_date):
        raise HTTPException(
            status_code=400,
            detail="timeframe=specific_day 时必须提供 start_date 和 end_date(YYYYMMDD)",
        )

    try:
        if timeframe == TimeFrame.SPECIFIC_DAY:
            query_start_date = datetime.strptime(start_date, "%Y%m%d").date()
            query_end_date = datetime.strptime(end_date, "%Y%m%d").date()
        else:
            query_start_date, query_end_date = get_date_range(timeframe.value)

        if query_start_date > query_end_date:
            raise ValueError("开始日期不能晚于结束日期")

        data = query_post_citation_rate(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            start_date=query_start_date,
            end_date=query_end_date,
        )

        return PostCitationRateResponse(
            status="success",
            data=[PostCitationRateData(**data)],
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "timeframe": timeframe.value,
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
                "calculation_method": "post_citation_rate",
                "row_count": 1,
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
    start_date: Optional[str] = Query(None, description="起始日期(格式: YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(格式: YYYYMMDD)"),
):
    if timeframe == TimeFrame.SPECIFIC_DAY and (not start_date or not end_date):
        raise HTTPException(
            status_code=400,
            detail="timeframe=specific_day 时必须提供 start_date 和 end_date(YYYYMMDD)",
        )

    try:
        if timeframe == TimeFrame.SPECIFIC_DAY:
            query_start_date = datetime.strptime(start_date, "%Y%m%d").date()
            query_end_date = datetime.strptime(end_date, "%Y%m%d").date()
        else:
            query_start_date, query_end_date = get_date_range(timeframe.value)

        if query_start_date > query_end_date:
            raise ValueError("开始日期不能晚于结束日期")

        rows = query_keyword_platform_brand_rates(
            tenant_key=tenant_key,
            job_id=job_id,
            start_date=query_start_date,
            end_date=query_end_date,
        )

        data = [
            KeywordPlatformBrandRateItem(
                keyword=item["keyword"],
                platform=item["platform"],
                brand=item["brand"],
                mention_rate=item["mention_rate"],
                first_mention_rate=item["first_mention_rate"],
                top3_mention_rate=item["top3_mention_rate"],
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
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
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
