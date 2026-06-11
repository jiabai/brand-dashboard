from datetime import UTC, datetime

import pytest
from api.v1.repositories.tenant_access import (
    TenantAccessGrantError,
    grant_tenant_access,
)
from api.v1.repositories.tenants import get_user_tenant_membership
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture
def tenant_access_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
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


def _insert_user(engine, *, email="ops@example.com", status="active"):
    now = datetime.now(UTC)
    with engine.begin() as conn:
        result = conn.execute(
            text(
            """
            INSERT INTO users (
                user_key, email, password_hash, first_name, phone_number,
                is_verified, status, created_at, updated_at
            ) VALUES (
                :user_key, :email, 'hash', :first_name, :phone_number,
                1, :status, :now, :now
            )
            """
        ),
        {
            "user_key": f"user_{email}",
            "email": email,
            "first_name": email.split("@")[0],
            "phone_number": "13800000000",
            "status": status,
            "now": now,
        },
        )
    return result.lastrowid


def _insert_tenant(engine, *, tenant_key="tn_demo", status="active"):
    now = datetime.now(UTC)
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
                VALUES (:tenant_key, :tenant_name, :status, :now, :now)
                """
            ),
            {
                "tenant_key": tenant_key,
                "tenant_name": f"Tenant {tenant_key}",
                "status": status,
                "now": now,
            },
        )
    return result.lastrowid


def _insert_membership(engine, *, user_id, tenant_id, role="viewer", status="active"):
    with engine.begin() as conn:
        conn.execute(
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


def _membership_row(engine, *, user_id, tenant_id):
    with engine.connect() as conn:
        return conn.execute(
            text(
                """
                SELECT role, status
                FROM user_tenants
                WHERE user_id = :user_id AND tenant_id = :tenant_id
                """
            ),
            {"user_id": user_id, "tenant_id": tenant_id},
        ).first()


def _audit_rows(engine):
    with engine.connect() as conn:
        return conn.execute(
            text(
                """
                SELECT actor_user_id, actor_scope, target_user_id, action,
                       old_role, new_role, old_status, new_status, reason
                FROM tenant_role_audit_logs
                ORDER BY id ASC
                """
            )
        ).fetchall()


def test_grant_tenant_access_creates_viewer_membership(tenant_access_engine):
    user_id = _insert_user(tenant_access_engine, email="Ops@Example.com")
    tenant_id = _insert_tenant(tenant_access_engine, tenant_key="tn_demo")

    result = grant_tenant_access(
        tenant_access_engine,
        email="OPS@example.com",
        tenant_key="tn_demo",
    )

    assert result == {
        "action": "created",
        "email": "ops@example.com",
        "tenant_key": "tn_demo",
        "role": "viewer",
    }
    assert tuple(_membership_row(tenant_access_engine, user_id=user_id, tenant_id=tenant_id)) == (
        "viewer",
        "active",
    )
    with Session(tenant_access_engine) as db:
        membership = get_user_tenant_membership(db, user_id=user_id, tenant_key="tn_demo")
    assert membership.role == "viewer"
    assert membership.member_status == "active"


def test_grant_tenant_access_is_idempotent_for_existing_membership(tenant_access_engine):
    user_id = _insert_user(tenant_access_engine)
    tenant_id = _insert_tenant(tenant_access_engine)
    _insert_membership(tenant_access_engine, user_id=user_id, tenant_id=tenant_id, role="viewer")

    result = grant_tenant_access(
        tenant_access_engine,
        email="ops@example.com",
        tenant_key="tn_demo",
        role="viewer",
    )

    assert result["action"] == "exists"
    assert tuple(_membership_row(tenant_access_engine, user_id=user_id, tenant_id=tenant_id)) == (
        "viewer",
        "active",
    )


def test_grant_tenant_access_updates_existing_role(tenant_access_engine):
    user_id = _insert_user(tenant_access_engine)
    tenant_id = _insert_tenant(tenant_access_engine)
    _insert_membership(tenant_access_engine, user_id=user_id, tenant_id=tenant_id, role="member")

    result = grant_tenant_access(
        tenant_access_engine,
        email="ops@example.com",
        tenant_key="tn_demo",
        role="admin",
    )

    assert result["action"] == "updated"
    assert tuple(_membership_row(tenant_access_engine, user_id=user_id, tenant_id=tenant_id)) == (
        "admin",
        "active",
    )
    audit_rows = _audit_rows(tenant_access_engine)
    assert len(audit_rows) == 1
    assert audit_rows[0]._mapping["actor_user_id"] == user_id
    assert audit_rows[0]._mapping["actor_scope"] == "platform"
    assert audit_rows[0]._mapping["target_user_id"] == user_id
    assert audit_rows[0]._mapping["old_role"] == "member"
    assert audit_rows[0]._mapping["new_role"] == "admin"


def test_grant_tenant_access_reactivates_disabled_membership(tenant_access_engine):
    user_id = _insert_user(tenant_access_engine)
    tenant_id = _insert_tenant(tenant_access_engine)
    _insert_membership(
        tenant_access_engine,
        user_id=user_id,
        tenant_id=tenant_id,
        role="member",
        status="inactive",
    )

    result = grant_tenant_access(
        tenant_access_engine,
        email="ops@example.com",
        tenant_key="tn_demo",
        role="viewer",
    )

    assert result["action"] == "reactivated"
    assert tuple(_membership_row(tenant_access_engine, user_id=user_id, tenant_id=tenant_id)) == (
        "viewer",
        "active",
    )
    assert len(_audit_rows(tenant_access_engine)) == 1


def test_grant_tenant_access_rejects_demoting_last_active_admin(tenant_access_engine):
    user_id = _insert_user(tenant_access_engine)
    tenant_id = _insert_tenant(tenant_access_engine)
    _insert_membership(tenant_access_engine, user_id=user_id, tenant_id=tenant_id, role="admin")

    with pytest.raises(TenantAccessGrantError, match="active admin"):
        grant_tenant_access(
            tenant_access_engine,
            email="ops@example.com",
            tenant_key="tn_demo",
            role="viewer",
        )

    assert tuple(_membership_row(tenant_access_engine, user_id=user_id, tenant_id=tenant_id)) == (
        "admin",
        "active",
    )
    assert _audit_rows(tenant_access_engine) == []


def test_grant_tenant_access_rejects_invalid_role(tenant_access_engine):
    with pytest.raises(TenantAccessGrantError, match="角色无效"):
        grant_tenant_access(
            tenant_access_engine,
            email="ops@example.com",
            tenant_key="tn_demo",
            role="owner",
        )


def test_grant_tenant_access_rejects_unknown_user(tenant_access_engine):
    _insert_tenant(tenant_access_engine)

    with pytest.raises(TenantAccessGrantError, match="用户不存在"):
        grant_tenant_access(
            tenant_access_engine,
            email="missing@example.com",
            tenant_key="tn_demo",
        )


def test_grant_tenant_access_rejects_unknown_tenant(tenant_access_engine):
    _insert_user(tenant_access_engine)

    with pytest.raises(TenantAccessGrantError, match="租户不存在"):
        grant_tenant_access(
            tenant_access_engine,
            email="ops@example.com",
            tenant_key="tn_missing",
        )


@pytest.mark.parametrize(
    ("user_status", "tenant_status", "message"),
    [
        ("inactive", "active", "账号状态不可授权"),
        ("active", "inactive", "租户状态不可授权"),
    ],
)
def test_grant_tenant_access_rejects_inactive_user_or_tenant(
    tenant_access_engine,
    user_status,
    tenant_status,
    message,
):
    _insert_user(tenant_access_engine, status=user_status)
    _insert_tenant(tenant_access_engine, status=tenant_status)

    with pytest.raises(TenantAccessGrantError, match=message):
        grant_tenant_access(
            tenant_access_engine,
            email="ops@example.com",
            tenant_key="tn_demo",
        )
