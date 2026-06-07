from datetime import UTC, datetime, timedelta

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import query_jobs
from api.v1.utils.jwt_utils import create_access_token
from api.v1.utils.security import hash_password
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

TEST_SECRET = "test-secret-with-at-least-32-bytes"


@pytest.fixture()
def query_job_project_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
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
                    is_verified BOOLEAN NOT NULL DEFAULT 1,
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
                    role VARCHAR(50) NOT NULL DEFAULT 'admin',
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP,
                    PRIMARY KEY (user_id, tenant_id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE monitoring_projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL,
                    project_id VARCHAR(128) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    industry VARCHAR(100),
                    category VARCHAR(100),
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_by INTEGER,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    UNIQUE (tenant_key, project_id),
                    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE llm_query_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL,
                    job_id VARCHAR(255) NOT NULL,
                    project_id VARCHAR(128),
                    category VARCHAR(64) NOT NULL,
                    brand VARCHAR(50),
                    competitor TEXT,
                    keyword VARCHAR(100) NOT NULL,
                    query_content TEXT NOT NULL,
                    query_status INTEGER NOT NULL DEFAULT 0,
                    executor_id VARCHAR(128),
                    total_runs INTEGER NOT NULL DEFAULT 15,
                    executed_runs INTEGER NOT NULL DEFAULT 0,
                    last_executed_date DATE,
                    effective_from TIMESTAMP NOT NULL,
                    effective_to TIMESTAMP,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (tenant_key) REFERENCES tenants(tenant_key) ON DELETE CASCADE
                )
                """
            )
        )
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _client(db_session):
    app = FastAPI()
    app.include_router(query_jobs.router, prefix="/api/v1/query-jobs")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _token(user_id=101):
    return create_access_token(user_id, TEST_SECRET)


def _seed_admin_and_project(db_session, *, project_id="proj_active"):
    now = datetime.now(UTC)
    tenant_result = db_session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, industry, status, created_at, updated_at)
            VALUES ('tn_allowed', 'Allowed Tenant', 'technology', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    db_session.execute(
        text(
            """
            INSERT INTO users (
                id, user_key, email, password_hash, is_verified, status, created_at, updated_at
            )
            VALUES (
                101, 'user_101', 'admin@example.com', :password_hash, 1, 'active', :now, :now
            )
            """
        ),
        {"password_hash": hash_password("User12345"), "now": now},
    )
    db_session.execute(
        text(
            """
            INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
            VALUES (101, :tenant_id, 'admin', 'active', :now)
            """
        ),
        {"tenant_id": tenant_result.lastrowid, "now": now},
    )
    db_session.execute(
        text(
            """
            INSERT INTO monitoring_projects (
              tenant_key, project_id, name, industry, category, status,
              created_by, created_at, updated_at
            )
            VALUES (
              'tn_allowed', :project_id, 'Project', 'auto', 'ev', 'active',
              101, :now, :now
            )
            """
        ),
        {"project_id": project_id, "now": now},
    )
    db_session.commit()


def _payload(*, project_id="proj_active", job_id="job_project_link"):
    now = datetime.now(UTC)
    return {
        "tenant_key": "tn_allowed",
        "job_id": job_id,
        "project_id": project_id,
        "executor_id": "exec_demo",
        "total_runs": 2,
        "executed_runs": 0,
        "last_executed_date": now.date().isoformat(),
        "effective_from": (now - timedelta(minutes=1)).isoformat(),
        "effective_to": None,
        "data": {
            "category": "智能手机",
            "brand": "Atlas",
            "competitor": ["Northstar"],
            "content": [
                {
                    "keyword": "续航",
                    "query_content": ["哪款手机适合长时间出差使用？", "手机续航哪家强？"],
                }
            ],
        },
    }


def test_load_query_jobs_persists_project_id_mapping(query_job_project_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed_admin_and_project(query_job_project_session, project_id="proj_active")
    client = _client(query_job_project_session)

    response = client.post(
        "/api/v1/query-jobs/load",
        json=_payload(project_id="proj_active"),
        headers={
            "Authorization": f"Bearer {_token()}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert response.status_code == 200
    assert response.json()["inserted_rows"] == 2
    rows = query_job_project_session.execute(
        text(
            """
            SELECT DISTINCT tenant_key, job_id, project_id
            FROM llm_query_jobs
            WHERE tenant_key = 'tn_allowed' AND job_id = 'job_project_link'
            """
        )
    ).mappings().all()
    assert [dict(row) for row in rows] == [
        {
            "tenant_key": "tn_allowed",
            "job_id": "job_project_link",
            "project_id": "proj_active",
        }
    ]


def test_load_query_jobs_rejects_project_outside_current_tenant(
    query_job_project_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed_admin_and_project(query_job_project_session, project_id="proj_active")
    client = _client(query_job_project_session)

    response = client.post(
        "/api/v1/query-jobs/load",
        json=_payload(project_id="proj_missing"),
        headers={
            "Authorization": f"Bearer {_token()}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert response.status_code == 404
    assert "项目不存在" in response.json()["detail"]


def test_status_query_still_reads_project_linked_jobs_by_job_id(
    query_job_project_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed_admin_and_project(query_job_project_session, project_id="proj_active")
    client = _client(query_job_project_session)

    load_response = client.post(
        "/api/v1/query-jobs/load",
        json=_payload(project_id="proj_active", job_id="job_dashboard_compat"),
        headers={
            "Authorization": f"Bearer {_token()}",
            "X-Tenant-Key": "tn_allowed",
        },
    )
    assert load_response.status_code == 200

    status_response = client.get(
        "/api/v1/query-jobs/status",
        params={"tenant_key": "tn_allowed", "job_id": "job_dashboard_compat"},
        headers={
            "Authorization": f"Bearer {_token()}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert status_response.status_code == 200
    body = status_response.json()
    assert body["count"] == 2
    assert {item["job_id"] for item in body["jobs"]} == {"job_dashboard_compat"}
