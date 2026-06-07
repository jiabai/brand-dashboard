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
    / "20260607_add_collection_lifecycle_model.mysql.sql"
)


def _compact_sql(sql: str) -> str:
    return " ".join(sql.split())


def test_mysql_schemas_declare_collection_lifecycle_model():
    expected_snippets = (
        "CREATE TABLE IF NOT EXISTS `collection_jobs`",
        "CREATE TABLE IF NOT EXISTS `collection_tasks`",
        "CREATE TABLE IF NOT EXISTS `collection_attempts`",
        "`collection_job_id` varchar(128)",
        "`collection_task_id` varchar(128)",
        "`attempt_id` varchar(128)",
        "`lease_owner` varchar(128)",
        "`lease_until` timestamp NULL DEFAULT NULL",
        "`last_error_message` text",
        "`error_message` text",
        "UNIQUE KEY `uk_tenant_collection_job` (`tenant_key`,`collection_job_id`)",
        "UNIQUE KEY `uk_tenant_collection_task` (`tenant_key`,`collection_task_id`)",
        "UNIQUE KEY `uk_tenant_collection_attempt` (`tenant_key`,`attempt_id`)",
        "KEY `idx_collection_jobs_tenant_project_status` (`tenant_key`,`project_id`,`status`)",
        "KEY `idx_collection_tasks_fetch` (`tenant_key`,`status`,`lease_until`,`id`)",
        "KEY `idx_collection_tasks_job_status` (`tenant_key`,`collection_job_id`,`status`)",
        "KEY `idx_collection_attempts_task` (`tenant_key`,`collection_task_id`)",
        "KEY `idx_collection_attempts_executor_status` (`tenant_key`,`executor_id`,`status`)",
        (
            "CONSTRAINT `collection_jobs_ibfk_project` FOREIGN KEY "
            "(`tenant_key`,`project_id`) REFERENCES `monitoring_projects` "
            "(`tenant_key`,`project_id`)"
        ),
        (
            "CONSTRAINT `collection_tasks_ibfk_job` FOREIGN KEY "
            "(`tenant_key`,`collection_job_id`) REFERENCES `collection_jobs` "
            "(`tenant_key`,`collection_job_id`) ON DELETE CASCADE"
        ),
        (
            "CONSTRAINT `collection_attempts_ibfk_task` FOREIGN KEY "
            "(`tenant_key`,`collection_task_id`) REFERENCES `collection_tasks` "
            "(`tenant_key`,`collection_task_id`) ON DELETE CASCADE"
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


def test_sqlite_schema_supports_collection_lifecycle_relations():
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
        INSERT INTO prompt_items
          (tenant_key, prompt_set_id, prompt_item_id, keyword, query_content, status)
        VALUES
          ('tenant_a', 'prompt_set_1', 'prompt_1', '数学', '数学培训哪家好', 'active')
        """
    )
    connection.execute(
        """
        INSERT INTO executors (executor_id, name, status, ip_address)
        VALUES ('executor_1', '执行器 1', 'active', '127.0.0.1')
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
            'pending',
            '2026-06-07 00:00:00',
            '2026-06-08 00:00:00',
            1
          )
        """
    )
    connection.execute(
        """
        INSERT INTO collection_tasks
          (
            tenant_key,
            collection_task_id,
            collection_job_id,
            project_id,
            platform,
            prompt_set_id,
            prompt_item_id,
            query_content,
            status,
            lease_owner,
            lease_until,
            reserved_at,
            attempt_count,
            max_attempts
          )
        VALUES
          (
            'tenant_a',
            'collection_task_1',
            'collection_job_1',
            'proj_1',
            'deepseek',
            'prompt_set_1',
            'prompt_1',
            '数学培训哪家好',
            'reserved',
            'executor_1',
            '2026-06-07 00:05:00',
            '2026-06-07 00:00:00',
            1,
            3
          )
        """
    )
    connection.execute(
        """
        INSERT INTO collection_attempts
          (
            tenant_key,
            attempt_id,
            collection_task_id,
            executor_id,
            status,
            started_at,
            finished_at,
            error_message
          )
        VALUES
          (
            'tenant_a',
            'attempt_1',
            'collection_task_1',
            'executor_1',
            'failed',
            '2026-06-07 00:00:01',
            '2026-06-07 00:00:30',
            '模型返回超时'
          )
        """
    )

    row = connection.execute(
        """
        SELECT
            collection_tasks.tenant_key,
            collection_tasks.status,
            collection_tasks.lease_owner,
            collection_tasks.lease_until,
            collection_attempts.status,
            collection_attempts.error_message
        FROM collection_tasks
        INNER JOIN collection_attempts
          ON collection_attempts.tenant_key = collection_tasks.tenant_key
         AND collection_attempts.collection_task_id = collection_tasks.collection_task_id
        WHERE collection_tasks.collection_task_id = 'collection_task_1'
        """
    ).fetchone()

    assert row == (
        "tenant_a",
        "reserved",
        "executor_1",
        "2026-06-07 00:05:00",
        "failed",
        "模型返回超时",
    )

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO collection_tasks
              (
                tenant_key,
                collection_task_id,
                collection_job_id,
                project_id,
                platform,
                query_content
              )
            VALUES
              (
                'tenant_b',
                'collection_task_cross_tenant',
                'collection_job_1',
                'proj_1',
                'deepseek',
                '跨租户任务不应该写入'
              )
            """
        )


def test_mysql_migration_creates_collection_lifecycle_model():
    migration_sql = _compact_sql(MYSQL_MIGRATION_FILE.read_text(encoding="utf-8"))

    for table_name in (
        "collection_jobs",
        "collection_tasks",
        "collection_attempts",
    ):
        assert f"CREATE TABLE IF NOT EXISTS `{table_name}`" in migration_sql

    assert "uk_tenant_collection_job" in migration_sql
    assert "uk_tenant_collection_task" in migration_sql
    assert "uk_tenant_collection_attempt" in migration_sql
    assert "idx_collection_tasks_fetch" in migration_sql
    assert "lease_until" in migration_sql
    assert "last_error_message" in migration_sql
    assert "error_message" in migration_sql
