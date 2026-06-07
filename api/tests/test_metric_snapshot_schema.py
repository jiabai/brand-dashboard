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
    / "20260607_add_metric_snapshots.mysql.sql"
)


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


def test_mysql_metric_snapshots_declares_dashboard_read_model_fields():
    required_snippets = (
        "`snapshot_id` varchar(128)",
        "`project_id` varchar(128)",
        "`analysis_run_id` varchar(128)",
        "`metric_date` date NOT NULL",
        "`brand_id` varchar(128)",
        "`brand_name` varchar(255)",
        "`platform` varchar(64)",
        "`keyword` varchar(100)",
        "`metric_name` varchar(64)",
        "`metric_value` decimal(18,6) NOT NULL",
        "`metric_definition_version` varchar(32)",
        "`expected_task_count` int(11) NOT NULL DEFAULT '0'",
        "`succeeded_task_count` int(11) NOT NULL DEFAULT '0'",
        "`failed_task_count` int(11) NOT NULL DEFAULT '0'",
        "`analyzed_answer_count` int(11) NOT NULL DEFAULT '0'",
        "`coverage_rate` decimal(8,6)",
        "`source_watermark` varchar(255)",
        "`dimension_hash` varchar(64)",
        "`generated_at` timestamp NOT NULL",
        "UNIQUE KEY `uk_metric_snapshots_identity`",
        "KEY `idx_metric_snapshots_analysis_run` (`tenant_key`,`analysis_run_id`)",
        (
            "CONSTRAINT `metric_snapshots_ibfk_analysis_run` FOREIGN KEY "
            "(`tenant_key`,`analysis_run_id`) REFERENCES `analysis_runs` "
            "(`tenant_key`,`analysis_run_id`)"
        ),
    )

    missing = []
    for schema_file in MYSQL_SCHEMA_FILES:
        section = _table_section(schema_file.read_text(encoding="utf-8"), "metric_snapshots")
        missing_snippets = [
            snippet for snippet in required_snippets if snippet not in section
        ]
        if missing_snippets:
            missing.append(
                {
                    "file": str(schema_file.relative_to(PROJECT_ROOT)),
                    "missing": missing_snippets,
                }
            )

    assert missing == []


def test_sqlite_metric_snapshots_bind_to_project_and_analysis_run():
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))

    connection.execute(
        """
        INSERT INTO tenants (tenant_key, tenant_name, status)
        VALUES ('tenant_a', 'Tenant A', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO monitoring_projects
          (tenant_key, project_id, name, industry, category, status)
        VALUES
          ('tenant_a', 'project_a', 'Project A', 'education', 'k12', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO prompt_sets
          (tenant_key, project_id, prompt_set_id, version, name, status)
        VALUES
          ('tenant_a', 'project_a', 'prompt_set_a', 1, 'Prompt Set A', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO collection_jobs
          (tenant_key, collection_job_id, project_id, prompt_set_id, status)
        VALUES
          ('tenant_a', 'collection_job_a', 'project_a', 'prompt_set_a', 'succeeded')
        """
    )
    connection.execute(
        """
        INSERT INTO analysis_runs
          (tenant_key, analysis_run_id, project_id, collection_job_id, status)
        VALUES
          ('tenant_a', 'analysis_run_a', 'project_a', 'collection_job_a', 'succeeded')
        """
    )

    insert_snapshot_sql = """
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
            'snapshot_a',
            'project_a',
            'analysis_run_a',
            '2026-06-07',
            'brand_a',
            '品牌A',
            'deepseek',
            '数学',
            'mention_rate',
            0.850000,
            'ratio',
            'brand_metrics_v1',
            10,
            9,
            1,
            9,
            0.900000,
            'legacy_job_a:2026-06-07T10:00:00+00:00',
            'dim_hash_a',
            '2026-06-07 11:00:00'
          )
        """
    connection.execute(insert_snapshot_sql)

    row = connection.execute(
        """
        SELECT
          metric_name,
          metric_value,
          metric_date,
          brand_id,
          platform,
          keyword,
          metric_definition_version,
          analysis_run_id,
          coverage_rate
        FROM metric_snapshots
        """
    ).fetchone()
    assert row == (
        "mention_rate",
        0.85,
        "2026-06-07",
        "brand_a",
        "deepseek",
        "数学",
        "brand_metrics_v1",
        "analysis_run_a",
        0.9,
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(insert_snapshot_sql)

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            insert_snapshot_sql.replace("analysis_run_a", "missing_analysis_run")
        )


def test_mysql_migration_creates_metric_snapshots():
    migration_sql = MYSQL_MIGRATION_FILE.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS `metric_snapshots`" in migration_sql
    assert "`metric_name` varchar(64)" in migration_sql
    assert "`metric_value` decimal(18,6) NOT NULL" in migration_sql
    assert "`metric_definition_version` varchar(32)" in migration_sql
    assert "`analysis_run_id` varchar(128)" in migration_sql
    assert "`coverage_rate` decimal(8,6)" in migration_sql
    assert "uk_metric_snapshots_identity" in migration_sql
    assert "metric_snapshots_ibfk_analysis_run" in migration_sql
