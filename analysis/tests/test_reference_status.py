from datetime import date

from src.plugins.metrics.reference_status import ReferenceStatusPlugin


def _plugin() -> ReferenceStatusPlugin:
    return ReferenceStatusPlugin(llm_config={})


def test_build_upsert_rows_empty_answers():
    rows, skipped = _plugin()._build_upsert_rows({}, date.today())
    assert rows == []
    assert skipped == 0


def test_build_upsert_rows_builds_row_and_converts_types():
    answers = {
        "k1": {
            "tenant_key": 1,
            "job_id": 2,
            "conversation_id": 3,
            "platform": "deepseek",
            "brand": "宝马",
            "category": "汽车",
            "keyword": "安全",
            "query_content": "宝马安全吗？",
            "url": "https://example.com/a",
            "is_published_link": True,
            "domain": "",
            "content_type": "官网",
            "date": date(2024, 1, 2),
        }
    }

    rows, skipped = _plugin()._build_upsert_rows(answers, date(2024, 1, 1))
    assert skipped == 0
    assert len(rows) == 1
    row = rows[0]
    assert row["date"] == date(2024, 1, 2)
    assert row["tenant_key"] == "1"
    assert row["job_id"] == "2"
    assert row["conversation_id"] == "3"
    assert row["platform"] == "deepseek"
    assert row["brand"] == "宝马"
    assert row["category"] == "汽车"
    assert row["keyword"] == "安全"
    assert row["query_content"] == "宝马安全吗？"
    assert row["url"] == "https://example.com/a"
    assert row["is_published_link"] == 1
    assert row["domain"] is None
    assert row["content_type"] == "官网"


def test_build_upsert_rows_skips_missing_required_fields():
    answers = {
        "k1": {
            "tenant_key": "t1",
            "job_id": "j1",
            "conversation_id": "c1",
            "platform": "deepseek",
            "category": "汽车",
            "keyword": "安全",
            "query_content": "宝马安全吗？",
        }
    }
    rows, skipped = _plugin()._build_upsert_rows(answers, date.today())
    assert rows == []
    assert skipped == 1


def test_build_upsert_rows_skips_blank_required_fields():
    answers = {
        "k1": {
            "tenant_key": "t1",
            "job_id": "j1",
            "conversation_id": "c1",
            "platform": "  ",
            "brand": "宝马",
            "category": "汽车",
            "keyword": "安全",
            "query_content": "宝马安全吗？",
            "url": "https://example.com/a",
        }
    }
    rows, skipped = _plugin()._build_upsert_rows(answers, date.today())
    assert rows == []
    assert skipped == 1


def test_build_upsert_rows_skips_blank_brand():
    answers = {
        "k1": {
            "tenant_key": "t1",
            "job_id": "j1",
            "conversation_id": "c1",
            "platform": "deepseek",
            "brand": " ",
            "category": "汽车",
            "keyword": "安全",
            "query_content": "宝马安全吗？",
            "url": "https://example.com/a",
        }
    }
    rows, skipped = _plugin()._build_upsert_rows(answers, date.today())
    assert rows == []
    assert skipped == 1


def test_build_upsert_rows_handles_boolean_like_values():
    answers = {
        "k1": {
            "tenant_key": "t1",
            "job_id": "j1",
            "conversation_id": "c1",
            "platform": "deepseek",
            "brand": "宝马",
            "category": "汽车",
            "keyword": "安全",
            "query_content": "宝马安全吗？",
            "url": "https://example.com/a",
            "is_published_link": "0",
        },
        "k2": {
            "tenant_key": "t2",
            "job_id": "j2",
            "conversation_id": "c2",
            "platform": "deepseek",
            "brand": "特斯拉",
            "category": "汽车",
            "keyword": "价格",
            "query_content": "宝马多少钱？",
            "url": "https://example.com/b",
            "is_published_link": "yes",
        },
    }
    rows, skipped = _plugin()._build_upsert_rows(answers, date.today())
    assert skipped == 0
    assert len(rows) == 2

    first = next(r for r in rows if r["conversation_id"] == "c1")
    second = next(r for r in rows if r["conversation_id"] == "c2")
    assert first["is_published_link"] == 0
    assert second["is_published_link"] == 1
