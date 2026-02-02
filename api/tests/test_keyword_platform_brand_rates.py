import unittest
from unittest.mock import MagicMock


class TestKeywordPlatformBrandRates(unittest.TestCase):
    def test_repository_function_executes_expected_grouping(self):
        from api.v1.repositories import database

        fake_rows = [
            ("三角洲陪玩", "deepseek", "五九电竞", 0.6935, 0.0323),
        ]

        execute_result = MagicMock()
        execute_result.fetchall.return_value = fake_rows

        show_columns_result = MagicMock()
        show_columns_result.fetchall.return_value = [
            ("keyword",),
            ("platform",),
            ("brand",),
            ("conversation_id",),
            ("is_mentioned",),
            ("is_first_mentioned",),
        ]

        conn = MagicMock()
        conn.execute.side_effect = lambda stmt, params=None: (
            show_columns_result
            if "SHOW COLUMNS FROM qa_brand_state" in str(stmt)
            else execute_result
        )

        class _ConnCtx:
            def __enter__(self):
                return conn

            def __exit__(self, exc_type, exc, tb):
                return False

        engine = MagicMock()
        engine.connect.return_value = _ConnCtx()

        original_engine = database.engine
        database.engine = engine
        try:
            result = database.query_keyword_platform_brand_rates(
                tenant_key="tn_1b02b3ef4fbd",
                job_id="job_20260123_172515_f38024e2",
                timeframe="30days",
                specific_date=None,
            )
        finally:
            database.engine = original_engine

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["keyword"], "三角洲陪玩")
        self.assertEqual(result[0]["platform"], "deepseek")
        self.assertEqual(result[0]["brand"], "五九电竞")
        self.assertAlmostEqual(result[0]["mention_rate"], 0.6935)
        self.assertAlmostEqual(result[0]["first_mention_rate"], 0.0323)

        executed_sql = str(conn.execute.call_args[0][0])
        self.assertIn("GROUP BY", executed_sql)
        self.assertIn("keyword", executed_sql)
        self.assertIn("platform", executed_sql)
        self.assertIn("brand", executed_sql)

