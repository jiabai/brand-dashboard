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


@pytest.fixture(scope="session")
def platform_db_engine():
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
                    company_legal_name VARCHAR(255),
                    company_type VARCHAR(100),
                    registration_no VARCHAR(100),
                    industry VARCHAR(100),
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    plan_type VARCHAR(50),
                    max_users INTEGER,
                    billing_cycle VARCHAR(50),
                    contract_start_date DATE,
                    contract_end_date DATE,
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
                CREATE TABLE llm_query_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL,
                    job_id VARCHAR(255) NOT NULL,
                    category VARCHAR(64),
                    brand VARCHAR(50),
                    query_status INTEGER NOT NULL DEFAULT 0,
                    effective_from TIMESTAMP,
                    effective_to TIMESTAMP,
                    created_at TIMESTAMP,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """
            )
        )
    return engine


@pytest.fixture(scope="function")
def db_session(platform_db_engine):
    connection = platform_db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session, monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _insert_user(db_session, *, user_id, email):
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
            "email": email,
            "password_hash": hash_password("User12345"),
            "now": now,
        },
    )
    db_session.flush()
    return user_id


def _token(user_id):
    return create_access_token(user_id, "test-secret-with-at-least-32-bytes")


def _insert_tenant(
    db_session,
    *,
    tenant_key,
    tenant_name,
    admin_email,
    status="active",
    plan_type="enterprise",
    max_users=200,
):
    now = datetime.now(UTC)
    tenant_result = db_session.execute(
        text(
            """
            INSERT INTO tenants (
                tenant_key,
                tenant_name,
                company_legal_name,
                industry,
                status,
                plan_type,
                max_users,
                billing_cycle,
                contract_start_date,
                contract_end_date,
                created_at,
                updated_at
            ) VALUES (
                :tenant_key,
                :tenant_name,
                :company_legal_name,
                :industry,
                :status,
                :plan_type,
                :max_users,
                'yearly',
                '2026-05-20',
                '2027-05-19',
                :now,
                :now
            )
            """
        ),
        {
            "tenant_key": tenant_key,
            "tenant_name": tenant_name,
            "company_legal_name": f"{tenant_name}有限公司",
            "industry": "互联网",
            "status": status,
            "plan_type": plan_type,
            "max_users": max_users,
            "now": now,
        },
    )
    admin_id = _insert_user(
        db_session,
        user_id=abs(hash(admin_email)) % 1000000 + 100,
        email=admin_email,
    )
    db_session.execute(
        text(
            """
            INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
            VALUES (:user_id, :tenant_id, 'admin', 'active', :now)
            """
        ),
        {
            "user_id": admin_id,
            "tenant_id": tenant_result.lastrowid,
            "now": now,
        },
    )
    db_session.flush()


def _insert_query_job(
    db_session,
    *,
    tenant_key,
    job_id,
    brand="品牌A",
    category="消费电子",
    query_status=1,
    created_at=None,
    is_deleted=0,
):
    created_at = created_at or datetime.now(UTC)
    db_session.execute(
        text(
            """
            INSERT INTO llm_query_jobs (
                tenant_key,
                job_id,
                category,
                brand,
                query_status,
                effective_from,
                effective_to,
                created_at,
                is_deleted
            ) VALUES (
                :tenant_key,
                :job_id,
                :category,
                :brand,
                :query_status,
                :effective_from,
                :effective_to,
                :created_at,
                :is_deleted
            )
            """
        ),
        {
            "tenant_key": tenant_key,
            "job_id": job_id,
            "category": category,
            "brand": brand,
            "query_status": query_status,
            "effective_from": datetime(2026, 5, 20, tzinfo=UTC),
            "effective_to": datetime(2026, 6, 20, tzinfo=UTC),
            "created_at": created_at,
            "is_deleted": is_deleted,
        },
    )
    db_session.flush()


def test_platform_tenants_requires_authentication(client):
    response = client.get("/api/v1/platform/tenants")

    assert response.status_code == 401


def test_platform_tenants_rejects_non_platform_admin(client, db_session, monkeypatch):
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    user_id = _insert_user(db_session, user_id=1, email="member@example.com")

    response = client.get(
        "/api/v1/platform/tenants",
        headers={"Authorization": f"Bearer {_token(user_id)}"},
    )

    assert response.status_code == 403


def test_platform_admin_can_list_tenants(client, db_session, monkeypatch):
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    platform_user_id = _insert_user(db_session, user_id=1, email="ops@example.com")
    _insert_tenant(
        db_session,
        tenant_key="tn_alibaba",
        tenant_name="阿里巴巴集团",
        admin_email="admin@alibaba.com",
    )

    response = client.get(
        "/api/v1/platform/tenants",
        headers={"Authorization": f"Bearer {_token(platform_user_id)}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["data"]["pagination"] == {
        "page": 1,
        "pageSize": 20,
        "total": 1,
        "totalPages": 1,
    }
    assert body["data"]["items"][0]["tenantKey"] == "tn_alibaba"
    assert body["data"]["items"][0]["tenantName"] == "阿里巴巴集团"
    assert body["data"]["items"][0]["adminEmail"] == "admin@alibaba.com"
    assert body["data"]["items"][0]["memberCount"] == 1
    assert body["data"]["items"][0]["jobCount"] == 0
    assert body["data"]["items"][0]["latestJob"] is None


def test_platform_tenant_list_includes_latest_job_summary(
    client,
    db_session,
    monkeypatch,
):
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    platform_user_id = _insert_user(db_session, user_id=1, email="ops@example.com")
    _insert_tenant(
        db_session,
        tenant_key="tn_alibaba",
        tenant_name="阿里巴巴集团",
        admin_email="admin@alibaba.com",
    )
    _insert_tenant(
        db_session,
        tenant_key="tn_tencent",
        tenant_name="腾讯集团",
        admin_email="admin@tencent.com",
    )
    _insert_query_job(
        db_session,
        tenant_key="tn_alibaba",
        job_id="job_old",
        brand="通义",
        category="AI 服务",
        query_status=2,
        created_at=datetime(2026, 5, 19, 8, 0, tzinfo=UTC),
    )
    _insert_query_job(
        db_session,
        tenant_key="tn_alibaba",
        job_id="job_latest",
        brand="通义",
        category="AI 服务",
        query_status=1,
        created_at=datetime(2026, 5, 21, 8, 0, tzinfo=UTC),
    )
    _insert_query_job(
        db_session,
        tenant_key="tn_alibaba",
        job_id="job_deleted",
        brand="不应展示",
        category="已删除",
        query_status=1,
        created_at=datetime(2026, 5, 22, 8, 0, tzinfo=UTC),
        is_deleted=1,
    )
    _insert_query_job(
        db_session,
        tenant_key="tn_tencent",
        job_id="job_tencent",
        brand="元宝",
        category="AI 服务",
        query_status=1,
        created_at=datetime(2026, 5, 20, 8, 0, tzinfo=UTC),
    )

    response = client.get(
        "/api/v1/platform/tenants",
        params={"q": "alibaba"},
        headers={"Authorization": f"Bearer {_token(platform_user_id)}"},
    )

    assert response.status_code == 200
    item = response.json()["data"]["items"][0]
    assert item["tenantKey"] == "tn_alibaba"
    assert item["jobCount"] == 2
    assert item["activeJobCount"] == 1
    assert item["latestJob"] == {
        "jobId": "job_latest",
        "brand": "通义",
        "category": "AI 服务",
        "queryStatus": 1,
        "effectiveFrom": "2026-05-20T00:00:00+00:00",
        "effectiveTo": "2026-06-20T00:00:00+00:00",
        "createdAt": "2026-05-21T08:00:00+00:00",
    }


def test_platform_tenant_list_filters_by_query_status_and_plan_type(
    client,
    db_session,
    monkeypatch,
):
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    platform_user_id = _insert_user(db_session, user_id=1, email="ops@example.com")
    _insert_tenant(
        db_session,
        tenant_key="tn_alibaba",
        tenant_name="阿里巴巴集团",
        admin_email="admin@alibaba.com",
        status="active",
        plan_type="enterprise",
    )
    _insert_tenant(
        db_session,
        tenant_key="tn_inactive",
        tenant_name="停用客户",
        admin_email="owner@inactive.com",
        status="inactive",
        plan_type="basic",
    )

    response = client.get(
        "/api/v1/platform/tenants",
        params={"q": "alibaba", "status": "active", "planType": "enterprise"},
        headers={"Authorization": f"Bearer {_token(platform_user_id)}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["pagination"]["total"] == 1
    assert [item["tenantKey"] for item in body["data"]["items"]] == ["tn_alibaba"]


def test_platform_tenant_list_omits_sensitive_fields(client, db_session, monkeypatch):
    monkeypatch.setenv("PLATFORM_ADMIN_EMAILS", "ops@example.com")
    platform_user_id = _insert_user(db_session, user_id=1, email="ops@example.com")
    _insert_tenant(
        db_session,
        tenant_key="tn_safe",
        tenant_name="安全客户",
        admin_email="admin@safe.com",
    )

    response = client.get(
        "/api/v1/platform/tenants",
        headers={"Authorization": f"Bearer {_token(platform_user_id)}"},
    )

    assert response.status_code == 200
    payload_text = response.text.lower()
    assert "password_hash" not in payload_text
    assert "activationtoken" not in payload_text
    assert "activation_token" not in payload_text
    assert "api_key" not in payload_text
