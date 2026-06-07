from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import auth
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
def platform_health_session():
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
    app.include_router(auth.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _insert_platform_user(session: Session, *, user_id=401, email="ops@example.com"):
    now = datetime(2026, 6, 7, 9, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO users (
                id, user_key, email, password_hash, is_verified, status, created_at, updated_at
            )
            VALUES (
                :user_id, :user_key, :email, :password_hash, 1, 'active', :now, :now
            )
            """
        ),
        {
            "user_id": user_id,
            "user_key": f"user_{user_id}",
            "email": email,
            "password_hash": hash_password("User12345"),
            "now": now,
        },
    )
    session.flush()
    return user_id


def _token(user_id):
    return create_access_token(user_id, TEST_SECRET)


def _seed_collection_health(session: Session):
    now = datetime(2026, 6, 7, 9, 0, 0, tzinfo=UTC)
    for tenant_key, tenant_name, project_id, project_name, prompt_set_id in (
        ("tn_a", "Tenant A", "proj_a", "Project A", "prompt_set_a"),
        ("tn_b", "Tenant B", "proj_b", "Project B", "prompt_set_b"),
    ):
        session.execute(
            text(
                """
                INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
                VALUES (:tenant_key, :tenant_name, 'active', :now, :now)
                """
            ),
            {"tenant_key": tenant_key, "tenant_name": tenant_name, "now": now},
        )
        session.execute(
            text(
                """
                INSERT INTO monitoring_projects
                  (
                    tenant_key,
                    project_id,
                    name,
                    industry,
                    category,
                    status,
                    created_at,
                    updated_at
                  )
                VALUES
                  (
                    :tenant_key,
                    :project_id,
                    :project_name,
                    'education',
                    'k12',
                    'active',
                    :now,
                    :now
                  )
                """
            ),
            {
                "tenant_key": tenant_key,
                "project_id": project_id,
                "project_name": project_name,
                "now": now,
            },
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
                  (
                    :tenant_key,
                    :project_id,
                    :prompt_set_id,
                    1,
                    :prompt_set_id,
                    'active',
                    :now,
                    :now
                  )
                """
            ),
            {
                "tenant_key": tenant_key,
                "project_id": project_id,
                "prompt_set_id": prompt_set_id,
                "now": now,
            },
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
                    :prompt_set_id,
                    :prompt_item_id,
                    'math',
                    '数学培训哪家好',
                    'active',
                    :now,
                    :now
                  )
                """
            ),
            {
                "tenant_key": tenant_key,
                "prompt_set_id": prompt_set_id,
                "prompt_item_id": f"prompt_item_{tenant_key}",
                "now": now,
            },
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
                    :tenant_key,
                    :collection_job_id,
                    :project_id,
                    :prompt_set_id,
                    'running',
                    :window_start,
                    :window_end,
                    6,
                    :now,
                    :now
                  )
                """
            ),
            {
                "tenant_key": tenant_key,
                "collection_job_id": f"collection_job_{tenant_key}",
                "project_id": project_id,
                "prompt_set_id": prompt_set_id,
                "window_start": now - timedelta(hours=2),
                "window_end": now + timedelta(hours=2),
                "now": now,
            },
        )

    session.execute(
        text(
            """
            INSERT INTO executors
              (executor_id, name, type, status, ip_address, api_key, created_at, updated_at)
            VALUES
              ('exec_a', '主执行器', 'collector', 'active', '127.0.0.1', 'key_a', :now, :now),
              ('exec_b', '备用执行器', 'collector', 'inactive', '127.0.0.2', 'key_b', :now, :now)
            """
        ),
        {"now": now},
    )

    tasks = [
        ("task_pending", "tn_a", "pending", None, None, 0, 3, None),
        (
            "task_reserved",
            "tn_a",
            "reserved",
            "exec_a",
            datetime.now(UTC) + timedelta(minutes=5),
            0,
            3,
            None,
        ),
        (
            "task_expired",
            "tn_a",
            "reserved",
            "exec_a",
            datetime.now(UTC) - timedelta(minutes=5),
            0,
            3,
            None,
        ),
        (
            "task_running",
            "tn_a",
            "running",
            "exec_a",
            datetime.now(UTC) + timedelta(minutes=5),
            1,
            3,
            None,
        ),
        ("task_failed_retry", "tn_a", "failed", None, None, 1, 3, "模型返回超时"),
        ("task_failed_terminal", "tn_b", "failed", None, None, 3, 3, "达到最大重试次数"),
    ]
    for (
        task_id,
        tenant_key,
        status,
        lease_owner,
        lease_until,
        attempts,
        max_attempts,
        error_message,
    ) in tasks:
        prompt_set_id = "prompt_set_a" if tenant_key == "tn_a" else "prompt_set_b"
        project_id = "proj_a" if tenant_key == "tn_a" else "proj_b"
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
                    :task_id,
                    :collection_job_id,
                    :project_id,
                    :prompt_set_id,
                    :prompt_item_id,
                    'deepseek',
                    :query_content,
                    1,
                    :status,
                    :lease_owner,
                    :lease_until,
                    :attempt_count,
                    :max_attempts,
                    :last_error_code,
                    :last_error_message,
                    :now,
                    :updated_at
                  )
                """
            ),
            {
                "tenant_key": tenant_key,
                "task_id": task_id,
                "collection_job_id": f"collection_job_{tenant_key}",
                "project_id": project_id,
                "prompt_set_id": prompt_set_id,
                "prompt_item_id": f"prompt_item_{tenant_key}",
                "query_content": f"{task_id} 的问题",
                "status": status,
                "lease_owner": lease_owner,
                "lease_until": lease_until,
                "attempt_count": attempts,
                "max_attempts": max_attempts,
                "last_error_code": "llm_timeout" if error_message else None,
                "last_error_message": error_message,
                "now": now,
                "updated_at": now + timedelta(minutes=attempts),
            },
        )

    session.execute(
        text(
            """
            INSERT INTO collection_attempts
              (
                tenant_key,
                attempt_id,
                collection_task_id,
                executor_id,
                status,
                started_at,
                created_at,
                updated_at
              )
            VALUES
              (
                'tn_a',
                'attempt_running',
                'task_running',
                'exec_a',
                'running',
                :now,
                :now,
                :now
              )
            """
        ),
        {"now": now},
    )
    session.commit()


def test_platform_admin_reads_collection_health_without_tenant_header(
    platform_health_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    user_id = _insert_platform_user(platform_health_session)
    _seed_collection_health(platform_health_session)
    client = _client(platform_health_session)

    response = client.get(
        "/api/v1/platform/collection-health",
        headers={"Authorization": f"Bearer {_token(user_id)}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    data = body["data"]
    assert data["summary"] == {
        "executorCount": 2,
        "activeExecutorCount": 1,
        "inactiveExecutorCount": 1,
        "pendingTaskCount": 1,
        "reservedTaskCount": 2,
        "runningTaskCount": 1,
        "failedTaskCount": 2,
        "retryableFailedTaskCount": 1,
        "expiredLeaseTaskCount": 1,
    }

    exec_a = next(item for item in data["executors"] if item["executorId"] == "exec_a")
    assert exec_a["healthStatus"] == "active"
    assert exec_a["activeLeaseCount"] == 2
    assert exec_a["runningAttemptCount"] == 1

    queue_a = next(item for item in data["queues"] if item["tenantKey"] == "tn_a")
    assert queue_a["tenantName"] == "Tenant A"
    assert queue_a["projectName"] == "Project A"
    assert queue_a["pendingTaskCount"] == 1
    assert queue_a["failedTaskCount"] == 1
    assert queue_a["expiredLeaseTaskCount"] == 1

    failed_ids = {item["collectionTaskId"] for item in data["failedTasks"]}
    assert failed_ids == {"task_failed_retry", "task_failed_terminal"}


def test_non_platform_user_cannot_read_collection_health(
    platform_health_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    user_id = _insert_platform_user(
        platform_health_session,
        user_id=402,
        email="member@example.com",
    )
    _seed_collection_health(platform_health_session)
    client = _client(platform_health_session)

    response = client.get(
        "/api/v1/platform/collection-health",
        headers={"Authorization": f"Bearer {_token(user_id)}"},
    )

    assert response.status_code == 403
