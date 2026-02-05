import unittest
from datetime import date
from unittest.mock import patch

from api.v1.repositories.database import query_keyword_platform_brand_rates
from api.v1.routes import dashboard
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestBrandMentionTrendApi(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/v1/dashboard")
        self.client = TestClient(app)

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
            "api.v1.routes.dashboard.query_brand_platform_keyword_daily_mention_rates",
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
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/v1/dashboard")
        self.client = TestClient(app)

    def test_filter_metadata_returns_unique_lists(self):
        rows = [
            {"platform": "Qwen", "keyword": "手机"},
            {"platform": "Qwen", "keyword": "笔记本"},
            {"platform": "Deepseek", "keyword": "手机"},
        ]

        with patch(
            "api.v1.routes.dashboard.query_filter_metadata",
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
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/v1/dashboard")
        self.client = TestClient(app)

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
            "api.v1.routes.dashboard.query_keyword_platform_brand_rates",
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
            "api.v1.routes.dashboard.query_keyword_platform_brand_rates",
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
            "api.v1.routes.dashboard.get_date_range",
            return_value=(date(2026, 1, 1), date(2026, 1, 31)),
        ):
            with patch("api.v1.routes.dashboard.query_keyword_platform_brand_rates") as query_mock:
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
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            start_date="20260101",
            end_date="20260131",
        )


class TestBrandMetricsApi(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/v1/dashboard")
        self.client = TestClient(app)

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
            "api.v1.routes.dashboard.get_date_range",
            return_value=(date(2026, 1, 1), date(2026, 1, 31)),
        ):
            with patch("api.v1.routes.dashboard.query_brand_metrics") as query_mock:
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
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            start_date="20260101",
            end_date="20260131",
            brand=None,
            platform=None,
        )

    def test_brand_metrics_uses_supplied_date_range_for_specific_day(self):
        rows = []

        with patch("api.v1.routes.dashboard.query_brand_metrics") as query_mock:
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
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            start_date="20260131",
            end_date="20260131",
            brand=None,
            platform=None,
        )


class TestDomainCitationRateApi(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/v1/dashboard")
        self.client = TestClient(app)

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
            {"domain": "www.baidu.com", "domain_citation_rate": 8.96},
            {"domain": "www.google.com", "domain_citation_rate": 3.73},
        ]

        with patch(
            "api.v1.routes.dashboard.get_date_range",
            return_value=(date(2026, 1, 1), date(2026, 1, 31)),
        ):
            with patch("api.v1.routes.dashboard.query_domain_citation_rate") as query_mock:
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
        self.assertEqual(payload["metadata"]["start_date"], "20260101")
        self.assertEqual(payload["metadata"]["end_date"], "20260131")
        self.assertEqual(payload["metadata"]["row_count"], 2)

        query_mock.assert_called_once_with(
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            brand="学而思",
            start_date="20260101",
            end_date="20260131",
        )

    def test_domain_citation_rate_uses_supplied_date_range_for_specific_day(self):
        rows = []

        with patch("api.v1.routes.dashboard.query_domain_citation_rate") as query_mock:
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
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            brand="学而思",
            start_date="20260102",
            end_date="20260131",
        )


class TestPlatformMetricsByBrandApi(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/v1/dashboard")
        self.client = TestClient(app)

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
            "api.v1.routes.dashboard.get_date_range",
            return_value=(date(2026, 1, 1), date(2026, 1, 31)),
        ):
            with patch(
                "api.v1.routes.dashboard.query_platform_metrics_by_brand"
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
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            brand="学而思",
            start_date="20260101",
            end_date="20260131",
        )

    def test_platform_metrics_by_brand_uses_supplied_date_range_for_specific_day(self):
        rows = []

        with patch("api.v1.routes.dashboard.query_platform_metrics_by_brand") as query_mock:
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
            tenant_key="tn_1b02b3ef4fbd",
            job_id="job_20260127_223236_989cc4db",
            brand="学而思",
            start_date="20260102",
            end_date="20260131",
        )


class TestKeywordPlatformBrandRatesQuery(unittest.TestCase):
    def test_query_keyword_platform_brand_rates_rejects_invalid_date_format(self):
        with self.assertRaises(ValueError):
            query_keyword_platform_brand_rates(
                tenant_key="tn_1b02b3ef4fbd",
                job_id="job_20260127_223236_989cc4db",
                start_date="2026-01-01",
                end_date="20260131",
            )

    def test_query_keyword_platform_brand_rates_rejects_start_after_end(self):
        with self.assertRaises(ValueError):
            query_keyword_platform_brand_rates(
                tenant_key="tn_1b02b3ef4fbd",
                job_id="job_20260127_223236_989cc4db",
                start_date="20260201",
                end_date="20260131",
            )
