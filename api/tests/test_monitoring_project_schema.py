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
    / "20260607_add_monitoring_project_model.mysql.sql"
)


def _compact_sql(sql: str) -> str:
    return " ".join(sql.split())


def test_mysql_schemas_declare_monitoring_project_model():
    expected_snippets = (
        "`monitoring_projects`",
        "`project_brands`",
        "`prompt_sets`",
        "`prompt_items`",
        "UNIQUE KEY `uk_tenant_project` (`tenant_key`,`project_id`)",
        (
            "UNIQUE KEY `uk_tenant_project_brand_role` "
            "(`tenant_key`,`project_id`,`brand_id`,`role`)"
        ),
        "UNIQUE KEY `uk_tenant_prompt_set` (`tenant_key`,`prompt_set_id`)",
        (
            "UNIQUE KEY `uk_tenant_project_prompt_version` "
            "(`tenant_key`,`project_id`,`version`)"
        ),
        (
            "UNIQUE KEY `uk_tenant_prompt_item` "
            "(`tenant_key`,`prompt_set_id`,`prompt_item_id`)"
        ),
        (
            "CONSTRAINT `project_brands_ibfk_project` FOREIGN KEY "
            "(`tenant_key`,`project_id`) REFERENCES `monitoring_projects` "
            "(`tenant_key`,`project_id`) ON DELETE CASCADE"
        ),
        (
            "CONSTRAINT `prompt_sets_ibfk_project` FOREIGN KEY "
            "(`tenant_key`,`project_id`) REFERENCES `monitoring_projects` "
            "(`tenant_key`,`project_id`) ON DELETE CASCADE"
        ),
        (
            "CONSTRAINT `prompt_items_ibfk_prompt_set` FOREIGN KEY "
            "(`tenant_key`,`prompt_set_id`) REFERENCES `prompt_sets` "
            "(`tenant_key`,`prompt_set_id`) ON DELETE CASCADE"
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


def test_sqlite_schema_supports_monitoring_project_relations():
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
          ('tenant_a', 'proj_1', '品牌监测项目', '教育', 'K12', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO project_brands
          (tenant_key, project_id, brand_id, brand_name, role, aliases, status)
        VALUES
          ('tenant_a', 'proj_1', 'brand_target', '品牌A', 'target', '["A"]', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO prompt_sets
          (tenant_key, project_id, prompt_set_id, version, name, status)
        VALUES
          ('tenant_a', 'proj_1', 'ps_1', 1, '默认问题集', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO prompt_items
          (tenant_key, prompt_set_id, prompt_item_id, keyword, query_content, status)
        VALUES
          ('tenant_a', 'ps_1', 'pi_1', '数学', '数学培训哪家好', 'active')
        """
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO prompt_items
              (tenant_key, prompt_set_id, prompt_item_id, keyword, query_content, status)
            VALUES
              ('tenant_a', 'ps_1', 'pi_1', '英语', '英语培训哪家好', 'active')
            """
        )

    connection.execute(
        """
        DELETE FROM monitoring_projects
        WHERE tenant_key = 'tenant_a' AND project_id = 'proj_1'
        """
    )

    for table in ("project_brands", "prompt_sets", "prompt_items"):
        count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count == 0


def test_mysql_migration_creates_monitoring_project_model():
    migration_sql = _compact_sql(MYSQL_MIGRATION_FILE.read_text(encoding="utf-8"))

    for table_name in (
        "monitoring_projects",
        "project_brands",
        "prompt_sets",
        "prompt_items",
    ):
        assert f"CREATE TABLE IF NOT EXISTS `{table_name}`" in migration_sql

    assert "uk_tenant_project" in migration_sql
    assert "uk_tenant_project_brand_role" in migration_sql
    assert "uk_tenant_prompt_set" in migration_sql
    assert "uk_tenant_project_prompt_version" in migration_sql
    assert "uk_tenant_prompt_item" in migration_sql
    assert "ON DELETE CASCADE" in migration_sql
