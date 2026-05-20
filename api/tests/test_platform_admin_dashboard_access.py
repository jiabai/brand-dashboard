from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import dashboard, query_jobs
from api.v1.utils.jwt_utils import create_access_token
from api.v1.utils.security import hash_password
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

TEST_SECRET = "test-secret-with-at-least-32-bytes"


@pytest.fixture(scope="session")
def platform_read_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE tenants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL UNIQUE,
                    tenant_name VARCHAR(255) NOT NULL UNIQUE,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key VARCHAR(36) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_verified BOOLEAN NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE user_tenants (
                    user_id INTEGER NOT NULL,
                    tenant_id INTEGER NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'member',
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP,
                    PRIMARY KEY (user_id, tenant_id)
                )
                """
            )
        )
    return engine


@pytest.fixture
def db_session(platform_read_engine):
    connection = platform_read_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _insert_user(db_session, *, user_id, email, status="active"):
    now = datetime.now(UTC)
    db_session.execute(
        text(
            """
            INSERT INTO users (
                id, user_key, email, password_hash, is_verified, status, created_at, updated_at
            ) VALUES (
                :user_id, :user_key, :email, :password_hash, 1, :status, :now, :now
            )
            """
        ),
        {
            "user_id": user_id,
            "user_key": f"user_{user_id}",
            "email": email,
            "password_hash": hash_password("User12345"),
            "status": status,
            "now": now,
        },
    )
    db_session.flush()
    return user_id


def _insert_tenant(db_session, *, tenant_key, tenant_name="演示租户", status="active"):
    now = datetime.now(UTC)
    result = db_session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
            VALUES (:tenant_key, :tenant_name, :status, :now, :now)
            """
        ),
        {
            "tenant_key": tenant_key,
            "tenant_name": tenant_name,
            "status": status,
            "now": now,
        },
    )
    db_session.flush()
    return result.lastrowid


def _insert_membership(db_session, *, user_id, tenant_id, role="member", status="active"):
    db_session.execute(
        text(
            """
            INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
            VALUES (:user_id, :tenant_id, :role, :status, :now)
            """
        ),
        {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "status": status,
            "now": datetime.now(UTC),
        },
    )
    db_session.flush()


def _token(user_id):
    return create_access_token(user_id, TEST_SECRET)


def _dashboard_client(db_session):
    class FakeDashboardService:
        def get_available_dates(self, tenant_key, job_id=None):
            return [f"{tenant_key}:{job_id}"]

    app = FastAPI()
    app.include_router(dashboard.router, prefix="/api/v1/dashboard")
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[dashboard.get_dashboard_service] = lambda: FakeDashboardService()
    return TestClient(app)


def _query_jobs_client(db_session):
    app = FastAPI()
    app.include_router(query_jobs.router, prefix="/api/v1/query-jobs")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def test_platform_admin_can_read_active_tenant_dashboard_without_membership(
    db_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    _insert_user(db_session, user_id=201, email="ops@example.com")
    _insert_tenant(db_session, tenant_key="tn_customer")
    client = _dashboard_client(db_session)

    response = client.get(
        "/api/v1/dashboard/available-dates",
        params={"tenant_key": "tn_customer", "job_id": "job_1"},
        headers={"Authorization": f"Bearer {_token(201)}"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == ["tn_customer:job_1"]


def test_non_platform_user_still_cannot_read_tenant_without_membership(
    db_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    _insert_user(db_session, user_id=202, email="member@example.com")
    _insert_tenant(db_session, tenant_key="tn_customer")
    client = _dashboard_client(db_session)

    response = client.get(
        "/api/v1/dashboard/available-dates",
        params={"tenant_key": "tn_customer", "job_id": "job_1"},
        headers={"Authorization": f"Bearer {_token(202)}"},
    )

    assert response.status_code == 403


def test_platform_admin_cannot_read_inactive_tenant_dashboard_without_membership(
    db_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    _insert_user(db_session, user_id=203, email="ops@example.com")
    _insert_tenant(db_session, tenant_key="tn_inactive", status="inactive")
    client = _dashboard_client(db_session)

    response = client.get(
        "/api/v1/dashboard/available-dates",
        params={"tenant_key": "tn_inactive", "job_id": "job_1"},
        headers={"Authorization": f"Bearer {_token(203)}"},
    )

    assert response.status_code == 403


def test_tenant_member_still_reads_own_dashboard(db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user(db_session, user_id=204, email="member@example.com")
    tenant_id = _insert_tenant(db_session, tenant_key="tn_member")
    _insert_membership(db_session, user_id=user_id, tenant_id=tenant_id, role="viewer")
    client = _dashboard_client(db_session)

    response = client.get(
        "/api/v1/dashboard/available-dates",
        params={"tenant_key": "tn_member", "job_id": "job_1"},
        headers={"Authorization": f"Bearer {_token(204)}"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == ["tn_member:job_1"]


def test_platform_admin_read_bypass_does_not_grant_tenant_write(
    db_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    _insert_user(db_session, user_id=205, email="ops@example.com")
    _insert_tenant(db_session, tenant_key="tn_customer")
    client = _query_jobs_client(db_session)
    payload = {
        "tenant_key": "tn_customer",
        "job_id": "job_1",
        "effective_from": "2026-05-20T00:00:00Z",
        "executor_id": "exec_1",
        "data": {
            "category": "教育",
            "brand": "品牌A",
            "content": [{"keyword": "数学", "query_content": ["数学培训哪家好"]}],
        },
    }

    with patch("api.v1.routes.query_jobs.insert_query_jobs", return_value=1):
        response = client.post(
            "/api/v1/query-jobs/load",
            json=payload,
            headers={
                "Authorization": f"Bearer {_token(205)}",
                "X-Tenant-Key": "tn_customer",
            },
        )

    assert response.status_code == 403
