from datetime import UTC, date, datetime
from pathlib import Path

from api.v1.services.dashboard_service import DashboardService
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
    metric_date: str,
    brand_id: str,
    brand_name: str,
    platform: str,
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
                :metric_date,
                :brand_id,
                :brand_name,
                :platform,
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
            "metric_date": metric_date,
            "brand_id": brand_id,
            "brand_name": brand_name,
            "platform": platform,
            "keyword": keyword,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "analyzed_answer_count": analyzed_answer_count,
            "dimension_hash": dimension_hash,
        },
    )


def _seed_metric_snapshots(session: Session) -> None:
    rows = [
        ("math", "mention_rate", 0.9, 10, "dim_math"),
        ("math", "first_mention_rate", 0.4, 10, "dim_math"),
        ("math", "top3_mention_rate", 0.7, 10, "dim_math"),
        ("science", "mention_rate", 0.3, 10, "dim_science"),
        ("science", "first_mention_rate", 0.1, 10, "dim_science"),
        ("science", "top3_mention_rate", 0.2, 10, "dim_science"),
    ]
    for index, (keyword, metric_name, metric_value, analyzed_count, dimension_hash) in enumerate(
        rows,
        start=1,
    ):
        _insert_metric_snapshot(
            session,
            snapshot_id=f"snapshot_{index}",
            metric_date="2026-06-07",
            brand_id="brand_a",
            brand_name="Brand A",
            platform="deepseek",
            keyword=keyword,
            metric_name=metric_name,
            metric_value=metric_value,
            analyzed_answer_count=analyzed_count,
            dimension_hash=dimension_hash,
        )
    session.commit()


def _seed_legacy_brand_facts(
    session: Session,
    *,
    job_id: str = "legacy_job_a",
    analysis_run_id: str | None = "analysis_run_a",
) -> None:
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO qa_brand_state
              (
                job_id,
                tenant_key,
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
                :job_id,
                'tenant_a',
                :analysis_run_id,
                '2026-06-07',
                'legacy_conv_1',
                'Brand A',
                'education',
                'deepseek',
                'legacy',
                0,
                0,
                0,
                'neutral',
                '[]',
                :now,
                :now
              ),
              (
                :job_id,
                'tenant_a',
                :analysis_run_id,
                '2026-06-07',
                'legacy_conv_2',
                'Brand A',
                'education',
                'deepseek',
                'legacy',
                1,
                1,
                1,
                'positive',
                '["Brand A"]',
                :now,
                :now
              )
            """
        ),
        {"job_id": job_id, "analysis_run_id": analysis_run_id, "now": now},
    )
    session.commit()


def test_brand_metrics_prefers_metric_snapshots_over_legacy_facts():
    engine = _build_engine()
    with Session(engine) as session:
        _seed_project_run(session)
        _seed_metric_snapshots(session)
        _seed_legacy_brand_facts(session)

    service = DashboardService(engine)

    metrics = service.get_brand_metrics(
        tenant_key="tenant_a",
        job_id="legacy_job_a",
        query_start_date=date(2026, 6, 7),
        query_end_date=date(2026, 6, 7),
    )

    assert len(metrics) == 1
    metric = metrics[0]
    assert metric.brand == "Brand A"
    assert metric.mention_rate == 0.6
    assert metric.first_mention_rate == 0.25
    assert metric.top3_mention_rate == 0.45
    assert metric.prompt_count == 20
    assert metric.keyword_coverage == 2


def test_keyword_platform_brand_rates_prefers_metric_snapshots():
    engine = _build_engine()
    with Session(engine) as session:
        _seed_project_run(session)
        _seed_metric_snapshots(session)
        _seed_legacy_brand_facts(session)

    service = DashboardService(engine)

    rows = service.get_keyword_platform_brand_rates(
        tenant_key="tenant_a",
        job_id="legacy_job_a",
        query_start_date=date(2026, 6, 7),
        query_end_date=date(2026, 6, 7),
    )

    assert [row.keyword for row in rows] == ["math", "science"]
    assert rows[0].platform == "deepseek"
    assert rows[0].brand == "Brand A"
    assert rows[0].mention_rate == 0.9
    assert rows[0].first_mention_rate == 0.4
    assert rows[0].top3_mention_rate == 0.7
    assert rows[1].mention_rate == 0.3


def test_brand_mention_trend_prefers_metric_snapshots():
    engine = _build_engine()
    with Session(engine) as session:
        _seed_project_run(session)
        _seed_metric_snapshots(session)
        _seed_legacy_brand_facts(session)

    service = DashboardService(engine)

    rows = service.get_brand_mention_trend(
        tenant_key="tenant_a",
        job_id="legacy_job_a",
        brand="Brand A",
        platform="deepseek",
        keyword="math",
        query_start_date=date(2026, 6, 7),
        query_end_date=date(2026, 6, 7),
    )

    assert len(rows) == 1
    assert rows[0].date == "20260607"
    assert rows[0].brand == "Brand A"
    assert rows[0].platform == "deepseek"
    assert rows[0].keyword == "math"
    assert rows[0].mention_rate == 0.9


def test_platform_metrics_by_brand_prefers_metric_snapshots():
    engine = _build_engine()
    with Session(engine) as session:
        _seed_project_run(session)
        _seed_metric_snapshots(session)
        _seed_legacy_brand_facts(session)

    service = DashboardService(engine)

    data = service.get_platform_metrics_by_brand(
        tenant_key="tenant_a",
        job_id="legacy_job_a",
        brand="Brand A",
        query_start_date=date(2026, 6, 7),
        query_end_date=date(2026, 6, 7),
    )

    assert data.brand == "Brand A"
    assert len(data.platforms) == 1
    assert data.platforms[0].platform == "deepseek"
    assert data.platforms[0].mention_rate == 0.6


def test_brand_metrics_falls_back_to_legacy_aggregation_when_snapshots_are_missing():
    engine = _build_engine()
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    with Session(engine) as session:
        session.execute(
            text(
                """
                INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
                VALUES ('tenant_a', 'Tenant A', 'active', :now, :now)
                """
            ),
            {"now": now},
        )
        _seed_legacy_brand_facts(
            session,
            job_id="legacy_job_without_snapshot",
            analysis_run_id=None,
        )

    service = DashboardService(engine)

    metrics = service.get_brand_metrics(
        tenant_key="tenant_a",
        job_id="legacy_job_without_snapshot",
        query_start_date=date(2026, 6, 7),
        query_end_date=date(2026, 6, 7),
    )

    assert len(metrics) == 1
    metric = metrics[0]
    assert metric.brand == "Brand A"
    assert metric.mention_rate == 0.5
    assert metric.first_mention_rate == 0.5
    assert metric.top3_mention_rate == 0.5
    assert metric.prompt_count == 2
    assert metric.keyword_coverage == 1


def test_metric_snapshot_metadata_exposes_freshness_coverage_and_completeness():
    engine = _build_engine()
    with Session(engine) as session:
        _seed_project_run(session)
        _seed_metric_snapshots(session)

    service = DashboardService(engine)

    metadata = service.get_metric_snapshot_metadata(
        tenant_key="tenant_a",
        job_id="legacy_job_a",
        query_start_date=date(2026, 6, 7),
        query_end_date=date(2026, 6, 7),
    )

    assert metadata["data_source"] == "metric_snapshot"
    assert metadata["snapshot_status"] == "available"
    assert metadata["metric_definition_version"] == "brand_metrics_v1"
    assert metadata["analysis_run_id"] == "analysis_run_a"
    assert metadata["metric_generated_at"] == "2026-06-07 11:00:00"
    assert metadata["metric_coverage_rate"] == 1.0
    assert metadata["metric_expected_task_count"] == 20
    assert metadata["metric_succeeded_task_count"] == 20
    assert metadata["metric_failed_task_count"] == 0
    assert metadata["metric_analyzed_answer_count"] == 20
    assert metadata["metric_snapshot_count"] == 6
    assert metadata["metric_dimension_count"] == 2


def test_metric_snapshot_metadata_marks_legacy_fallback_when_snapshot_is_missing():
    engine = _build_engine()
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    with Session(engine) as session:
        session.execute(
            text(
                """
                INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
                VALUES ('tenant_a', 'Tenant A', 'active', :now, :now)
                """
            ),
            {"now": now},
        )
        _seed_legacy_brand_facts(
            session,
            job_id="legacy_job_without_snapshot",
            analysis_run_id=None,
        )

    service = DashboardService(engine)

    metadata = service.get_metric_snapshot_metadata(
        tenant_key="tenant_a",
        job_id="legacy_job_without_snapshot",
        query_start_date=date(2026, 6, 7),
        query_end_date=date(2026, 6, 7),
    )

    assert metadata["data_source"] == "legacy_aggregation"
    assert metadata["snapshot_status"] == "missing"
    assert metadata["metric_generated_at"] is None
    assert metadata["metric_coverage_rate"] is None
