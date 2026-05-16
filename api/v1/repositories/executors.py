from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


def insert_executor(
    db: Session,
    *,
    executor_id: str,
    name: str,
    executor_type: str | None,
    ip_address: str,
    api_key: str,
    now: datetime,
) -> None:
    db.execute(
        text(
            """
            INSERT INTO executors (
                executor_id,
                name,
                type,
                status,
                ip_address,
                api_key,
                created_at,
                updated_at
            )
            VALUES (:executor_id, :name, :type, 'active', :ip_address, :api_key, :now, :now)
            """
        ),
        {
            "executor_id": executor_id,
            "name": name,
            "type": executor_type,
            "ip_address": ip_address,
            "api_key": api_key,
            "now": now,
        },
    )


def get_active_executor_by_ip(db: Session, ip_address: str):
    return db.execute(
        text(
            """
            SELECT executor_id, api_key, name
            FROM executors
            WHERE ip_address = :ip_address AND status = 'active'
            """
        ),
        {"ip_address": ip_address},
    ).first()


def get_executor_credentials(db: Session, executor_id: str):
    return db.execute(
        text("SELECT api_key, status FROM executors WHERE executor_id = :executor_id"),
        {"executor_id": executor_id},
    ).first()


def list_executors(db: Session):
    return db.execute(
        text(
            """
            SELECT executor_id, name, type, status, ip_address, created_at
            FROM executors
            """
        )
    ).fetchall()


def deactivate_executor(db: Session, executor_id: str, now: datetime) -> int:
    result = db.execute(
        text(
            """
            UPDATE executors
            SET status = 'inactive', updated_at = :now
            WHERE executor_id = :executor_id
            """
        ),
        {"executor_id": executor_id, "now": now},
    )
    return result.rowcount

