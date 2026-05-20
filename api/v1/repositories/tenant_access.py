from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Engine, text

VALID_TENANT_ACCESS_ROLES = frozenset({"admin", "member", "viewer"})


class TenantAccessGrantError(ValueError):
    pass


def _normalize_email(email: str | None) -> str:
    return (email or "").strip().lower()


def _normalize_tenant_key(tenant_key: str | None) -> str:
    return (tenant_key or "").strip()


def _normalize_role(role: str | None) -> str:
    return (role or "viewer").strip().lower()


def grant_tenant_access(
    engine: Engine,
    *,
    email: str,
    tenant_key: str,
    role: str = "viewer",
):
    normalized_email = _normalize_email(email)
    normalized_tenant_key = _normalize_tenant_key(tenant_key)
    normalized_role = _normalize_role(role)

    if not normalized_email:
        raise TenantAccessGrantError("缺少用户邮箱")
    if not normalized_tenant_key:
        raise TenantAccessGrantError("缺少 tenant_key")
    if normalized_role not in VALID_TENANT_ACCESS_ROLES:
        raise TenantAccessGrantError("角色无效，仅支持 viewer/member/admin")

    now = datetime.now(UTC)

    with engine.begin() as conn:
        user = conn.execute(
            text(
                """
                SELECT id, email, status
                FROM users
                WHERE lower(email) = :email
                """
            ),
            {"email": normalized_email},
        ).first()
        if not user:
            raise TenantAccessGrantError("用户不存在")
        user_data = user._mapping
        if user_data["status"] != "active":
            raise TenantAccessGrantError("账号状态不可授权")

        tenant = conn.execute(
            text(
                """
                SELECT id, tenant_key, status
                FROM tenants
                WHERE tenant_key = :tenant_key
                """
            ),
            {"tenant_key": normalized_tenant_key},
        ).first()
        if not tenant:
            raise TenantAccessGrantError("租户不存在")
        tenant_data = tenant._mapping
        if tenant_data["status"] != "active":
            raise TenantAccessGrantError("租户状态不可授权")

        membership = conn.execute(
            text(
                """
                SELECT role, status
                FROM user_tenants
                WHERE user_id = :user_id
                  AND tenant_id = :tenant_id
                """
            ),
            {"user_id": user_data["id"], "tenant_id": tenant_data["id"]},
        ).first()

        action = "exists"
        if not membership:
            conn.execute(
                text(
                    """
                    INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
                    VALUES (:user_id, :tenant_id, :role, 'active', :now)
                    """
                ),
                {
                    "user_id": user_data["id"],
                    "tenant_id": tenant_data["id"],
                    "role": normalized_role,
                    "now": now,
                },
            )
            action = "created"
        else:
            membership_data = membership._mapping
            if membership_data["status"] != "active":
                conn.execute(
                    text(
                        """
                        UPDATE user_tenants
                        SET role = :role,
                            status = 'active'
                        WHERE user_id = :user_id
                          AND tenant_id = :tenant_id
                        """
                    ),
                    {
                        "user_id": user_data["id"],
                        "tenant_id": tenant_data["id"],
                        "role": normalized_role,
                    },
                )
                action = "reactivated"
            elif membership_data["role"] != normalized_role:
                conn.execute(
                    text(
                        """
                        UPDATE user_tenants
                        SET role = :role
                        WHERE user_id = :user_id
                          AND tenant_id = :tenant_id
                        """
                    ),
                    {
                        "user_id": user_data["id"],
                        "tenant_id": tenant_data["id"],
                        "role": normalized_role,
                    },
                )
                action = "updated"

    return {
        "action": action,
        "email": normalized_email,
        "tenant_key": normalized_tenant_key,
        "role": normalized_role,
    }
