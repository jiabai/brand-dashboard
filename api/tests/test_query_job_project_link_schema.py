from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _compact(sql: str) -> str:
    return " ".join(sql.split())


def test_llm_query_jobs_schema_contains_nullable_project_link():
    mysql_schema = (ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    sqlite_schema = (ROOT / "database" / "schema_sqlite.sql").read_text(encoding="utf-8")
    business_schema = (ROOT / "database" / "schema_business.sql").read_text(encoding="utf-8")

    for sql in (mysql_schema, business_schema):
        compact = _compact(sql)
        assert "`project_id` varchar(128)" in compact
        assert "KEY `idx_lqj_project` (`tenant_key`,`project_id`)" in compact

    sqlite_compact = _compact(sqlite_schema)
    assert "project_id VARCHAR(128)" in sqlite_compact
    assert "idx_lqj_project ON llm_query_jobs (tenant_key, project_id)" in sqlite_compact


def test_project_link_migration_documents_safe_compatible_column():
    migration = (
        ROOT
        / "database"
        / "migrations"
        / "20260607_add_project_id_to_query_jobs.mysql.sql"
    )

    sql = _compact(migration.read_text(encoding="utf-8"))

    assert "ADD COLUMN `project_id` varchar(128)" in sql
    assert "NULL" in sql
    assert "ADD INDEX `idx_lqj_project` (`tenant_key`, `project_id`)" in sql
