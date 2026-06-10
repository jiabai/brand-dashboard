from datetime import UTC, datetime, timedelta

import pytest
from api.v1.repositories import auth as auth_repository
from api.v1.utils.security import verify_token
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def memory_engine(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    monkeypatch.setenv("AUTH_BASE_URL", "https://example.com")
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
                    subdomain VARCHAR(100),
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


def _seed_tenant(engine, *, tenant_key="tn_demo", subdomain=None):
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO tenants (tenant_key, tenant_name, subdomain, created_at, updated_at)
                VALUES (:tenant_key, :tenant_name, :subdomain, :now, :now)
                """
            ),
            {
                "tenant_key": tenant_key,
                "tenant_name": f"企业{tenant_key}",
                "subdomain": subdomain,
                "now": now,
            },
        )
        return conn.execute(
            text("SELECT id FROM tenants WHERE tenant_key = :tenant_key"),
            {"tenant_key": tenant_key},
        ).fetchone()[0]


def _seed_admin(
    engine,
    tenant_id,
    *,
    email,
    user_status="pending_activation",
    membership_created_at=None,
):
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO users (
                    user_key, email, password_hash, is_verified, status, created_at, updated_at
                ) VALUES (:user_key, :email, 'x', 0, :status, :now, :now)
                """
            ),
            {
                "user_key": f"uk_{email}",
                "email": email,
                "status": user_status,
                "now": now,
            },
        )
        user_id = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()[0]
        conn.execute(
            text(
                """
                INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
                VALUES (:user_id, :tenant_id, 'admin', 'active', :created_at)
                """
            ),
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "created_at": membership_created_at or now,
            },
        )
    return user_id


def test_regenerate_returns_new_activation_payload(memory_engine):
    tenant_id = _seed_tenant(memory_engine)
    user_id = _seed_admin(memory_engine, tenant_id, email="admin@demo.test")

    result = auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")

    assert result["tenantKey"] == "tn_demo"
    assert result["tenantName"] == "企业tn_demo"
    assert result["adminEmail"] == "admin@demo.test"
    assert result["activationUrl"].startswith("https://example.com/activate?token=")
    assert result["loginUrl"] == "https://example.com/login"

    payload = verify_token(
        result["activationToken"], "test-secret-with-at-least-32-bytes"
    )
    assert payload["type"] == "activation"
    assert payload["user_id"] == user_id
    assert payload["tenant_key"] == "tn_demo"
    assert payload["email"] == "admin@demo.test"
    expected_exp = (datetime.now(UTC) + timedelta(days=7)).timestamp()
    assert abs(payload["exp"] - expected_exp) < 60


def test_regenerate_targets_earliest_admin(memory_engine):
    tenant_id = _seed_tenant(memory_engine)
    early = datetime(2026, 1, 1, tzinfo=UTC)
    late = datetime(2026, 5, 1, tzinfo=UTC)
    _seed_admin(
        memory_engine,
        tenant_id,
        email="late-admin@demo.test",
        membership_created_at=late,
    )
    _seed_admin(
        memory_engine,
        tenant_id,
        email="first-admin@demo.test",
        membership_created_at=early,
    )

    result = auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")

    assert result["adminEmail"] == "first-admin@demo.test"


def test_regenerate_rejects_unknown_tenant(memory_engine):
    with pytest.raises(LookupError, match="租户不存在"):
        auth_repository.regenerate_admin_activation(memory_engine, "tn_missing")


def test_regenerate_rejects_tenant_without_admin(memory_engine):
    _seed_tenant(memory_engine)
    with pytest.raises(ValueError, match="该租户未设置管理员"):
        auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")


def test_regenerate_rejects_active_admin(memory_engine):
    tenant_id = _seed_tenant(memory_engine)
    _seed_admin(memory_engine, tenant_id, email="admin@demo.test", user_status="active")
    with pytest.raises(ValueError, match="账号已激活"):
        auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")


def test_regenerate_rejects_abnormal_admin(memory_engine):
    tenant_id = _seed_tenant(memory_engine)
    _seed_admin(
        memory_engine, tenant_id, email="admin@demo.test", user_status="suspended"
    )
    with pytest.raises(ValueError, match="账号状态异常"):
        auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")
