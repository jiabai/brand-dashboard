import sqlite3
from pathlib import Path

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
    / "20260606_add_qa_brand_state_idempotency_key.mysql.sql"
)


def _compact_sql(sql: str) -> str:
    return " ".join(sql.split())


def test_mysql_schemas_declare_qa_brand_state_idempotency_key():
    expected_unique_key = (
        "UNIQUE KEY `uk_tenant_job_conv_brand` "
        "(`tenant_key`(191),`job_id`(191),`conversation_id`(191),`brand`)"
    )

    missing = []
    for schema_file in MYSQL_SCHEMA_FILES:
        schema_sql = _compact_sql(schema_file.read_text(encoding="utf-8"))
        if expected_unique_key not in schema_sql:
            missing.append(str(schema_file.relative_to(PROJECT_ROOT)))

    assert missing == []


def test_sqlite_schema_supports_qa_brand_state_upsert_without_duplicate_rows():
    connection = sqlite3.connect(":memory:")
    connection.executescript(SQLITE_SCHEMA_FILE.read_text(encoding="utf-8"))

    insert_sql = """
        INSERT INTO qa_brand_state
          (
            job_id,
            tenant_key,
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
            brands_found
          )
        VALUES
          (
            :job_id,
            :tenant_key,
            :date,
            :conversation_id,
            :brand,
            :category,
            :platform,
            :keyword,
            :is_mentioned,
            :is_first_mentioned,
            :is_top3_mentioned,
            :sentiment_status,
            :brands_found
          )
    """
    upsert_sql = insert_sql + """
        ON CONFLICT(tenant_key, job_id, conversation_id, brand)
        DO UPDATE SET
            date = excluded.date,
            category = excluded.category,
            platform = excluded.platform,
            keyword = excluded.keyword,
            is_mentioned = excluded.is_mentioned,
            is_first_mentioned = excluded.is_first_mentioned,
            is_top3_mentioned = excluded.is_top3_mentioned,
            sentiment_status = excluded.sentiment_status,
            brands_found = excluded.brands_found,
            updated_at = CURRENT_TIMESTAMP
    """
    base_row = {
        "job_id": "job_1",
        "tenant_key": "tenant_a",
        "date": "2026-06-06",
        "conversation_id": "conv_1",
        "brand": "brand_a",
        "category": "category_a",
        "platform": "deepseek",
        "keyword": "keyword_a",
        "is_mentioned": 0,
        "is_first_mentioned": 0,
        "is_top3_mentioned": 0,
        "sentiment_status": "unknown",
        "brands_found": "[]",
    }

    connection.execute(insert_sql, base_row)
    connection.execute(
        upsert_sql,
        {
            **base_row,
            "is_mentioned": 1,
            "is_first_mentioned": 1,
            "sentiment_status": "positive",
            "brands_found": '["brand_a"]',
        },
    )

    count, is_mentioned, is_first_mentioned, sentiment_status = connection.execute(
        """
        SELECT COUNT(*), MAX(is_mentioned), MAX(is_first_mentioned), MAX(sentiment_status)
        FROM qa_brand_state
        WHERE tenant_key = 'tenant_a'
          AND job_id = 'job_1'
          AND conversation_id = 'conv_1'
          AND brand = 'brand_a'
        """
    ).fetchone()

    assert count == 1
    assert is_mentioned == 1
    assert is_first_mentioned == 1
    assert sentiment_status == "positive"


def test_mysql_migration_documents_precheck_and_adds_unique_key():
    migration_sql = MYSQL_MIGRATION_FILE.read_text(encoding="utf-8")

    assert "check_duplicate_analysis_rows.py" in migration_sql
    assert (
        "ALTER TABLE `qa_brand_state`"
        in migration_sql
        or "ALTER TABLE qa_brand_state" in migration_sql
    )
    assert "ADD UNIQUE KEY `uk_tenant_job_conv_brand`" in migration_sql
    assert "`tenant_key`(191), `job_id`(191), `conversation_id`(191), `brand`" in migration_sql
