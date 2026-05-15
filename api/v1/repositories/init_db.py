"""数据库 schema 自动初始化模块

根据当前方言（MySQL / SQLite）自动选择并执行对应的 schema SQL 文件。
仅在建表（空库）时执行，已有表的数据库不会被修改。
"""

import logging
from pathlib import Path

from sqlalchemy import text

from api.v1.repositories.connection import engine, get_dialect

logger = logging.getLogger(__name__)

_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "database"


def _has_tables(conn, dialect: str) -> bool:
    """检查数据库中是否已有业务表"""
    if dialect == "sqlite":
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        ).fetchall()
    else:
        result = conn.execute(text("SHOW TABLES")).fetchall()
    return len(result) > 0


def init_db(force: bool = False) -> None:
    """根据方言自动初始化数据库 schema。

    Args:
        force: 为 True 时强制重新执行 schema SQL（危险，仅用于开发/测试）
    """
    dialect = get_dialect()
    schema_file = _SCHEMA_DIR / ("schema_sqlite.sql" if dialect == "sqlite" else "schema.sql")

    if not schema_file.exists():
        logger.warning("Schema file not found: %s, skipping init", schema_file)
        return

    schema_sql = schema_file.read_text(encoding="utf-8")

    with engine.begin() as conn:
        if not force and _has_tables(conn, dialect):
            logger.info("Database already has tables, skipping schema init (dialect=%s)", dialect)
            return

        # SQLite 不支持在一个 execute 中执行多条语句，需按分号拆分
        if dialect == "sqlite":
            statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
            for stmt in statements:
                conn.execute(text(stmt))
        else:
            conn.execute(text(schema_sql))

        logger.info("Database schema initialized (dialect=%s, file=%s)", dialect, schema_file.name)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
