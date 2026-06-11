from datetime import UTC, datetime

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import projects as projects_routes
from api.v1.utils.jwt_utils import create_access_token
from api.v1.utils.security import hash_password
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

TEST_SECRET = "test-secret-with-at-least-32-bytes"


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE tenants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_key VARCHAR(255) NOT NULL UNIQUE,
                tenant_name VARCHAR(255) NOT NULL UNIQUE,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP, updated_at TIMESTAMP
            )"""))
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_key VARCHAR(36) NOT NULL UNIQUE,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                is_verified BOOLEAN NOT NULL DEFAULT 1,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP, updated_at TIMESTAMP
            )"""))
        conn.execute(text("""
            CREATE TABLE user_tenants (
                user_id INTEGER NOT NULL, tenant_id INTEGER NOT NULL,
                role VARCHAR(50) NOT NULL DEFAULT 'admin',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP, PRIMARY KEY (user_id, tenant_id)
            )"""))
        conn.execute(text("""
            CREATE TABLE monitoring_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_key VARCHAR(255) NOT NULL, project_id VARCHAR(128) NOT NULL,
                name VARCHAR(255) NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
                UNIQUE (tenant_key, project_id)
            )"""))
        conn.execute(text("""
            CREATE TABLE project_brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_key VARCHAR(255) NOT NULL, project_id VARCHAR(128) NOT NULL,
                brand_id VARCHAR(128) NOT NULL, brand_name VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'competitor',
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL
            )"""))
        conn.execute(text("""
            CREATE TABLE collection_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_key VARCHAR(255) NOT NULL, collection_job_id VARCHAR(128) NOT NULL,
                project_id VARCHAR(128) NOT NULL, source_job_id VARCHAR(255),
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                window_start TIMESTAMP, window_end TIMESTAMP,
                expected_task_count INTEGER NOT NULL DEFAULT 0,
                succeeded_task_count INTEGER NOT NULL DEFAULT 0,
                failed_task_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
                UNIQUE (tenant_key, collection_job_id)
            )"""))
    connection = engine.connect()
    transaction = connection.begin()
    db = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield db
    db.close()
    transaction.rollback()
    connection.close()


def _client(db):
    app = FastAPI()
    app.include_router(projects_routes.router, prefix="/api/v1/projects")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def _token(user_id=101):
    return create_access_token(user_id, TEST_SECRET)


def _seed(db):
    now = datetime.now(UTC)
    t = db.execute(text(
        "INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)"
        " VALUES ('tn_a', 'A', 'active', :now, :now)"), {"now": now})
    db.execute(text(
        "INSERT INTO users (id, user_key, email, password_hash,"
        " is_verified, status, created_at, updated_at)"
        " VALUES (101, 'u101', 'a@x.com', :ph, 1, 'active', :now, :now)"),
        {"ph": hash_password("User12345"), "now": now})
    db.execute(text(
        "INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)"
        " VALUES (101, :tid, 'admin', 'active', :now)"), {"tid": t.lastrowid, "now": now})
    for pid in ("prj_1", "prj_2"):
        db.execute(text(
            "INSERT INTO monitoring_projects (tenant_key, project_id, name,"
            " status, created_at, updated_at)"
            " VALUES ('tn_a', :pid, 'P', 'active', :now, :now)"), {"pid": pid, "now": now})
    db.execute(text(
        "INSERT INTO project_brands (tenant_key, project_id, brand_id,"
        " brand_name, role, status, created_at, updated_at)"
        " VALUES ('tn_a', 'prj_1', 'b1', 'QuickCEP', 'target', 'active', :now, :now)"),
        {"now": now})
    db.execute(text(
        "INSERT INTO project_brands (tenant_key, project_id, brand_id,"
        " brand_name, role, status, created_at, updated_at)"
        " VALUES ('tn_a', 'prj_1', 'b2', 'CompetitorX', 'competitor', 'active', :now, :now)"),
        {"now": now})
    db.commit()


def _insert_cj(db, *, cj_id, project_id, source_job_id, window_start, status="succeeded"):
    now = datetime.now(UTC)
    db.execute(text(
        "INSERT INTO collection_jobs (tenant_key, collection_job_id, project_id, source_job_id,"
        " status, window_start, window_end, expected_task_count, succeeded_task_count,"
        " failed_task_count, created_at, updated_at)"
        " VALUES ('tn_a', :cj, :pid, :sj, :st, :ws, NULL, 12, 12, 0, :now, :now)"),
        {"cj": cj_id, "pid": project_id, "sj": source_job_id, "st": status,
         "ws": window_start, "now": now})
    db.commit()


def test_lists_only_source_job_id_jobs_for_project_with_target_brand(session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed(session)
    _insert_cj(
        session, cj_id="col_1", project_id="prj_1",
        source_job_id="job_legacy_1", window_start="2026-02-09")
    _insert_cj(
        session, cj_id="col_2", project_id="prj_1",
        source_job_id=None, window_start="2026-02-10")
    _insert_cj(
        session, cj_id="col_other", project_id="prj_2",
        source_job_id="job_legacy_2", window_start="2026-02-11")

    client = _client(session)
    resp = client.get(
        "/api/v1/projects/prj_1/collection-jobs",
        headers={"Authorization": f"Bearer {_token()}", "X-Tenant-Key": "tn_a"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["target_brand"] == "QuickCEP"
    jobs = body["collection_jobs"]
    assert {j["collection_job_id"] for j in jobs} == {"col_1"}
    assert jobs[0]["source_job_id"] == "job_legacy_1"
    assert jobs[0]["status"] == "succeeded"


def test_orders_by_window_start_desc(session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed(session)
    _insert_cj(
        session, cj_id="col_old", project_id="prj_1",
        source_job_id="job_old", window_start="2026-01-01")
    _insert_cj(
        session, cj_id="col_new", project_id="prj_1",
        source_job_id="job_new", window_start="2026-03-01")

    client = _client(session)
    resp = client.get(
        "/api/v1/projects/prj_1/collection-jobs",
        headers={"Authorization": f"Bearer {_token()}", "X-Tenant-Key": "tn_a"},
    )
    assert [j["collection_job_id"] for j in resp.json()["collection_jobs"]] == [
        "col_new", "col_old"]


def test_target_brand_null_when_absent(session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed(session)
    _insert_cj(
        session, cj_id="col_2only", project_id="prj_2",
        source_job_id="job_p2", window_start="2026-02-09")

    client = _client(session)
    resp = client.get(
        "/api/v1/projects/prj_2/collection-jobs",
        headers={"Authorization": f"Bearer {_token()}", "X-Tenant-Key": "tn_a"},
    )
    assert resp.status_code == 200
    assert resp.json()["target_brand"] is None


def test_requires_authenticated_tenant_member(session):
    _seed(session)
    client = _client(session)
    resp = client.get(
        "/api/v1/projects/prj_1/collection-jobs",
        headers={"X-Tenant-Key": "tn_a"},
    )
    assert resp.status_code == 401
