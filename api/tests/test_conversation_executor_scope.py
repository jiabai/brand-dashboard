from datetime import UTC, datetime

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import conversation
from api.v1.routes.query_jobs import verify_executor
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def conversation_scope_engine():
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
                    tenant_key VARCHAR(255) PRIMARY KEY,
                    tenant_name VARCHAR(255) NOT NULL,
                    industry VARCHAR(100),
                    status VARCHAR(20) NOT NULL DEFAULT 'active'
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
                    executor_id VARCHAR(128),
                    query_status INTEGER NOT NULL DEFAULT 1,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE llm_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL,
                    job_id VARCHAR(255) NOT NULL,
                    conversation_id VARCHAR(255) NOT NULL,
                    platform VARCHAR(64) NOT NULL,
                    keyword VARCHAR(100) NOT NULL,
                    brand VARCHAR(50),
                    category VARCHAR(64) NOT NULL,
                    query_content TEXT NOT NULL,
                    answer_content TEXT NOT NULL,
                    generated_date DATE,
                    extracted_at TIMESTAMP NOT NULL,
                    UNIQUE (tenant_key, conversation_id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE llm_conversation_references (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL,
                    job_id VARCHAR(255) NOT NULL,
                    conversation_id VARCHAR(255) NOT NULL,
                    platform VARCHAR(64) NOT NULL,
                    brand VARCHAR(50),
                    category VARCHAR(64) NOT NULL,
                    keyword VARCHAR(100) NOT NULL,
                    query_content TEXT NOT NULL,
                    url VARCHAR(1024) NOT NULL,
                    domain VARCHAR(100),
                    cite_index INTEGER,
                    site_name VARCHAR(255),
                    content_type VARCHAR(50),
                    generated_date DATE,
                    UNIQUE (tenant_key, conversation_id, url)
                )
                """
            )
        )
    return engine


@pytest.fixture(scope="function")
def conversation_scope_session(conversation_scope_engine):
    connection = conversation_scope_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    for table in (
        "llm_conversation_references",
        "llm_conversations",
        "llm_query_jobs",
        "tenants",
    ):
        session.execute(text(f"DELETE FROM {table}"))
    session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, industry, status)
            VALUES ('tn_allowed', '允许访问租户', '互联网', 'active')
            """
        )
    )
    session.flush()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _build_client(db_session, *, executor_id="exec_allowed"):
    app = FastAPI()
    app.include_router(conversation.router, prefix="/api/v1/conversation")
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[verify_executor] = lambda: executor_id
    return TestClient(app)


def _payload(job_id="job_allowed"):
    return {
        "tenant_key": "tn_allowed",
        "job_id": job_id,
        "platform": "deepseek",
        "items": [
            {
                "conversation_id": "conv_1",
                "keyword": "数学",
                "brand": "品牌A",
                "category": "教育",
                "query_content": "数学培训哪家好",
                "answer_content": "品牌A不错",
                "extracted_at": datetime.now(UTC).isoformat(),
            }
        ],
    }


def test_conversation_load_rejects_executor_without_matching_job(
    conversation_scope_session,
):
    client = _build_client(conversation_scope_session, executor_id="exec_wrong")

    response = client.post("/api/v1/conversation/load", json=_payload())

    assert response.status_code == 403


def test_conversation_load_allows_executor_with_matching_job(conversation_scope_session):
    conversation_scope_session.execute(
        text(
            """
            INSERT INTO llm_query_jobs (tenant_key, job_id, executor_id, query_status, is_deleted)
            VALUES ('tn_allowed', 'job_allowed', 'exec_allowed', 1, 0)
            """
        )
    )
    conversation_scope_session.flush()
    client = _build_client(conversation_scope_session, executor_id="exec_allowed")

    response = client.post("/api/v1/conversation/load", json=_payload())

    assert response.status_code == 200
    assert response.json()["inserted_conversations"] == 1
