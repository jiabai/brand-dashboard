from datetime import date

from analysis.src.plugins.metrics.mention_status import MentionStatusPlugin
from analysis.src.plugins.metrics.reference_status import ReferenceStatusPlugin


def test_mention_status_builds_fact_rows_with_analysis_run_id():
    plugin = MentionStatusPlugin(llm_config={})

    rows, skipped = plugin._build_qa_brand_state_rows(
        date(2026, 6, 7),
        [
            {
                "tenant_key": "tenant_a",
                "job_id": "legacy_job_a",
                "analysis_run_id": "analysis_run_a",
                "conversation_id": "conv_a",
                "brand": "品牌A",
                "category": "教育",
                "platform": "deepseek",
                "keyword": "数学",
                "is_mentioned": True,
                "is_first_mentioned": True,
                "is_top3_mentioned": True,
                "sentiment_status": "positive",
                "brands_found": ["品牌A"],
            }
        ],
    )

    assert skipped == 0
    assert rows[0]["analysis_run_id"] == "analysis_run_a"


def test_reference_status_builds_fact_rows_with_analysis_run_id():
    plugin = ReferenceStatusPlugin(llm_config={})

    rows, skipped = plugin._build_upsert_rows(
        {
            "ref_a": {
                "tenant_key": "tenant_a",
                "job_id": "legacy_job_a",
                "analysis_run_id": "analysis_run_a",
                "conversation_id": "conv_a",
                "platform": "deepseek",
                "brand": "品牌A",
                "category": "教育",
                "keyword": "数学",
                "query_content": "数学培训哪家好",
                "url": "https://example.com/a",
                "is_published_link": False,
                "domain": "example.com",
                "content_type": "website",
            }
        },
        date(2026, 6, 7),
    )

    assert skipped == 0
    assert rows[0]["analysis_run_id"] == "analysis_run_a"
