import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from api.v1.repositories.connection import get_db
from api.v1.routes import projects
from api.v1.utils.jwt_utils import create_access_token
from api.v1.utils.security import hash_password
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQLITE_SCHEMA_FILE = PROJECT_ROOT / "api" / "database" / "schema_sqlite.sql"
MYSQL_SCHEMA_FILES = (
    PROJECT_ROOT / "api" / "database" / "schema.sql",
    PROJECT_ROOT / "api" / "database" / "schema_business.sql",
)
MYSQL_MIGRATION_FILE = (
    PROJECT_ROOT
    / "api"
    / "database"
    / "migrations"
    / "20260608_add_generated_reports.mysql.sql"
)
TEST_SECRET = "test-secret-with-at-least-32-bytes"


@pytest.fixture()
def report_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")
        raw_connection = conn.connection.driver_connection
        raw_connection.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))

    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _compact_sql(sql: str) -> str:
    return " ".join(sql.split())


def _table_section(sql: str, table_name: str) -> str:
    compact = _compact_sql(sql)
    marker = f"CREATE TABLE IF NOT EXISTS `{table_name}`"
    start = compact.find(marker)
    if start == -1:
        start = compact.find(f"CREATE TABLE `{table_name}`")
    assert start != -1, f"{table_name} table missing"
    next_table = compact.find(" CREATE TABLE", start + 1)
    return compact[start:] if next_table == -1 else compact[start:next_table]


def _client(db_session):
    app = FastAPI()
    app.include_router(projects.router, prefix="/api/v1/projects")
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


def _headers():
    token = create_access_token(101, TEST_SECRET)
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Key": "tenant_a",
    }


def _seed_project_lifecycle(session: Session, *, tenant_key: str = "tenant_a"):
    now = datetime(2026, 6, 8, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
            VALUES (:tenant_key, :tenant_name, 'active', :now, :now)
            """
        ),
        {
            "tenant_key": tenant_key,
            "tenant_name": f"{tenant_key} name",
            "now": now,
        },
    )
    session.execute(
        text(
            """
            INSERT INTO monitoring_projects
              (tenant_key, project_id, name, industry, category, status, created_at, updated_at)
            VALUES
              (:tenant_key, 'project_a', 'Project A', 'education', 'k12', 'active', :now, :now)
            """
        ),
        {"tenant_key": tenant_key, "now": now},
    )
    session.execute(
        text(
            """
            INSERT INTO prompt_sets
              (tenant_key, project_id, prompt_set_id, version, name, status, created_at, updated_at)
            VALUES
              (:tenant_key, 'project_a', 'prompt_set_a', 1, 'Prompt Set A', 'active', :now, :now)
            """
        ),
        {"tenant_key": tenant_key, "now": now},
    )
    for collection_job_id, analysis_run_id, day_offset in (
        ("collection_previous", "analysis_previous", -1),
        ("collection_current", "analysis_current", 0),
    ):
        metric_day = now + timedelta(days=day_offset)
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
                    window_start,
                    window_end,
                    expected_task_count,
                    succeeded_task_count,
                    failed_task_count,
                    created_at,
                    updated_at
                  )
                VALUES
                  (
                    :tenant_key,
                    :collection_job_id,
                    'project_a',
                    'prompt_set_a',
                    :source_job_id,
                    'succeeded',
                    :window_start,
                    :window_end,
                    10,
                    10,
                    0,
                    :now,
                    :now
                  )
                """
            ),
            {
                "tenant_key": tenant_key,
                "collection_job_id": collection_job_id,
                "source_job_id": f"legacy_{collection_job_id}",
                "window_start": metric_day - timedelta(hours=1),
                "window_end": metric_day + timedelta(hours=1),
                "now": now,
            },
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
                    started_at,
                    finished_at,
                    created_at,
                    updated_at
                  )
                VALUES
                  (
                    :tenant_key,
                    :analysis_run_id,
                    'project_a',
                    :collection_job_id,
                    'succeeded',
                    :now,
                    :now,
                    :now,
                    :now
                  )
                """
            ),
            {
                "tenant_key": tenant_key,
                "analysis_run_id": analysis_run_id,
                "collection_job_id": collection_job_id,
                "now": now,
            },
        )
    session.flush()


def _seed_user_tenant(session: Session):
    now = datetime(2026, 6, 8, 10, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO users (
                id, user_key, email, password_hash, is_verified, status, created_at, updated_at
            ) VALUES (
                101, 'user_101', 'member@example.com', :password_hash, 1, 'active', :now, :now
            )
            """
        ),
        {
            "password_hash": hash_password("User12345"),
            "now": now,
        },
    )
    tenant_id = session.execute(
        text("SELECT id FROM tenants WHERE tenant_key = 'tenant_a'")
    ).scalar_one()
    session.execute(
        text(
            """
            INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
            VALUES (101, :tenant_id, 'member', 'active', :now)
            """
        ),
        {
            "tenant_id": tenant_id,
            "now": now,
        },
    )
    session.flush()


def _insert_metric_snapshot(
    session: Session,
    *,
    tenant_key: str = "tenant_a",
    analysis_run_id: str = "analysis_current",
    metric_name: str,
    metric_value: float,
    suffix: str,
):
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
                :tenant_key,
                :snapshot_id,
                'project_a',
                :analysis_run_id,
                '2026-06-08',
                'brand_a',
                'Brand A',
                'deepseek',
                'math',
                :metric_name,
                :metric_value,
                'ratio',
                'brand_metrics_v1',
                10,
                10,
                0,
                10,
                1.000000,
                :analysis_run_id,
                'dim_brand_a_deepseek_math',
                '2026-06-08 12:00:00'
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "snapshot_id": f"snapshot_{suffix}",
            "analysis_run_id": analysis_run_id,
            "metric_name": metric_name,
            "metric_value": metric_value,
        },
    )


def _seed_metric_snapshots(session: Session):
    for metric_name, metric_value in (
        ("mention_rate", 0.600000),
        ("first_mention_rate", 0.300000),
        ("top3_mention_rate", 0.700000),
        ("sentiment_negative_ratio", 0.200000),
        ("reference_rate", 0.400000),
    ):
        _insert_metric_snapshot(
            session,
            metric_name=metric_name,
            metric_value=metric_value,
            suffix=metric_name,
        )


def _seed_alert_event(session: Session):
    now = datetime(2026, 6, 8, 13, 0, 0, tzinfo=UTC)
    session.execute(
        text(
            """
            INSERT INTO alert_rules
              (
                tenant_key,
                alert_rule_id,
                project_id,
                name,
                rule_type,
                metric_name,
                threshold_value,
                severity,
                status,
                created_at,
                updated_at
              )
            VALUES
              (
                'tenant_a',
                'rule_mention_drop',
                'project_a',
                'Mention rate drop',
                'metric_drop',
                'mention_rate',
                0.200000,
                'critical',
                'active',
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
            INSERT INTO alert_events
              (
                tenant_key,
                alert_event_id,
                alert_rule_id,
                project_id,
                analysis_run_id,
                collection_job_id,
                metric_date,
                metric_name,
                metric_definition_version,
                brand_id,
                brand_name,
                platform,
                keyword,
                dimension_hash,
                previous_metric_date,
                previous_value,
                current_value,
                delta_value,
                threshold_value,
                severity,
                event_status,
                title,
                message,
                triggered_at,
                created_at,
                updated_at
              )
            VALUES
              (
                'tenant_a',
                'event_mention_drop',
                'rule_mention_drop',
                'project_a',
                'analysis_current',
                'collection_current',
                '2026-06-08',
                'mention_rate',
                'brand_metrics_v1',
                'brand_a',
                'Brand A',
                'deepseek',
                'math',
                'dim_brand_a_deepseek_math',
                '2026-06-07',
                0.900000,
                0.600000,
                0.300000,
                0.200000,
                'critical',
                'open',
                'Mention rate drop',
                'Brand A mention rate dropped',
                :now,
                :now,
                :now
              )
            """
        ),
        {"now": now},
    )


def _seed_report_ready_project(session: Session):
    _seed_project_lifecycle(session)
    _seed_project_lifecycle(session, tenant_key="tenant_other")
    _seed_user_tenant(session)
    _seed_metric_snapshots(session)
    _seed_alert_event(session)
    session.commit()


def test_report_schema_declares_generated_reports():
    snippets = (
        "`report_id` varchar(128)",
        "`project_id` varchar(128)",
        "`report_type` varchar(32)",
        "`title` varchar(255)",
        "`timeframe` varchar(32)",
        "`start_date` date NOT NULL",
        "`end_date` date NOT NULL",
        "`summary_json` json NOT NULL",
        "`metrics_json` json NOT NULL",
        "`alerts_json` json",
        "UNIQUE KEY `uk_tenant_generated_report`",
        "KEY `idx_generated_reports_project_generated`",
        "FOREIGN KEY (`tenant_key`,`project_id`) REFERENCES `monitoring_projects`",
    )

    missing = []
    for schema_file in MYSQL_SCHEMA_FILES:
        sql = schema_file.read_text(encoding="utf-8")
        report_section = _table_section(sql, "generated_reports")
        missing_report = [snippet for snippet in snippets if snippet not in report_section]
        if missing_report:
            missing.append(
                {
                    "file": str(schema_file.relative_to(PROJECT_ROOT)),
                    "missing": missing_report,
                }
            )

    assert missing == []
    migration_sql = MYSQL_MIGRATION_FILE.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS `generated_reports`" in migration_sql


def test_sqlite_generated_reports_bind_to_project():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))

    now = "2026-06-08 10:00:00"
    connection.execute(
        """
        INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
        VALUES ('tenant_a', 'Tenant A', 'active', ?, ?)
        """,
        (now, now),
    )
    connection.execute(
        """
        INSERT INTO monitoring_projects
          (tenant_key, project_id, name, status, created_at, updated_at)
        VALUES ('tenant_a', 'project_a', 'Project A', 'active', ?, ?)
        """,
        (now, now),
    )
    connection.execute(
        """
        INSERT INTO generated_reports
          (
            tenant_key, report_id, project_id, report_type, title, timeframe,
            start_date, end_date, status, summary_json, metrics_json, alerts_json,
            generated_at, created_at, updated_at
          )
        VALUES
          (
            'tenant_a', 'report_a', 'project_a', 'project_summary', 'Weekly report',
            'custom', '2026-06-01', '2026-06-08', 'generated',
            '{"metric_count": 1}', '{"core_metrics": []}', '{"event_count": 0}',
            ?, ?, ?
          )
        """,
        (now, now, now),
    )
    row = connection.execute(
        """
        SELECT report_id, project_id, title, start_date, end_date
        FROM generated_reports
        """
    ).fetchone()
    assert row == ("report_a", "project_a", "Weekly report", "2026-06-01", "2026-06-08")

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO generated_reports
              (
                tenant_key, report_id, project_id, report_type, title, timeframe,
                start_date, end_date, status, summary_json, metrics_json, generated_at
              )
            VALUES
              (
                'tenant_a', 'report_missing_project', 'missing_project', 'project_summary',
                'Bad report', 'custom', '2026-06-01', '2026-06-08', 'generated',
                '{}', '{}', ?
              )
            """,
            (now,),
        )


def test_project_report_generation_persists_core_metrics_and_alert_window(
    report_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed_report_ready_project(report_session)
    client = _client(report_session)

    response = client.post(
        "/api/v1/projects/project_a/reports",
        headers=_headers(),
        json={
            "report_id": "report_weekly_a",
            "title": "Weekly brand health",
            "timeframe": "custom",
            "start_date": "2026-06-01",
            "end_date": "2026-06-08",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    report = body["report"]
    assert report["report_id"] == "report_weekly_a"
    assert report["tenant_key"] == "tenant_a"
    assert report["project_id"] == "project_a"
    assert report["start_date"] == "2026-06-01"
    assert report["end_date"] == "2026-06-08"
    assert report["summary"]["metric_count"] == 5
    assert report["summary"]["data_window"] == {
        "start_date": "2026-06-01",
        "end_date": "2026-06-08",
    }
    assert report["metrics"]["core_metrics"] == [
        {
            "brand_id": "brand_a",
            "brand_name": "Brand A",
            "metric_definition_version": "brand_metrics_v1",
            "analyzed_answer_count": 10,
            "mention_rate": 0.6,
            "first_mention_rate": 0.3,
            "top3_mention_rate": 0.7,
            "sentiment_negative_ratio": 0.2,
            "reference_rate": 0.4,
        }
    ]
    assert report["alerts"]["event_count"] == 1
    assert report["alerts"]["open_event_count"] == 1
    assert report["alerts"]["events"][0]["alert_event_id"] == "event_mention_drop"

    persisted = report_session.execute(
        text(
            """
            SELECT report_id, generated_by, summary_json, metrics_json, alerts_json
            FROM generated_reports
            WHERE tenant_key = 'tenant_a'
              AND project_id = 'project_a'
            """
        )
    ).mappings().one()
    assert persisted["report_id"] == "report_weekly_a"
    assert persisted["generated_by"] == 101
    assert "mention_rate" in persisted["metrics_json"]
    assert "event_mention_drop" in persisted["alerts_json"]


def test_project_reports_api_lists_only_current_tenant_reports(
    report_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed_report_ready_project(report_session)
    client = _client(report_session)
    client.post(
        "/api/v1/projects/project_a/reports",
        headers=_headers(),
        json={
            "report_id": "report_weekly_a",
            "title": "Weekly brand health",
            "start_date": "2026-06-01",
            "end_date": "2026-06-08",
        },
    )
    report_session.execute(
        text(
            """
            INSERT INTO generated_reports
              (
                tenant_key,
                report_id,
                project_id,
                report_type,
                title,
                timeframe,
                start_date,
                end_date,
                status,
                summary_json,
                metrics_json,
                alerts_json,
                generated_at
              )
            VALUES
              (
                'tenant_other',
                'report_other',
                'project_a',
                'project_summary',
                'Other tenant report',
                'custom',
                '2026-06-01',
                '2026-06-08',
                'generated',
                '{}',
                '{"core_metrics": []}',
                '{"event_count": 0}',
                '2026-06-08 12:00:00'
              )
            """
        )
    )
    report_session.commit()

    response = client.get("/api/v1/projects/project_a/reports", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["project_id"] == "project_a"
    assert body["count"] == 1
    assert body["reports"][0]["report_id"] == "report_weekly_a"
    assert body["reports"][0]["tenant_key"] == "tenant_a"
