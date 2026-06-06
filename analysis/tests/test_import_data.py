from datetime import date
from pathlib import Path

from src.plugins.utils.import_mention_data import (
    _build_insert_rows,
    _iter_answers,
    _parse_date_from_payload,
)


def test_iter_answers_from_dict():
    payload = {
        "data": {
            "answers": {"k1": {"a": 1}, "k2": {"b": 2}, "k3": "x"}
        }
    }
    answers = list(_iter_answers(payload))
    assert answers == [{"a": 1}, {"b": 2}]


def test_iter_answers_from_list():
    payload = {"data": {"answers": [{"a": 1}, {"b": 2}, "x"]}}
    answers = list(_iter_answers(payload))
    assert answers == [{"a": 1}, {"b": 2}]


def test_parse_date_from_payload_prefers_date_directory(tmp_path: Path):
    p = tmp_path / "any.json"
    p.write_text("{}", encoding="utf-8")
    payload = {
        "date_directory": "20251214",
        "analysis_timestamp": "2025-12-22T00:00:00",
    }
    assert _parse_date_from_payload(payload, p) == date(2025, 12, 14)


def test_build_insert_rows_converts_types_and_dedups():
    answers = [
        {
            "tenant_key": "t1",
            "job_id": "j1",
            "conversation_id": "c1",
            "brand": "BMW",
            "category": "汽车",
            "platform": "deepseek",
            "keyword": "驾驶乐趣",
            "is_mentioned": True,
            "is_first_mentioned": "0",
            "is_top3_mentioned": True,
            "sentiment_status": "positive",
            "brands_found": ["宝马", "BMW"],
        },
        {
            "tenant_key": "t1",
            "job_id": "j1",
            "conversation_id": "c1",
            "brand": "BMW",
            "category": "汽车",
            "platform": "deepseek",
            "keyword": "驾驶乐趣",
            "is_mentioned": True,
            "is_first_mentioned": True,
            "is_top3_mentioned": True,
            "sentiment_status": "positive",
            "brands_found": ["宝马"],
        },
        {
            "tenant_key": "t2",
            "job_id": "j2",
            "conversation_id": "c2",
            "brand": "BMW",
            "category": "汽车",
            "platform": "deepseek",
            "keyword": "安全",
            "is_mentioned": 0,
            "is_first_mentioned": 1,
            "is_top3_mentioned": 1,
            "sentiment_status": "neutral",
            "brands_found": None,
        },
    ]
    rows, skipped = _build_insert_rows(date(2025, 12, 14), answers)
    assert skipped == 1
    assert len(rows) == 2

    first = rows[0]
    assert first["is_mentioned"] == 1
    assert first["is_first_mentioned"] == 0
    assert first["is_top3_mentioned"] == 1
    assert isinstance(first["brands_found"], str)

    second = rows[1]
    assert second["is_mentioned"] == 0
    assert second["is_first_mentioned"] == 1
    assert second["is_top3_mentioned"] == 1
    assert second["brands_found"] is None


def test_build_insert_rows_skips_missing_required_fields():
    rows, skipped = _build_insert_rows(
        date(2025, 12, 14), [{"tenant_key": "t1"}]
    )
    assert rows == []
    assert skipped == 1
