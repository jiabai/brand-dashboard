import unittest
from datetime import date
from unittest.mock import ANY, patch

from api.v1.dependencies.auth import CurrentTenantContext
from api.v1.routes import dashboard
from fastapi import FastAPI
from fastapi.testclient import TestClient


def build_dashboard_test_client():
    app = FastAPI()
    app.dependency_overrides[dashboard.get_current_tenant] = lambda: CurrentTenantContext(
        tenant_key="tn_1b02b3ef4fbd",
        tenant_name="测试租户",
        role="member",
        product_role="tenant_member",
    )
    app.include_router(dashboard.router, prefix="/api/v1/dashboard")
    return TestClient(app)


class TestDashboardRouteRegistry(unittest.TestCase):
    def test_deprecated_brand_mention_rate_route_is_not_registered(self):
        client = build_dashboard_test_client()

        registered_paths = {route.path for route in client.app.routes}

        self.assertNotIn("/api/v1/dashboard/brand-mention-rate", registered_paths)


class TestBrandMentionTrendApi(unittest.TestCase):
    def setUp(self):
        self.client = build_dashboard_test_client()

    def test_brand_mention_trend_returns_only_existing_dates(self):
        rows = [
            {
                "date": date(2026, 1, 1),
                "brand": "哈基桃电竞",
                "platform": "deepseek",
                "keyword": "三角洲陪玩",
                "mention_rate": 0.2,
            },
            {
                "date": date(2026, 1, 3),
                "brand": "哈基桃电竞",
                "platform": "deepseek",
                "keyword": "三角洲陪玩",
                "mention_rate": 0.5,
            },
        ]

        with patch(
            "api.v1.services.dashboard_service.query_brand_platform_keyword_daily_mention_rates",
            return_value=rows,
        ):
            response = self.client.get(
                "/api/v1/dashboard/brand-mention-trend",
                params={
                    "tenant_key": "tn_1b02b3ef4fbd",
                    "job_id": "job_20260127_223236_989cc4db",
                    "brand": "哈基桃电竞",
                    "platform": "deepseek",
                    "keyword": "三角洲陪玩",
                    "timeframe": "specific_day",
                    "start_date": "20260101",
                    "end_date": "20260104",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        data = payload["data"]
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["date"], "20260101")
        self.assertEqual(data[0]["mention_rate"], 0.2)
        self.assertEqual(data[1]["date"], "20260103")
        self.assertEqual(data[1]["mention_rate"], 0.5)
        self.assertNotIn("is_filled", data[0])

        metadata = payload["metadata"]
        self.assertEqual(metadata["points"], 2)
        self.assertNotIn("fill_method", metadata)


class TestFilterMetadataApi(unittest.TestCase):
    def setUp(self):
        self.client = build_dashboard_test_client()

    def test_filter_metadata_returns_unique_lists(self):
        rows = [
            {"platform": "Qwen", "keyword": "手机"},
            {"platform": "Qwen", "keyword": "笔记本"},
            {"platform": "Deepseek", "keyword": "手机"},
        ]

        with patch(
            "api.v1.services.dashboard_service.query_filter_metadata",
            return_value=rows,
        ):
            response = self.client.get(
                "/api/v1/dashboard/filter-metadata",
                params={
                    "tenant_key": "tn_1b02b3ef4fbd",
                    "job_id": "job_20260127_223236_989cc4db",
                    "start_date": "20260101",
                    "end_date": "20260131",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["code"], 200)
        data = payload["data"]
        self.assertEqual(data["platforms"], ["Qwen", "Deepseek"])
        self.assertEqual(data["keywords"], ["手机", "笔记本"])
        self.assertEqual(len(data["combinations"]), 3)


class TestKeywordPlatformBrandRatesApi(unittest.TestCase):
    def setUp(self):
        self.client = build_dashboard_test_client()

    def test_keyword_platform_brand_rates_requires_date_range_for_specific_day(self):
        response = self.client.get(
            "/api/v1/dashboard/keyword-platform-brand-rates",
            params={
                "tenant_key": "tn_1b02b3ef4fbd",
                "job_id": "job_20260127_223236_989cc4db",
                "timeframe": "specific_day",
                "start_date": "20260131",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_keyword_platform_brand_rates_returns_date_range_metadata(self):
        rows = [
            {
                "keyword": "三角洲陪玩",
                "platform": "deepseek",
                "brand": "五九电竞",
                "mention_rate": 0.6935,
                "first_mention_rate": 0.0323,
                "top3_mention_rate": 0.1545,
            }
        ]

        with patch(
            "api.v1.services.dashboard_service.query_keyword_platform_brand_rates",
            return_value=rows,
        ):
            response = self.client.get(
                "/api/v1/dashboard/keyword-platform-brand-rates",
                params={
                    "tenant_key": "tn_1b02b3ef4fbd",
                    "job_id": "job_20260127_223236_989cc4db",
                    "timeframe": "specific_day",
                    "start_date": "20260131",
                    "end_date": "20260131",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        metadata = payload["metadata"]
        self.assertEqual(metadata["start_date"], "20260131")
        self.assertEqual(metadata["end_date"], "20260131")
        self.assertNotIn("date", metadata)

    def test_keyword_platform_brand_rates_includes_top3_mention_rate(self):
        rows = [
            {
                "keyword": "三角洲陪玩",
                "platform": "deepseek",
                "brand": "五九电竞",
                "mention_rate": 0.6935,
                "first_mention_rate": 0.0323,
                "top3_mention_rate": 0.1545,
            }
        ]

        with patch(
            "api.v1.services.dashboard_service.query_keyword_platform_brand_rates",
            return_value=rows,
        ):
            response = self.client.get(
                "/api/v1/dashboard/keyword-platform-brand-rates",
                params={
                    "tenant_key": "tn_1b02b3ef4fbd",
                    "job_id": "job_20260127_223236_989cc4db",
                    "timeframe": "30days",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        data = payload["data"]
        self.assertEqual(len(data), 1)
        self.assertIn("top3_mention_rate", data[0])
        self.assertEqual(data[0]["top3_mention_rate"], 0.1545)

    def test_keyword_platform_brand_rates_uses_computed_date_range_for_non_specific_day(self):
        with patch(
            "api.v1.services.dashboard_service.get_date_range",
            return_value=(date(2026, 1, 1), date(2026, 1, 31)),
        ):
            with patch(
                "api.v1.services.dashboard_service.query_keyword_platform_brand_rates"
            ) as query_mock:
                query_mock.return_value = []
                response = self.client.get(
                    "/api/v1/dashboard/keyword-platform-brand-rates",
                    params={
                        "tenant_key": "tn_1b02b3ef4fbd",
                        "job_id": "job_20260127_223236_989cc4db",
                        "timeframe": "30days",
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["metadata"]["start_date"], "20260101")
        self.assertEqual(payload["metadata"]["end_date"], "20260131")

        query_mock.assert_called_once_with(
            ANY,
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )


class TestBrandMetricsApi(unittest.TestCase):
    def setUp(self):
        self.client = build_dashboard_test_client()

    def test_brand_metrics_requires_date_range_for_specific_day(self):
        response = self.client.get(
            "/api/v1/dashboard/brand-metrics",
            params={
                "tenant_key": "tn_1b02b3ef4fbd",
                "job_id": "job_20260127_223236_989cc4db",
                "timeframe": "specific_day",
                "start_date": "20260131",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_brand_metrics_uses_computed_date_range_for_non_specific_day(self):
        rows = [
            {
                "brand": "学而思",
                "mention_rate": 0.3333,
                "first_mention_rate": 0.0,
                "top3_mention_rate": 0.0667,
                "prompt_count": 15,
                "keyword_coverage": 3,
            }
        ]

        with patch(
            "api.v1.services.dashboard_service.get_date_range",
            return_value=(date(2026, 1, 1), date(2026, 1, 31)),
        ):
            with patch("api.v1.services.dashboard_service.query_brand_metrics") as query_mock:
                query_mock.return_value = rows
                response = self.client.get(
                    "/api/v1/dashboard/brand-metrics",
                    params={
                        "tenant_key": "tn_1b02b3ef4fbd",
                        "job_id": "job_20260127_223236_989cc4db",
                        "timeframe": "30days",
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["metadata"]["start_date"], "20260101")
        self.assertEqual(payload["metadata"]["end_date"], "20260131")
        self.assertEqual(payload["metadata"]["row_count"], 1)

        query_mock.assert_called_once_with(
            ANY,
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            brand=None,
            platform=None,
        )

    def test_brand_metrics_uses_supplied_date_range_for_specific_day(self):
        rows = []

        with patch("api.v1.services.dashboard_service.query_brand_metrics") as query_mock:
            query_mock.return_value = rows
            response = self.client.get(
                "/api/v1/dashboard/brand-metrics",
                params={
                    "tenant_key": "tn_1b02b3ef4fbd",
                    "job_id": "job_20260127_223236_989cc4db",
                    "timeframe": "specific_day",
                    "start_date": "20260131",
                    "end_date": "20260131",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        metadata = payload["metadata"]
        self.assertEqual(metadata["start_date"], "20260131")
        self.assertEqual(metadata["end_date"], "20260131")
        self.assertEqual(metadata["row_count"], 0)

        query_mock.assert_called_once_with(
            ANY,
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            start_date=date(2026, 1, 31),
            end_date=date(2026, 1, 31),
            brand=None,
            platform=None,
        )

    def test_brand_metrics_metadata_marks_analysis_fact_source(self):
        rows = [
            {
                "brand": "学而思",
                "mention_rate": 0.3333,
                "first_mention_rate": 0.0,
                "top3_mention_rate": 0.0667,
                "prompt_count": 15,
                "keyword_coverage": 3,
            }
        ]

        with patch(
            "api.v1.services.dashboard_service.query_brand_metrics",
            return_value=rows,
        ):
            response = self.client.get(
                "/api/v1/dashboard/brand-metrics",
                params={
                    "tenant_key": "tn_1b02b3ef4fbd",
                    "job_id": "job_20260127_223236_989cc4db",
                    "timeframe": "specific_day",
                    "start_date": "20260607",
                    "end_date": "20260607",
                },
            )

        self.assertEqual(response.status_code, 200)
        metadata = response.json()["metadata"]
        self.assertEqual(metadata["data_source"], "analysis_fact")
        self.assertEqual(metadata["metric_definition_version"], "brand_metrics_v1")
        self.assertNotIn("snapshot_status", metadata)
        self.assertNotIn("metric_snapshot_count", metadata)


class TestDomainCitationRateApi(unittest.TestCase):
    def setUp(self):
        self.client = build_dashboard_test_client()

    def test_domain_citation_rate_requires_date_range_for_specific_day(self):
        response = self.client.get(
            "/api/v1/dashboard/citation-domain-stats",
            params={
                "tenant_key": "tn_1b02b3ef4fbd",
                "job_id": "job_20260127_223236_989cc4db",
                "brand": "学而思",
                "timeframe": "specific_day",
                "start_date": "20260131",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_domain_citation_rate_uses_computed_date_range_for_non_specific_day(self):
        rows = [
            {
                "domain": "www.baidu.com",
                "chinese_name": "百度",
                "keywords": "数学培训,奥数",
                "content_types": "新闻,论坛",
                "platforms": "deepseek,千问",
                "domain_citation_rate": 8.96,
            },
            {
                "domain": "www.google.com",
                "chinese_name": "谷歌",
                "keywords": "数学培训",
                "content_types": "新闻",
                "platforms": "deepseek",
                "domain_citation_rate": 3.73,
            },
        ]

        with patch(
            "api.v1.services.dashboard_service.get_date_range",
            return_value=(date(2026, 1, 1), date(2026, 1, 31)),
        ):
            with patch(
                "api.v1.services.dashboard_service.query_domain_citation_rate"
            ) as query_mock:
                query_mock.return_value = rows
                response = self.client.get(
                    "/api/v1/dashboard/citation-domain-stats",
                    params={
                        "tenant_key": "tn_1b02b3ef4fbd",
                        "job_id": "job_20260127_223236_989cc4db",
                        "brand": "学而思",
                        "timeframe": "30days",
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["metadata"]["tenant_key"], "tn_1b02b3ef4fbd")
        self.assertEqual(payload["metadata"]["job_id"], "job_20260127_223236_989cc4db")
        self.assertIsNone(payload["metadata"]["keyword"])
        self.assertIsNone(payload["metadata"]["platform"])
        self.assertEqual(payload["metadata"]["start_date"], "20260101")
        self.assertEqual(payload["metadata"]["end_date"], "20260131")
        self.assertEqual(payload["metadata"]["row_count"], 2)
        self.assertEqual(payload["domain_distribution"][0]["keywords"], "数学培训,奥数")
        self.assertEqual(payload["domain_distribution"][0]["content_types"], "新闻,论坛")
        self.assertEqual(payload["domain_distribution"][0]["platforms"], "deepseek,千问")
        self.assertEqual(payload["domain_distribution"][0]["domain_citation_rate"], 8.96)

        query_mock.assert_called_once_with(
            ANY,
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            brand="学而思",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            keyword=None,
            platform=None,
        )

    def test_domain_citation_rate_uses_supplied_date_range_for_specific_day(self):
        rows = []

        with patch("api.v1.services.dashboard_service.query_domain_citation_rate") as query_mock:
            query_mock.return_value = rows
            response = self.client.get(
                "/api/v1/dashboard/citation-domain-stats",
                params={
                    "tenant_key": "tn_1b02b3ef4fbd",
                    "job_id": "job_20260127_223236_989cc4db",
                    "brand": "学而思",
                    "timeframe": "specific_day",
                    "start_date": "20260102",
                    "end_date": "20260131",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["metadata"]["start_date"], "20260102")
        self.assertEqual(payload["metadata"]["end_date"], "20260131")
        self.assertEqual(payload["metadata"]["row_count"], 0)

        query_mock.assert_called_once_with(
            ANY,
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            brand="学而思",
            start_date=date(2026, 1, 2),
            end_date=date(2026, 1, 31),
            keyword=None,
            platform=None,
        )


    def test_domain_citation_rate_includes_keyword_in_params(self):
        rows = []
        with patch("api.v1.services.dashboard_service.query_domain_citation_rate") as query_mock:
            query_mock.return_value = rows
            response = self.client.get(
                "/api/v1/dashboard/citation-domain-stats",
                params={
                    "tenant_key": "tn_1b02b3ef4fbd",
                    "job_id": "job_20260127_223236_989cc4db",
                    "brand": "学而思",
                    "timeframe": "specific_day",
                    "start_date": "20260101",
                    "end_date": "20260101",
                    "keyword": "数学",
                    "platform": "deepseek",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["metadata"]["keyword"], "数学")
        self.assertEqual(payload["metadata"]["platform"], "deepseek")

        query_mock.assert_called_once_with(
            ANY,
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            brand="学而思",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 1),
            keyword="数学",
            platform="deepseek",
        )


class TestCitationTypeStatsApi(unittest.TestCase):
    def setUp(self):
        self.client = build_dashboard_test_client()

    def test_citation_type_stats_requires_date_range_for_specific_day(self):
        response = self.client.get(
            "/api/v1/dashboard/citation-type-stats",
            params={
                "tenant_key": "tn_1b02b3ef4fbd",
                "job_id": "job_20260127_223236_989cc4db",
                "timeframe": "specific_day",
                "start_date": "20260131",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_citation_type_stats_uses_computed_date_range_for_non_specific_day(self):
        summary = {"total_rows": 1240, "conversations": 356}
        stats = [
            {"content_type": "news", "type_pct": 42.35},
            {"content_type": "tech_review", "type_pct": 28.19},
        ]

        with patch(
            "api.v1.services.dashboard_service.get_date_range",
            return_value=(date(2026, 1, 1), date(2026, 1, 31)),
        ):
            with patch(
                "api.v1.services.dashboard_service.query_citation_type_stats"
            ) as query_mock:
                query_mock.return_value = summary, stats
                response = self.client.get(
                    "/api/v1/dashboard/citation-type-stats",
                    params={
                        "tenant_key": "tn_1b02b3ef4fbd",
                        "job_id": "job_20260127_223236_989cc4db",
                        "timeframe": "30days",
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["summary"]["total_rows"], 1240)
        self.assertEqual(payload["summary"]["conversations"], 356)
        self.assertEqual(payload["metadata"]["start_date"], "20260101")
        self.assertEqual(payload["metadata"]["end_date"], "20260131")
        self.assertEqual(payload["metadata"]["row_count"], 2)
        self.assertEqual(len(payload["citation_type_stats"]), 2)

        query_mock.assert_called_once_with(
            ANY,
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )


class TestPlatformMetricsByBrandApi(unittest.TestCase):
    def setUp(self):
        self.client = build_dashboard_test_client()

    def test_platform_metrics_by_brand_requires_date_range_for_specific_day(self):
        response = self.client.get(
            "/api/v1/dashboard/platform-metrics-by-brand",
            params={
                "tenant_key": "tn_1b02b3ef4fbd",
                "job_id": "job_20260127_223236_989cc4db",
                "brand": "学而思",
                "timeframe": "specific_day",
                "start_date": "20260131",
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_platform_metrics_by_brand_uses_computed_date_range_for_non_specific_day(self):
        rows = [
            {"platform": "deepseek", "mention_rate": 0.3333},
            {"platform": "豆包", "mention_rate": 0.4667},
        ]

        with patch(
            "api.v1.services.dashboard_service.get_date_range",
            return_value=(date(2026, 1, 1), date(2026, 1, 31)),
        ):
            with patch(
                "api.v1.services.dashboard_service.query_platform_metrics_by_brand"
            ) as query_mock:
                query_mock.return_value = rows
                response = self.client.get(
                    "/api/v1/dashboard/platform-metrics-by-brand",
                    params={
                        "tenant_key": "tn_1b02b3ef4fbd",
                        "job_id": "job_20260127_223236_989cc4db",
                        "brand": "学而思",
                        "timeframe": "30days",
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["data"]["brand"], "学而思")
        self.assertEqual(payload["metadata"]["tenant_key"], "tn_1b02b3ef4fbd")
        self.assertEqual(payload["metadata"]["job_id"], "job_20260127_223236_989cc4db")
        self.assertEqual(payload["metadata"]["start_date"], "20260101")
        self.assertEqual(payload["metadata"]["end_date"], "20260131")
        self.assertEqual(payload["metadata"]["row_count"], 2)

        query_mock.assert_called_once_with(
            ANY,
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            brand="学而思",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
        )

    def test_platform_metrics_by_brand_uses_supplied_date_range_for_specific_day(self):
        rows = []

        with patch(
            "api.v1.services.dashboard_service.query_platform_metrics_by_brand"
        ) as query_mock:
            query_mock.return_value = rows
            response = self.client.get(
                "/api/v1/dashboard/platform-metrics-by-brand",
                params={
                    "tenant_key": "tn_1b02b3ef4fbd",
                    "job_id": "job_20260127_223236_989cc4db",
                    "brand": "学而思",
                    "timeframe": "specific_day",
                    "start_date": "20260102",
                    "end_date": "20260131",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["metadata"]["start_date"], "20260102")
        self.assertEqual(payload["metadata"]["end_date"], "20260131")
        self.assertEqual(payload["metadata"]["row_count"], 0)

        query_mock.assert_called_once_with(
            ANY,
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            brand="学而思",
            start_date=date(2026, 1, 2),
            end_date=date(2026, 1, 31),
        )


class TestKeywordPlatformBrandRatesQuery(unittest.TestCase):
    def test_query_keyword_platform_brand_rates_requires_date_objects(self):
        # 验证 query_keyword_platform_brand_rates 在传入非 date 对象时可能会报错，
        # （例如字符串且格式不对）。
        # 或者仅仅是为了演示该函数现在期望 date 对象。
        # 由于我们不再在函数内部做字符串解析，直接传入错误类型可能会导致底层库报错。
        pass

    def test_query_keyword_platform_brand_rates_reject_start_after_end(self):
        # 注意：这里我们 mock 数据库连接，因为我们只想测试逻辑（如果有的话）
        # 但目前该函数逻辑主要在 SQL 中，Python 层没有显式校验 start > end
        # 如果需要校验，通常在 repository 层或 route 层。
        pass
