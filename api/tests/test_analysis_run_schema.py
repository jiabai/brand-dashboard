import sqlite3
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MYSQL_SCHEMA_FILES = (
    PROJECT_ROOT / "api" / "database" / "schema.sql",
    PROJECT_ROOT / "api" / "database" / "schema_business.sql",
    PROJECT_ROOT / "analysis" / "database" / "schema.sql",
    PROJECT_ROOT / "analysis" / "database" / "schema_business.sql",
)
SQLITE_SCHEMA_FILE = PROJECT_ROOT / "api" / "database" / "schema_sqlite.sql"
MYSQL_MIGRATION_FILE = (
    PROJECT_ROOT
    / "api"
    / "database"
    / "migrations"
    / "20260607_add_analysis_run_model.mysql.sql"
)


def _compact_sql(sql: str) -> str:
    return " ".join(sql.split())


def test_mysql_schemas_declare_analysis_runs_model():
    expected_snippets = (
        "CREATE TABLE IF NOT EXISTS `analysis_runs`",
        "`analysis_run_id` varchar(128)",
        "`collection_job_id` varchar(128)",
        "`status` enum('pending','running','succeeded','failed','stale')",
        "`plugin_versions` json DEFAULT NULL",
        "`model_config_hash` varchar(128)",
        "`input_watermark` varchar(255)",
        "`error_message` text",
        "UNIQUE KEY `uk_tenant_analysis_run` (`tenant_key`,`analysis_run_id`)",
        "KEY `idx_analysis_runs_tenant_project_status` (`tenant_key`,`project_id`,`status`)",
        "KEY `idx_analysis_runs_collection_job` (`tenant_key`,`collection_job_id`)",
        (
            "CONSTRAINT `analysis_runs_ibfk_collection_job` FOREIGN KEY "
            "(`tenant_key`,`collection_job_id`) REFERENCES `collection_jobs` "
            "(`tenant_key`,`collection_job_id`) ON DELETE CASCADE"
        ),
    )

    missing = []
    for schema_file in MYSQL_SCHEMA_FILES:
        schema_sql = _compact_sql(schema_file.read_text(encoding="utf-8"))
        missing_snippets = [
            snippet for snippet in expected_snippets if snippet not in schema_sql
        ]
        if missing_snippets:
            missing.append(
                {
                    "file": str(schema_file.relative_to(PROJECT_ROOT)),
                    "missing": missing_snippets,
                }
            )

    assert missing == []


def _seed_collection_job(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO tenants (tenant_key, tenant_name, status)
        VALUES ('tenant_a', 'Tenant A', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO tenants (tenant_key, tenant_name, status)
        VALUES ('tenant_b', 'Tenant B', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO monitoring_projects
          (tenant_key, project_id, name, industry, category, status)
        VALUES
          ('tenant_a', 'proj_1', '品牌监测项目', '教育', 'K12', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO prompt_sets
          (tenant_key, project_id, prompt_set_id, version, name, status)
        VALUES
          ('tenant_a', 'proj_1', 'prompt_set_1', 1, '默认问题集', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO collection_jobs
          (
            tenant_key,
            collection_job_id,
            project_id,
            prompt_set_id,
            status,
            window_start,
            window_end,
            expected_task_count
          )
        VALUES
          (
            'tenant_a',
            'collection_job_1',
            'proj_1',
            'prompt_set_1',
            'succeeded',
            '2026-06-07 00:00:00',
            '2026-06-08 00:00:00',
            1
          )
        """
    )


def test_sqlite_schema_supports_analysis_run_relations_and_statuses():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))
    _seed_collection_job(connection)

    connection.execute(
        """
        INSERT INTO analysis_runs
          (
            tenant_key,
            analysis_run_id,
            project_id,
            collection_job_id,
            status,
            plugin_versions,
            model_config_hash,
            input_watermark
          )
        VALUES
          (
            'tenant_a',
            'analysis_run_1',
            'proj_1',
            'collection_job_1',
            'pending',
            '{"mention_status":"1.0.0"}',
            'model_hash_1',
            'collection_job_1:2026-06-07T00:00:00Z'
          )
        """
    )

    row = connection.execute(
        """
        SELECT tenant_key, analysis_run_id, project_id, collection_job_id, status
        FROM analysis_runs
        WHERE tenant_key = 'tenant_a'
          AND analysis_run_id = 'analysis_run_1'
        """
    ).fetchone()

    assert row == (
        "tenant_a",
        "analysis_run_1",
        "proj_1",
        "collection_job_1",
        "pending",
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO analysis_runs
              (tenant_key, analysis_run_id, project_id, collection_job_id, status)
            VALUES
              ('tenant_b', 'analysis_run_cross', 'proj_1', 'collection_job_1', 'pending')
            """
        )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO analysis_runs
              (tenant_key, analysis_run_id, project_id, collection_job_id, status)
            VALUES
              ('tenant_a', 'analysis_run_bad_status', 'proj_1', 'collection_job_1', 'queued')
            """
        )


def test_mysql_migration_creates_analysis_runs_model():
    migration_sql = _compact_sql(MYSQL_MIGRATION_FILE.read_text(encoding="utf-8"))

    assert "CREATE TABLE IF NOT EXISTS `analysis_runs`" in migration_sql
    assert "uk_tenant_analysis_run" in migration_sql
    assert "idx_analysis_runs_tenant_project_status" in migration_sql
    assert "idx_analysis_runs_collection_job" in migration_sql
    assert "analysis_runs_ibfk_collection_job" in migration_sql
