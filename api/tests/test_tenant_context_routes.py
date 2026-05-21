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
def tenant_db_engine():
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
                    industry VARCHAR(100),
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


@pytest.fixture(scope="function")
def tenant_db_session(tenant_db_engine):
    connection = tenant_db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _insert_tenant_member(tenant_db_session, *, role="member"):
    now = datetime.now(UTC)
    tenant_result = tenant_db_session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, industry, status, created_at, updated_at)
            VALUES ('tn_allowed', '允许访问租户', '互联网', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    tenant_db_session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, industry, status, created_at, updated_at)
            VALUES ('tn_other', '其他租户', '互联网', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    tenant_db_session.execute(
        text(
            """
            INSERT INTO users (
                id, user_key, email, password_hash, is_verified, status, created_at, updated_at
            ) VALUES (
                101, 'user_101', 'member@example.com', :password_hash, 1, 'active', :now, :now
            )
            """
        ),
        {"password_hash": hash_password("User12345"), "now": now},
    )
    tenant_db_session.execute(
        text(
            """
            INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
            VALUES (101, :tenant_id, :role, 'active', :now)
            """
        ),
        {"tenant_id": tenant_result.lastrowid, "role": role, "now": now},
    )
    tenant_db_session.flush()
    return 101


def _token(user_id=101):
    return create_access_token(user_id, TEST_SECRET)


def _dashboard_client(tenant_db_session):
    class FakeDashboardService:
        def get_available_dates(self, tenant_key, job_id=None):
            return ["20260101"]

    app = FastAPI()
    app.include_router(dashboard.router, prefix="/api/v1/dashboard")
    app.dependency_overrides[get_db] = lambda: tenant_db_session
    app.dependency_overrides[dashboard.get_dashboard_service] = lambda: FakeDashboardService()
    return TestClient(app)


def _query_jobs_client(tenant_db_session):
    app = FastAPI()
    app.include_router(query_jobs.router, prefix="/api/v1/query-jobs")
    app.dependency_overrides[get_db] = lambda: tenant_db_session
    return TestClient(app)


def test_dashboard_available_dates_requires_authentication(tenant_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _insert_tenant_member(tenant_db_session)
    client = _dashboard_client(tenant_db_session)

    response = client.get(
        "/api/v1/dashboard/available-dates",
        params={"tenant_key": "tn_allowed", "job_id": "job_1"},
    )

    assert response.status_code == 401


def test_dashboard_available_dates_rejects_cross_tenant(tenant_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _insert_tenant_member(tenant_db_session)
    client = _dashboard_client(tenant_db_session)

    response = client.get(
        "/api/v1/dashboard/available-dates",
        params={"tenant_key": "tn_other", "job_id": "job_1"},
        headers={"Authorization": f"Bearer {_token()}"},
    )

    assert response.status_code == 403


def test_dashboard_available_dates_allows_member_tenant(tenant_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _insert_tenant_member(tenant_db_session)
    client = _dashboard_client(tenant_db_session)

    response = client.get(
        "/api/v1/dashboard/available-dates",
        params={"tenant_key": "tn_allowed", "job_id": "job_1"},
        headers={"Authorization": f"Bearer {_token()}"},
    )

    assert response.status_code == 200
    assert response.json()["data"] == ["20260101"]


def test_query_job_status_requires_authentication(tenant_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _insert_tenant_member(tenant_db_session)
    client = _query_jobs_client(tenant_db_session)

    with (
        patch("api.v1.routes.query_jobs.sync_query_jobs_status"),
        patch("api.v1.routes.query_jobs.list_query_jobs_status_records", return_value=[]),
    ):
        response = client.get(
            "/api/v1/query-jobs/status",
            params={"tenant_key": "tn_allowed"},
        )

    assert response.status_code == 401


def test_query_job_load_requires_tenant_admin(tenant_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _insert_tenant_member(tenant_db_session, role="member")
    client = _query_jobs_client(tenant_db_session)
    payload = {
        "tenant_key": "tn_allowed",
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
                "Authorization": f"Bearer {_token()}",
                "X-Tenant-Key": "tn_allowed",
            },
        )

    assert response.status_code == 403

