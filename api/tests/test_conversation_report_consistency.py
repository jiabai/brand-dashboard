from datetime import UTC, datetime, timedelta

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import conversation, query_jobs
from api.v1.routes.query_jobs import verify_executor
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def consistency_engine():
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
                    category VARCHAR(64) NOT NULL,
                    brand VARCHAR(50),
                    competitor TEXT,
                    keyword VARCHAR(100) NOT NULL,
                    query_content TEXT NOT NULL,
                    query_status INTEGER NOT NULL DEFAULT 1,
                    executor_id VARCHAR(128),
                    total_runs INTEGER NOT NULL DEFAULT 1,
                    executed_runs INTEGER NOT NULL DEFAULT 0,
                    last_executed_date DATE,
                    effective_from TIMESTAMP NOT NULL,
                    effective_to TIMESTAMP,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
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
                    query_content TEXT NOT NULL
                        CHECK (query_content <> 'force_db_failure'),
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
def consistency_session(consistency_engine):
    connection = consistency_engine.connect()
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
            VALUES ('tn_consistency', '一致性租户', '教育', 'active')
            """
        )
    )
    session.commit()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _build_client(db_session, *, executor_id="exec_consistency"):
    app = FastAPI()
    app.include_router(conversation.router, prefix="/api/v1/conversation")
    app.include_router(query_jobs.router, prefix="/api/v1/query-jobs")
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[verify_executor] = lambda: executor_id
    return TestClient(app)


def _insert_job(db_session, *, query_content: str) -> int:
    now = datetime.now(UTC)
    result = db_session.execute(
        text(
            """
            INSERT INTO llm_query_jobs (
              tenant_key, job_id, category, brand, competitor, keyword,
              query_content, query_status, executor_id, total_runs,
              executed_runs, last_executed_date, effective_from, effective_to,
              is_deleted, created_at, updated_at
            )
            VALUES (
              'tn_consistency', 'job_consistency', '教育', '品牌A', NULL, '数学',
              :query_content, 1, 'exec_consistency', 1,
              0, NULL, :effective_from, NULL,
              0, :now, :now
            )
            """
        ),
        {
            "query_content": query_content,
            "effective_from": now - timedelta(minutes=1),
            "now": now,
        },
    )
    db_session.commit()
    return int(result.lastrowid)


def _conversation_payload(*, query_content: str):
    return {
        "tenant_key": "tn_consistency",
        "job_id": "job_consistency",
        "platform": "deepseek",
        "items": [
            {
                "conversation_id": f"conv_{query_content}",
                "keyword": "数学",
                "brand": "品牌A",
                "category": "教育",
                "query_content": query_content,
                "answer_content": "品牌A不错",
                "extracted_at": datetime.now(UTC).isoformat(),
            }
        ],
    }


def _executed_runs(db_session, record_id: int) -> int:
    return int(
        db_session.execute(
            text("SELECT executed_runs FROM llm_query_jobs WHERE id = :id"),
            {"id": record_id},
        ).scalar_one()
    )


def test_report_does_not_complete_when_conversation_load_failed(consistency_session):
    record_id = _insert_job(
        consistency_session,
        query_content="force_db_failure",
    )
    client = _build_client(consistency_session)

    load_response = client.post(
        "/api/v1/conversation/load",
        json=_conversation_payload(query_content="force_db_failure"),
    )

    assert load_response.status_code == 500
    assert _executed_runs(consistency_session, record_id) == 0

    report_response = client.post(
        "/api/v1/query-jobs/report",
        json={"id": record_id},
    )

    assert report_response.status_code == 200
    assert report_response.json()["success"] is False
    assert "入库" in report_response.json()["message"]
    assert _executed_runs(consistency_session, record_id) == 0


def test_report_completes_after_conversation_load_succeeds(consistency_session):
    record_id = _insert_job(
        consistency_session,
        query_content="数学培训哪家好",
    )
    client = _build_client(consistency_session)

    load_response = client.post(
        "/api/v1/conversation/load",
        json=_conversation_payload(query_content="数学培训哪家好"),
    )

    assert load_response.status_code == 200
    assert load_response.json()["inserted_conversations"] == 1

    report_response = client.post(
        "/api/v1/query-jobs/report",
        json={"id": record_id},
    )

    assert report_response.status_code == 200
    assert report_response.json()["success"] is True
    assert _executed_runs(consistency_session, record_id) == 1
