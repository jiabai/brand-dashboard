"""全局测试配置

提供 SQLite 内存数据库 fixture，测试无需外部 MySQL 依赖。
使用方式：在测试函数参数中声明 db_engine 即可获取已初始化的内存数据库引擎。
"""

from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def db_engine():
    """创建 SQLite 内存数据库引擎，并用 schema_sqlite.sql 初始化表结构。

    scope="session" 确保整个测试会话共享同一引擎，避免重复建表。
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    schema_path = Path(__file__).resolve().parent.parent / "api" / "database" / "schema_sqlite.sql"
    if not schema_path.exists():
        pytest.skip(f"Schema file not found: {schema_path}")

    schema_sql = schema_path.read_text(encoding="utf-8")
    statements = [s.strip() for s in schema_sql.split(";") if s.strip()]

    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))

    yield engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    """创建数据库会话，每个测试函数结束后自动回滚。

    使用 SAVEPOINT 实现嵌套事务隔离，确保测试之间数据互不影响。
    """
    connection = db_engine.connect()
    transaction = connection.begin()

    from sqlalchemy.orm import Session
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()
