"""数据库方言抽象层

将 MySQL / SQLite 的语法差异集中在此模块，让 repositories 层无需关心底层方言。
"""
from sqlalchemy import text

from api.v1.repositories.connection import get_dialect


def get_columns(conn, table: str) -> set[str]:
    """获取表的列名集合。

    MySQL: SHOW COLUMNS FROM <table>
    SQLite: PRAGMA table_info(<table>)
    """
    dialect = get_dialect()
    if dialect == "mysql":
        result = conn.execute(text(f"SHOW COLUMNS FROM {table}")).fetchall()
        return {row[0] for row in result}
    else:
        result = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        return {row[1] for row in result}


def group_concat_expr(column: str, distinct: bool = True, separator: str = ",") -> str:
    """生成 GROUP_CONCAT SQL 片段。

    MySQL: GROUP_CONCAT(DISTINCT <column> SEPARATOR '<sep>')
    SQLite: GROUP_CONCAT(DISTINCT <column>, '<sep>')
    """
    dist = "DISTINCT " if distinct else ""
    dialect = get_dialect()
    if dialect == "mysql":
        return f"GROUP_CONCAT({dist}{column} SEPARATOR '{separator}')"
    else:
        return f"GROUP_CONCAT({dist}{column}, '{separator}')"


def upsert_sql(
    table: str,
    columns: list[str],
    unique_keys: list[str],
) -> str:
    """生成方言适配的 upsert SQL。

    MySQL: INSERT INTO ... ON DUPLICATE KEY UPDATE <non-key>=VALUES(<col>)
    SQLite: INSERT OR REPLACE INTO ... （适用于 unique key 覆盖整行的场景）

    Args:
        table: 目标表名
        columns: 所有列名列表（含 unique key 列）
        unique_keys: 唯一约束列名列表，用于确定哪些列在冲突时更新

    Returns:
        带命名参数占位符的 SQL 字符串，如 :tenant_key, :job_id 等
    """
    cols = ", ".join(columns)
    vals = ", ".join(f":{c}" for c in columns)
    dialect = get_dialect()

    if dialect == "mysql":
        update_cols = [c for c in columns if c not in unique_keys]
        updates = ", ".join(f"{c} = VALUES({c})" for c in update_cols)
        return (
            f"INSERT INTO {table} ({cols}) VALUES ({vals}) "
            f"ON DUPLICATE KEY UPDATE {updates}"
        )
    else:
        # SQLite: INSERT OR REPLACE（整行替换，适用于 unique key 覆盖场景）
        # 对于需要部分更新的场景，应使用 INSERT ... ON CONFLICT DO UPDATE SET
        return f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({vals})"


def upsert_sql_with_conflict(
    table: str,
    columns: list[str],
    unique_keys: list[str],
) -> str:
    """生成 SQLite ON CONFLICT 风格的 upsert SQL（仅部分列更新）。

    MySQL: INSERT INTO ... ON DUPLICATE KEY UPDATE <non-key>=VALUES(<col>)
    SQLite: INSERT INTO ... ON CONFLICT(<unique_keys>) DO UPDATE SET <non-key>=excluded.<col>

    与 upsert_sql 不同，此函数在 SQLite 下只更新非唯一键列，保留原行其他字段值。
    适用于 upsert 时需要保留 created_at 等字段的场景。

    Args:
        table: 目标表名
        columns: 所有列名列表
        unique_keys: 唯一约束列名列表

    Returns:
        带命名参数占位符的 SQL 字符串
    """
    cols = ", ".join(columns)
    vals = ", ".join(f":{c}" for c in columns)
    dialect = get_dialect()

    if dialect == "mysql":
        update_cols = [c for c in columns if c not in unique_keys]
        updates = ", ".join(f"{c} = VALUES({c})" for c in update_cols)
        return (
            f"INSERT INTO {table} ({cols}) VALUES ({vals}) "
            f"ON DUPLICATE KEY UPDATE {updates}"
        )
    else:
        conflict_cols = ", ".join(unique_keys)
        update_cols = [c for c in columns if c not in unique_keys]
        updates = ", ".join(f"{c} = excluded.{c}" for c in update_cols)
        return (
            f"INSERT INTO {table} ({cols}) VALUES ({vals}) "
            f"ON CONFLICT({conflict_cols}) DO UPDATE SET {updates}"
        )
