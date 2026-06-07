from datetime import UTC, datetime, timedelta
from pathlib import Path

from analysis.src.plugins.metrics.mention_status import MentionStatusPlugin
from analysis.src.plugins.metrics.reference_status import ReferenceStatusPlugin
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQLITE_SCHEMA_FILE = PROJECT_ROOT / "api" / "database" / "schema_sqlite.sql"


def _build_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")
        raw_connection = conn.connection.driver_connection
        raw_connection.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))
    return Session(bind=engine)


def _seed_inputs(session: Session) -> None:
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
            VALUES ('tenant_a', 'Tenant A', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO monitoring_projects
              (tenant_key, project_id, name, industry, category, status, created_at, updated_at)
            VALUES
              ('tenant_a', 'project_a', '品牌监测项目', '教育', 'K12', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO project_brands
              (
                tenant_key,
                project_id,
                brand_id,
                brand_name,
                role,
                aliases,
                status,
                created_at,
                updated_at
              )
            VALUES
              ('tenant_a', 'project_a', 'brand_a', '品牌A', 'target', '[]', 'active', :now, :now),
              (
                'tenant_a',
                'project_a',
                'brand_b',
                '品牌B',
                'competitor',
                '[]',
                'active',
                :now,
                :now
              )
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO prompt_sets
              (tenant_key, project_id, prompt_set_id, version, name, status, created_at, updated_at)
            VALUES
              ('tenant_a', 'project_a', 'prompt_set_a', 1, '默认问题集', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO collection_jobs
              (
                tenant_key,
                collection_job_id,
                project_id,
                prompt_set_id,
                source_job_id,
                status,
                window_start,
                window_end,
                expected_task_count,
                succeeded_task_count,
                created_at,
                updated_at
              )
            VALUES
              (
                'tenant_a',
                'collection_job_a',
                'project_a',
                'prompt_set_a',
                'legacy_job_a',
                'succeeded',
                :window_start,
                :window_end,
                1,
                1,
                :now,
                :now
              )
            """
        ),
        {
            "window_start": now - timedelta(hours=1),
            "window_end": now + timedelta(hours=1),
            "now": now,
        },
    )
    session.execute(
        text(
            """
            INSERT INTO llm_conversations
              (
                tenant_key,
                job_id,
                conversation_id,
                platform,
                brand,
                category,
                keyword,
                query_content,
                answer_content,
                generated_date,
                extracted_at,
                created_at,
                updated_at
              )
            VALUES
              (
                'tenant_a',
                'legacy_job_a',
                'conv_a',
                'deepseek',
                '品牌A',
                '教育',
                '数学',
                '数学培训哪家好',
                '品牌A排在首位，品牌B也被提到。',
                '2026-06-07',
                :now,
                :now,
                :now
              )
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO llm_conversation_references
              (
                tenant_key,
                job_id,
                conversation_id,
                platform,
                brand,
                category,
                keyword,
                query_content,
                url,
                domain,
                cite_index,
                site_name,
                content_type,
                generated_date,
                created_at,
                updated_at
              )
            VALUES
              (
                'tenant_a',
                'legacy_job_a',
                'conv_a',
                'deepseek',
                '品牌A',
                '教育',
                '数学',
                '数学培训哪家好',
                'https://example.com/a',
                'example.com',
                1,
                'Example',
                NULL,
                '2026-06-07',
                :now,
                :now
              )
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO analysis_runs
              (
                tenant_key,
                analysis_run_id,
                project_id,
                collection_job_id,
                status,
                plugin_versions,
                input_watermark,
                started_at,
                finished_at,
                error_code,
                error_message,
                created_at,
                updated_at
              )
            VALUES
              (
                'tenant_a',
                'analysis_run_failed',
                'project_a',
                'collection_job_a',
                'failed',
                '{"mention_status":"MentionStatusPlugin"}',
                'legacy_job_a:2026-06-07T10:00:00+00:00',
                :started_at,
                :finished_at,
                'plugin_error',
                'LLM timeout',
                :started_at,
                :finished_at
              )
            """
        ),
        {
            "started_at": now,
            "finished_at": now + timedelta(minutes=3),
        },
    )
    session.execute(
        text(
            """
            INSERT INTO qa_brand_state
              (
                tenant_key,
                job_id,
                analysis_run_id,
                date,
                conversation_id,
                brand,
                category,
                platform,
                keyword,
                is_mentioned,
                is_first_mentioned,
                is_top3_mentioned,
                sentiment_status
              )
            VALUES
              (
                'tenant_a',
                'legacy_job_a',
                'analysis_run_failed',
                '2026-06-07',
                'conv_a',
                '品牌A',
                '教育',
                'deepseek',
                '数学',
                1,
                1,
                1,
                'positive'
              )
            """
        )
    )
    session.execute(
        text(
            """
            INSERT INTO qa_reference
              (
                tenant_key,
                job_id,
                analysis_run_id,
                date,
                conversation_id,
                platform,
                brand,
                category,
                keyword,
                query_content,
                url,
                is_published_link,
                domain,
                content_type
              )
            VALUES
              (
                'tenant_a',
                'legacy_job_a',
                'analysis_run_failed',
                '2026-06-07',
                'conv_a',
                'deepseek',
                '品牌A',
                '教育',
                '数学',
                '数学培训哪家好',
                'https://example.com/a',
                0,
                'example.com',
                'website'
              )
            """
        )
    )
    session.commit()


def _patch_mention_analyze(monkeypatch, plugin: MentionStatusPlugin) -> None:
    def fake_analyze(text: str, brand_name: str):
        assert brand_name == "品牌A"
        assert "品牌A排在首位" in text
        return {
            "target_brand": "品牌A",
            "is_mentioned": True,
            "is_first_mentioned": True,
            "is_top3_mentioned": True,
            "sentiment_status": "positive",
            "brands_found": ["品牌A", "品牌B"],
            "competitor_states": [
                {
                    "brand": "品牌B",
                    "is_mentioned": True,
                    "is_first_mentioned": False,
                    "is_top3_mentioned": True,
                    "sentiment_status": "neutral",
                }
            ],
        }

    monkeypatch.setattr(plugin, "analyze", fake_analyze)


def test_retry_failed_analysis_run_creates_new_run_and_rebinds_partial_facts(
    monkeypatch,
):
    from api.v1.services import analysis_runner

    session = _build_session()
    _seed_inputs(session)
    mention_plugin = MentionStatusPlugin(llm_config={})
    reference_plugin = ReferenceStatusPlugin(llm_config={})
    _patch_mention_analyze(monkeypatch, mention_plugin)

    result = analysis_runner.retry_analysis_run(
        session,
        tenant_key="tenant_a",
        analysis_run_id="analysis_run_failed",
        retry_analysis_run_id="analysis_run_retry",
        plugins={
            "mention_status": mention_plugin,
            "reference_status": reference_plugin,
        },
        now=datetime(2026, 6, 7, 11, 0, 0, tzinfo=UTC),
    )

    assert result.status_code == 200
    assert result.retried_from_analysis_run_id == "analysis_run_failed"
    assert result.analysis_run.analysis_run_id == "analysis_run_retry"
    assert result.analysis_run.status == "succeeded"

    run_rows = session.execute(
        text(
            """
            SELECT analysis_run_id, status, error_code, error_message
            FROM analysis_runs
            ORDER BY analysis_run_id
            """
        )
    ).all()
    assert run_rows == [
        ("analysis_run_failed", "failed", "plugin_error", "LLM timeout"),
        ("analysis_run_retry", "succeeded", None, None),
    ]

    fact_runs = session.execute(
        text(
            """
            SELECT DISTINCT analysis_run_id
            FROM qa_brand_state
            ORDER BY analysis_run_id
            """
        )
    ).all()
    assert fact_runs == [("analysis_run_retry",)]

    reference_runs = session.execute(
        text(
            """
            SELECT DISTINCT analysis_run_id
            FROM qa_reference
            ORDER BY analysis_run_id
            """
        )
    ).all()
    assert reference_runs == [("analysis_run_retry",)]


def test_retry_rejects_succeeded_analysis_run(monkeypatch):
    from api.v1.services import analysis_runner

    session = _build_session()
    _seed_inputs(session)
    mention_plugin = MentionStatusPlugin(llm_config={})
    reference_plugin = ReferenceStatusPlugin(llm_config={})
    _patch_mention_analyze(monkeypatch, mention_plugin)
    analysis_runner.run_collection_analysis(
        session,
        tenant_key="tenant_a",
        collection_job_id="collection_job_a",
        analysis_run_id="analysis_run_succeeded",
        plugins={
            "mention_status": mention_plugin,
            "reference_status": reference_plugin,
        },
        now=datetime(2026, 6, 7, 10, 30, 0, tzinfo=UTC),
    )

    result = analysis_runner.retry_analysis_run(
        session,
        tenant_key="tenant_a",
        analysis_run_id="analysis_run_succeeded",
        retry_analysis_run_id="analysis_run_retry",
        plugins={
            "mention_status": mention_plugin,
            "reference_status": reference_plugin,
        },
        now=datetime(2026, 6, 7, 11, 0, 0, tzinfo=UTC),
    )

    assert result.status_code == 409
    assert "failed" in result.message
