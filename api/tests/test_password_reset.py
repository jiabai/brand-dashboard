from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from api.v1.dependencies.auth import CurrentUser, get_current_user
from api.v1.repositories import auth as auth_repository
from api.v1.repositories.connection import get_engine
from api.v1.routes import auth as auth_routes
from api.v1.utils.security import hash_password, sign_token, verify_password
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def memory_engine(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    monkeypatch.setenv("AUTH_BASE_URL", "https://example.com")
    auth_repository._reset_email_last_sent.clear()
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
                    tenant_key VARCHAR(64) NOT NULL UNIQUE,
                    tenant_name VARCHAR(255) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE user_tenants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tenant_id INTEGER NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'active'
                )
                """
            )
        )
    return engine


def _seed_user(engine, *, email="user@demo.test", password="OldPass12345", status="active"):
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO users (
                    user_key, email, password_hash, is_verified, status, created_at, updated_at
                ) VALUES (:user_key, :email, :password_hash, 1, :status, :now, :now)
                """
            ),
            {
                "user_key": f"uk_{email}",
                "email": email,
                "password_hash": hash_password(password),
                "status": status,
                "now": now,
            },
        )
        return conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()[0]


def _password_hash_of(engine, user_id):
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT password_hash FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        ).fetchone()[0]


def test_request_reset_returns_token_payload_for_active_user(memory_engine):
    user_id = _seed_user(memory_engine)

    result = auth_repository.request_password_reset(memory_engine, "user@demo.test")

    assert result is not None
    assert result["email"] == "user@demo.test"
    assert result["resetUrl"].startswith("https://example.com/reset-password?token=")
    activation = auth_repository.reset_password_with_token(
        memory_engine, result["resetToken"], "NewPass12345"
    )
    assert activation["userId"] == user_id
    assert verify_password("NewPass12345", _password_hash_of(memory_engine, user_id))


def test_request_reset_returns_none_for_unknown_and_inactive_users(memory_engine):
    _seed_user(memory_engine, email="pending@demo.test", status="pending_activation")
    _seed_user(memory_engine, email="suspended@demo.test", status="suspended")

    assert auth_repository.request_password_reset(memory_engine, "missing@demo.test") is None
    assert auth_repository.request_password_reset(memory_engine, "pending@demo.test") is None
    assert auth_repository.request_password_reset(memory_engine, "suspended@demo.test") is None


def test_request_reset_enforces_per_email_cooldown(memory_engine):
    _seed_user(memory_engine)

    first = auth_repository.request_password_reset(memory_engine, "user@demo.test")
    second = auth_repository.request_password_reset(memory_engine, "user@demo.test")

    assert first is not None
    assert second is None


def test_reset_token_is_single_use(memory_engine):
    _seed_user(memory_engine)
    result = auth_repository.request_password_reset(memory_engine, "user@demo.test")

    auth_repository.reset_password_with_token(memory_engine, result["resetToken"], "NewPass12345")
    with pytest.raises(ValueError, match="重置链接无效或已失效"):
        auth_repository.reset_password_with_token(
            memory_engine, result["resetToken"], "OtherPass12345"
        )


def test_password_change_invalidates_outstanding_reset_tokens(memory_engine):
    user_id = _seed_user(memory_engine)
    result = auth_repository.request_password_reset(memory_engine, "user@demo.test")

    auth_repository.change_password(memory_engine, user_id, "OldPass12345", "ChangedPass1")
    with pytest.raises(ValueError, match="重置链接无效或已失效"):
        auth_repository.reset_password_with_token(
            memory_engine, result["resetToken"], "NewPass12345"
        )


def test_reset_rejects_expired_token(memory_engine):
    user_id = _seed_user(memory_engine)
    password_hash = _password_hash_of(memory_engine, user_id)
    expired_token = sign_token(
        {
            "user_id": user_id,
            "email": "user@demo.test",
            "type": "password_reset",
            "pwd_fp": auth_repository._password_fingerprint(password_hash),
            "exp": int((datetime.now(UTC) - timedelta(minutes=1)).timestamp()),
        },
        "test-secret-with-at-least-32-bytes",
    )

    with pytest.raises(ValueError, match="重置链接无效或已失效"):
        auth_repository.reset_password_with_token(memory_engine, expired_token, "NewPass12345")


def test_reset_rejects_activation_token_type(memory_engine):
    user_id = _seed_user(memory_engine)
    activation_token = sign_token(
        {
            "user_id": user_id,
            "email": "user@demo.test",
            "type": "activation",
            "exp": int((datetime.now(UTC) + timedelta(days=7)).timestamp()),
        },
        "test-secret-with-at-least-32-bytes",
    )

    with pytest.raises(ValueError, match="重置链接无效或已失效"):
        auth_repository.reset_password_with_token(
            memory_engine, activation_token, "NewPass12345"
        )


def test_change_password_requires_correct_current_password(memory_engine):
    user_id = _seed_user(memory_engine)

    with pytest.raises(ValueError, match="当前密码错误"):
        auth_repository.change_password(memory_engine, user_id, "WrongPass123", "NewPass12345")

    auth_repository.change_password(memory_engine, user_id, "OldPass12345", "NewPass12345")
    assert verify_password("NewPass12345", _password_hash_of(memory_engine, user_id))


def test_request_reset_cooldown_ignores_email_case_variants(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    monkeypatch.setenv("AUTH_BASE_URL", "https://example.com")
    auth_repository._reset_email_last_sent.clear()
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
                    email VARCHAR(255) NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_verified BOOLEAN NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
    _seed_user(engine)

    first = auth_repository.request_password_reset(engine, "user@demo.test")
    case_variant = auth_repository.request_password_reset(engine, "User@demo.test")

    assert first is not None
    assert case_variant is None


def test_request_reset_cooldown_releases_after_window(memory_engine, monkeypatch):
    _seed_user(memory_engine)

    first = auth_repository.request_password_reset(memory_engine, "user@demo.test")
    real_now = auth_repository.time.time()
    monkeypatch.setattr(auth_repository.time, "time", lambda: real_now + 61)
    second = auth_repository.request_password_reset(memory_engine, "user@demo.test")

    assert first is not None
    assert second is not None


def test_reset_rejects_token_after_account_suspended(memory_engine):
    user_id = _seed_user(memory_engine)
    result = auth_repository.request_password_reset(memory_engine, "user@demo.test")

    with memory_engine.begin() as conn:
        conn.execute(
            text("UPDATE users SET status = 'suspended' WHERE id = :user_id"),
            {"user_id": user_id},
        )

    with pytest.raises(ValueError, match="重置链接无效或已失效"):
        auth_repository.reset_password_with_token(
            memory_engine, result["resetToken"], "NewPass12345"
        )


def _public_client(memory_engine):
    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/api/v1")
    app.dependency_overrides[get_engine] = lambda: memory_engine
    return TestClient(app)


def _authed_client(memory_engine, user_id):
    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/api/v1")
    app.dependency_overrides[get_engine] = lambda: memory_engine
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id,
        email="user@demo.test",
        status="active",
    )
    return TestClient(app)


def test_forgot_password_responses_are_byte_identical(memory_engine):
    _seed_user(memory_engine)
    _seed_user(memory_engine, email="pending@demo.test", status="pending_activation")
    client = _public_client(memory_engine)

    responses = []
    with patch(
        "api.v1.routes.auth.send_password_reset_email",
        return_value={"status": "sent", "to": None, "message": ""},
    ):
        for email in [
            "user@demo.test",
            "missing@demo.test",
            "pending@demo.test",
            "user@demo.test",
        ]:
            responses.append(client.post(
                "/api/v1/public/auth/forgot-password", json={"email": email}
            ))

    assert {r.status_code for r in responses} == {200}
    assert len({r.text for r in responses}) == 1
    body = responses[0].json()
    assert body["message"] == "如果该邮箱已注册并激活，重置邮件已发送"
    assert body["data"] is None


def test_forgot_password_sends_email_only_for_active_user(memory_engine):
    _seed_user(memory_engine)
    client = _public_client(memory_engine)

    with patch(
        "api.v1.routes.auth.send_password_reset_email",
        return_value={"status": "sent", "to": None, "message": ""},
    ) as send_email:
        client.post("/api/v1/public/auth/forgot-password", json={"email": "user@demo.test"})
        client.post("/api/v1/public/auth/forgot-password", json={"email": "missing@demo.test"})

    send_email.assert_called_once()
    sent_payload = send_email.call_args.args[0]
    assert sent_payload["email"] == "user@demo.test"
    assert sent_payload["resetUrl"].startswith("https://example.com/reset-password?token=")


def test_forgot_password_swallows_email_exceptions(memory_engine):
    _seed_user(memory_engine)
    client = _public_client(memory_engine)

    with patch(
        "api.v1.routes.auth.send_password_reset_email",
        side_effect=RuntimeError("smtp-secret leaked"),
    ):
        response = client.post(
            "/api/v1/public/auth/forgot-password", json={"email": "user@demo.test"}
        )

    assert response.status_code == 200
    assert "smtp-secret" not in response.text
    assert response.json()["message"] == "如果该邮箱已注册并激活，重置邮件已发送"


def test_forgot_password_logs_unsent_delivery_without_token(memory_engine, caplog):
    _seed_user(memory_engine)
    client = _public_client(memory_engine)

    with patch(
        "api.v1.routes.auth.send_password_reset_email",
        return_value={"status": "failed", "to": "user@demo.test", "message": "x"},
    ) as send_email, caplog.at_level("WARNING"):
        response = client.post(
            "/api/v1/public/auth/forgot-password", json={"email": "user@demo.test"}
        )

    assert response.status_code == 200
    assert any("密码重置邮件未发送" in record.message for record in caplog.records)
    reset_token = send_email.call_args.args[0]["resetToken"]
    assert reset_token not in caplog.text


def test_reset_password_route_roundtrip(memory_engine):
    _seed_user(memory_engine)
    client = _public_client(memory_engine)

    with patch(
        "api.v1.routes.auth.send_password_reset_email",
        return_value={"status": "sent", "to": None, "message": ""},
    ) as send_email:
        client.post("/api/v1/public/auth/forgot-password", json={"email": "user@demo.test"})
    token = send_email.call_args.args[0]["resetToken"]

    response = client.post(
        "/api/v1/public/auth/reset-password",
        json={"token": token, "password": "NewPass12345", "confirmPassword": "NewPass12345"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "密码已重置"

    login = client.post(
        "/api/v1/public/auth/login",
        json={"email": "user@demo.test", "password": "NewPass12345"},
    )
    assert login.status_code == 200


def test_reset_password_route_rejects_mismatch_and_bad_token(memory_engine):
    client = _public_client(memory_engine)

    mismatch = client.post(
        "/api/v1/public/auth/reset-password",
        json={"token": "x.y", "password": "NewPass12345", "confirmPassword": "Different123"},
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["message"] == "两次密码不一致"

    bad_token = client.post(
        "/api/v1/public/auth/reset-password",
        json={"token": "x.y", "password": "NewPass12345", "confirmPassword": "NewPass12345"},
    )
    assert bad_token.status_code == 400
    assert bad_token.json()["message"] == "重置链接无效或已失效"


def test_change_password_route_requires_auth_and_current_password(memory_engine):
    user_id = _seed_user(memory_engine)

    unauthed = _public_client(memory_engine).post(
        "/api/v1/auth/change-password",
        json={
            "currentPassword": "OldPass12345",
            "newPassword": "NewPass12345",
            "confirmPassword": "NewPass12345",
        },
    )
    assert unauthed.status_code == 401

    client = _authed_client(memory_engine, user_id)
    wrong = client.post(
        "/api/v1/auth/change-password",
        json={
            "currentPassword": "WrongPass123",
            "newPassword": "NewPass12345",
            "confirmPassword": "NewPass12345",
        },
    )
    assert wrong.status_code == 400
    assert wrong.json()["message"] == "当前密码错误"

    mismatch = client.post(
        "/api/v1/auth/change-password",
        json={
            "currentPassword": "OldPass12345",
            "newPassword": "NewPass12345",
            "confirmPassword": "Different123",
        },
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["message"] == "两次密码不一致"

    ok = client.post(
        "/api/v1/auth/change-password",
        json={
            "currentPassword": "OldPass12345",
            "newPassword": "NewPass12345",
            "confirmPassword": "NewPass12345",
        },
    )
    assert ok.status_code == 200
    assert ok.json()["message"] == "密码已修改"
