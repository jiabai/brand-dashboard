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


def get_tenant_summary_by_key(db: Session, tenant_key: str):
    return db.execute(
        text(
            """
            SELECT tenant_key, tenant_name, status
            FROM tenants
            WHERE tenant_key = :tenant_key
            """
        ),
        {"tenant_key": tenant_key},
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


def list_platform_tenant_summaries(
    db: Session,
    *,
    q: str | None = None,
    status: str | None = None,
    plan_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    where_clauses = []
    params = {}

    normalized_q = (q or "").strip().lower()
    if normalized_q:
        where_clauses.append(
            """
            (
                lower(t.tenant_key) LIKE :q
                OR lower(t.tenant_name) LIKE :q
                OR EXISTS (
                    SELECT 1
                    FROM user_tenants search_ut
                    JOIN users search_u ON search_u.id = search_ut.user_id
                    WHERE search_ut.tenant_id = t.id
                      AND lower(search_u.email) LIKE :q
                )
            )
            """
        )
        params["q"] = f"%{normalized_q}%"

    if status:
        where_clauses.append("t.status = :status")
        params["status"] = status

    if plan_type:
        where_clauses.append("t.plan_type = :plan_type")
        params["plan_type"] = plan_type

    where_sql = " AND ".join(where_clauses) if where_clauses else "1 = 1"
    total = db.execute(
        text(f"SELECT COUNT(*) FROM tenants t WHERE {where_sql}"),
        params,
    ).scalar_one()

    offset = (page - 1) * page_size
    rows = db.execute(
        text(
            f"""
            SELECT
                t.tenant_key,
                t.tenant_name,
                t.company_legal_name,
                t.industry,
                t.status,
                t.plan_type,
                t.max_users,
                t.billing_cycle,
                t.contract_start_date,
                t.contract_end_date,
                (
                    SELECT admin_u.email
                    FROM user_tenants admin_ut
                    JOIN users admin_u ON admin_u.id = admin_ut.user_id
                    WHERE admin_ut.tenant_id = t.id
                      AND admin_ut.role = 'admin'
                    ORDER BY admin_ut.created_at ASC
                    LIMIT 1
                ) AS admin_email,
                (
                    SELECT admin_u.status
                    FROM user_tenants admin_ut
                    JOIN users admin_u ON admin_u.id = admin_ut.user_id
                    WHERE admin_ut.tenant_id = t.id
                      AND admin_ut.role = 'admin'
                    ORDER BY admin_ut.created_at ASC
                    LIMIT 1
                ) AS admin_status,
                (
                    SELECT COUNT(*)
                    FROM user_tenants member_ut
                    WHERE member_ut.tenant_id = t.id
                ) AS member_count,
                t.created_at
            FROM tenants t
            WHERE {where_sql}
            ORDER BY t.created_at DESC, t.id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {
            **params,
            "limit": page_size,
            "offset": offset,
        },
    ).fetchall()

    return {
        "items": rows,
        "total": int(total or 0),
    }
