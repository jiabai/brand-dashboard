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


def _seed_tenant(session: Session) -> None:
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
            VALUES ('tenant_a', 'Tenant A', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    session.commit()


def _seed_project_run(session: Session) -> None:
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
            VALUES ('tenant_a', 'Tenant A', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO monitoring_projects
              (tenant_key, project_id, name, industry, category, status, created_at, updated_at)
            VALUES
              ('tenant_a', 'project_a', 'Project A', 'education', 'k12', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO prompt_sets
              (tenant_key, project_id, prompt_set_id, version, name, status, created_at, updated_at)
            VALUES
              ('tenant_a', 'project_a', 'prompt_set_a', 1, 'Prompt Set A', 'active', :now, :now)
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO collection_jobs
              (
                tenant_key,
                collection_job_id,
                project_id,
                prompt_set_id,
                source_job_id,
                status,
                expected_task_count,
                succeeded_task_count,
                failed_task_count,
                created_at,
                updated_at
              )
            VALUES
              (
                'tenant_a',
                'collection_job_a',
                'project_a',
                'prompt_set_a',
                'legacy_job_a',
                'succeeded',
                20,
                20,
                0,
                :now,
                :now
              )
            """
        ),
        {"now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO analysis_runs
              (
                tenant_key,
                analysis_run_id,
                project_id,
                collection_job_id,
                status,
                input_watermark,
                started_at,
                finished_at,
                created_at,
                updated_at
              )
            VALUES
              (
                'tenant_a',
                'analysis_run_a',
                'project_a',
                'collection_job_a',
                'succeeded',
                'legacy_job_a:2026-06-07T10:00:00+00:00',
                :now,
                :now,
                :now,
                :now
              )
            """
        ),
        {"now": now},
    )
    session.commit()


def _insert_metric_snapshot(
    session: Session,
    *,
    snapshot_id: str,
    keyword: str,
    metric_name: str,
    metric_value: float,
    analyzed_answer_count: int,
    dimension_hash: str,
) -> None:
    session.execute(
        text(
            """
            INSERT INTO metric_snapshots
              (
                tenant_key,
                snapshot_id,
                project_id,
                analysis_run_id,
                metric_date,
                brand_id,
                brand_name,
                platform,
                keyword,
                metric_name,
                metric_value,
                metric_unit,
                metric_definition_version,
                expected_task_count,
                succeeded_task_count,
                failed_task_count,
                analyzed_answer_count,
                coverage_rate,
                source_watermark,
                dimension_hash,
                generated_at
              )
            VALUES
              (
                'tenant_a',
                :snapshot_id,
                'project_a',
                'analysis_run_a',
                '2026-06-07',
                'brand_a',
                'Brand A',
                'deepseek',
                :keyword,
                :metric_name,
                :metric_value,
                'ratio',
                'brand_metrics_v1',
                20,
                20,
                0,
                :analyzed_answer_count,
                1.000000,
                'legacy_job_a:2026-06-07T10:00:00+00:00',
                :dimension_hash,
                '2026-06-07 11:00:00'
              )
            """
        ),
        {
            "snapshot_id": snapshot_id,
            "keyword": keyword,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "analyzed_answer_count": analyzed_answer_count,
            "dimension_hash": dimension_hash,
        },
    )


def _seed_sentiment_snapshots(session: Session) -> None:
    rows = [
        ("math", "sentiment_positive_ratio", 0.6, 10, "dim_math"),
        ("math", "sentiment_negative_ratio", 0.2, 10, "dim_math"),
        ("math", "sentiment_neutral_ratio", 0.2, 10, "dim_math"),
        ("math", "sentiment_unknown_ratio", 0.0, 10, "dim_math"),
        ("science", "sentiment_positive_ratio", 0.2, 5, "dim_science"),
        ("science", "sentiment_negative_ratio", 0.6, 5, "dim_science"),
        ("science", "sentiment_neutral_ratio", 0.0, 5, "dim_science"),
        ("science", "sentiment_unknown_ratio", 0.2, 5, "dim_science"),
    ]
    for index, (keyword, metric_name, metric_value, analyzed_count, dimension_hash) in enumerate(
        rows,
        start=1,
    ):
        _insert_metric_snapshot(
            session,
            snapshot_id=f"sentiment_snapshot_{index}",
            keyword=keyword,
            metric_name=metric_name,
            metric_value=metric_value,
            analyzed_answer_count=analyzed_count,
            dimension_hash=dimension_hash,
        )
    session.commit()


def _insert_brand_state(
    session: Session,
    *,
    conversation_id: str,
    sentiment_status: str,
    brand: str = "Brand A",
    platform: str = "deepseek",
    keyword: str = "math",
    job_id: str = "legacy_job_a",
    analysis_run_id: str | None = "analysis_run_a",
) -> None:
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO qa_brand_state
              (
                tenant_key,
                job_id,
                analysis_run_id,
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
                'tenant_a',
                :job_id,
                :analysis_run_id,
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
            "job_id": job_id,
            "analysis_run_id": analysis_run_id,
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


def test_sentiment_analysis_prefers_metric_snapshots_over_legacy_facts():
    engine = _build_engine()
    with Session(engine) as session:
        _seed_project_run(session)
        _seed_sentiment_snapshots(session)
        _insert_brand_state(session, conversation_id="legacy_negative", sentiment_status="negative")
        session.commit()

    client = _build_client(engine)
    response = client.get(
        "/api/v1/dashboard/sentiment-analysis",
        params={
            "tenant_key": "tenant_a",
            "job_id": "legacy_job_a",
            "timeframe": "specific_day",
            "start_date": "20260607",
            "end_date": "20260607",
            "brand": "Brand A",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["data_source"] == "metric_snapshot"
    assert payload["metadata"]["sample_count"] == 15

    distribution = {item["sentiment_status"]: item for item in payload["data"]["distribution"]}
    assert distribution["positive"]["answer_count"] == 7
    assert distribution["negative"]["answer_count"] == 5
    assert distribution["neutral"]["answer_count"] == 2
    assert distribution["unknown"]["answer_count"] == 1
    assert distribution["positive"]["ratio"] == 0.4667

    keyword_rows = payload["data"]["keywords"]
    assert keyword_rows[0]["keyword"] == "math"
    assert keyword_rows[0]["sentiment_status"] == "positive"
    assert keyword_rows[0]["answer_count"] == 6


def test_sentiment_analysis_falls_back_to_legacy_brand_facts():
    engine = _build_engine()
    with Session(engine) as session:
        _seed_tenant(session)
        _insert_brand_state(
            session,
            conversation_id="conv_positive",
            sentiment_status="positive",
            analysis_run_id=None,
        )
        _insert_brand_state(
            session,
            conversation_id="conv_negative",
            sentiment_status="negative",
            analysis_run_id=None,
        )
        _insert_brand_state(
            session,
            conversation_id="conv_neutral",
            sentiment_status="neutral",
            analysis_run_id=None,
        )
        session.commit()

    client = _build_client(engine)
    response = client.get(
        "/api/v1/dashboard/sentiment-analysis",
        params={
            "tenant_key": "tenant_a",
            "job_id": "legacy_job_a",
            "timeframe": "specific_day",
            "start_date": "20260607",
            "end_date": "20260607",
            "brand": "Brand A",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["data_source"] == "legacy_fact"
    assert payload["metadata"]["sample_count"] == 3
    assert {item["sentiment_status"] for item in payload["data"]["distribution"]} == {
        "negative",
        "neutral",
        "positive",
    }


def test_sentiment_analysis_returns_explicit_empty_state_for_missing_data():
    engine = _build_engine()
    with Session(engine) as session:
        _seed_tenant(session)

    client = _build_client(engine)
    response = client.get(
        "/api/v1/dashboard/sentiment-analysis",
        params={
            "tenant_key": "tenant_a",
            "job_id": "missing_job",
            "timeframe": "specific_day",
            "start_date": "20260607",
            "end_date": "20260607",
            "brand": "Brand A",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["distribution"] == []
    assert payload["data"]["keywords"] == []
    assert payload["metadata"]["data_source"] == "empty"
    assert payload["metadata"]["sample_count"] == 0
