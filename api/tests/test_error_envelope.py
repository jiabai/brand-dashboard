"""全局 HTTPException 错误信封回归测试.

覆盖 api.main 全局异常 handler 的对外契约:
所有 HTTPException(含框架自身抛出的未路由 404)统一输出业务信封
{"status": "error", "message": ..., "code": ...},HTTP 状态码与 code 一致。
契约定义见 docs/references/20260519-000000-tenant-account-api-reference.md §1.1。
"""

import asyncio

from api.main import app, http_exception_handler
from api.v1.dependencies.auth import CurrentUser, get_current_user
from fastapi import HTTPException
from fastapi.testclient import TestClient


def test_auth_401_returns_business_envelope():
    client = TestClient(app)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {
        "status": "error",
        "message": "未提供有效的认证令牌",
        "code": 401,
    }


def test_platform_403_returns_business_envelope(monkeypatch):
    monkeypatch.delenv("PLATFORM_ADMIN_EMAILS", raising=False)
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=1, email="member@example.com", status="active"
    )
    try:
        client = TestClient(app)

        response = client.get("/api/v1/platform/tenants")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
    assert response.json() == {
        "status": "error",
        "message": "需要平台管理员权限",
        "code": 403,
    }


def test_unrouted_404_returns_business_envelope():
    client = TestClient(app)

    response = client.get("/api/v1/__no_such_route__")

    assert response.status_code == 404
    assert response.json() == {
        "status": "error",
        "message": "Not Found",
        "code": 404,
    }


def test_handler_preserves_exception_headers():
    exc = HTTPException(
        status_code=401,
        detail="未提供有效的认证令牌",
        headers={"WWW-Authenticate": "Bearer"},
    )

    response = asyncio.run(http_exception_handler(None, exc))

    assert response.headers["www-authenticate"] == "Bearer"
