from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from api.v1.repositories.tenant_members import (
    TenantMemberGovernanceError,
    update_tenant_member,
)

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
    actor_email: str | None = None,
    reason: str | None = None,
):
    normalized_email = _normalize_email(email)
    normalized_tenant_key = _normalize_tenant_key(tenant_key)
    normalized_role = _normalize_role(role)
    normalized_actor_email = _normalize_email(actor_email) or normalized_email
    normalized_reason = (reason or "").strip() or "local tenant access grant"

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

        actor = conn.execute(
            text(
                """
                SELECT id, status
                FROM users
                WHERE lower(email) = :email
                """
            ),
            {"email": normalized_actor_email},
        ).first()
        if not actor:
            raise TenantAccessGrantError("鎿嶄綔浜轰笉瀛樺湪")
        actor_data = actor._mapping
        if actor_data["status"] != "active":
            raise TenantAccessGrantError("鎿嶄綔浜虹姸鎬佷笉鍙敤")

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
            conn.execute(
                text(
                    """
                    INSERT INTO tenant_role_audit_logs (
                        tenant_id,
                        target_user_id,
                        actor_user_id,
                        actor_scope,
                        action,
                        old_role,
                        new_role,
                        old_status,
                        new_status,
                        reason,
                        created_at
                    ) VALUES (
                        :tenant_id,
                        :target_user_id,
                        :actor_user_id,
                        'platform',
                        'membership_updated',
                        NULL,
                        :new_role,
                        NULL,
                        'active',
                        :reason,
                        :created_at
                    )
                    """
                ),
                {
                    "tenant_id": tenant_data["id"],
                    "target_user_id": user_data["id"],
                    "actor_user_id": actor_data["id"],
                    "new_role": normalized_role,
                    "reason": normalized_reason,
                    "created_at": now,
                },
            )
            action = "created"
        else:
            membership_data = membership._mapping
            session = Session(bind=conn)
            if membership_data["status"] != "active":
                try:
                    update_tenant_member(
                        session,
                        tenant_key=normalized_tenant_key,
                        target_user_id=user_data["id"],
                        actor_user_id=actor_data["id"],
                        actor_scope="platform",
                        role=normalized_role,
                        status="active",
                        reason=normalized_reason,
                    )
                except TenantMemberGovernanceError as exc:
                    raise TenantAccessGrantError(str(exc)) from exc
                action = "reactivated"
            elif membership_data["role"] != normalized_role:
                try:
                    update_tenant_member(
                        session,
                        tenant_key=normalized_tenant_key,
                        target_user_id=user_data["id"],
                        actor_user_id=actor_data["id"],
                        actor_scope="platform",
                        role=normalized_role,
                        reason=normalized_reason,
                    )
                except TenantMemberGovernanceError as exc:
                    raise TenantAccessGrantError(str(exc)) from exc
                action = "updated"

    return {
        "action": action,
        "email": normalized_email,
        "tenant_key": normalized_tenant_key,
        "role": normalized_role,
    }
