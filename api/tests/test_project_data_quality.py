from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import projects
from api.v1.utils.jwt_utils import create_access_token
from api.v1.utils.security import hash_password
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQLITE_SCHEMA_FILE = PROJECT_ROOT / "api" / "database" / "schema_sqlite.sql"
TEST_SECRET = "test-secret-with-at-least-32-bytes"


@pytest.fixture()
def quality_session():
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


def _client(db_session):
    app = FastAPI()
    app.include_router(projects.router, prefix="/api/v1/projects")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _headers():
    token = create_access_token(101, TEST_SECRET)
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Key": "tenant_a",
    }


def _seed_tenant_project(session: Session, *, tenant_key: str = "tenant_a"):
    now = datetime(2026, 6, 8, 9, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
            VALUES (:tenant_key, :tenant_name, 'active', :now, :now)
            """
        ),
        {
            "tenant_key": tenant_key,
            "tenant_name": f"{tenant_key} name",
            "now": now,
        },
    )
    session.execute(
        text(
            """
            INSERT INTO monitoring_projects
              (tenant_key, project_id, name, industry, category, status, created_at, updated_at)
            VALUES
              (:tenant_key, 'project_a', 'Project A', 'education', 'k12', 'active', :now, :now)
            """
        ),
        {"tenant_key": tenant_key, "now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO prompt_sets
              (tenant_key, project_id, prompt_set_id, version, name, status, created_at, updated_at)
            VALUES
              (:tenant_key, 'project_a', 'prompt_set_a', 1, 'Prompt Set A', 'active', :now, :now)
            """
        ),
        {"tenant_key": tenant_key, "now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO prompt_items
              (
                tenant_key,
                prompt_set_id,
                prompt_item_id,
                keyword,
                query_content,
                status,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                'prompt_set_a',
                'prompt_item_a',
                'math',
                'Which tutoring brand is mentioned?',
                'active',
                :now,
                :now
              )
            """
        ),
        {"tenant_key": tenant_key, "now": now},
    )
    session.flush()


def _seed_user_tenant(session: Session):
    now = datetime(2026, 6, 8, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO users (
                id, user_key, email, password_hash, is_verified, status, created_at, updated_at
            ) VALUES (
                101, 'user_101', 'member@example.com', :password_hash, 1, 'active', :now, :now
            )
            """
        ),
        {
            "password_hash": hash_password("User12345"),
            "now": now,
        },
    )
    tenant_id = session.execute(
        text("SELECT id FROM tenants WHERE tenant_key = 'tenant_a'")
    ).scalar_one()
    session.execute(
        text(
            """
            INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
            VALUES (101, :tenant_id, 'member', 'active', :now)
            """
        ),
        {
            "tenant_id": tenant_id,
            "now": now,
        },
    )
    session.flush()


def _insert_collection_job(
    session: Session,
    *,
    tenant_key: str = "tenant_a",
    collection_job_id: str = "collection_current",
    status: str = "failed",
):
    now = datetime(2026, 6, 8, 10, 0, 0, tzinfo=UTC)
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
                :tenant_key,
                :collection_job_id,
                'project_a',
                'prompt_set_a',
                :source_job_id,
                :status,
                :window_start,
                :window_end,
                4,
                3,
                1,
                :now,
                :now
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "collection_job_id": collection_job_id,
            "source_job_id": f"legacy_{collection_job_id}",
            "status": status,
            "window_start": now - timedelta(hours=2),
            "window_end": now,
            "now": now,
        },
    )


def _insert_collection_task(
    session: Session,
    *,
    tenant_key: str = "tenant_a",
    collection_task_id: str,
    status: str,
    attempt_count: int,
    max_attempts: int,
    error_code: str | None = None,
    error_message: str | None = None,
):
    now = datetime(2026, 6, 8, 11, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO collection_tasks
              (
                tenant_key,
                collection_task_id,
                collection_job_id,
                project_id,
                prompt_set_id,
                prompt_item_id,
                platform,
                query_content,
                run_index,
                status,
                attempt_count,
                max_attempts,
                last_error_code,
                last_error_message,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                :collection_task_id,
                'collection_current',
                'project_a',
                'prompt_set_a',
                'prompt_item_a',
                'deepseek',
                'Which tutoring brand is mentioned?',
                1,
                :status,
                :attempt_count,
                :max_attempts,
                :error_code,
                :error_message,
                :now,
                :now
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "collection_task_id": collection_task_id,
            "status": status,
            "attempt_count": attempt_count,
            "max_attempts": max_attempts,
            "error_code": error_code,
            "error_message": error_message,
            "now": now + timedelta(minutes=attempt_count),
        },
    )


def _insert_analysis_run(
    session: Session,
    *,
    tenant_key: str = "tenant_a",
    analysis_run_id: str,
    status: str,
):
    now = datetime(2026, 6, 8, 12, 0, 0, tzinfo=UTC)
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
                stale_at,
                error_code,
                error_message,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                :analysis_run_id,
                'project_a',
                'collection_current',
                :status,
                '{"mention_status": "v1"}',
                'collection_current',
                :now,
                :now,
                :stale_at,
                :error_code,
                :error_message,
                :now,
                :now
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "analysis_run_id": analysis_run_id,
            "status": status,
            "stale_at": now if status == "stale" else None,
            "error_code": "stale" if status == "stale" else None,
            "error_message": "Prompt set changed" if status == "stale" else None,
            "now": now,
        },
    )


def _insert_brand_state(
    session: Session,
    *,
    tenant_key: str = "tenant_a",
    conversation_id: str,
):
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
                sentiment_status,
                brands_found,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                'legacy_collection_current',
                'analysis_current',
                '2026-06-08',
                :conversation_id,
                'Brand A',
                'education',
                'deepseek',
                'math',
                1,
                0,
                1,
                'positive',
                '["Brand A"]',
                '2026-06-08 13:00:00',
                '2026-06-08 13:00:00'
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "conversation_id": conversation_id,
        },
    )


def _seed_quality_data(session: Session):
    _seed_tenant_project(session)
    _seed_tenant_project(session, tenant_key="tenant_other")
    _seed_user_tenant(session)
    _insert_collection_job(session)
    _insert_collection_job(session, tenant_key="tenant_other")
    _insert_collection_task(
        session,
        collection_task_id="task_failed_retry",
        status="failed",
        attempt_count=1,
        max_attempts=3,
        error_code="llm_timeout",
        error_message="LLM timed out",
    )
    _insert_collection_task(
        session,
        collection_task_id="task_failed_terminal",
        status="failed",
        attempt_count=3,
        max_attempts=3,
        error_code="quota_exceeded",
        error_message="Quota exceeded",
    )
    _insert_collection_task(
        session,
        collection_task_id="task_succeeded",
        status="succeeded",
        attempt_count=1,
        max_attempts=3,
    )
    _insert_collection_task(
        session,
        tenant_key="tenant_other",
        collection_task_id="task_other_failed",
        status="failed",
        attempt_count=1,
        max_attempts=3,
        error_code="other",
        error_message="Other tenant error",
    )
    _insert_analysis_run(session, analysis_run_id="analysis_current", status="succeeded")
    _insert_analysis_run(session, analysis_run_id="analysis_stale", status="stale")
    _insert_analysis_run(
        session,
        tenant_key="tenant_other",
        analysis_run_id="analysis_other_stale",
        status="stale",
    )
    for index in range(1, 4):
        _insert_brand_state(session, conversation_id=f"conv_{index}")
    session.commit()


def test_project_data_quality_api_returns_failed_stale_coverage_and_actions(
    quality_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed_quality_data(quality_session)
    client = _client(quality_session)

    response = client.get("/api/v1/projects/project_a/data-quality", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["project_id"] == "project_a"
    assert body["summary"] == {
        "failed_collection_task_count": 2,
        "retryable_failed_collection_task_count": 1,
        "stale_analysis_run_count": 1,
        "recomputable_analysis_run_count": 1,
        "analysis_fact_count": 3,
        "analysis_dimension_count": 1,
        "analysis_coverage_rate": 0.75,
    }

    failed_ids = {item["collection_task_id"] for item in body["failed_collection_tasks"]}
    assert failed_ids == {"task_failed_retry", "task_failed_terminal"}
    retryable = next(
        item
        for item in body["failed_collection_tasks"]
        if item["collection_task_id"] == "task_failed_retry"
    )
    assert retryable["can_retry"] is True
    assert retryable["keyword"] == "math"
    assert retryable["last_error_code"] == "llm_timeout"

    terminal = next(
        item
        for item in body["failed_collection_tasks"]
        if item["collection_task_id"] == "task_failed_terminal"
    )
    assert terminal["can_retry"] is False

    assert body["metric_coverage"]["data_source"] == "analysis_fact"
    assert body["metric_coverage"]["coverage_status"] == "available"
    assert body["metric_coverage"]["analysis_run_id"] == "analysis_current"
    assert body["metric_coverage"]["expected_task_count"] == 4
    assert body["metric_coverage"]["succeeded_task_count"] == 3
    assert body["metric_coverage"]["failed_task_count"] == 1
    assert body["metric_coverage"]["analyzed_answer_count"] == 3
    assert body["metric_coverage"]["analysis_fact_count"] == 3

    stale_runs = body["stale_analysis_runs"]
    assert [item["analysis_run_id"] for item in stale_runs] == ["analysis_stale"]
    assert stale_runs[0]["can_recompute"] is True
    assert stale_runs[0]["recompute_endpoint"] == "/api/v1/analysis-runs/analysis_stale/retry"

    assert body["recompute_actions"] == [
        {
            "action_type": "retry_analysis_run",
            "analysis_run_id": "analysis_stale",
            "label": "Retry analysis run analysis_stale",
            "method": "POST",
            "endpoint": "/api/v1/analysis-runs/analysis_stale/retry",
            "enabled": True,
        }
    ]


def test_project_data_quality_api_returns_404_for_other_tenant_project(
    quality_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed_tenant_project(quality_session, tenant_key="tenant_a")
    _seed_user_tenant(quality_session)
    client = _client(quality_session)

    response = client.get("/api/v1/projects/missing_project/data-quality", headers=_headers())

    assert response.status_code == 404
