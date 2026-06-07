from datetime import UTC, date, datetime
from pathlib import Path

from api.v1.dependencies.auth import CurrentTenantContext
from api.v1.routes import dashboard
from api.v1.services.dashboard_service import DashboardService
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQLITE_SCHEMA_FILE = PROJECT_ROOT / "api" / "database" / "schema_sqlite.sql"


def _build_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")
        raw_connection = conn.connection.driver_connection
        raw_connection.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))
    return engine


def _build_client(engine):
    app = FastAPI()
    app.dependency_overrides[dashboard.get_current_tenant] = lambda: CurrentTenantContext(
        tenant_key="tenant_a",
        tenant_name="Tenant A",
        role="member",
        product_role="tenant_member",
    )
    app.dependency_overrides[dashboard.get_dashboard_service] = lambda: DashboardService(engine)
    app.include_router(dashboard.router, prefix="/api/v1/dashboard")
    return TestClient(app)


def _insert_tenant(session: Session, tenant_key: str) -> None:
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
            VALUES (:tenant_key, :tenant_name, 'active', :now, :now)
            """
        ),
        {"tenant_key": tenant_key, "tenant_name": tenant_key, "now": now},
    )


def _insert_conversation(
    session: Session,
    *,
    tenant_key: str = "tenant_a",
    job_id: str = "job_a",
    conversation_id: str,
    platform: str,
    brand: str,
    keyword: str,
    answer_content: str,
) -> None:
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO llm_conversations
              (
                tenant_key,
                job_id,
                conversation_id,
                platform,
                brand,
                category,
                keyword,
                query_content,
                answer_content,
                generated_date,
                extracted_at,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                :job_id,
                :conversation_id,
                :platform,
                :brand,
                'education',
                :keyword,
                :query_content,
                :answer_content,
                :generated_date,
                :now,
                :now,
                :now
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "job_id": job_id,
            "conversation_id": conversation_id,
            "platform": platform,
            "brand": brand,
            "keyword": keyword,
            "query_content": f"{keyword} 怎么选？",
            "answer_content": answer_content,
            "generated_date": date(2026, 6, 7),
            "now": now,
        },
    )


def _insert_brand_state(
    session: Session,
    *,
    conversation_id: str,
    platform: str,
    brand: str,
    keyword: str,
    sentiment_status: str,
    tenant_key: str = "tenant_a",
    job_id: str = "job_a",
) -> None:
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO qa_brand_state
              (
                tenant_key,
                job_id,
                date,
                conversation_id,
                brand,
                category,
                platform,
                keyword,
                is_mentioned,
                is_first_mentioned,
                is_top3_mentioned,
                sentiment_status,
                brands_found,
                created_at,
                updated_at
              )
            VALUES
              (
                :tenant_key,
                :job_id,
                :date,
                :conversation_id,
                :brand,
                'education',
                :platform,
                :keyword,
                1,
                0,
                1,
                :sentiment_status,
                :brands_found,
                :now,
                :now
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "job_id": job_id,
            "date": date(2026, 6, 7),
            "conversation_id": conversation_id,
            "brand": brand,
            "platform": platform,
            "keyword": keyword,
            "sentiment_status": sentiment_status,
            "brands_found": f'["{brand}"]',
            "now": now,
        },
    )


def _insert_reference(
    session: Session,
    *,
    conversation_id: str,
    platform: str,
    brand: str,
    keyword: str,
    url: str,
) -> None:
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO qa_reference
              (
                tenant_key,
                job_id,
                date,
                conversation_id,
                platform,
                brand,
                category,
                keyword,
                query_content,
                url,
                is_published_link,
                domain,
                content_type,
                created_at,
                updated_at
              )
            VALUES
              (
                'tenant_a',
                'job_a',
                :date,
                :conversation_id,
                :platform,
                :brand,
                'education',
                :keyword,
                :query_content,
                :url,
                1,
                'example.com',
                'news',
                :now,
                :now
              )
            """
        ),
        {
            "date": date(2026, 6, 7),
            "conversation_id": conversation_id,
            "platform": platform,
            "brand": brand,
            "keyword": keyword,
            "query_content": f"{keyword} 怎么选？",
            "url": url,
            "now": now,
        },
    )


def _seed_answer_snapshots(session: Session) -> None:
    _insert_tenant(session, "tenant_a")
    _insert_tenant(session, "tenant_b")
    _insert_conversation(
        session,
        conversation_id="conv_ref",
        platform="deepseek",
        brand="Brand A",
        keyword="math",
        answer_content="Brand A 在数学培训里被正向推荐，并给出引用。",
    )
    _insert_brand_state(
        session,
        conversation_id="conv_ref",
        platform="deepseek",
        brand="Brand A",
        keyword="math",
        sentiment_status="positive",
    )
    _insert_reference(
        session,
        conversation_id="conv_ref",
        platform="deepseek",
        brand="Brand A",
        keyword="math",
        url="https://example.com/ref",
    )

    _insert_conversation(
        session,
        conversation_id="conv_no_ref",
        platform="qwen",
        brand="Brand A",
        keyword="science",
        answer_content="Brand A 在科学培训问题里有负向反馈，但没有引用。",
    )
    _insert_brand_state(
        session,
        conversation_id="conv_no_ref",
        platform="qwen",
        brand="Brand A",
        keyword="science",
        sentiment_status="negative",
    )

    _insert_conversation(
        session,
        conversation_id="conv_other_brand",
        platform="deepseek",
        brand="Brand B",
        keyword="math",
        answer_content="Brand B 的回答不应出现在 Brand A 筛选中。",
    )
    _insert_brand_state(
        session,
        conversation_id="conv_other_brand",
        platform="deepseek",
        brand="Brand B",
        keyword="math",
        sentiment_status="positive",
    )

    _insert_conversation(
        session,
        tenant_key="tenant_b",
        job_id="job_a",
        conversation_id="conv_other_tenant",
        platform="deepseek",
        brand="Brand A",
        keyword="math",
        answer_content="其他租户数据不应泄漏。",
    )
    _insert_brand_state(
        session,
        tenant_key="tenant_b",
        job_id="job_a",
        conversation_id="conv_other_tenant",
        platform="deepseek",
        brand="Brand A",
        keyword="math",
        sentiment_status="positive",
    )
    session.commit()


def test_answer_snapshots_filters_by_brand_platform_keyword_sentiment_and_reference():
    engine = _build_engine()
    with Session(engine) as session:
        _seed_answer_snapshots(session)
    client = _build_client(engine)

    response = client.get(
        "/api/v1/dashboard/answer-snapshots",
        params={
            "tenant_key": "tenant_a",
            "job_id": "job_a",
            "timeframe": "specific_day",
            "start_date": "20260607",
            "end_date": "20260607",
            "brand": "Brand A",
            "platform": "deepseek",
            "keyword": "math",
            "sentiment": "positive",
            "has_reference": "true",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["metadata"]["total_count"] == 1
    item = payload["data"][0]
    assert item["conversation_id"] == "conv_ref"
    assert item["date"] == "20260607"
    assert item["brand"] == "Brand A"
    assert item["platform"] == "deepseek"
    assert item["keyword"] == "math"
    assert item["sentiment_status"] == "positive"
    assert item["has_reference"] is True
    assert item["reference_count"] == 1
    assert item["references"][0]["url"] == "https://example.com/ref"


def test_answer_snapshots_can_filter_unreferenced_negative_answers():
    engine = _build_engine()
    with Session(engine) as session:
        _seed_answer_snapshots(session)
    client = _build_client(engine)

    response = client.get(
        "/api/v1/dashboard/answer-snapshots",
        params={
            "tenant_key": "tenant_a",
            "job_id": "job_a",
            "timeframe": "specific_day",
            "start_date": "20260607",
            "end_date": "20260607",
            "brand": "Brand A",
            "sentiment": "negative",
            "has_reference": "false",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["total_count"] == 1
    item = payload["data"][0]
    assert item["conversation_id"] == "conv_no_ref"
    assert item["has_reference"] is False
    assert item["references"] == []
