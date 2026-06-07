from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQLITE_SCHEMA_FILE = PROJECT_ROOT / "api" / "database" / "schema_sqlite.sql"


@pytest.fixture()
def snapshot_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")
        raw_connection = conn.connection.driver_connection
        raw_connection.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _seed_snapshot_inputs(session: Session, *, analysis_status: str = "succeeded"):
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
              ('tenant_a', 'project_a', 'Project A', 'education', 'k12', 'active', :now, :now)
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
              ('tenant_a', 'project_a', 'brand_a', 'Brand A', 'target', '[]', 'active', :now, :now)
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
              ('tenant_a', 'project_a', 'prompt_set_a', 1, 'Prompt Set A', 'active', :now, :now)
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
                failed_task_count,
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
                5,
                4,
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
            INSERT INTO analysis_runs
              (
                tenant_key,
                analysis_run_id,
                project_id,
                collection_job_id,
                status,
                input_watermark,
                started_at,
                finished_at,
                created_at,
                updated_at
              )
            VALUES
              (
                'tenant_a',
                'analysis_run_a',
                'project_a',
                'collection_job_a',
                :analysis_status,
                'legacy_job_a:2026-06-07T10:00:00+00:00',
                :now,
                :now,
                :now,
                :now
              )
            """
        ),
        {"analysis_status": analysis_status, "now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO qa_brand_state
              (
                job_id,
                tenant_key,
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
                sentiment_status,
                brands_found,
                created_at,
                updated_at
              )
            VALUES
              (
                'legacy_job_a',
                'tenant_a',
                'analysis_run_a',
                '2026-06-07',
                'conv_1',
                'Brand A',
                'education',
                'deepseek',
                'math',
                1,
                1,
                1,
                'positive',
                '["Brand A"]',
                :now,
                :now
              ),
              (
                'legacy_job_a',
                'tenant_a',
                'analysis_run_a',
                '2026-06-07',
                'conv_2',
                'Brand A',
                'education',
                'deepseek',
                'math',
                1,
                0,
                1,
                'negative',
                '["Brand A"]',
                :now,
                :now
              ),
              (
                'legacy_job_a',
                'tenant_a',
                'analysis_run_a',
                '2026-06-07',
                'conv_3',
                'Brand A',
                'education',
                'deepseek',
                'math',
                0,
                0,
                0,
                'neutral',
                '[]',
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
            INSERT INTO qa_reference
              (
                job_id,
                tenant_key,
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
                content_type,
                created_at,
                updated_at
              )
            VALUES
              (
                'legacy_job_a',
                'tenant_a',
                'analysis_run_a',
                '2026-06-07',
                'conv_1',
                'deepseek',
                'Brand A',
                'education',
                'math',
                'Which brand is best?',
                'https://example.com/a',
                0,
                'example.com',
                'article',
                :now,
                :now
              ),
              (
                'legacy_job_a',
                'tenant_a',
                'analysis_run_a',
                '2026-06-07',
                'conv_3',
                'deepseek',
                'Brand A',
                'education',
                'math',
                'Which brand is best?',
                'https://example.org/b',
                0,
                'example.org',
                'article',
                :now,
                :now
              )
            """
        ),
        {"now": now},
    )
    session.commit()


def test_generate_metric_snapshots_for_succeeded_analysis_run(snapshot_session):
    from api.v1.services import metric_snapshots

    _seed_snapshot_inputs(snapshot_session)

    result = metric_snapshots.generate_metric_snapshots_for_analysis_run(
        snapshot_session,
        tenant_key="tenant_a",
        analysis_run_id="analysis_run_a",
        generated_at=datetime(2026, 6, 7, 11, 0, 0, tzinfo=UTC),
    )

    assert result.status_code == 200
    assert result.snapshot_count == 8

    rows = snapshot_session.execute(
        text(
            """
            SELECT
              snapshot_id,
              metric_name,
              metric_value,
              metric_unit,
              metric_definition_version,
              metric_date,
              brand_id,
              brand_name,
              platform,
              keyword,
              expected_task_count,
              succeeded_task_count,
              failed_task_count,
              analyzed_answer_count,
              coverage_rate,
              source_watermark,
              analysis_run_id
            FROM metric_snapshots
            WHERE tenant_key = 'tenant_a'
              AND analysis_run_id = 'analysis_run_a'
            ORDER BY metric_name
            """
        )
    ).all()
    assert len(rows) == 8

    metrics = {row.metric_name: row.metric_value for row in rows}
    assert set(metrics) == {
        "first_mention_rate",
        "mention_rate",
        "reference_rate",
        "sentiment_negative_ratio",
        "sentiment_neutral_ratio",
        "sentiment_positive_ratio",
        "sentiment_unknown_ratio",
        "top3_mention_rate",
    }
    assert metrics["mention_rate"] == pytest.approx(0.666667)
    assert metrics["first_mention_rate"] == pytest.approx(0.333333)
    assert metrics["top3_mention_rate"] == pytest.approx(0.666667)
    assert metrics["sentiment_positive_ratio"] == pytest.approx(0.333333)
    assert metrics["sentiment_negative_ratio"] == pytest.approx(0.333333)
    assert metrics["sentiment_neutral_ratio"] == pytest.approx(0.333333)
    assert metrics["sentiment_unknown_ratio"] == pytest.approx(0.0)
    assert metrics["reference_rate"] == pytest.approx(0.666667)

    for row in rows:
        assert row.metric_unit == "ratio"
        assert row.metric_definition_version == "brand_metrics_v1"
        assert row.metric_date == "2026-06-07"
        assert row.brand_id == "brand_a"
        assert row.brand_name == "Brand A"
        assert row.platform == "deepseek"
        assert row.keyword == "math"
        assert row.expected_task_count == 5
        assert row.succeeded_task_count == 4
        assert row.failed_task_count == 1
        assert row.analyzed_answer_count == 3
        assert row.coverage_rate == pytest.approx(0.8)
        assert row.source_watermark == "legacy_job_a:2026-06-07T10:00:00+00:00"
        assert row.analysis_run_id == "analysis_run_a"

    first_snapshot_ids = {row.snapshot_id for row in rows}
    second_result = metric_snapshots.generate_metric_snapshots_for_analysis_run(
        snapshot_session,
        tenant_key="tenant_a",
        analysis_run_id="analysis_run_a",
        generated_at=datetime(2026, 6, 7, 11, 30, 0, tzinfo=UTC),
    )

    assert second_result.status_code == 200
    assert second_result.snapshot_count == 8
    second_rows = snapshot_session.execute(
        text(
            """
            SELECT snapshot_id
            FROM metric_snapshots
            WHERE tenant_key = 'tenant_a'
              AND analysis_run_id = 'analysis_run_a'
            """
        )
    ).all()
    assert len(second_rows) == 8
    assert {row.snapshot_id for row in second_rows} == first_snapshot_ids


def test_generate_metric_snapshots_rejects_failed_analysis_run(snapshot_session):
    from api.v1.services import metric_snapshots

    _seed_snapshot_inputs(snapshot_session, analysis_status="failed")

    result = metric_snapshots.generate_metric_snapshots_for_analysis_run(
        snapshot_session,
        tenant_key="tenant_a",
        analysis_run_id="analysis_run_a",
        generated_at=datetime(2026, 6, 7, 11, 0, 0, tzinfo=UTC),
    )

    assert result.status_code == 409
    snapshot_count = snapshot_session.execute(
        text("SELECT COUNT(*) FROM metric_snapshots")
    ).scalar_one()
    assert snapshot_count == 0
