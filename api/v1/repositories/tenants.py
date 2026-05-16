from sqlalchemy import text
from sqlalchemy.orm import Session


def tenant_exists(db: Session, tenant_key: str) -> bool:
    row = db.execute(
        text("SELECT 1 FROM tenants WHERE tenant_key = :tenant_key"),
        {"tenant_key": tenant_key},
    ).first()
    return row is not None

