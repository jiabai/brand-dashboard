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
    tenant_key: str | None = None,
    q: str | None = None,
    status: str | None = None,
    plan_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    where_clauses = []
    params = {}

    normalized_tenant_key = (tenant_key or "").strip()
    if normalized_tenant_key:
        where_clauses.append("t.tenant_key = :tenant_key")
        params["tenant_key"] = normalized_tenant_key

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
                t.tenant_key AS tenant_key,
                t.tenant_name AS tenant_name,
                t.company_legal_name AS company_legal_name,
                t.industry AS industry,
                t.status AS tenant_status,
                t.plan_type AS plan_type,
                t.max_users AS max_users,
                t.billing_cycle AS billing_cycle,
                t.contract_start_date AS contract_start_date,
                t.contract_end_date AS contract_end_date,
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
                    SELECT admin_u.first_name
                    FROM user_tenants admin_ut
                    JOIN users admin_u ON admin_u.id = admin_ut.user_id
                    WHERE admin_ut.tenant_id = t.id
                      AND admin_ut.role = 'admin'
                    ORDER BY admin_ut.created_at ASC
                    LIMIT 1
                ) AS admin_first_name,
                (
                    SELECT admin_u.last_name
                    FROM user_tenants admin_ut
                    JOIN users admin_u ON admin_u.id = admin_ut.user_id
                    WHERE admin_ut.tenant_id = t.id
                      AND admin_ut.role = 'admin'
                    ORDER BY admin_ut.created_at ASC
                    LIMIT 1
                ) AS admin_last_name,
                (
                    SELECT admin_u.phone_number
                    FROM user_tenants admin_ut
                    JOIN users admin_u ON admin_u.id = admin_ut.user_id
                    WHERE admin_ut.tenant_id = t.id
                      AND admin_ut.role = 'admin'
                    ORDER BY admin_ut.created_at ASC
                    LIMIT 1
                ) AS admin_phone,
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
                t.created_at AS created_at,
                (
                    SELECT COUNT(DISTINCT job_count.job_id)
                    FROM llm_query_jobs job_count
                    WHERE job_count.tenant_key = t.tenant_key
                      AND job_count.is_deleted = 0
                ) AS job_count,
                (
                    SELECT COUNT(DISTINCT active_jobs.job_id)
                    FROM llm_query_jobs active_jobs
                    WHERE active_jobs.tenant_key = t.tenant_key
                      AND active_jobs.is_deleted = 0
                      AND active_jobs.query_status = 1
                ) AS active_job_count,
                (
                    SELECT latest_job.job_id
                    FROM llm_query_jobs latest_job
                    WHERE latest_job.tenant_key = t.tenant_key
                      AND latest_job.is_deleted = 0
                    ORDER BY latest_job.created_at DESC, latest_job.id DESC
                    LIMIT 1
                ) AS latest_job_id,
                (
                    SELECT latest_job.brand
                    FROM llm_query_jobs latest_job
                    WHERE latest_job.tenant_key = t.tenant_key
                      AND latest_job.is_deleted = 0
                    ORDER BY latest_job.created_at DESC, latest_job.id DESC
                    LIMIT 1
                ) AS latest_job_brand,
                (
                    SELECT latest_job.category
                    FROM llm_query_jobs latest_job
                    WHERE latest_job.tenant_key = t.tenant_key
                      AND latest_job.is_deleted = 0
                    ORDER BY latest_job.created_at DESC, latest_job.id DESC
                    LIMIT 1
                ) AS latest_job_category,
                (
                    SELECT latest_job.query_status
                    FROM llm_query_jobs latest_job
                    WHERE latest_job.tenant_key = t.tenant_key
                      AND latest_job.is_deleted = 0
                    ORDER BY latest_job.created_at DESC, latest_job.id DESC
                    LIMIT 1
                ) AS latest_job_query_status,
                (
                    SELECT latest_job.effective_from
                    FROM llm_query_jobs latest_job
                    WHERE latest_job.tenant_key = t.tenant_key
                      AND latest_job.is_deleted = 0
                    ORDER BY latest_job.created_at DESC, latest_job.id DESC
                    LIMIT 1
                ) AS latest_job_effective_from,
                (
                    SELECT latest_job.effective_to
                    FROM llm_query_jobs latest_job
                    WHERE latest_job.tenant_key = t.tenant_key
                      AND latest_job.is_deleted = 0
                    ORDER BY latest_job.created_at DESC, latest_job.id DESC
                    LIMIT 1
                ) AS latest_job_effective_to,
                (
                    SELECT latest_job.created_at
                    FROM llm_query_jobs latest_job
                    WHERE latest_job.tenant_key = t.tenant_key
                      AND latest_job.is_deleted = 0
                    ORDER BY latest_job.created_at DESC, latest_job.id DESC
                    LIMIT 1
                ) AS latest_job_created_at
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


def get_platform_tenant_summary(db: Session, *, tenant_key: str):
    result = list_platform_tenant_summaries(
        db,
        tenant_key=tenant_key,
        page=1,
        page_size=1,
    )
    return result["items"][0] if result["items"] else None
