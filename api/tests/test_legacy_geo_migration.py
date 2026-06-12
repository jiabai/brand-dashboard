import importlib.util
import sqlite3
from pathlib import Path

from api.v1.repositories.fact_metrics import list_project_fact_metric_rows
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_SCRIPT = PROJECT_ROOT / "scripts" / "migrate_legacy_geo_sqlite.py"
SQLITE_SCHEMA = PROJECT_ROOT / "api" / "database" / "schema_sqlite.sql"


def _load_migration_module():
    spec = importlib.util.spec_from_file_location("migrate_legacy_geo_sqlite", MIGRATION_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _create_legacy_source(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE tenants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_key VARCHAR(255) NOT NULL UNIQUE,
            tenant_name VARCHAR(255) NOT NULL UNIQUE,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE TABLE executors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            executor_id VARCHAR(128) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(64),
            status VARCHAR(20),
            ip_address VARCHAR(45) NOT NULL,
            api_key VARCHAR(255),
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE TABLE llm_query_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_key VARCHAR(255) NOT NULL,
            job_id VARCHAR(255) NOT NULL,
            category VARCHAR(64) NOT NULL,
            brand VARCHAR(50),
            competitor TEXT,
            keyword VARCHAR(100) NOT NULL,
            query_content TEXT NOT NULL,
            query_status INTEGER NOT NULL DEFAULT 0,
            executor_id VARCHAR(128),
            total_runs INTEGER NOT NULL DEFAULT 15,
            executed_runs INTEGER NOT NULL DEFAULT 0,
            last_executed_date DATE,
            effective_from TIMESTAMP NOT NULL,
            effective_to TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            is_deleted INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE llm_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_key VARCHAR(255) NOT NULL,
            job_id VARCHAR(255) NOT NULL,
            conversation_id VARCHAR(255) NOT NULL,
            platform VARCHAR(64) NOT NULL,
            brand VARCHAR(50),
            category VARCHAR(64) NOT NULL,
            keyword VARCHAR(100) NOT NULL,
            query_content TEXT NOT NULL,
            answer_content TEXT NOT NULL,
            generated_date DATE,
            extracted_at TIMESTAMP,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE TABLE qa_brand_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id VARCHAR(255) NOT NULL,
            tenant_key VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            conversation_id VARCHAR(255) NOT NULL,
            brand VARCHAR(50) NOT NULL,
            category VARCHAR(64) NOT NULL,
            platform VARCHAR(64) NOT NULL,
            keyword VARCHAR(100) NOT NULL,
            is_mentioned INTEGER NOT NULL DEFAULT 0,
            is_first_mentioned INTEGER NOT NULL DEFAULT 0,
            is_top3_mentioned INTEGER NOT NULL DEFAULT 0,
            sentiment_status VARCHAR(20) NOT NULL,
            brands_found TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE TABLE qa_reference (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id VARCHAR(255) NOT NULL,
            tenant_key VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            conversation_id VARCHAR(255) NOT NULL,
            platform VARCHAR(64) NOT NULL,
            brand VARCHAR(50),
            category VARCHAR(64) NOT NULL,
            keyword VARCHAR(100) NOT NULL,
            query_content TEXT NOT NULL,
            url VARCHAR(1024) NOT NULL,
            is_published_link INTEGER NOT NULL DEFAULT 0,
            domain VARCHAR(64),
            content_type VARCHAR(50),
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        """
    )
    con.execute(
        """
        INSERT INTO tenants (tenant_key, tenant_name, status, created_at, updated_at)
        VALUES ('tn_demo', 'Demo Tenant', 'active', '2026-01-01', '2026-01-01')
        """
    )
    con.execute(
        """
        INSERT INTO executors (
            executor_id, name, type, status, ip_address, api_key, created_at, updated_at
        )
        VALUES ('exec_demo', 'Demo Executor', 'local', 'active', '127.0.0.1', 'secret',
                '2026-01-01', '2026-01-01')
        """
    )
    con.execute(
        """
        INSERT INTO llm_query_jobs (
            tenant_key, job_id, category, brand, competitor, keyword, query_content,
            query_status, executor_id, total_runs, executed_runs, effective_from,
            created_at, updated_at, is_deleted
        )
        VALUES (
            'tn_demo', 'job_with_facts', 'CX', 'QuickCEP', '["Zendesk"]',
            'support', 'Which support tool is best?', 2, 'exec_demo', 1, 1,
            '2026-01-01', '2026-01-01', '2026-01-01', 0
        )
        """
    )
    con.execute(
        """
        INSERT INTO llm_query_jobs (
            tenant_key, job_id, category, brand, competitor, keyword, query_content,
            query_status, executor_id, total_runs, executed_runs, effective_from,
            created_at, updated_at, is_deleted
        )
        VALUES (
            'tn_demo', 'job_config_only', 'CX', 'ConfigOnlyBrand', '[]',
            'routing', 'Which routing tool is best?', 1, 'exec_demo', 1, 0,
            '2026-02-01', '2026-02-01', '2026-02-01', 0
        )
        """
    )
    con.execute(
        """
        INSERT INTO llm_conversations (
            tenant_key, job_id, conversation_id, platform, brand, category, keyword,
            query_content, answer_content, generated_date, extracted_at, created_at, updated_at
        )
        VALUES (
            'tn_demo', 'job_with_facts', 'conv_1', 'deepseek', 'QuickCEP', 'CX',
            'support', 'Which support tool is best?', 'QuickCEP is mentioned.',
            '2026-01-02', '2026-01-02', '2026-01-02', '2026-01-02'
        )
        """
    )
    con.executemany(
        """
        INSERT INTO qa_brand_state (
            job_id, tenant_key, date, conversation_id, brand, category, platform, keyword,
            is_mentioned, is_first_mentioned, is_top3_mentioned, sentiment_status,
            brands_found, created_at, updated_at
        )
        VALUES (
            'job_with_facts', 'tn_demo', '2026-01-02', 'conv_1', ?, 'CX', 'deepseek',
            'support', ?, ?, ?, ?, '[]', '2026-01-02', '2026-01-02'
        )
        """,
        [
            ("QuickCEP", 1, 1, 1, "positive"),
            ("Zendesk", 0, 0, 0, "neutral"),
        ],
    )
    con.execute(
        """
        INSERT INTO qa_reference (
            job_id, tenant_key, date, conversation_id, platform, brand, category, keyword,
            query_content, url, is_published_link, domain, content_type, created_at, updated_at
        )
        VALUES (
            'job_with_facts', 'tn_demo', '2026-01-02', 'conv_1', 'deepseek',
            'QuickCEP', 'CX', 'support', 'Which support tool is best?',
            'https://example.com/post', 1, 'example.com', 'article',
            '2026-01-02', '2026-01-02'
        )
        """
    )
    con.commit()
    con.close()


def test_migrates_legacy_jobs_to_current_project_and_analysis_model(tmp_path):
    module = _load_migration_module()
    source = tmp_path / "legacy.db"
    target = tmp_path / "migrated.db"
    _create_legacy_source(source)

    summary = module.migrate_legacy_geo_sqlite(source, target, SQLITE_SCHEMA, overwrite=True)

    assert summary.job_count == 2
    assert summary.project_count == 2
    assert summary.analysis_run_count == 2
    assert summary.qa_brand_state_rows == 2
    assert summary.qa_reference_rows == 1

    con = sqlite3.connect(target)
    con.row_factory = sqlite3.Row
    projects = con.execute(
        """
        SELECT project_id, name, status
        FROM monitoring_projects
        ORDER BY project_id
        """
    ).fetchall()
    assert len(projects) == 2
    assert {row["status"] for row in projects} == {"active"}

    query_jobs = con.execute(
        """
        SELECT job_id, project_id
        FROM llm_query_jobs
        ORDER BY job_id
        """
    ).fetchall()
    assert query_jobs[0]["job_id"] == "job_config_only"
    assert query_jobs[0]["project_id"]
    assert query_jobs[1]["job_id"] == "job_with_facts"
    assert query_jobs[1]["project_id"]

    fact_row = con.execute(
        """
        SELECT bs.analysis_run_id, ar.project_id, ar.status
        FROM qa_brand_state bs
        JOIN analysis_runs ar
          ON ar.tenant_key = bs.tenant_key
         AND ar.analysis_run_id = bs.analysis_run_id
        WHERE bs.job_id = 'job_with_facts'
        LIMIT 1
        """
    ).fetchone()
    assert fact_row["analysis_run_id"]
    assert fact_row["project_id"] == query_jobs[1]["project_id"]
    assert fact_row["status"] == "succeeded"

    brand_roles = {
        (row["brand_name"], row["role"])
        for row in con.execute("SELECT brand_name, role FROM project_brands")
    }
    assert ("QuickCEP", "target") in brand_roles
    assert ("Zendesk", "competitor") in brand_roles
    assert ("ConfigOnlyBrand", "target") in brand_roles

    assert con.execute("SELECT COUNT(*) FROM prompt_items").fetchone()[0] == 2
    assert con.execute("SELECT COUNT(*) FROM collection_jobs").fetchone()[0] == 2
    con.close()

    engine = create_engine(f"sqlite:///{target}")
    with Session(engine) as session:
        metric_rows = list_project_fact_metric_rows(
            session,
            tenant_key="tn_demo",
            project_id=query_jobs[1]["project_id"],
            start_date="2026-01-02",
            end_date="2026-01-02",
        )
    assert {row["metric_name"] for row in metric_rows} == {
        "mention_rate",
        "first_mention_rate",
        "top3_mention_rate",
        "sentiment_negative_ratio",
        "reference_rate",
    }
