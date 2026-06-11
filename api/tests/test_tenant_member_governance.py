from datetime import UTC, datetime

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

TEST_SECRET = "test-secret-with-at-least-32-bytes"


@pytest.fixture
def tenant_member_engine():
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
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    phone_number VARCHAR(50),
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
                CREATE TABLE tenant_role_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id INTEGER NOT NULL,
                    target_user_id INTEGER NOT NULL,
                    actor_user_id INTEGER NOT NULL,
                    actor_scope VARCHAR(20) NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    old_role VARCHAR(50),
                    new_role VARCHAR(50),
                    old_status VARCHAR(20),
                    new_status VARCHAR(20),
                    reason TEXT,
                    created_at TIMESTAMP
                )
                """
            )
        )
    return engine


@pytest.fixture
def db_session(tenant_member_engine):
    connection = tenant_member_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _token(user_id: int) -> str:
    return create_access_token(user_id, TEST_SECRET)


def _insert_user(db_session, *, user_id: int, email: str, status: str = "active"):
    now = datetime.now(UTC)
    db_session.execute(
        text(
            """
            INSERT INTO users (
                id, user_key, email, password_hash, first_name, last_name,
                phone_number, is_verified, status, created_at, updated_at
            ) VALUES (
                :user_id, :user_key, :email, :password_hash, :first_name, NULL,
                :phone_number, 1, :status, :now, :now
            )
            """
        ),
        {
            "user_id": user_id,
            "user_key": f"user_{user_id}",
            "email": email,
            "password_hash": hash_password("User12345"),
            "first_name": email.split("@")[0],
            "phone_number": f"1380000{user_id:04d}",
            "status": status,
            "now": now,
        },
    )
    db_session.flush()
    return user_id


def _insert_tenant(db_session, *, tenant_key: str = "tn_demo"):
    now = datetime.now(UTC)
    result = db_session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
            VALUES (:tenant_key, :tenant_name, 'active', :now, :now)
            """
        ),
        {
            "tenant_key": tenant_key,
            "tenant_name": f"Tenant {tenant_key}",
            "now": now,
        },
    )
    db_session.flush()
    return result.lastrowid


def _insert_membership(
    db_session,
    *,
    user_id: int,
    tenant_id: int,
    role: str,
    status: str = "active",
):
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


def _membership(db_session, *, user_id: int, tenant_id: int):
    return db_session.execute(
        text(
            """
            SELECT role, status
            FROM user_tenants
            WHERE user_id = :user_id AND tenant_id = :tenant_id
            """
        ),
        {"user_id": user_id, "tenant_id": tenant_id},
    ).first()


def _audit_logs(db_session):
    return db_session.execute(
        text(
            """
            SELECT actor_user_id, actor_scope, target_user_id, action,
                   old_role, new_role, old_status, new_status, reason
            FROM tenant_role_audit_logs
            ORDER BY id ASC
            """
        )
    ).fetchall()


def _seed_members(db_session):
    tenant_id = _insert_tenant(db_session)
    admin_id = _insert_user(db_session, user_id=1, email="admin@example.com")
    member_id = _insert_user(db_session, user_id=2, email="member@example.com")
    viewer_id = _insert_user(db_session, user_id=3, email="viewer@example.com")
    _insert_membership(db_session, user_id=admin_id, tenant_id=tenant_id, role="admin")
    _insert_membership(db_session, user_id=member_id, tenant_id=tenant_id, role="member")
    _insert_membership(db_session, user_id=viewer_id, tenant_id=tenant_id, role="viewer")
    return tenant_id, admin_id, member_id, viewer_id


def test_tenant_admin_can_list_members(client, db_session):
    _, admin_id, member_id, viewer_id = _seed_members(db_session)

    response = client.get(
        "/api/v1/tenants/tn_demo/members",
        headers={"Authorization": f"Bearer {_token(admin_id)}"},
    )

    assert response.status_code == 200
    members = response.json()["data"]["members"]
    assert [member["userId"] for member in members] == [admin_id, member_id, viewer_id]
    assert members[0]["email"] == "admin@example.com"
    assert members[0]["role"] == "admin"
    assert members[1]["role"] == "member"


def test_platform_admin_can_list_tenant_members_without_membership(
    client,
    db_session,
    monkeypatch,
):
    _, admin_id, member_id, viewer_id = _seed_members(db_session)
    platform_id = _insert_user(db_session, user_id=9, email="ops@example.com")
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")

    response = client.get(
        "/api/v1/platform/tenants/tn_demo/members",
        headers={"Authorization": f"Bearer {_token(platform_id)}"},
    )

    assert response.status_code == 200
    members = response.json()["data"]["members"]
    assert [member["userId"] for member in members] == [admin_id, member_id, viewer_id]
    assert members[0]["email"] == "admin@example.com"
    assert members[1]["role"] == "member"
    assert members[2]["role"] == "viewer"


def test_non_platform_user_cannot_list_platform_tenant_members(client, db_session):
    _, _, member_id, _ = _seed_members(db_session)

    response = client.get(
        "/api/v1/platform/tenants/tn_demo/members",
        headers={"Authorization": f"Bearer {_token(member_id)}"},
    )

    assert response.status_code == 403


def test_tenant_admin_updates_member_role_and_writes_audit(client, db_session):
    tenant_id, admin_id, member_id, _ = _seed_members(db_session)

    response = client.patch(
        f"/api/v1/tenants/tn_demo/members/{member_id}",
        json={"role": "viewer", "reason": "scope cleanup"},
        headers={"Authorization": f"Bearer {_token(admin_id)}"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["member"]["role"] == "viewer"
    assert tuple(_membership(db_session, user_id=member_id, tenant_id=tenant_id)) == (
        "viewer",
        "active",
    )
    logs = _audit_logs(db_session)
    assert len(logs) == 1
    assert logs[0]._mapping["actor_user_id"] == admin_id
    assert logs[0]._mapping["actor_scope"] == "tenant"
    assert logs[0]._mapping["target_user_id"] == member_id
    assert logs[0]._mapping["action"] == "role_updated"
    assert logs[0]._mapping["old_role"] == "member"
    assert logs[0]._mapping["new_role"] == "viewer"
    assert logs[0]._mapping["reason"] == "scope cleanup"


def test_non_admin_cannot_manage_tenant_members(client, db_session):
    _, _, member_id, viewer_id = _seed_members(db_session)

    response = client.patch(
        f"/api/v1/tenants/tn_demo/members/{viewer_id}",
        json={"role": "member"},
        headers={"Authorization": f"Bearer {_token(member_id)}"},
    )

    assert response.status_code == 403


def test_platform_admin_emergency_update_requires_reason(client, db_session, monkeypatch):
    _, _, member_id, _ = _seed_members(db_session)
    platform_id = _insert_user(db_session, user_id=9, email="ops@example.com")
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")

    response = client.patch(
        f"/api/v1/platform/tenants/tn_demo/members/{member_id}",
        json={"role": "viewer"},
        headers={"Authorization": f"Bearer {_token(platform_id)}"},
    )

    assert response.status_code == 400
    assert _audit_logs(db_session) == []


def test_platform_admin_can_update_member_role_with_audit(client, db_session, monkeypatch):
    tenant_id, _, member_id, _ = _seed_members(db_session)
    platform_id = _insert_user(db_session, user_id=9, email="ops@example.com")
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")

    response = client.patch(
        f"/api/v1/platform/tenants/tn_demo/members/{member_id}",
        json={"role": "viewer", "reason": "customer support ticket CS-123"},
        headers={"Authorization": f"Bearer {_token(platform_id)}"},
    )

    assert response.status_code == 200
    assert tuple(_membership(db_session, user_id=member_id, tenant_id=tenant_id)) == (
        "viewer",
        "active",
    )
    logs = _audit_logs(db_session)
    assert len(logs) == 1
    assert logs[0]._mapping["actor_user_id"] == platform_id
    assert logs[0]._mapping["actor_scope"] == "platform"
    assert logs[0]._mapping["target_user_id"] == member_id
    assert logs[0]._mapping["old_role"] == "member"
    assert logs[0]._mapping["new_role"] == "viewer"
    assert logs[0]._mapping["reason"] == "customer support ticket CS-123"


@pytest.mark.parametrize(
    "payload",
    [
        {"role": "member", "reason": "cannot remove final admin"},
        {"status": "inactive", "reason": "cannot disable final admin"},
    ],
)
def test_cannot_remove_last_active_admin(client, db_session, payload):
    tenant_id = _insert_tenant(db_session)
    admin_id = _insert_user(db_session, user_id=1, email="admin@example.com")
    _insert_membership(db_session, user_id=admin_id, tenant_id=tenant_id, role="admin")

    response = client.patch(
        f"/api/v1/tenants/tn_demo/members/{admin_id}",
        json=payload,
        headers={"Authorization": f"Bearer {_token(admin_id)}"},
    )

    assert response.status_code == 400
    assert tuple(_membership(db_session, user_id=admin_id, tenant_id=tenant_id)) == (
        "admin",
        "active",
    )
    assert _audit_logs(db_session) == []
