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
    / "20260607_add_alert_rules_and_events.mysql.sql"
)
TEST_SECRET = "test-secret-with-at-least-32-bytes"


@pytest.fixture()
def alert_session():
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


def _seed_project_lifecycle(session: Session, *, tenant_key: str = "tenant_a"):
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    tenant_name = f"{tenant_key} name"
    session.execute(
        text(
            """
            INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
            VALUES (:tenant_key, :tenant_name, 'active', :now, :now)
            """
        ),
        {"tenant_key": tenant_key, "tenant_name": tenant_name, "now": now},
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
        metric_day = datetime(2026, 6, 7 + day_offset, 10, 0, 0, tzinfo=UTC)
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


def _insert_metric_snapshot(
    session: Session,
    *,
    tenant_key: str = "tenant_a",
    analysis_run_id: str,
    metric_date: str,
    metric_name: str,
    metric_value: float,
    snapshot_suffix: str,
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
                :metric_date,
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
                '2026-06-07 12:00:00'
              )
            """
        ),
        {
            "tenant_key": tenant_key,
            "snapshot_id": f"snapshot_{snapshot_suffix}",
            "analysis_run_id": analysis_run_id,
            "metric_date": metric_date,
            "metric_name": metric_name,
            "metric_value": metric_value,
        },
    )


def _seed_alert_rules(session: Session):
    now = datetime(2026, 6, 7, 12, 0, 0, tzinfo=UTC)
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
                metric_definition_version,
                brand_id,
                brand_name,
                platform,
                keyword,
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
                'brand_metrics_v1',
                'brand_a',
                'Brand A',
                'deepseek',
                'math',
                0.200000,
                'critical',
                'active',
                :now,
                :now
              ),
              (
                'tenant_a',
                'rule_negative_rise',
                'project_a',
                'Negative sentiment rise',
                'metric_rise',
                'sentiment_negative_ratio',
                'brand_metrics_v1',
                'brand_a',
                'Brand A',
                'deepseek',
                'math',
                0.200000,
                'warning',
                'active',
                :now,
                :now
              )
            """
        ),
        {"now": now},
    )


def _seed_snapshot_changes(session: Session):
    _seed_project_lifecycle(session)
    _insert_metric_snapshot(
        session,
        analysis_run_id="analysis_previous",
        metric_date="2026-06-06",
        metric_name="mention_rate",
        metric_value=0.800000,
        snapshot_suffix="prev_mention",
    )
    _insert_metric_snapshot(
        session,
        analysis_run_id="analysis_current",
        metric_date="2026-06-07",
        metric_name="mention_rate",
        metric_value=0.500000,
        snapshot_suffix="curr_mention",
    )
    _insert_metric_snapshot(
        session,
        analysis_run_id="analysis_previous",
        metric_date="2026-06-06",
        metric_name="sentiment_negative_ratio",
        metric_value=0.100000,
        snapshot_suffix="prev_negative",
    )
    _insert_metric_snapshot(
        session,
        analysis_run_id="analysis_current",
        metric_date="2026-06-07",
        metric_name="sentiment_negative_ratio",
        metric_value=0.400000,
        snapshot_suffix="curr_negative",
    )
    _seed_alert_rules(session)
    session.commit()


def _seed_user_tenant(session: Session):
    now = datetime(2026, 6, 7, 10, 0, 0, tzinfo=UTC)
    result = session.execute(
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
    return result.lastrowid or 101


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


def test_alert_schema_declares_rules_and_events():
    rule_snippets = (
        "`alert_rule_id` varchar(128)",
        "`project_id` varchar(128)",
        "`rule_type` varchar(32)",
        "`metric_name` varchar(64)",
        "`threshold_value` decimal(18,6) NOT NULL",
        "`severity` varchar(20)",
        "`status` varchar(20)",
        "UNIQUE KEY `uk_alert_rules_identity`",
        "KEY `idx_alert_rules_project_status`",
        "FOREIGN KEY (`tenant_key`,`project_id`) REFERENCES `monitoring_projects`",
    )
    event_snippets = (
        "`alert_event_id` varchar(128)",
        "`alert_rule_id` varchar(128)",
        "`analysis_run_id` varchar(128)",
        "`collection_job_id` varchar(128)",
        "`previous_value` decimal(18,6)",
        "`current_value` decimal(18,6) NOT NULL",
        "`delta_value` decimal(18,6) NOT NULL",
        "`event_status` varchar(20)",
        "UNIQUE KEY `uk_alert_events_dedupe`",
        "KEY `idx_alert_events_project_status`",
        "FOREIGN KEY (`tenant_key`,`analysis_run_id`) REFERENCES `analysis_runs`",
    )

    missing = []
    for schema_file in MYSQL_SCHEMA_FILES:
        sql = schema_file.read_text(encoding="utf-8")
        rule_section = _table_section(sql, "alert_rules")
        event_section = _table_section(sql, "alert_events")
        missing_rule = [snippet for snippet in rule_snippets if snippet not in rule_section]
        missing_event = [snippet for snippet in event_snippets if snippet not in event_section]
        if missing_rule or missing_event:
            missing.append(
                {
                    "file": str(schema_file.relative_to(PROJECT_ROOT)),
                    "missing_rules": missing_rule,
                    "missing_events": missing_event,
                }
            )

    assert missing == []
    migration_sql = MYSQL_MIGRATION_FILE.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS `alert_rules`" in migration_sql
    assert "CREATE TABLE IF NOT EXISTS `alert_events`" in migration_sql


def test_sqlite_alert_events_bind_to_project_rule_and_analysis_run():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))

    raw = connection
    now = "2026-06-07 10:00:00"
    raw.execute(
        """
        INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
        VALUES ('tenant_a', 'Tenant A', 'active', ?, ?)
        """,
        (now, now),
    )
    raw.execute(
        """
        INSERT INTO monitoring_projects
          (tenant_key, project_id, name, status, created_at, updated_at)
        VALUES ('tenant_a', 'project_a', 'Project A', 'active', ?, ?)
        """,
        (now, now),
    )
    raw.execute(
        """
        INSERT INTO prompt_sets
          (tenant_key, project_id, prompt_set_id, version, status, created_at, updated_at)
        VALUES ('tenant_a', 'project_a', 'prompt_set_a', 1, 'active', ?, ?)
        """,
        (now, now),
    )
    raw.execute(
        """
        INSERT INTO collection_jobs
          (tenant_key, collection_job_id, project_id, prompt_set_id, status, created_at, updated_at)
        VALUES ('tenant_a', 'collection_a', 'project_a', 'prompt_set_a', 'succeeded', ?, ?)
        """,
        (now, now),
    )
    raw.execute(
        """
        INSERT INTO analysis_runs
          (
            tenant_key,
            analysis_run_id,
            project_id,
            collection_job_id,
            status,
            created_at,
            updated_at
          )
        VALUES
          (
            'tenant_a',
            'analysis_a',
            'project_a',
            'collection_a',
            'succeeded',
            ?,
            ?
          )
        """,
        (now, now),
    )
    raw.execute(
        """
        INSERT INTO alert_rules
          (
            tenant_key, alert_rule_id, project_id, name, rule_type, metric_name,
            threshold_value, severity, status, created_at, updated_at
          )
        VALUES
          (
            'tenant_a', 'rule_a', 'project_a', 'Mention drop', 'metric_drop',
            'mention_rate', 0.200000, 'critical', 'active', ?, ?
          )
        """,
        (now, now),
    )
    raw.execute(
        """
        INSERT INTO alert_events
          (
            tenant_key, alert_event_id, alert_rule_id, project_id, analysis_run_id,
            collection_job_id, metric_date, metric_name, metric_definition_version,
            brand_id, brand_name, platform, keyword, dimension_hash,
            previous_metric_date, previous_value, current_value, delta_value,
            threshold_value, severity, event_status, title, message, triggered_at,
            created_at, updated_at
          )
        VALUES
          (
            'tenant_a', 'event_a', 'rule_a', 'project_a', 'analysis_a',
            'collection_a', '2026-06-07', 'mention_rate', 'brand_metrics_v1',
            'brand_a', 'Brand A', 'deepseek', 'math', 'dim_a',
            '2026-06-06', 0.800000, 0.500000, 0.300000,
            0.200000, 'critical', 'open', 'Mention rate drop',
            'Brand A mention rate dropped', ?, ?, ?
          )
        """,
        (now, now, now),
    )

    row = raw.execute(
        """
        SELECT alert_event_id, alert_rule_id, project_id, analysis_run_id, delta_value
        FROM alert_events
        """
    ).fetchone()
    assert row == ("event_a", "rule_a", "project_a", "analysis_a", 0.3)

    with pytest.raises(sqlite3.IntegrityError):
        raw.execute(
            """
            INSERT INTO alert_events
              (
                tenant_key, alert_event_id, alert_rule_id, project_id, analysis_run_id,
                collection_job_id, metric_date, metric_name, metric_definition_version,
                brand_id, platform, keyword, dimension_hash, current_value,
                delta_value, threshold_value, severity, title, message, triggered_at
              )
            VALUES
              (
                'tenant_a', 'event_missing_run', 'rule_a', 'project_a', 'missing_run',
                'collection_a', '2026-06-07', 'mention_rate', 'brand_metrics_v1',
                'brand_a', 'deepseek', 'math', 'dim_a', 0.500000,
                0.300000, 0.200000, 'critical', 'Missing run', 'bad', ?
              )
            """,
            (now,),
        )


def test_alert_rule_evaluation_records_metric_drop_and_rise_events(alert_session):
    from api.v1.services import alerts

    _seed_snapshot_changes(alert_session)

    result = alerts.evaluate_alert_rules_for_analysis_run(
        alert_session,
        tenant_key="tenant_a",
        analysis_run_id="analysis_current",
        triggered_at=datetime(2026, 6, 7, 13, 0, 0, tzinfo=UTC),
    )

    assert result.status_code == 200
    assert result.created_event_count == 2
    assert result.matched_rule_count == 2

    rows = alert_session.execute(
        text(
            """
            SELECT
              alert_rule_id,
              metric_name,
              previous_value,
              current_value,
              delta_value,
              threshold_value,
              severity,
              event_status
            FROM alert_events
            WHERE tenant_key = 'tenant_a'
            ORDER BY alert_rule_id
            """
        )
    ).all()
    assert len(rows) == 2
    assert rows[0].alert_rule_id == "rule_mention_drop"
    assert rows[0].metric_name == "mention_rate"
    assert rows[0].previous_value == pytest.approx(0.8)
    assert rows[0].current_value == pytest.approx(0.5)
    assert rows[0].delta_value == pytest.approx(0.3)
    assert rows[0].severity == "critical"
    assert rows[0].event_status == "open"
    assert rows[1].alert_rule_id == "rule_negative_rise"
    assert rows[1].metric_name == "sentiment_negative_ratio"
    assert rows[1].delta_value == pytest.approx(0.3)

    second_result = alerts.evaluate_alert_rules_for_analysis_run(
        alert_session,
        tenant_key="tenant_a",
        analysis_run_id="analysis_current",
        triggered_at=datetime(2026, 6, 7, 14, 0, 0, tzinfo=UTC),
    )
    assert second_result.status_code == 200
    assert second_result.created_event_count == 0
    assert alert_session.execute(text("SELECT COUNT(*) FROM alert_events")).scalar_one() == 2


def test_project_alerts_api_lists_current_tenant_rules_and_events(
    alert_session,
    monkeypatch,
):
    monkeypatch.setenv("AUTH_SECRET", TEST_SECRET)
    _seed_snapshot_changes(alert_session)
    _seed_project_lifecycle(alert_session, tenant_key="tenant_other")
    _seed_user_tenant(alert_session)
    from api.v1.services import alerts

    alerts.evaluate_alert_rules_for_analysis_run(
        alert_session,
        tenant_key="tenant_a",
        analysis_run_id="analysis_current",
        triggered_at=datetime(2026, 6, 7, 13, 0, 0, tzinfo=UTC),
    )
    client = _client(alert_session)

    response = client.get("/api/v1/projects/project_a/alerts", headers=_headers())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["project_id"] == "project_a"
    assert body["rule_count"] == 2
    assert body["event_count"] == 2
    assert {event["alert_rule_id"] for event in body["events"]} == {
        "rule_mention_drop",
        "rule_negative_rise",
    }
    assert all(event["tenant_key"] == "tenant_a" for event in body["events"])
