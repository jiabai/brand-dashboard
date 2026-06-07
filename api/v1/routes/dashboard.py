from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Engine

from api.v1.dependencies.auth import get_current_tenant_for_dashboard_read
from api.v1.models.schemas import (
    AnswerSnapshotsResponse,
    AvailableDatesResponse,
    BrandMentionTrendResponse,
    BrandMetricsResponse,
    CitationTypeStatsResponse,
    CitationUrlResponse,
    DomainCitationRateResponse,
    DomainCitationSummaryResponse,
    FilterMetadataResponse,
    KeywordPlatformBrandRatesResponse,
    PlatformMentionRateResponse,
    PlatformMetricsByBrandResponse,
    PostCitationRateResponse,
    TimeFrame,
)
from api.v1.repositories.connection import get_engine
from api.v1.services.dashboard_service import DashboardService

get_current_tenant = get_current_tenant_for_dashboard_read

router = APIRouter(dependencies=[Depends(get_current_tenant)])


def get_dashboard_service(engine: Engine = Depends(get_engine)) -> DashboardService:
    return DashboardService(engine)


def _build_metadata(**kwargs):
    """构建统一的 metadata 字典，过滤 None 值。"""
    return {k: v for k, v in kwargs.items() if v is not None}


@router.get("/platform-mention-rates", response_model=PlatformMentionRateResponse)
async def get_platform_mention_rates(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    category: str = Query(..., description="商品大类"),
    brand: str = Query(..., description="品牌名称"),
    keyword: str = Query(..., description='品牌关键词，或"全部"'),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    date: Optional[str] = Query(None, description="具体日期(格式: YYYYMMDD)"),
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        response_data, total_queries = service.get_platform_mention_rates(
            tenant_key=tenant_key,
            job_id=job_id,
            category=category,
            brand=brand,
            keyword=keyword,
            timeframe=timeframe,
            date=date,
        )
        meta_date = date or datetime.now(UTC).strftime("%Y%m%d")
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
            },
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
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        query_start_date, query_end_date = service.resolve_date_range(
            timeframe, start_date, end_date,
        )
        data = service.get_brand_mention_trend(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            platform=platform,
            keyword=keyword,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
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
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        query_start_date, query_end_date = service.resolve_date_range(
            timeframe, start_date, end_date,
        )
        response_data = service.get_citation_url_stats(
            tenant_key=tenant_key,
            job_id=job_id,
            keyword=keyword,
            domain=domain,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
        )
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
                "url_count": len(response_data),
            },
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
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        query_start_date, query_end_date = service.resolve_date_range(
            timeframe, start_date, end_date,
        )
        summary, stats = service.get_citation_type_stats(
            tenant_key=tenant_key,
            job_id=job_id,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
        )
        return CitationTypeStatsResponse(
            status="success",
            summary=summary,
            citation_type_stats=stats,
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
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        data = service.get_filter_metadata(
            tenant_key=tenant_key,
            job_id=job_id,
            start_date=start_date,
            end_date=end_date,
        )
        return FilterMetadataResponse(code=200, message="success", data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取筛选元数据失败: {str(e)}") from e


@router.get("/available-dates", response_model=AvailableDatesResponse)
async def get_dashboard_available_dates(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: Optional[str] = Query(None, description="任务ID"),
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        dates = service.get_available_dates(tenant_key, job_id)
        return AvailableDatesResponse(
            status="success",
            data=dates,
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "count": len(dates),
            },
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
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        query_start_date, query_end_date = service.resolve_date_range(
            timeframe, start_date, end_date,
        )
        metrics = service.get_brand_metrics(
            tenant_key=tenant_key,
            job_id=job_id,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
            brand=brand,
            platform=platform,
        )
        snapshot_metadata = service.get_metric_snapshot_metadata(
            tenant_key=tenant_key,
            job_id=job_id,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
        )
        return BrandMetricsResponse(
            status="success",
            data=metrics,
            metadata=_build_metadata(
                tenant_key=tenant_key,
                job_id=job_id,
                timeframe=timeframe.value,
                start_date=query_start_date.strftime("%Y%m%d"),
                end_date=query_end_date.strftime("%Y%m%d"),
                calculation_method="mention_count_ratio",
                row_count=len(metrics),
                **snapshot_metadata,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取品牌总指标失败: {str(e)}") from e


@router.get("/answer-snapshots", response_model=AnswerSnapshotsResponse)
async def get_answer_snapshots(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    start_date: Optional[str] = Query(None, description="起始日期(格式: YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(格式: YYYYMMDD)"),
    brand: Optional[str] = Query(None, description="品牌名称"),
    platform: Optional[str] = Query(None, description="平台名称"),
    keyword: Optional[str] = Query(None, description="关键词"),
    sentiment: Optional[str] = Query(None, description="情绪状态"),
    has_reference: Optional[bool] = Query(None, description="是否有引用"),
    limit: int = Query(50, ge=1, le=100, description="返回条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        query_start_date, query_end_date = service.resolve_date_range(
            timeframe, start_date, end_date,
        )
        data, total_count = service.get_answer_snapshots(
            tenant_key=tenant_key,
            job_id=job_id,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
            brand=brand,
            platform=platform,
            keyword=keyword,
            sentiment=sentiment,
            has_reference=has_reference,
            limit=limit,
            offset=offset,
        )
        return AnswerSnapshotsResponse(
            status="success",
            data=data,
            metadata=_build_metadata(
                tenant_key=tenant_key,
                job_id=job_id,
                timeframe=timeframe.value,
                start_date=query_start_date.strftime("%Y%m%d"),
                end_date=query_end_date.strftime("%Y%m%d"),
                brand=brand,
                platform=platform,
                keyword=keyword,
                sentiment=sentiment,
                has_reference=has_reference,
                limit=limit,
                offset=offset,
                row_count=len(data),
                total_count=total_count,
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取问答快照失败: {str(e)}") from e


@router.get("/platform-metrics-by-brand", response_model=PlatformMetricsByBrandResponse)
async def get_platform_metrics_by_brand(
    tenant_key: str = Query(..., description="租户唯一字符串标识（tenants.tenant_key）"),
    job_id: str = Query(..., description="任务ID"),
    brand: str = Query(..., description="品牌名称"),
    timeframe: TimeFrame = Query(..., description="时间范围"),
    start_date: Optional[str] = Query(None, description="起始日期(格式: YYYYMMDD)"),
    end_date: Optional[str] = Query(None, description="结束日期(格式: YYYYMMDD)"),
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        query_start_date, query_end_date = service.resolve_date_range(
            timeframe, start_date, end_date,
        )
        data = service.get_platform_metrics_by_brand(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
        )
        return PlatformMetricsByBrandResponse(
            status="success",
            data=data,
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "timeframe": timeframe.value,
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
                "calculation_method": "platform_metrics_by_brand",
                "row_count": len(data.platforms),
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
    keyword: Optional[str] = Query(None, description="关键词，用于筛选引用信源"),
    platform: Optional[str] = Query(None, description="中国大模型平台"),
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        query_start_date, query_end_date = service.resolve_date_range(
            timeframe, start_date, end_date,
        )
        domain_distribution = service.get_domain_citation_rate(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
            keyword=keyword,
            platform=platform,
        )
        return DomainCitationRateResponse(
            status="success",
            domain_distribution=domain_distribution,
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
            },
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
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        query_start_date, query_end_date = service.resolve_date_range(
            timeframe, start_date, end_date,
        )
        domain_distribution = service.get_domain_citation_summary(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
        )
        return DomainCitationSummaryResponse(
            status="success",
            domain_distribution=domain_distribution,
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
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        query_start_date, query_end_date = service.resolve_date_range(
            timeframe, start_date, end_date,
        )
        data = service.get_post_citation_rate(
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
        )
        return PostCitationRateResponse(
            status="success",
            data=data,
            metadata={
                "tenant_key": tenant_key,
                "job_id": job_id,
                "timeframe": timeframe.value,
                "start_date": query_start_date.strftime("%Y%m%d"),
                "end_date": query_end_date.strftime("%Y%m%d"),
                "calculation_method": "post_citation_rate",
                "row_count": 1,
            },
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
    service: DashboardService = Depends(get_dashboard_service),
):
    try:
        query_start_date, query_end_date = service.resolve_date_range(
            timeframe, start_date, end_date,
        )
        data = service.get_keyword_platform_brand_rates(
            tenant_key=tenant_key,
            job_id=job_id,
            query_start_date=query_start_date,
            query_end_date=query_end_date,
        )
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
