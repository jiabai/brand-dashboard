from datetime import date, datetime
from typing import Any, List, Optional, Tuple

from sqlalchemy import Engine

from api.v1.models.schemas import (
    BrandMentionTrendItem,
    BrandMetricsItem,
    CitationTypeStatsItem,
    CitationTypeStatsSummary,
    CitationUrlData,
    DomainCitationRateItem,
    DomainCitationSummaryItem,
    FilterMetadataCombination,
    FilterMetadataData,
    KeywordPlatformBrandRateItem,
    PlatformMentionRateData,
    PlatformMetricsByBrandData,
    PlatformMetricsByBrandItem,
    PostCitationRateData,
    TimeFrame,
)
from api.v1.repositories.brand_mention import (
    query_brand_metrics,
    query_brand_platform_keyword_daily_mention_rates,
    query_brand_platform_mention_data,
    query_platform_metrics_by_brand,
)
from api.v1.repositories.citation import (
    query_citation_type_stats,
    query_citation_url_stats,
    query_domain_citation_rate,
    query_domain_citation_summary,
    query_post_citation_rate,
)
from api.v1.repositories.filter_metadata import (
    get_available_dates,
    query_filter_metadata,
    query_keyword_platform_brand_rates,
)
from api.v1.repositories.metric_snapshots import query_snapshot_quality_metadata
from api.v1.utils.date_range import get_date_range
from api.v1.utils.url_domain_resolver import resolve_url_domain


class DashboardService:
    """仪表盘业务服务层，封装数据查询、转换和业务逻辑。

    通过构造函数注入 engine，支持测试时替换为 mock engine。
    """

    PLATFORM_COLORS = {
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

    def __init__(self, engine: Engine):
        self._engine = engine

    @staticmethod
    def resolve_date_range(
        timeframe: TimeFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Tuple[date, date]:
        if timeframe == TimeFrame.SPECIFIC_DAY:
            if not start_date or not end_date:
                raise ValueError(
                    "timeframe=specific_day 时必须提供 start_date 和 end_date(YYYYMMDD)"
                )
            query_start_date = datetime.strptime(start_date, "%Y%m%d").date()
            query_end_date = datetime.strptime(end_date, "%Y%m%d").date()
        else:
            query_start_date, query_end_date = get_date_range(timeframe.value)

        if query_start_date > query_end_date:
            raise ValueError("开始日期不能晚于结束日期")

        return query_start_date, query_end_date

    @staticmethod
    def get_platform_color(platform_name: str) -> str:
        return DashboardService.PLATFORM_COLORS.get(platform_name, "#6b7280")

    def get_platform_mention_rates(
        self, tenant_key: str, job_id: str, category: str,
        brand: str, keyword: str, timeframe: TimeFrame,
        date: Optional[str] = None,
    ) -> Tuple[List[PlatformMentionRateData], int]:
        platform_data_list = query_brand_platform_mention_data(
            self._engine,
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            category=category,
            keyword=keyword,
            timeframe=timeframe.value,
            specific_date=date,
        )
        response_data = [
            PlatformMentionRateData(
                name=p["platform"],
                mention_rate=p["mention_rate"],
                first_mention_rate=p["first_mention_rate"],
                color=self.get_platform_color(p["platform"]),
            )
            for p in platform_data_list
        ]
        total_queries = sum((p["query_count"] for p in platform_data_list), start=0)
        return response_data, total_queries

    def get_brand_mention_trend(
        self, tenant_key: str, job_id: str, brand: str,
        platform: str, keyword: str,
        query_start_date: date, query_end_date: date,
    ) -> List[BrandMentionTrendItem]:
        rows = query_brand_platform_keyword_daily_mention_rates(
            self._engine,
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
        return data

    def get_citation_url_stats(
        self, tenant_key: str, job_id: str, keyword: str,
        domain: str, query_start_date: date, query_end_date: date,
    ) -> List[CitationUrlData]:
        citation_data_list = query_citation_url_stats(
            self._engine,
            tenant_key=tenant_key,
            job_id=job_id,
            keyword=keyword,
            domain=domain,
            start_date=query_start_date,
            end_date=query_end_date,
        )
        response_data = []
        for citation_data in citation_data_list:
            citation_count = citation_data["citation_count"]
            total_questions = citation_data["total_questions"]
            domain_info = resolve_url_domain(citation_data["url"])
            chinese_name = domain_info["chinese_name"]
            citation_rate = (
                round(citation_count / total_questions * 100, 2)
                if total_questions > 0
                else 0.0
            )
            response_data.append(
                CitationUrlData(
                    answer_reference_url=citation_data["url"],
                    citation_count=citation_count,
                    total_questions=total_questions,
                    chinese_name=chinese_name,
                    citation_rate=citation_rate,
                )
            )
        return response_data

    def get_citation_type_stats(
        self, tenant_key: str, job_id: str,
        query_start_date: date, query_end_date: date,
    ) -> Tuple[CitationTypeStatsSummary, List[CitationTypeStatsItem]]:
        summary, stats = query_citation_type_stats(
            self._engine,
            tenant_key=tenant_key,
            job_id=job_id,
            start_date=query_start_date,
            end_date=query_end_date,
        )
        return (
            CitationTypeStatsSummary(**summary),
            [CitationTypeStatsItem(**item) for item in stats],
        )

    def get_filter_metadata(
        self, tenant_key: str, job_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> FilterMetadataData:
        rows = query_filter_metadata(
            self._engine,
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
        return FilterMetadataData(
            platforms=platforms,
            keywords=keywords,
            combinations=combinations,
        )

    def get_available_dates(
        self, tenant_key: str, job_id: Optional[str] = None,
    ) -> List[str]:
        return get_available_dates(self._engine, tenant_key, job_id)

    def get_brand_metrics(
        self, tenant_key: str, job_id: str,
        query_start_date: date, query_end_date: date,
        brand: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[BrandMetricsItem]:
        metrics = query_brand_metrics(
            self._engine,
            tenant_key=tenant_key,
            job_id=job_id,
            start_date=query_start_date,
            end_date=query_end_date,
            brand=brand,
            platform=platform,
        )
        return [
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

    def get_metric_snapshot_metadata(
        self,
        tenant_key: str,
        job_id: str,
        query_start_date: date,
        query_end_date: date,
    ) -> dict[str, Any]:
        try:
            return query_snapshot_quality_metadata(
                self._engine,
                tenant_key=tenant_key,
                job_id=job_id,
                start_date=query_start_date,
                end_date=query_end_date,
            )
        except Exception:
            return {
                "data_source": "legacy_aggregation",
                "snapshot_status": "missing",
                "metric_definition_version": "brand_metrics_v1",
                "analysis_run_id": None,
                "metric_generated_at": None,
                "metric_coverage_rate": None,
                "metric_expected_task_count": None,
                "metric_succeeded_task_count": None,
                "metric_failed_task_count": None,
                "metric_analyzed_answer_count": None,
                "metric_snapshot_count": 0,
                "metric_dimension_count": 0,
            }

    def get_platform_metrics_by_brand(
        self, tenant_key: str, job_id: str, brand: str,
        query_start_date: date, query_end_date: date,
    ) -> PlatformMetricsByBrandData:
        platforms = query_platform_metrics_by_brand(
            self._engine,
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            start_date=query_start_date,
            end_date=query_end_date,
        )
        return PlatformMetricsByBrandData(
            brand=brand,
            platforms=[
                PlatformMetricsByBrandItem(
                    platform=item["platform"],
                    mention_rate=item["mention_rate"],
                )
                for item in platforms
            ],
        )

    def get_domain_citation_rate(
        self, tenant_key: str, job_id: str, brand: str,
        query_start_date: date, query_end_date: date,
        keyword: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[DomainCitationRateItem]:
        domain_distribution = query_domain_citation_rate(
            self._engine,
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            start_date=query_start_date,
            end_date=query_end_date,
            keyword=keyword,
            platform=platform,
        )
        return [
            DomainCitationRateItem(
                domain=item["domain"],
                chinese_name=item["chinese_name"],
                keywords=item["keywords"],
                content_types=item["content_types"],
                platforms=item["platforms"],
                domain_citation_rate=item["domain_citation_rate"],
            )
            for item in domain_distribution
        ]

    def get_domain_citation_summary(
        self, tenant_key: str, job_id: str, brand: str,
        query_start_date: date, query_end_date: date,
    ) -> List[DomainCitationSummaryItem]:
        domain_distribution = query_domain_citation_summary(
            self._engine,
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            start_date=query_start_date,
            end_date=query_end_date,
        )
        return [
            DomainCitationSummaryItem(
                domain=item["domain"],
                chinese_name=item["chinese_name"],
                citation_count=item["citation_count"],
                keyword_coverage=item["keyword_coverage"],
                platform_coverage=item["platform_coverage"],
                domain_citation_rate=item["domain_citation_rate"],
            )
            for item in domain_distribution
        ]

    def get_post_citation_rate(
        self, tenant_key: str, job_id: str, brand: str,
        query_start_date: date, query_end_date: date,
    ) -> List[PostCitationRateData]:
        data = query_post_citation_rate(
            self._engine,
            tenant_key=tenant_key,
            job_id=job_id,
            brand=brand,
            start_date=query_start_date,
            end_date=query_end_date,
        )
        return [PostCitationRateData(**data)]

    def get_keyword_platform_brand_rates(
        self, tenant_key: str, job_id: str,
        query_start_date: date, query_end_date: date,
    ) -> List[KeywordPlatformBrandRateItem]:
        rows = query_keyword_platform_brand_rates(
            self._engine,
            tenant_key=tenant_key,
            job_id=job_id,
            start_date=query_start_date,
            end_date=query_end_date,
        )
        return [
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
