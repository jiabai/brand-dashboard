from datetime import UTC, datetime
from pathlib import Path

import pytest
from api.v1.repositories.auth import authenticate_user
from api.v1.repositories.platform_admins import (
    PlatformAdminBootstrapError,
    ensure_platform_admin_user,
    merge_platform_admin_email,
    update_platform_admin_env_file,
)
from api.v1.utils.security import hash_password, verify_password
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def bootstrap_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _create_bootstrap_schema(engine)
    return engine


def _create_bootstrap_schema(engine):
    with engine.begin() as conn:
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
                CREATE TABLE tenants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL UNIQUE,
                    tenant_name VARCHAR(255) NOT NULL UNIQUE
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


@pytest.fixture
def db_session(bootstrap_engine):
    connection = bootstrap_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _insert_user(db_session, *, email, password="OldPassword123", status="active"):
    now = datetime.now(UTC)
    result = db_session.execute(
        text(
            """
            INSERT INTO users (
                user_key, email, password_hash, is_verified, status, created_at, updated_at
            ) VALUES (
                :user_key, :email, :password_hash, :is_verified, :status, :now, :now
            )
            """
        ),
        {
            "user_key": f"user_{email}",
            "email": email,
            "password_hash": hash_password(password),
            "is_verified": status == "active",
            "status": status,
            "now": now,
        },
    )
    db_session.flush()
    return result.lastrowid


def _user_row(db_session, email):
    return db_session.execute(
        text("SELECT email, password_hash, is_verified, status FROM users WHERE email = :email"),
        {"email": email},
    ).fetchone()


def test_bootstrap_rejects_email_outside_platform_admin_allowlist(db_session):
    with pytest.raises(PlatformAdminBootstrapError, match="邮箱未配置为平台管理员"):
        ensure_platform_admin_user(
            db_session.get_bind(),
            email="ops@example.com",
            password="StrongPassword123",
            admin_emails="other@example.com",
        )


def test_bootstrap_creates_active_verified_user_with_hashed_password(db_session):
    result = ensure_platform_admin_user(
        db_session.get_bind(),
        email="Ops@Example.com",
        password="StrongPassword123",
        admin_emails="ops@example.com",
    )

    row = _user_row(db_session, "ops@example.com")
    assert result["action"] == "created"
    assert result["email"] == "ops@example.com"
    assert row.status == "active"
    assert bool(row.is_verified) is True
    assert row.password_hash != "StrongPassword123"
    assert verify_password("StrongPassword123", row.password_hash)


def test_bootstrap_keeps_existing_active_password_without_reset(db_session):
    _insert_user(db_session, email="ops@example.com", password="OldPassword123")

    result = ensure_platform_admin_user(
        db_session.get_bind(),
        email="ops@example.com",
        password="NewPassword123",
        admin_emails="ops@example.com",
    )

    row = _user_row(db_session, "ops@example.com")
    assert result["action"] == "exists"
    assert verify_password("OldPassword123", row.password_hash)
    assert not verify_password("NewPassword123", row.password_hash)


def test_bootstrap_resets_existing_active_password_when_explicit(db_session):
    _insert_user(db_session, email="ops@example.com", password="OldPassword123")

    result = ensure_platform_admin_user(
        db_session.get_bind(),
        email="ops@example.com",
        password="NewPassword123",
        admin_emails="ops@example.com",
        reset_password=True,
    )

    row = _user_row(db_session, "ops@example.com")
    assert result["action"] == "password_reset"
    assert verify_password("NewPassword123", row.password_hash)


@pytest.mark.parametrize("status", ["inactive", "suspended"])
def test_bootstrap_rejects_inactive_or_suspended_users(db_session, status):
    _insert_user(db_session, email="ops@example.com", status=status)

    with pytest.raises(PlatformAdminBootstrapError, match="账号状态"):
        ensure_platform_admin_user(
            db_session.get_bind(),
            email="ops@example.com",
            password="StrongPassword123",
            admin_emails="ops@example.com",
            reset_password=True,
        )


def test_bootstrap_activates_pending_user(db_session):
    _insert_user(
        db_session,
        email="ops@example.com",
        password="TempPassword123",
        status="pending_activation",
    )

    result = ensure_platform_admin_user(
        db_session.get_bind(),
        email="ops@example.com",
        password="StrongPassword123",
        admin_emails="ops@example.com",
    )

    row = _user_row(db_session, "ops@example.com")
    assert result["action"] == "activated"
    assert row.status == "active"
    assert bool(row.is_verified) is True
    assert verify_password("StrongPassword123", row.password_hash)


def test_bootstrap_user_can_login_with_platform_admin_role(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    _create_bootstrap_schema(engine)
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    ensure_platform_admin_user(
        engine,
        email="ops@example.com",
        password="StrongPassword123",
        admin_emails="ops@example.com",
    )

    result = authenticate_user(engine, "ops@example.com", "StrongPassword123")

    assert result["user"]["platformRoles"] == ["platform_admin"]
    assert result["user"]["tenants"] == []


def test_merge_platform_admin_email_preserves_existing_values():
    assert merge_platform_admin_email("", "ops@example.com") == "ops@example.com"
    assert (
        merge_platform_admin_email("admin@example.com, ops@example.com", "Ops@Example.com")
        == "admin@example.com,ops@example.com"
    )


def test_update_platform_admin_env_file_creates_or_updates_allowlist(tmp_path):
    env_file = Path(tmp_path) / ".env"
    env_file.write_text(
        "DB_DIALECT=sqlite\nPLATFORM_ADMIN_EMAILS=admin@example.com\n",
        encoding="utf-8",
    )

    result = update_platform_admin_env_file(env_file, "ops@example.com")

    assert result["changed"] is True
    assert "PLATFORM_ADMIN_EMAILS=admin@example.com,ops@example.com" in env_file.read_text(
        encoding="utf-8"
    )
