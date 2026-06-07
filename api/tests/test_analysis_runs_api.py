from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import analysis_runs as analysis_runs_route
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
def analysis_run_api_session():
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
    app.include_router(analysis_runs_route.router, prefix="/api/v1/analysis-runs")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _token(user_id=101):
    return create_access_token(user_id, TEST_SECRET)


def _insert_user_tenant(db_session, *, role="member", user_id=101):
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    tenant_result = db_session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, industry, status, created_at, updated_at)
            VALUES ('tn_allowed', 'Allowed Tenant', 'education', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    tenant_id = tenant_result.lastrowid
    db_session.execute(
        text(
            """
            INSERT INTO users (
                id, user_key, email, password_hash, is_verified, status, created_at, updated_at
            ) VALUES (
                :user_id, :user_key, :email, :password_hash, 1, 'active', :now, :now
            )
            """
        ),
        {
            "user_id": user_id,
            "user_key": f"user_{user_id}",
            "email": f"user{user_id}@example.com",
            "password_hash": hash_password("User12345"),
            "now": now,
        },
    )
    db_session.execute(
        text(
            """
            INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
            VALUES (:user_id, :tenant_id, :role, 'active', :now)
            """
        ),
        {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "now": now,
        },
    )
    db_session.flush()
    return user_id


def _seed_failed_analysis_run(db_session):
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    db_session.execute(
        text(
            """
            INSERT INTO monitoring_projects
              (tenant_key, project_id, name, industry, category, status, created_at, updated_at)
            VALUES
              ('tn_allowed', 'project_a', 'Project A', 'education', 'k12', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    db_session.execute(
        text(
            """
            INSERT INTO prompt_sets
              (tenant_key, project_id, prompt_set_id, version, name, status, created_at, updated_at)
            VALUES
              ('tn_allowed', 'project_a', 'prompt_set_a', 1, 'Prompt Set A', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    db_session.execute(
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
                'tn_allowed',
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
    db_session.execute(
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
                'tn_allowed',
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
    db_session.commit()


def _headers(user_id):
    return {
        "Authorization": f"Bearer {_token(user_id)}",
        "X-Tenant-Key": "tn_allowed",
    }


def test_get_analysis_run_exposes_failure_details(
    analysis_run_api_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user_tenant(analysis_run_api_session, role="member")
    _seed_failed_analysis_run(analysis_run_api_session)
    client = _client(analysis_run_api_session)

    response = client.get(
        "/api/v1/analysis-runs/analysis_run_failed",
        headers=_headers(user_id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["analysis_run"]["analysis_run_id"] == "analysis_run_failed"
    assert body["analysis_run"]["status"] == "failed"
    assert body["analysis_run"]["error_code"] == "plugin_error"
    assert body["analysis_run"]["error_message"] == "LLM timeout"
    assert body["analysis_run"]["can_retry"] is True


def test_retry_analysis_run_requires_tenant_admin(
    analysis_run_api_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user_tenant(analysis_run_api_session, role="member")
    _seed_failed_analysis_run(analysis_run_api_session)
    client = _client(analysis_run_api_session)

    response = client.post(
        "/api/v1/analysis-runs/analysis_run_failed/retry",
        json={"analysis_run_id": "analysis_run_retry"},
        headers=_headers(user_id),
    )

    assert response.status_code == 403


def test_retry_analysis_run_returns_new_run(
    analysis_run_api_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user_tenant(analysis_run_api_session, role="admin")
    _seed_failed_analysis_run(analysis_run_api_session)
    client = _client(analysis_run_api_session)

    def fake_retry_analysis_run(
        db,
        *,
        tenant_key,
        analysis_run_id,
        retry_analysis_run_id=None,
        now=None,
        plugins=None,
    ):
        assert tenant_key == "tn_allowed"
        assert analysis_run_id == "analysis_run_failed"
        assert retry_analysis_run_id == "analysis_run_retry"
        return SimpleNamespace(
            status_code=200,
            message="analysis run 已重试",
            retried_from_analysis_run_id="analysis_run_failed",
            analysis_run=SimpleNamespace(
                id=2,
                tenant_key="tn_allowed",
                analysis_run_id="analysis_run_retry",
                project_id="project_a",
                collection_job_id="collection_job_a",
                status="succeeded",
                plugin_versions='{"mention_status":"MentionStatusPlugin"}',
                model_config_hash=None,
                input_watermark="legacy_job_a:2026-06-07T11:00:00+00:00",
                started_at=now,
                finished_at=now,
                stale_at=None,
                error_code=None,
                error_message=None,
            ),
        )

    monkeypatch.setattr(
        analysis_runs_route.analysis_runner,
        "retry_analysis_run",
        fake_retry_analysis_run,
    )

    response = client.post(
        "/api/v1/analysis-runs/analysis_run_failed/retry",
        json={"analysis_run_id": "analysis_run_retry"},
        headers=_headers(user_id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["retried_from_analysis_run_id"] == "analysis_run_failed"
    assert body["analysis_run"]["analysis_run_id"] == "analysis_run_retry"
    assert body["analysis_run"]["status"] == "succeeded"
