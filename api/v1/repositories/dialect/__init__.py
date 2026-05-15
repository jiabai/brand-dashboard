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
