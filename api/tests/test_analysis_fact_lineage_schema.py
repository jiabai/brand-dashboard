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
    / "20260607_add_analysis_run_id_to_analysis_facts.mysql.sql"
)


def _compact_sql(sql: str) -> str:
    return " ".join(sql.split())


def _table_section(sql: str, table_name: str) -> str:
    compact = _compact_sql(sql)
    marker = "CREATE TABLE"
    start = compact.find(f"{marker} `{table_name}`")
    if start == -1:
        start = compact.find(f"{marker} IF NOT EXISTS `{table_name}`")
    assert start != -1, f"{table_name} table missing"
    next_table = compact.find(" CREATE TABLE", start + 1)
    return compact[start:] if next_table == -1 else compact[start:next_table]


def test_mysql_fact_tables_declare_analysis_run_lineage():
    expected = {
        "qa_brand_state": (
            "`analysis_run_id` varchar(128)",
            "KEY `idx_qbrs_analysis_run` (`tenant_key`,`analysis_run_id`)",
            (
                "CONSTRAINT `qa_brand_state_ibfk_analysis_run` FOREIGN KEY "
                "(`tenant_key`,`analysis_run_id`) REFERENCES `analysis_runs` "
                "(`tenant_key`,`analysis_run_id`)"
            ),
        ),
        "qa_reference": (
            "`analysis_run_id` varchar(128)",
            "KEY `idx_qr_analysis_run` (`tenant_key`,`analysis_run_id`)",
            (
                "CONSTRAINT `qa_reference_ibfk_analysis_run` FOREIGN KEY "
                "(`tenant_key`,`analysis_run_id`) REFERENCES `analysis_runs` "
                "(`tenant_key`,`analysis_run_id`)"
            ),
        ),
    }

    missing = []
    for schema_file in MYSQL_SCHEMA_FILES:
        schema_sql = schema_file.read_text(encoding="utf-8")
        for table_name, snippets in expected.items():
            section = _table_section(schema_sql, table_name)
            missing_snippets = [
                snippet for snippet in snippets if snippet not in section
            ]
            if missing_snippets:
                missing.append(
                    {
                        "file": str(schema_file.relative_to(PROJECT_ROOT)),
                        "table": table_name,
                        "missing": missing_snippets,
                    }
                )

    assert missing == []


def test_sqlite_fact_tables_bind_to_analysis_run():
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
          ('tenant_a', 'proj_a', 'Project A', 'education', 'k12', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO prompt_sets
          (tenant_key, project_id, prompt_set_id, version, name, status)
        VALUES
          ('tenant_a', 'proj_a', 'prompt_set_a', 1, 'Prompt Set A', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO collection_jobs
          (tenant_key, collection_job_id, project_id, prompt_set_id, status)
        VALUES
          ('tenant_a', 'collection_job_a', 'proj_a', 'prompt_set_a', 'succeeded')
        """
    )
    connection.execute(
        """
        INSERT INTO analysis_runs
          (tenant_key, analysis_run_id, project_id, collection_job_id, status)
        VALUES
          ('tenant_a', 'analysis_run_a', 'proj_a', 'collection_job_a', 'running')
        """
    )

    connection.execute(
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
            sentiment_status
          )
        VALUES
          (
            'tenant_a',
            'legacy_job_a',
            'analysis_run_a',
            '2026-06-07',
            'conv_a',
            '品牌A',
            '教育',
            'deepseek',
            '数学',
            1,
            1,
            1,
            'positive'
          )
        """
    )
    connection.execute(
        """
        INSERT INTO qa_reference
          (
            tenant_key,
            job_id,
            analysis_run_id,
            date,
            conversation_id,
            platform,
            brand,
            category,
            keyword,
            query_content,
            url,
            is_published_link
          )
        VALUES
          (
            'tenant_a',
            'legacy_job_a',
            'analysis_run_a',
            '2026-06-07',
            'conv_a',
            'deepseek',
            '品牌A',
            '教育',
            '数学',
            '数学培训哪家好',
            'https://example.com/a',
            0
          )
        """
    )

    fact_lineage = connection.execute(
        """
        SELECT qbs.analysis_run_id, qr.analysis_run_id
        FROM qa_brand_state qbs
        JOIN qa_reference qr
          ON qr.tenant_key = qbs.tenant_key
         AND qr.conversation_id = qbs.conversation_id
        """
    ).fetchone()
    assert fact_lineage == ("analysis_run_a", "analysis_run_a")

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
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
                sentiment_status
              )
            VALUES
              (
                'tenant_a',
                'legacy_job_a',
                'missing_run',
                '2026-06-07',
                'conv_b',
                '品牌A',
                '教育',
                'deepseek',
                '数学',
                'unknown'
              )
            """
        )


def test_mysql_migration_adds_analysis_run_lineage_to_fact_tables():
    migration_sql = MYSQL_MIGRATION_FILE.read_text(encoding="utf-8")

    assert "ALTER TABLE `qa_brand_state`" in migration_sql
    assert "ADD COLUMN `analysis_run_id`" in migration_sql
    assert "idx_qbrs_analysis_run" in migration_sql
    assert "qa_brand_state_ibfk_analysis_run" in migration_sql
    assert "ALTER TABLE `qa_reference`" in migration_sql
    assert "idx_qr_analysis_run" in migration_sql
    assert "qa_reference_ibfk_analysis_run" in migration_sql
