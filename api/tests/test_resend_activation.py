from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from api.v1.dependencies.auth import CurrentUser, require_platform_admin
from api.v1.repositories import auth as auth_repository
from api.v1.routes import auth as auth_routes
from api.v1.utils.security import verify_token
from fastapi import FastAPI
from fastapi.testclient import TestClient
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


def test_regenerate_builds_subdomain_activation_url(memory_engine):
    tenant_id = _seed_tenant(memory_engine, tenant_key="tn_acme", subdomain="acme")
    _seed_admin(memory_engine, tenant_id, email="admin@acme.test")

    result = auth_repository.regenerate_admin_activation(memory_engine, "tn_acme")

    assert result["activationUrl"].startswith(
        "https://acme.example.com/activate?token="
    )
    assert result["loginUrl"] == "https://acme.example.com/login"


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


@pytest.mark.parametrize("abnormal_status", ["inactive", "suspended"])
def test_regenerate_rejects_abnormal_admin(memory_engine, abnormal_status):
    tenant_id = _seed_tenant(memory_engine)
    _seed_admin(
        memory_engine, tenant_id, email="admin@demo.test", user_status=abnormal_status
    )
    with pytest.raises(ValueError, match="账号状态异常"):
        auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")


@pytest.fixture()
def platform_client():
    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/api/v1")
    app.dependency_overrides[require_platform_admin] = lambda: CurrentUser(
        user_id=1,
        email="platform@example.com",
        status="active",
    )
    return TestClient(app)


_REPO_RESULT = {
    "tenantKey": "tn_demo",
    "tenantName": "示例企业",
    "adminEmail": "admin@demo.test",
    "activationToken": "new-token",
    "activationUrl": "https://example.com/activate?token=new-token",
    "loginUrl": "https://example.com/login",
}


def test_resend_route_returns_payload_with_email_delivery(platform_client):
    with patch(
        "api.v1.routes.auth.regenerate_admin_activation",
        return_value=dict(_REPO_RESULT),
    ) as regenerate, patch(
        "api.v1.routes.auth.send_admin_activation_email",
        return_value={
            "status": "sent",
            "to": "admin@demo.test",
            "message": "激活邮件已发送",
        },
    ) as send_email:
        response = platform_client.post(
            "/api/v1/platform/tenants/tn_demo/resend-activation"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["message"] == "激活令牌已重新签发"
    assert body["data"]["adminEmail"] == "admin@demo.test"
    assert body["data"]["activationUrl"].startswith("https://example.com/activate")
    assert body["data"]["emailDelivery"]["status"] == "sent"
    regenerate.assert_called_once()
    assert regenerate.call_args.args[1] == "tn_demo"
    send_email.assert_called_once_with(dict(_REPO_RESULT))


def test_resend_route_maps_lookup_error_to_404(platform_client):
    with patch(
        "api.v1.routes.auth.regenerate_admin_activation",
        side_effect=LookupError("租户不存在"),
    ):
        response = platform_client.post(
            "/api/v1/platform/tenants/tn_missing/resend-activation"
        )

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "error"
    assert body["message"] == "租户不存在"
    assert body["code"] == 404


def test_resend_route_maps_value_error_to_400(platform_client):
    with patch(
        "api.v1.routes.auth.regenerate_admin_activation",
        side_effect=ValueError("账号已激活"),
    ):
        response = platform_client.post(
            "/api/v1/platform/tenants/tn_demo/resend-activation"
        )

    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "error"
    assert body["message"] == "账号已激活"
    assert body["code"] == 400


def test_resend_route_keeps_success_when_email_raises(platform_client):
    with patch(
        "api.v1.routes.auth.regenerate_admin_activation",
        return_value=dict(_REPO_RESULT),
    ), patch(
        "api.v1.routes.auth.send_admin_activation_email",
        side_effect=RuntimeError("smtp-secret leaked in raw exception"),
    ):
        response = platform_client.post(
            "/api/v1/platform/tenants/tn_demo/resend-activation"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["emailDelivery"]["status"] == "failed"
    assert (
        body["data"]["emailDelivery"]["message"]
        == "激活邮件发送失败，请复制激活链接人工发送"
    )
    assert "smtp-secret" not in response.text


def test_resend_route_requires_platform_admin():
    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post("/api/v1/platform/tenants/tn_demo/resend-activation")

    assert response.status_code == 401
