import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

current_dir = Path(__file__).resolve().parent
env_path = current_dir.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

_is_production = os.getenv("ENV", "development") == "production"

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

engine = create_engine(
    f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@"
    f"{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/"
    f"{DATABASE_CONFIG['database']}?charset={DATABASE_CONFIG['charset']}",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False
)

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