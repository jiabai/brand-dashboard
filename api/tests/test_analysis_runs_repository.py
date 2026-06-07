from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from api.v1.repositories import analysis_runs
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQLITE_SCHEMA_FILE = PROJECT_ROOT / "api" / "database" / "schema_sqlite.sql"


@pytest.fixture()
def analysis_run_session():
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


def _seed_collection_job(session: Session):
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
            VALUES ('tn_a', 'Tenant A', 'active', :now, :now)
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
              ('tn_a', 'proj_a', 'Project A', 'education', 'k12', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO prompt_sets
              (
                tenant_key,
                project_id,
                prompt_set_id,
                version,
                name,
                status,
                created_at,
                updated_at
              )
            VALUES
              ('tn_a', 'proj_a', 'prompt_set_a', 1, 'Prompt Set A', 'active', :now, :now)
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
                status,
                window_start,
                window_end,
                expected_task_count,
                created_at,
                updated_at
              )
            VALUES
              (
                'tn_a',
                'collection_job_a',
                'proj_a',
                'prompt_set_a',
                'succeeded',
                :window_start,
                :window_end,
                2,
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
    session.commit()


def _create_run(session: Session, *, analysis_run_id="analysis_run_a"):
    return analysis_runs.create_analysis_run(
        session,
        tenant_key="tn_a",
        analysis_run_id=analysis_run_id,
        collection_job_id="collection_job_a",
        plugin_versions='{"mention_status":"1.0.0"}',
        model_config_hash="model_hash_1",
        input_watermark="collection_job_a:2026-06-07T10:00:00Z",
        now=datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC),
    )


def test_create_analysis_run_defaults_to_pending_and_derives_project(
    analysis_run_session,
):
    _seed_collection_job(analysis_run_session)

    result = _create_run(analysis_run_session)

    assert result.status_code == 200
    run = result.analysis_run
    assert run.analysis_run_id == "analysis_run_a"
    assert run.project_id == "proj_a"
    assert run.collection_job_id == "collection_job_a"
    assert run.status == "pending"
    assert run.started_at is None
    assert run.finished_at is None


def test_analysis_run_success_state_machine(analysis_run_session):
    _seed_collection_job(analysis_run_session)
    assert _create_run(analysis_run_session).status_code == 200

    started = analysis_runs.start_analysis_run(
        analysis_run_session,
        tenant_key="tn_a",
        analysis_run_id="analysis_run_a",
        now=datetime(2026, 6, 7, 10, 1, 0, tzinfo=UTC),
    )
    assert started.status_code == 200
    assert started.analysis_run.status == "running"
    assert started.analysis_run.started_at is not None

    completed = analysis_runs.complete_analysis_run(
        analysis_run_session,
        tenant_key="tn_a",
        analysis_run_id="analysis_run_a",
        status="succeeded",
        now=datetime(2026, 6, 7, 10, 2, 0, tzinfo=UTC),
    )

    assert completed.status_code == 200
    assert completed.analysis_run.status == "succeeded"
    assert completed.analysis_run.finished_at is not None
    assert completed.analysis_run.error_code is None
    assert completed.analysis_run.error_message is None


def test_analysis_run_failure_records_error(analysis_run_session):
    _seed_collection_job(analysis_run_session)
    assert (
        _create_run(
            analysis_run_session,
            analysis_run_id="analysis_run_failed",
        ).status_code
        == 200
    )
    assert (
        analysis_runs.start_analysis_run(
            analysis_run_session,
            tenant_key="tn_a",
            analysis_run_id="analysis_run_failed",
            now=datetime(2026, 6, 7, 10, 1, 0, tzinfo=UTC),
        ).status_code
        == 200
    )

    failed = analysis_runs.complete_analysis_run(
        analysis_run_session,
        tenant_key="tn_a",
        analysis_run_id="analysis_run_failed",
        status="failed",
        error_code="plugin_error",
        error_message="mention_status 写入失败",
        now=datetime(2026, 6, 7, 10, 2, 0, tzinfo=UTC),
    )

    assert failed.status_code == 200
    assert failed.analysis_run.status == "failed"
    assert failed.analysis_run.error_code == "plugin_error"
    assert failed.analysis_run.error_message == "mention_status 写入失败"
    assert failed.analysis_run.finished_at is not None


def test_mark_analysis_run_stale_after_success(analysis_run_session):
    _seed_collection_job(analysis_run_session)
    assert _create_run(analysis_run_session).status_code == 200
    assert (
        analysis_runs.start_analysis_run(
            analysis_run_session,
            tenant_key="tn_a",
            analysis_run_id="analysis_run_a",
            now=datetime(2026, 6, 7, 10, 1, 0, tzinfo=UTC),
        ).status_code
        == 200
    )
    assert (
        analysis_runs.complete_analysis_run(
            analysis_run_session,
            tenant_key="tn_a",
            analysis_run_id="analysis_run_a",
            status="succeeded",
            now=datetime(2026, 6, 7, 10, 2, 0, tzinfo=UTC),
        ).status_code
        == 200
    )

    stale = analysis_runs.mark_analysis_run_stale(
        analysis_run_session,
        tenant_key="tn_a",
        analysis_run_id="analysis_run_a",
        reason="collection_job_a 新增原始回答",
        now=datetime(2026, 6, 7, 11, 0, 0, tzinfo=UTC),
    )

    assert stale.status_code == 200
    assert stale.analysis_run.status == "stale"
    assert stale.analysis_run.stale_at is not None
    assert stale.analysis_run.error_message == "collection_job_a 新增原始回答"


def test_invalid_analysis_run_transitions_are_rejected(analysis_run_session):
    _seed_collection_job(analysis_run_session)
    assert _create_run(analysis_run_session).status_code == 200

    stale_pending = analysis_runs.mark_analysis_run_stale(
        analysis_run_session,
        tenant_key="tn_a",
        analysis_run_id="analysis_run_a",
        reason="尚未运行的分析不应标记 stale",
        now=datetime(2026, 6, 7, 10, 1, 0, tzinfo=UTC),
    )
    assert stale_pending.status_code == 409

    assert (
        analysis_runs.start_analysis_run(
            analysis_run_session,
            tenant_key="tn_a",
            analysis_run_id="analysis_run_a",
            now=datetime(2026, 6, 7, 10, 2, 0, tzinfo=UTC),
        ).status_code
        == 200
    )
    assert (
        analysis_runs.complete_analysis_run(
            analysis_run_session,
            tenant_key="tn_a",
            analysis_run_id="analysis_run_a",
            status="succeeded",
            now=datetime(2026, 6, 7, 10, 3, 0, tzinfo=UTC),
        ).status_code
        == 200
    )

    invalid_complete = analysis_runs.complete_analysis_run(
        analysis_run_session,
        tenant_key="tn_a",
        analysis_run_id="analysis_run_a",
        status="failed",
        error_code="late_error",
        error_message="成功后不能再失败",
        now=datetime(2026, 6, 7, 10, 4, 0, tzinfo=UTC),
    )

    assert invalid_complete.status_code == 409
    row = analysis_run_session.execute(
        text(
            """
            SELECT status, error_code
            FROM analysis_runs
            WHERE tenant_key = 'tn_a'
              AND analysis_run_id = 'analysis_run_a'
            """
        )
    ).one()
    assert row.status == "succeeded"
    assert row.error_code is None
