from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from api.v1.repositories.auth import _get_auth_secret
from api.v1.repositories.connection import get_db
from api.v1.repositories.tenants import (
    get_tenant_summary_by_key,
    get_user_identity,
    get_user_tenant_membership,
)
from api.v1.utils.jwt_utils import verify_access_token
from api.v1.utils.platform_roles import get_platform_roles_for_email

TENANT_ROLE_TO_PRODUCT_ROLE = {
    "admin": "tenant_admin",
    "member": "tenant_member",
    "viewer": "tenant_viewer",
}


@dataclass(frozen=True)
class CurrentUser:
    user_id: int
    email: str
    status: str


@dataclass(frozen=True)
class CurrentTenantContext:
    tenant_key: str
    tenant_name: str
    role: str
    product_role: str
    access_scope: str = "tenant_member"


def _unauthorized(message: str = "未提供有效的认证令牌") -> HTTPException:
    return HTTPException(status_code=401, detail=message)


def _forbidden(message: str) -> HTTPException:
    return HTTPException(status_code=403, detail=message)


def get_current_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    db: Session = Depends(get_db),
) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise _unauthorized()

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise _unauthorized()

    try:
        payload = verify_access_token(token, _get_auth_secret())
    except Exception as exc:
        raise _unauthorized("认证令牌无效或已过期") from exc

    if payload.get("type") != "access":
        raise _unauthorized("令牌类型错误")

    subject = payload.get("sub") or payload.get("user_id")
    if subject is None:
        raise _unauthorized("令牌缺少用户身份")

    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise _unauthorized("令牌用户身份无效") from exc

    user_row = get_user_identity(db, user_id)
    if not user_row:
        raise _unauthorized("用户不存在")

    _, email, status = user_row
    if status != "active":
        raise _forbidden("账号不可用")

    return CurrentUser(user_id=user_id, email=email, status=status)


def _resolve_current_tenant(
    *,
    x_tenant_key: str | None,
    query_tenant_key: str | None,
    current_user: CurrentUser,
    db: Session,
    required_role: str | None,
) -> CurrentTenantContext:
    selected_tenant_key = (x_tenant_key or "").strip() or None
    query_tenant_key = (query_tenant_key or "").strip() or None

    if selected_tenant_key and query_tenant_key and selected_tenant_key != query_tenant_key:
        raise HTTPException(status_code=400, detail="租户上下文不一致")

    tenant_key = selected_tenant_key or query_tenant_key
    if not tenant_key:
        raise HTTPException(status_code=400, detail="缺少租户上下文")

    membership = get_user_tenant_membership(
        db,
        user_id=current_user.user_id,
        tenant_key=tenant_key,
    )
    if not membership:
        raise _forbidden("无权访问该租户")

    tenant_key, tenant_name, tenant_status, role, member_status = membership
    if tenant_status != "active":
        raise _forbidden("租户不可用")
    if member_status != "active":
        raise _forbidden("租户成员关系不可用")
    if required_role and role != required_role and role != "admin":
        raise _forbidden(f"需要 {required_role} 权限")

    return CurrentTenantContext(
        tenant_key=tenant_key,
        tenant_name=tenant_name,
        role=role,
        product_role=TENANT_ROLE_TO_PRODUCT_ROLE.get(role, role),
    )


def get_current_tenant(
    x_tenant_key: Annotated[str | None, Header(alias="X-Tenant-Key")] = None,
    query_tenant_key: Annotated[str | None, Query(alias="tenant_key")] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentTenantContext:
    return _resolve_current_tenant(
        x_tenant_key=x_tenant_key,
        query_tenant_key=query_tenant_key,
        current_user=current_user,
        db=db,
        required_role=None,
    )


def get_current_tenant_for_dashboard_read(
    x_tenant_key: Annotated[str | None, Header(alias="X-Tenant-Key")] = None,
    query_tenant_key: Annotated[str | None, Query(alias="tenant_key")] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentTenantContext:
    selected_tenant_key = (x_tenant_key or "").strip() or None
    query_tenant_key = (query_tenant_key or "").strip() or None

    if selected_tenant_key and query_tenant_key and selected_tenant_key != query_tenant_key:
        raise HTTPException(status_code=400, detail="租户上下文不一致")

    tenant_key = selected_tenant_key or query_tenant_key
    if not tenant_key:
        raise HTTPException(status_code=400, detail="缺少租户上下文")

    membership = get_user_tenant_membership(
        db,
        user_id=current_user.user_id,
        tenant_key=tenant_key,
    )
    if membership:
        tenant_key, tenant_name, tenant_status, role, member_status = membership
        if tenant_status != "active":
            raise _forbidden("租户不可用")
        if member_status != "active":
            raise _forbidden("租户成员关系不可用")
        return CurrentTenantContext(
            tenant_key=tenant_key,
            tenant_name=tenant_name,
            role=role,
            product_role=TENANT_ROLE_TO_PRODUCT_ROLE.get(role, role),
        )

    if "platform_admin" not in get_platform_roles_for_email(current_user.email):
        raise _forbidden("无权访问该租户")

    tenant = get_tenant_summary_by_key(db, tenant_key)
    if not tenant:
        raise _forbidden("无权访问该租户")

    tenant_key, tenant_name, tenant_status = tenant
    if tenant_status != "active":
        raise _forbidden("租户不可用")

    return CurrentTenantContext(
        tenant_key=tenant_key,
        tenant_name=tenant_name,
        role="platform_admin_readonly",
        product_role="platform_admin",
        access_scope="platform_readonly",
    )


def require_current_tenant(required_role: str | None = None):
    def dependency(
        x_tenant_key: Annotated[str | None, Header(alias="X-Tenant-Key")] = None,
        query_tenant_key: Annotated[str | None, Query(alias="tenant_key")] = None,
        current_user: CurrentUser = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> CurrentTenantContext:
        return _resolve_current_tenant(
            x_tenant_key=x_tenant_key,
            query_tenant_key=query_tenant_key,
            current_user=current_user,
            db=db,
            required_role=required_role,
        )

    return dependency


def require_platform_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    if "platform_admin" not in get_platform_roles_for_email(current_user.email):
        raise _forbidden("需要平台管理员权限")
    return current_user
