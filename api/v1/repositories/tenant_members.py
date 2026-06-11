from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

VALID_TENANT_MEMBER_ROLES = frozenset({"admin", "member", "viewer"})
VALID_TENANT_MEMBER_STATUSES = frozenset({"active", "inactive"})


class TenantMemberGovernanceError(ValueError):
    pass


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def _load_tenant_member(
    db: Session,
    *,
    tenant_key: str,
    user_id: int,
) -> Mapping[str, Any] | None:
    return db.execute(
        text(
            """
            SELECT
              t.id AS tenant_id,
              t.tenant_key AS tenant_key,
              t.tenant_name AS tenant_name,
              t.status AS tenant_status,
              u.id AS user_id,
              u.email AS email,
              u.first_name AS first_name,
              u.last_name AS last_name,
              u.phone_number AS phone_number,
              u.status AS user_status,
              ut.role AS role,
              ut.status AS member_status,
              ut.created_at AS created_at
            FROM user_tenants ut
            JOIN tenants t ON t.id = ut.tenant_id
            JOIN users u ON u.id = ut.user_id
            WHERE t.tenant_key = :tenant_key
              AND u.id = :user_id
            LIMIT 1
            """
        ),
        {"tenant_key": tenant_key, "user_id": user_id},
    ).mappings().first()


def list_tenant_members(
    db: Session,
    *,
    tenant_key: str,
) -> list[Mapping[str, Any]]:
    return db.execute(
        text(
            """
            SELECT
              u.id AS user_id,
              u.email AS email,
              u.first_name AS first_name,
              u.last_name AS last_name,
              u.phone_number AS phone_number,
              u.status AS user_status,
              ut.role AS role,
              ut.status AS member_status,
              ut.created_at AS created_at
            FROM user_tenants ut
            JOIN tenants t ON t.id = ut.tenant_id
            JOIN users u ON u.id = ut.user_id
            WHERE t.tenant_key = :tenant_key
            ORDER BY ut.created_at ASC, u.id ASC
            """
        ),
        {"tenant_key": tenant_key},
    ).mappings().all()


def tenant_exists(
    db: Session,
    *,
    tenant_key: str,
) -> bool:
    return bool(
        db.execute(
            text(
                """
                SELECT 1
                FROM tenants
                WHERE tenant_key = :tenant_key
                LIMIT 1
                """
            ),
            {"tenant_key": tenant_key},
        ).first()
    )


def _count_other_active_admins(
    db: Session,
    *,
    tenant_id: int,
    target_user_id: int,
) -> int:
    return int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM user_tenants ut
                JOIN users u ON u.id = ut.user_id
                WHERE ut.tenant_id = :tenant_id
                  AND ut.user_id != :target_user_id
                  AND ut.role = 'admin'
                  AND ut.status = 'active'
                  AND u.status = 'active'
                """
            ),
            {"tenant_id": tenant_id, "target_user_id": target_user_id},
        ).scalar_one()
        or 0
    )


def _ensure_not_removing_last_active_admin(
    db: Session,
    *,
    current_member: Mapping[str, Any],
    new_role: str,
    new_status: str,
) -> None:
    is_current_active_admin = (
        current_member["role"] == "admin"
        and current_member["member_status"] == "active"
        and current_member["user_status"] == "active"
    )
    remains_active_admin = new_role == "admin" and new_status == "active"
    if not is_current_active_admin or remains_active_admin:
        return

    other_admin_count = _count_other_active_admins(
        db,
        tenant_id=current_member["tenant_id"],
        target_user_id=current_member["user_id"],
    )
    if other_admin_count < 1:
        raise TenantMemberGovernanceError("至少需要保留一个 active admin")


def _audit_action(
    *,
    old_role: str,
    new_role: str,
    old_status: str,
    new_status: str,
) -> str:
    role_changed = old_role != new_role
    status_changed = old_status != new_status
    if role_changed and status_changed:
        return "membership_updated"
    if role_changed:
        return "role_updated"
    return "status_updated"


def update_tenant_member(
    db: Session,
    *,
    tenant_key: str,
    target_user_id: int,
    actor_user_id: int,
    actor_scope: str,
    role: str | None = None,
    status: str | None = None,
    reason: str | None = None,
) -> Mapping[str, Any]:
    normalized_role = _normalize_optional(role)
    normalized_status = _normalize_optional(status)
    normalized_reason = (reason or "").strip() or None

    if normalized_role is None and normalized_status is None:
        raise TenantMemberGovernanceError("至少需要提供 role 或 status")
    if normalized_role is not None and normalized_role not in VALID_TENANT_MEMBER_ROLES:
        raise TenantMemberGovernanceError("角色无效，仅支持 admin/member/viewer")
    if normalized_status is not None and normalized_status not in VALID_TENANT_MEMBER_STATUSES:
        raise TenantMemberGovernanceError("成员状态无效，仅支持 active/inactive")
    if actor_scope not in {"tenant", "platform"}:
        raise TenantMemberGovernanceError("操作者范围无效")

    current_member = _load_tenant_member(
        db,
        tenant_key=tenant_key,
        user_id=target_user_id,
    )
    if current_member is None:
        raise TenantMemberGovernanceError("租户成员不存在")
    if current_member["tenant_status"] != "active":
        raise TenantMemberGovernanceError("租户状态不可用")

    old_role = current_member["role"]
    old_status = current_member["member_status"]
    new_role = normalized_role or old_role
    new_status = normalized_status or old_status

    _ensure_not_removing_last_active_admin(
        db,
        current_member=current_member,
        new_role=new_role,
        new_status=new_status,
    )

    if old_role == new_role and old_status == new_status:
        return current_member

    now = datetime.now(UTC)
    db.execute(
        text(
            """
            UPDATE user_tenants
            SET role = :role,
                status = :status
            WHERE user_id = :user_id
              AND tenant_id = :tenant_id
            """
        ),
        {
            "role": new_role,
            "status": new_status,
            "user_id": current_member["user_id"],
            "tenant_id": current_member["tenant_id"],
        },
    )
    db.execute(
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
              :actor_scope,
              :action,
              :old_role,
              :new_role,
              :old_status,
              :new_status,
              :reason,
              :created_at
            )
            """
        ),
        {
            "tenant_id": current_member["tenant_id"],
            "target_user_id": current_member["user_id"],
            "actor_user_id": actor_user_id,
            "actor_scope": actor_scope,
            "action": _audit_action(
                old_role=old_role,
                new_role=new_role,
                old_status=old_status,
                new_status=new_status,
            ),
            "old_role": old_role,
            "new_role": new_role,
            "old_status": old_status,
            "new_status": new_status,
            "reason": normalized_reason,
            "created_at": now,
        },
    )

    updated = _load_tenant_member(
        db,
        tenant_key=tenant_key,
        user_id=target_user_id,
    )
    if updated is None:
        raise TenantMemberGovernanceError("租户成员不存在")
    return updated
