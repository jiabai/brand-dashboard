from datetime import UTC, datetime

import pytest
from api.v1.repositories.connection import get_db
from api.v1.utils.security import hash_password
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def auth_db_engine():
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
def db_session(auth_db_engine):
    connection = auth_db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _insert_user_tenant(
    db_session,
    *,
    tenant_key="tn_allowed",
    tenant_name="允许访问租户",
    tenant_status="active",
    user_id=101,
    email="member@example.com",
    user_status="active",
    role="member",
    member_status="active",
):
    now = datetime.now(UTC)
    tenant_result = db_session.execute(
        text(
            """
            INSERT INTO tenants (
                tenant_key, tenant_name, industry, status, created_at, updated_at
            ) VALUES (
                :tenant_key, :tenant_name, :industry, :status, :now, :now
            )
            """
        ),
        {
            "tenant_key": tenant_key,
            "tenant_name": tenant_name,
            "industry": "互联网",
            "status": tenant_status,
            "now": now,
        },
    )
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
            "status": user_status,
            "now": now,
        },
    )
    db_session.execute(
        text(
            """
            INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
            VALUES (:user_id, :tenant_id, :role, :member_status, :now)
            """
        ),
        {
            "user_id": user_id,
            "tenant_id": tenant_result.lastrowid,
            "role": role,
            "member_status": member_status,
            "now": now,
        },
    )
    db_session.flush()
    return user_id


def _build_probe_client(db_session):
    from api.v1.dependencies.auth import get_current_tenant

    app = FastAPI()

    @app.get("/probe")
    def probe(tenant=Depends(get_current_tenant)):
        return {"tenantKey": tenant.tenant_key, "role": tenant.role}

    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _access_token(user_id):
    from api.v1.utils.jwt_utils import create_access_token

    return create_access_token(user_id, "test-secret-with-at-least-32-bytes")


def test_current_tenant_accepts_authorized_member(db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    user_id = _insert_user_tenant(db_session)
    client = _build_probe_client(db_session)

    response = client.get(
        "/probe",
        headers={
            "Authorization": f"Bearer {_access_token(user_id)}",
            "X-Tenant-Key": "tn_allowed",
        },
    )

    assert response.status_code == 200
    assert response.json() == {"tenantKey": "tn_allowed", "role": "member"}


def test_current_tenant_rejects_missing_authorization(db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    _insert_user_tenant(db_session)
    client = _build_probe_client(db_session)

    response = client.get("/probe", headers={"X-Tenant-Key": "tn_allowed"})

    assert response.status_code == 401


def test_current_tenant_rejects_cross_tenant_access(db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    user_id = _insert_user_tenant(db_session)
    db_session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, industry, status)
            VALUES ('tn_other', '其他租户', '互联网', 'active')
            """
        )
    )
    db_session.flush()
    client = _build_probe_client(db_session)

    response = client.get(
        "/probe",
        headers={
            "Authorization": f"Bearer {_access_token(user_id)}",
            "X-Tenant-Key": "tn_other",
        },
    )

    assert response.status_code == 403


def test_auth_me_returns_current_user_and_tenants(db_session, monkeypatch):
    from api.v1.routes import auth

    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    user_id = _insert_user_tenant(
        db_session,
        role="admin",
        email="admin@example.com",
    )
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {_access_token(user_id)}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["user"]["email"] == "admin@example.com"
    assert body["data"]["user"]["tenants"][0]["role"] == "tenant_admin"
