import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool, StaticPool

current_dir = Path(__file__).resolve().parent

env_path = current_dir.parent.parent / '.env'  # api/.env
load_dotenv(dotenv_path=env_path)

_is_production = os.getenv("ENV", "development") == "production"
_db_dialect = os.getenv("DB_DIALECT", "mysql").lower()


def _build_mysql_engine():
    _db_password = os.getenv("DB_PASSWORD")
    if not _db_password:
        if _is_production:
            raise RuntimeError("DB_PASSWORD environment variable is required in production")
        _db_password = "devpassword"

    DATABASE_CONFIG = {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": _db_password,
        "database": os.getenv("DB_NAME", "geo"),
        "charset": os.getenv("DB_CHARSET", "utf8mb4"),
    }

    url = (
        f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@"
        f"{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/"
        f"{DATABASE_CONFIG['database']}?charset={DATABASE_CONFIG['charset']}"
    )
    return create_engine(
        url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        echo=False,
    ), DATABASE_CONFIG


def _build_sqlite_engine():
    db_path = os.getenv("DB_SQLITE_PATH", "data/geo.db")
    # 支持相对路径：基于项目根目录解析
    if not Path(db_path).is_absolute():
        project_root = Path(__file__).resolve().parent.parent.parent
        db_path = str(project_root / db_path)

    # 确保 SQLite 文件所在目录存在
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    url = f"sqlite:///{db_path}"
    eng = create_engine(
        url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # 启用 WAL 模式：提升并发读性能，避免写锁阻塞所有读操作
    # busy_timeout：写锁争用时最多等待 5 秒
    with eng.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA busy_timeout=5000"))
        conn.commit()

    return eng, {"dialect": "sqlite"}


if _db_dialect == "sqlite":
    engine, DATABASE_CONFIG = _build_sqlite_engine()
elif _db_dialect == "mysql":
    engine, DATABASE_CONFIG = _build_mysql_engine()
else:
    raise ValueError(f"Unsupported DB_DIALECT: {_db_dialect!r}. Use 'mysql' or 'sqlite'.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话（FastAPI 依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    """获取数据库引擎（FastAPI 依赖注入）"""
    return engine


def get_dialect() -> str:
    """返回当前数据库方言名称 ('mysql' 或 'sqlite')"""
    return _db_dialect
