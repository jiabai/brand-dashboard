import unittest
from datetime import date
from unittest.mock import patch

from api.v1.routes import dashboard
from api.v1.routes.dashboard import fill_missing_dates_locf
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestFillMissingDatesLocf(unittest.TestCase):
    def test_fill_missing_dates_locf_carries_forward(self):
        rows = [
            {"date": date(2026, 1, 1), "mention_rate": 0.2},
            {"date": date(2026, 1, 3), "mention_rate": 0.5},
        ]
        result = fill_missing_dates_locf(
            rows=rows,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 4),
            initial_value=0.0,
        )

        expected = [
            {"date": "20260101", "mention_rate": 0.2, "is_filled": False},
            {"date": "20260102", "mention_rate": 0.2, "is_filled": True},
            {"date": "20260103", "mention_rate": 0.5, "is_filled": False},
            {"date": "20260104", "mention_rate": 0.5, "is_filled": True},
        ]
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()


class TestBrandMentionTrendApi(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(dashboard.router, prefix="/api/v1/dashboard")
        self.client = TestClient(app)

    def test_brand_mention_trend_locf(self):
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
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0]["mention_rate"], 0.2)
        self.assertEqual(data[1]["mention_rate"], 0.2)
        self.assertEqual(data[2]["mention_rate"], 0.5)
        self.assertEqual(data[3]["mention_rate"], 0.5)
        self.assertEqual(data[0]["is_filled"], False)
        self.assertEqual(data[1]["is_filled"], True)
        self.assertEqual(data[2]["is_filled"], False)
        self.assertEqual(data[3]["is_filled"], True)
