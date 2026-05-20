from sqlalchemy import text
from sqlalchemy.orm import Session


def tenant_exists(db: Session, tenant_key: str) -> bool:
    row = db.execute(
        text("SELECT 1 FROM tenants WHERE tenant_key = :tenant_key"),
        {"tenant_key": tenant_key},
    ).first()
    return row is not None


def get_user_identity(db: Session, user_id: int):
    return db.execute(
        text(
            """
            SELECT id, email, status
            FROM users
            WHERE id = :user_id
            """
        ),
        {"user_id": user_id},
    ).first()


def get_user_tenant_membership(db: Session, *, user_id: int, tenant_key: str):
    return db.execute(
        text(
            """
            SELECT
                t.tenant_key,
                t.tenant_name,
                t.status AS tenant_status,
                ut.role,
                ut.status AS member_status
            FROM user_tenants ut
            JOIN tenants t ON t.id = ut.tenant_id
            WHERE ut.user_id = :user_id
              AND t.tenant_key = :tenant_key
            """
        ),
        {"user_id": user_id, "tenant_key": tenant_key},
    ).first()


def list_user_tenant_summaries(db: Session, user_id: int):
    return db.execute(
        text(
            """
            SELECT
                t.tenant_key,
                t.tenant_name,
                ut.role,
                ut.status AS member_status,
                t.status AS tenant_status
            FROM user_tenants ut
            JOIN tenants t ON t.id = ut.tenant_id
            WHERE ut.user_id = :user_id
            ORDER BY t.id ASC
            """
        ),
        {"user_id": user_id},
    ).fetchall()

