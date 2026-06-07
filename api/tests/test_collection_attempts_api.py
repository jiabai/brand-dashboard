from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import collection_attempts, collection_tasks
from api.v1.routes.query_jobs import verify_executor
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQLITE_SCHEMA_FILE = PROJECT_ROOT / "api" / "database" / "schema_sqlite.sql"


@pytest.fixture()
def collection_attempt_session():
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


def _client(db_session, *, executor_id="exec_a"):
    app = FastAPI()
    app.include_router(collection_attempts.router, prefix="/api/v1/collection-attempts")
    app.include_router(collection_tasks.router, prefix="/api/v1/collection-tasks")
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[verify_executor] = lambda: executor_id
    return TestClient(app)


def _seed_reserved_task(
    session: Session,
    *,
    collection_task_id: str = "task_1",
    executor_id: str = "exec_a",
    attempt_count: int = 0,
    max_attempts: int = 3,
):
    now = datetime(2026, 6, 7, 8, 0, 0, tzinfo=UTC)
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
                'tn_a',
                'prompt_set_a',
                'prompt_item_a',
                'math',
                '数学培训哪家好',
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
                'running',
                :window_start,
                :window_end,
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
    for known_executor_id in ("exec_a", "exec_b"):
        session.execute(
            text(
                """
                INSERT INTO executors
                  (executor_id, name, status, ip_address, api_key, created_at, updated_at)
                VALUES
                  (:executor_id, :executor_id, 'active', '127.0.0.1', :executor_id, :now, :now)
                """
            ),
            {"executor_id": known_executor_id, "now": now},
        )
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
                lease_owner,
                lease_until,
                reserved_at,
                attempt_count,
                max_attempts,
                created_at,
                updated_at
              )
            VALUES
              (
                'tn_a',
                :collection_task_id,
                'collection_job_a',
                'proj_a',
                'prompt_set_a',
                'prompt_item_a',
                'deepseek',
                '数学培训哪家好',
                1,
                'reserved',
                :executor_id,
                :lease_until,
                :now,
                :attempt_count,
                :max_attempts,
                :now,
                :now
              )
            """
        ),
        {
            "collection_task_id": collection_task_id,
            "executor_id": executor_id,
            "lease_until": datetime.now(UTC) + timedelta(minutes=5),
            "attempt_count": attempt_count,
            "max_attempts": max_attempts,
            "now": now,
        },
    )
    session.commit()


def _start(client: TestClient, *, attempt_id="attempt_1", task_id="task_1"):
    return client.post(
        f"/api/v1/collection-attempts/{attempt_id}/start",
        json={"tenant_key": "tn_a", "collection_task_id": task_id},
    )


def _complete(
    client: TestClient,
    *,
    attempt_id="attempt_1",
    status="succeeded",
    error_message=None,
):
    payload = {
        "tenant_key": "tn_a",
        "status": status,
        "raw_response_id": "raw_1" if status == "succeeded" else None,
    }
    if error_message:
        payload["error_message"] = error_message
    return client.post(
        f"/api/v1/collection-attempts/{attempt_id}/complete",
        json=payload,
    )


def test_start_creates_running_attempt_for_current_lease_holder(
    collection_attempt_session,
):
    _seed_reserved_task(collection_attempt_session)
    client = _client(collection_attempt_session, executor_id="exec_a")

    response = _start(client)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["attempt"]["attempt_id"] == "attempt_1"
    assert body["attempt"]["status"] == "running"
    assert body["attempt"]["executor_id"] == "exec_a"

    task_row = collection_attempt_session.execute(
        text(
            """
            SELECT status, attempt_count, started_at
            FROM collection_tasks
            WHERE collection_task_id = 'task_1'
            """
        )
    ).one()
    assert task_row.status == "running"
    assert task_row.attempt_count == 1
    assert task_row.started_at is not None


def test_start_rejects_executor_that_does_not_hold_lease(collection_attempt_session):
    _seed_reserved_task(collection_attempt_session, executor_id="exec_a")
    client = _client(collection_attempt_session, executor_id="exec_b")

    response = _start(client)

    assert response.status_code == 403
    assert "无权启动" in response.json()["detail"]


def test_complete_success_marks_attempt_and_task_succeeded(collection_attempt_session):
    _seed_reserved_task(collection_attempt_session)
    client = _client(collection_attempt_session, executor_id="exec_a")
    assert _start(client).status_code == 200

    response = _complete(client, status="succeeded")

    assert response.status_code == 200
    body = response.json()
    assert body["attempt"]["status"] == "succeeded"
    assert body["attempt"]["raw_response_id"] == "raw_1"

    task_row = collection_attempt_session.execute(
        text(
            """
            SELECT status, lease_owner, lease_until, finished_at
            FROM collection_tasks
            WHERE collection_task_id = 'task_1'
            """
        )
    ).one()
    assert task_row.status == "succeeded"
    assert task_row.lease_owner is None
    assert task_row.lease_until is None
    assert task_row.finished_at is not None


def test_complete_failure_releases_task_for_retry(collection_attempt_session):
    _seed_reserved_task(collection_attempt_session, max_attempts=2)
    client = _client(collection_attempt_session, executor_id="exec_a")
    assert _start(client).status_code == 200

    response = _complete(client, status="failed", error_message="模型返回超时")

    assert response.status_code == 200
    assert response.json()["attempt"]["status"] == "failed"

    task_row = collection_attempt_session.execute(
        text(
            """
            SELECT status, lease_owner, last_error_message, attempt_count, max_attempts
            FROM collection_tasks
            WHERE collection_task_id = 'task_1'
            """
        )
    ).one()
    assert task_row.status == "failed"
    assert task_row.lease_owner is None
    assert task_row.last_error_message == "模型返回超时"
    assert task_row.attempt_count == 1
    assert task_row.max_attempts == 2

    retry_client = _client(collection_attempt_session, executor_id="exec_b")
    retry_response = retry_client.get(
        "/api/v1/collection-tasks/fetch",
        params={"executor_id": "exec_b", "tenant_key": "tn_a"},
    )
    assert retry_response.status_code == 200
    assert retry_response.json()["task"]["collection_task_id"] == "task_1"
    assert retry_response.json()["task"]["lease_owner"] == "exec_b"


def test_complete_timeout_exhausting_retries_keeps_task_failed(
    collection_attempt_session,
):
    _seed_reserved_task(collection_attempt_session, attempt_count=1, max_attempts=2)
    client = _client(collection_attempt_session, executor_id="exec_a")
    assert _start(client).status_code == 200

    response = _complete(client, status="timeout", error_message="执行器心跳超时")

    assert response.status_code == 200
    assert response.json()["attempt"]["status"] == "timeout"

    task_row = collection_attempt_session.execute(
        text(
            """
            SELECT status, lease_owner, lease_until, last_error_message, attempt_count
            FROM collection_tasks
            WHERE collection_task_id = 'task_1'
            """
        )
    ).one()
    assert task_row.status == "failed"
    assert task_row.lease_owner is None
    assert task_row.lease_until is None
    assert task_row.last_error_message == "执行器心跳超时"
    assert task_row.attempt_count == 2

    retry_client = _client(collection_attempt_session, executor_id="exec_b")
    retry_response = retry_client.get(
        "/api/v1/collection-tasks/fetch",
        params={"executor_id": "exec_b", "tenant_key": "tn_a"},
    )
    assert retry_response.json() == {"success": True, "count": 0, "task": None}
