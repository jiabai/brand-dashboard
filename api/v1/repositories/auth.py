import os
import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List
from urllib.parse import urlparse

from sqlalchemy import Engine, text

from api.v1.utils.security import hash_password, sign_token, verify_password, verify_token


def _get_auth_secret() -> str:
    secret = os.getenv("AUTH_SECRET")
    if not secret:
        if os.getenv("ENV", "development") == "production":
            raise RuntimeError("AUTH_SECRET environment variable is required in production")
        return "dev_secret"
    return secret


def _generate_tenant_key() -> str:
    return f"tn_{secrets.token_hex(6)}"


def _generate_invite_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


def _build_tenant_base_url(subdomain: str | None) -> str:
    base_url = os.getenv("AUTH_BASE_URL", "https://yourplatform.com")
    parsed = urlparse(base_url)
    scheme = parsed.scheme or "https"
    host = parsed.netloc or parsed.path
    host = host.split("/")[0]
    if subdomain:
        if host.startswith(f"{subdomain}."):
            tenant_host = host
        else:
            tenant_host = f"{subdomain}.{host}"
    else:
        tenant_host = host
    return f"{scheme}://{tenant_host}"


def create_tenant_with_admin(engine: Engine, payload: Dict[str, Any]) -> Dict[str, Any]:
    tenant_name = payload["tenantName"]
    admin_email = payload["adminEmail"]
    preferred_subdomain = payload.get("preferredSubdomain")
    tenant_key = _generate_tenant_key()
    now = datetime.now(UTC)
    secret = _get_auth_secret()

    with engine.begin() as conn:
        existing_tenant = conn.execute(
            text("SELECT id FROM tenants WHERE tenant_name = :tenant_name"),
            {"tenant_name": tenant_name},
        ).fetchone()
        if existing_tenant:
            raise ValueError("企业名称已被使用")

        existing_email = conn.execute(
            text("SELECT id, status FROM users WHERE email = :email"),
            {"email": admin_email},
        ).fetchone()
        user_id = None
        if existing_email:
            user_id, status = existing_email
            if status in {"inactive", "suspended"}:
                raise ValueError("账号状态异常")

        if preferred_subdomain:
            existing_subdomain = conn.execute(
                text("SELECT id FROM tenants WHERE subdomain = :subdomain"),
                {"subdomain": preferred_subdomain},
            ).fetchone()
            if existing_subdomain:
                raise ValueError("子域名已被占用")

        tenant_result = conn.execute(
            text(
                """
                INSERT INTO tenants (
                    tenant_key,
                    tenant_name,
                    subdomain,
                    company_legal_name,
                    company_type,
                    registration_no,
                    industry,
                    contact_name,
                    contact_email,
                    contact_phone,
                    plan_type,
                    max_users,
                    billing_cycle,
                    contract_start_date,
                    contract_end_date,
                    created_by,
                    created_at,
                    updated_at
                ) VALUES (
                    :tenant_key,
                    :tenant_name,
                    :subdomain,
                    :company_legal_name,
                    :company_type,
                    :registration_no,
                    :industry,
                    :contact_name,
                    :contact_email,
                    :contact_phone,
                    :plan_type,
                    :max_users,
                    :billing_cycle,
                    :contract_start_date,
                    :contract_end_date,
                    :created_by,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "tenant_key": tenant_key,
                "tenant_name": tenant_name,
                "subdomain": preferred_subdomain,
                "company_legal_name": payload.get("companyLegalName"),
                "company_type": payload.get("companyType"),
                "registration_no": payload.get("registrationNo"),
                "industry": payload.get("industry"),
                "contact_name": payload.get("adminName"),
                "contact_email": admin_email,
                "contact_phone": payload.get("adminPhone"),
                "plan_type": payload.get("planType"),
                "max_users": payload.get("maxUsers"),
                "billing_cycle": payload.get("billingCycle"),
                "contract_start_date": payload.get("contractStartDate"),
                "contract_end_date": payload.get("contractEndDate"),
                "created_by": payload.get("salesPersonId"),
                "created_at": now,
                "updated_at": now,
            },
        )
        tenant_id = tenant_result.lastrowid

        if user_id is None:
            temp_password = secrets.token_urlsafe(16)
            password_hash = hash_password(temp_password)
            user_result = conn.execute(
                text(
                    """
                    INSERT INTO users (
                        user_key,
                        email,
                        password_hash,
                        first_name,
                        phone_number,
                        is_verified,
                        status,
                        created_at,
                        updated_at
                    ) VALUES (
                        :user_key,
                        :email,
                        :password_hash,
                        :first_name,
                        :phone_number,
                        :is_verified,
                        :status,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "user_key": secrets.token_hex(16),
                    "email": admin_email,
                    "password_hash": password_hash,
                    "first_name": payload.get("adminName"),
                    "phone_number": payload.get("adminPhone"),
                    "is_verified": False,
                    "status": "pending_activation",
                    "created_at": now,
                    "updated_at": now,
                },
            )
            user_id = user_result.lastrowid

        conn.execute(
            text(
                """
                INSERT INTO user_tenants (
                    user_id,
                    tenant_id,
                    role,
                    status,
                    created_at
                ) VALUES (
                    :user_id,
                    :tenant_id,
                    :role,
                    :status,
                    :created_at
                )
                """
            ),
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role": "admin",
                "status": "active",
                "created_at": now,
            },
        )

        invite_code = None
        for _ in range(5):
            candidate = _generate_invite_code()
            exists = conn.execute(
                text("SELECT 1 FROM invitation_codes WHERE code = :code"),
                {"code": candidate},
            ).fetchone()
            if not exists:
                invite_code = candidate
                break
        if not invite_code:
            raise ValueError("邀请码生成失败")

        expires_at = now + timedelta(days=30)
        conn.execute(
            text(
                """
                INSERT INTO invitation_codes (
                    tenant_id,
                    code,
                    status,
                    max_uses,
                    usage_count,
                    expires_at,
                    created_by,
                    created_at,
                    updated_at
                ) VALUES (
                    :tenant_id,
                    :code,
                    :status,
                    :max_uses,
                    :usage_count,
                    :expires_at,
                    :created_by,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "tenant_id": tenant_id,
                "code": invite_code,
                "status": "active",
                "max_uses": payload.get("maxUsers"),
                "usage_count": 0,
                "expires_at": expires_at,
                "created_by": user_id,
                "created_at": now,
                "updated_at": now,
            },
        )

    activation_token = sign_token(
        {
            "user_id": user_id,
            "tenant_key": tenant_key,
            "email": admin_email,
            "type": "activation",
            "exp": int((now + timedelta(days=7)).timestamp()),
        },
        secret,
    )

    tenant_base_url = _build_tenant_base_url(preferred_subdomain)
    return {
        "tenantKey": tenant_key,
        "tenantName": tenant_name,
        "adminEmail": admin_email,
        "activationToken": activation_token,
        "activationUrl": f"{tenant_base_url}/activate?token={activation_token}",
        "loginUrl": f"{tenant_base_url}/login",
        "inviteCode": invite_code,
    }


def activate_admin_account(engine: Engine, token: str, password: str) -> Dict[str, Any]:
    payload = verify_token(token, _get_auth_secret())
    if payload.get("type") != "activation":
        raise ValueError("无效的激活令牌")
    user_id = int(payload["user_id"])
    now = datetime.now(UTC)

    with engine.begin() as conn:
        user_row = conn.execute(
            text("SELECT id, email, status FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        ).fetchone()
        if not user_row:
            raise ValueError("用户不存在")
        if user_row[2] == "active":
            raise ValueError("账号已激活")

        conn.execute(
            text(
                """
                UPDATE users SET
                    password_hash = :password_hash,
                    status = :status,
                    is_verified = :is_verified,
                    updated_at = :updated_at
                WHERE id = :user_id
                """
            ),
            {
                "password_hash": hash_password(password),
                "status": "active",
                "is_verified": True,
                "updated_at": now,
                "user_id": user_id,
            },
        )

        tenant_row = conn.execute(
            text(
                """
                SELECT t.tenant_key, t.subdomain
                FROM tenants t
                JOIN user_tenants ut ON ut.tenant_id = t.id
                WHERE ut.user_id = :user_id
                LIMIT 1
                """
            ),
            {"user_id": user_id},
        ).fetchone()

    tenant_key = tenant_row[0] if tenant_row else payload.get("tenant_key")
    tenant_base_url = _build_tenant_base_url(tenant_row[1] if tenant_row else None)
    return {
        "userId": user_id,
        "email": user_row[1],
        "tenantKey": tenant_key,
        "loginUrl": f"{tenant_base_url}/login",
    }


def verify_invite_code(engine: Engine, code: str) -> Dict[str, Any]:
    now = datetime.now(UTC)
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT
                    ic.status,
                    ic.max_uses,
                    ic.usage_count,
                    ic.expires_at,
                    t.tenant_key,
                    t.tenant_name
                FROM invitation_codes ic
                JOIN tenants t ON ic.tenant_id = t.id
                WHERE ic.code = :code
                """
            ),
            {"code": code},
        ).fetchone()
    if not row:
        raise ValueError("邀请码不存在")
    status, max_uses, usage_count, expires_at, tenant_key, tenant_name = row
    if status != "active":
        raise ValueError("邀请码已失效")
    if expires_at and expires_at < now:
        raise ValueError("邀请码已过期")
    if max_uses is not None and usage_count >= max_uses:
        raise ValueError("邀请码使用次数已达上限")

    return {
        "tenantKey": tenant_key,
        "tenantName": tenant_name,
        "expiresAt": expires_at.isoformat() if expires_at else None,
    }


def register_employee(engine: Engine, payload: Dict[str, Any]) -> Dict[str, Any]:
    now = datetime.now(UTC)
    code = payload["inviteCode"]
    email = payload["email"]
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
                SELECT
                    ic.id,
                    ic.status,
                    ic.max_uses,
                    ic.usage_count,
                    ic.expires_at,
                    t.id,
                    t.tenant_key,
                    t.tenant_name
                FROM invitation_codes ic
                JOIN tenants t ON ic.tenant_id = t.id
                WHERE ic.code = :code
                """
            ),
            {"code": code},
        ).fetchone()
        if not row:
            raise ValueError("邀请码不存在")
        (
            invite_id,
            status,
            max_uses,
            usage_count,
            expires_at,
            tenant_id,
            tenant_key,
            tenant_name,
        ) = row
        if status != "active":
            raise ValueError("邀请码已失效")
        if expires_at and expires_at < now:
            raise ValueError("邀请码已过期")
        if max_uses is not None and usage_count >= max_uses:
            raise ValueError("邀请码使用次数已达上限")

        user_row = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()
        if user_row:
            user_id = user_row[0]
        else:
            user_result = conn.execute(
                text(
                    """
                    INSERT INTO users (
                        user_key,
                        email,
                        password_hash,
                        first_name,
                        phone_number,
                        is_verified,
                        status,
                        created_at,
                        updated_at
                    ) VALUES (
                        :user_key,
                        :email,
                        :password_hash,
                        :first_name,
                        :phone_number,
                        :is_verified,
                        :status,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "user_key": secrets.token_hex(16),
                    "email": email,
                    "password_hash": hash_password(payload["password"]),
                    "first_name": payload.get("realName"),
                    "phone_number": payload.get("phoneNumber"),
                    "is_verified": True,
                    "status": "active",
                    "created_at": now,
                    "updated_at": now,
                },
            )
            user_id = user_result.lastrowid

        existing_link = conn.execute(
            text(
                """
                SELECT 1 FROM user_tenants
                WHERE user_id = :user_id AND tenant_id = :tenant_id
                """
            ),
            {"user_id": user_id, "tenant_id": tenant_id},
        ).fetchone()
        if existing_link:
            raise ValueError("用户已加入该租户")

        conn.execute(
            text(
                """
                INSERT INTO user_tenants (
                    user_id,
                    tenant_id,
                    role,
                    status,
                    created_at
                ) VALUES (
                    :user_id,
                    :tenant_id,
                    :role,
                    :status,
                    :created_at
                )
                """
            ),
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role": "member",
                "status": "active",
                "created_at": now,
            },
        )

        conn.execute(
            text(
                """
                UPDATE invitation_codes SET
                    usage_count = usage_count + 1,
                    updated_at = :updated_at
                WHERE id = :invite_id
                """
            ),
            {"updated_at": now, "invite_id": invite_id},
        )

    return {
        "userId": user_id,
        "tenantKey": tenant_key,
        "tenantName": tenant_name,
    }


def authenticate_user(engine: Engine, email: str, password: str) -> Dict[str, Any]:
    with engine.begin() as conn:
        user_row = conn.execute(
            text(
                """
                SELECT id, email, password_hash, status
                FROM users
                WHERE email = :email
                """
            ),
            {"email": email},
        ).fetchone()
        if not user_row:
            raise ValueError("账号或密码错误")
        user_id, user_email, password_hash, status = user_row
        if status != "active":
            raise ValueError("账号未激活")
        if not verify_password(password, password_hash):
            raise ValueError("账号或密码错误")

        tenant_rows = conn.execute(
            text(
                """
                SELECT t.tenant_key, t.tenant_name
                FROM user_tenants ut
                JOIN tenants t ON ut.tenant_id = t.id
                WHERE ut.user_id = :user_id
                ORDER BY t.id ASC
                """
            ),
            {"user_id": user_id},
        ).fetchall()

    access_token = sign_token(
        {
            "user_id": user_id,
            "type": "access",
            "exp": int((datetime.now(UTC) + timedelta(hours=12)).timestamp()),
        },
        _get_auth_secret(),
    )

    tenants: List[Dict[str, Any]] = [
        {"tenantKey": row[0], "tenantName": row[1]} for row in tenant_rows
    ]

    return {
        "accessToken": access_token,
        "user": {
            "userId": user_id,
            "email": user_email,
            "tenants": tenants,
        },
    }
