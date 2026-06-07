from datetime import UTC, datetime

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

TEST_SECRET = "test-secret-with-at-least-32-bytes"


@pytest.fixture()
def project_db_session():
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
                    status VARCHAR(20) NOT NULL DEFAULT 'draft',
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
                CREATE TABLE project_brands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL,
                    project_id VARCHAR(128) NOT NULL,
                    brand_id VARCHAR(128) NOT NULL,
                    brand_name VARCHAR(255) NOT NULL,
                    role VARCHAR(20) NOT NULL DEFAULT 'competitor',
                    aliases TEXT,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    UNIQUE (tenant_key, project_id, brand_id, role),
                    FOREIGN KEY (tenant_key, project_id)
                        REFERENCES monitoring_projects(tenant_key, project_id) ON DELETE CASCADE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE prompt_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL,
                    project_id VARCHAR(128) NOT NULL,
                    prompt_set_id VARCHAR(128) NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    name VARCHAR(255),
                    status VARCHAR(20) NOT NULL DEFAULT 'draft',
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    UNIQUE (tenant_key, prompt_set_id),
                    UNIQUE (tenant_key, project_id, version),
                    FOREIGN KEY (tenant_key, project_id)
                        REFERENCES monitoring_projects(tenant_key, project_id) ON DELETE CASCADE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE prompt_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL,
                    prompt_set_id VARCHAR(128) NOT NULL,
                    prompt_item_id VARCHAR(128) NOT NULL,
                    keyword VARCHAR(100) NOT NULL,
                    query_content TEXT NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    UNIQUE (tenant_key, prompt_set_id, prompt_item_id),
                    FOREIGN KEY (tenant_key, prompt_set_id)
                        REFERENCES prompt_sets(tenant_key, prompt_set_id) ON DELETE CASCADE
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
    app.include_router(projects.router, prefix="/api/v1/projects")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _token(user_id=101):
    return create_access_token(user_id, TEST_SECRET)


def _insert_tenant(
    db_session,
    *,
    tenant_key,
    tenant_name,
):
    now = datetime.now(UTC)
    result = db_session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, industry, status, created_at, updated_at)
            VALUES (:tenant_key, :tenant_name, 'technology', 'active', :now, :now)
            """
        ),
        {"tenant_key": tenant_key, "tenant_name": tenant_name, "now": now},
    )
    db_session.flush()
    return result.lastrowid


def _insert_user_tenant(db_session, *, role="member", user_id=101):
    tenant_id = _insert_tenant(
        db_session,
        tenant_key="tn_allowed",
        tenant_name="Allowed Tenant",
    )
    _insert_tenant(
        db_session,
        tenant_key="tn_other",
        tenant_name="Other Tenant",
    )
    now = datetime.now(UTC)
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
            "email": "member@example.com",
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
        {"user_id": user_id, "tenant_id": tenant_id, "role": role, "now": now},
    )
    db_session.flush()
    return user_id


def _insert_project(db_session, *, tenant_key="tn_allowed", project_id="proj_1"):
    now = datetime.now(UTC)
    db_session.execute(
        text(
            """
            INSERT INTO monitoring_projects (
                tenant_key, project_id, name, industry, category, status,
                created_by, created_at, updated_at
            )
            VALUES (
                :tenant_key, :project_id, :name, 'auto', 'ev', 'active',
                101, :now, :now
            )
            """
        ),
        {
            "tenant_key": tenant_key,
            "project_id": project_id,
            "name": f"Project {project_id}",
            "now": now,
        },
    )
    db_session.flush()


def test_project_list_requires_authentication(project_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _insert_user_tenant(project_db_session)
    client = _client(project_db_session)

    response = client.get("/api/v1/projects", headers={"X-Tenant-Key": "tn_allowed"})

    assert response.status_code == 401


def test_project_list_returns_only_current_tenant_projects(project_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user_tenant(project_db_session)
    _insert_project(project_db_session, tenant_key="tn_allowed", project_id="proj_allowed")
    _insert_project(project_db_session, tenant_key="tn_other", project_id="proj_other")
    client = _client(project_db_session)

    response = client.get(
        "/api/v1/projects",
        headers={
            "Authorization": f"Bearer {_token(user_id)}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["count"] == 1
    assert body["projects"][0]["project_id"] == "proj_allowed"
    assert body["projects"][0]["tenant_key"] == "tn_allowed"


def test_create_project_requires_tenant_admin(project_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user_tenant(project_db_session, role="member")
    client = _client(project_db_session)

    response = client.post(
        "/api/v1/projects",
        json={"project_id": "proj_new", "name": "New Project", "category": "ev"},
        headers={
            "Authorization": f"Bearer {_token(user_id)}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert response.status_code == 403


def test_create_project_rejects_body_tenant_key(project_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user_tenant(project_db_session, role="admin")
    client = _client(project_db_session)

    response = client.post(
        "/api/v1/projects",
        json={
            "tenant_key": "tn_other",
            "project_id": "proj_new",
            "name": "New Project",
            "category": "ev",
        },
        headers={
            "Authorization": f"Bearer {_token(user_id)}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert response.status_code == 422


def test_create_project_uses_server_tenant_context(project_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user_tenant(project_db_session, role="admin")
    client = _client(project_db_session)

    response = client.post(
        "/api/v1/projects",
        json={
            "project_id": "proj_new",
            "name": "New Project",
            "industry": "auto",
            "category": "ev",
        },
        headers={
            "Authorization": f"Bearer {_token(user_id)}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["project"]["tenant_key"] == "tn_allowed"
    assert body["project"]["project_id"] == "proj_new"


def test_project_detail_includes_brand_and_prompt_set_config(project_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user_tenant(project_db_session)
    _insert_project(project_db_session, project_id="proj_detail")
    now = datetime.now(UTC)
    project_db_session.execute(
        text(
            """
            INSERT INTO project_brands (
                tenant_key, project_id, brand_id, brand_name, role, aliases, status,
                created_at, updated_at
            )
            VALUES (
                'tn_allowed', 'proj_detail', 'brand_target', 'Target Brand', 'target',
                '["TB"]', 'active', :now, :now
            )
            """
        ),
        {"now": now},
    )
    project_db_session.execute(
        text(
            """
            INSERT INTO prompt_sets (
                tenant_key, project_id, prompt_set_id, version, name, status,
                created_at, updated_at
            )
            VALUES (
                'tn_allowed', 'proj_detail', 'ps_1', 1, 'Default Set', 'active',
                :now, :now
            )
            """
        ),
        {"now": now},
    )
    project_db_session.execute(
        text(
            """
            INSERT INTO prompt_items (
                tenant_key, prompt_set_id, prompt_item_id, keyword, query_content,
                status, sort_order, created_at, updated_at
            )
            VALUES (
                'tn_allowed', 'ps_1', 'pi_1', 'battery',
                'Which EV brand has the best battery?', 'active', 10, :now, :now
            )
            """
        ),
        {"now": now},
    )
    client = _client(project_db_session)

    response = client.get(
        "/api/v1/projects/proj_detail",
        headers={
            "Authorization": f"Bearer {_token(user_id)}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert response.status_code == 200
    project = response.json()["project"]
    assert project["project_id"] == "proj_detail"
    assert project["brands"][0]["brand_id"] == "brand_target"
    assert project["brands"][0]["aliases"] == ["TB"]
    assert project["prompt_sets"][0]["prompt_set_id"] == "ps_1"
    assert project["prompt_sets"][0]["items"][0]["prompt_item_id"] == "pi_1"


def test_configure_project_brand_requires_admin_and_upserts(project_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user_tenant(project_db_session, role="admin")
    _insert_project(project_db_session, project_id="proj_brand")
    client = _client(project_db_session)

    response = client.post(
        "/api/v1/projects/proj_brand/brands",
        json={
            "brand_id": "brand_target",
            "brand_name": "Target Brand",
            "role": "target",
            "aliases": ["TB", "Target"],
        },
        headers={
            "Authorization": f"Bearer {_token(user_id)}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["brand"]["aliases"] == ["TB", "Target"]

    update_response = client.post(
        "/api/v1/projects/proj_brand/brands",
        json={
            "brand_id": "brand_target",
            "brand_name": "Target Brand Updated",
            "role": "target",
            "aliases": ["TBU"],
        },
        headers={
            "Authorization": f"Bearer {_token(user_id)}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["brand"]["brand_name"] == "Target Brand Updated"
    count = project_db_session.execute(text("SELECT COUNT(*) FROM project_brands")).scalar_one()
    assert count == 1


def test_create_prompt_set_with_items(project_db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    user_id = _insert_user_tenant(project_db_session, role="admin")
    _insert_project(project_db_session, project_id="proj_prompt")
    client = _client(project_db_session)

    response = client.post(
        "/api/v1/projects/proj_prompt/prompt-sets",
        json={
            "prompt_set_id": "ps_1",
            "version": 1,
            "name": "Launch Questions",
            "status": "active",
            "items": [
                {
                    "prompt_item_id": "pi_1",
                    "keyword": "battery",
                    "query_content": "Which EV brand has the best battery?",
                    "sort_order": 10,
                }
            ],
        },
        headers={
            "Authorization": f"Bearer {_token(user_id)}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert response.status_code == 200
    prompt_set = response.json()["prompt_set"]
    assert prompt_set["prompt_set_id"] == "ps_1"
    assert prompt_set["items"][0]["prompt_item_id"] == "pi_1"
