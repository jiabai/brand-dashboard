import os
import secrets
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, text
from sqlalchemy.engine import Connection

from api.v1.utils.security import hash_password


class PlatformAdminBootstrapError(ValueError):
    """Raised when a platform admin bootstrap operation is unsafe or invalid."""


def _parse_admin_emails(value: str | None) -> list[str]:
    return [item.strip().lower() for item in (value or "").split(",") if item.strip()]


def is_platform_admin_email(email: str, admin_emails: str | None = None) -> bool:
    configured = os.getenv("PLATFORM_ADMIN_EMAILS", "") if admin_emails is None else admin_emails
    return email.strip().lower() in set(_parse_admin_emails(configured))


def merge_platform_admin_email(existing: str | None, email: str) -> str:
    values = _parse_admin_emails(existing)
    normalized_email = email.strip().lower()
    if normalized_email and normalized_email not in values:
        values.append(normalized_email)
    return ",".join(values)


def update_platform_admin_env_file(path: str | Path, email: str) -> dict[str, Any]:
    env_path = Path(path)
    env_path.parent.mkdir(parents=True, exist_ok=True)

    existing_text = env_path.read_text(encoding="utf-8") if env_path.exists() else ""
    lines = existing_text.splitlines()
    next_value = None
    found = False
    next_lines = []

    for line in lines:
        if line.startswith("PLATFORM_ADMIN_EMAILS="):
            found = True
            current_value = line.split("=", 1)[1]
            next_value = merge_platform_admin_email(current_value, email)
            next_lines.append(f"PLATFORM_ADMIN_EMAILS={next_value}")
        else:
            next_lines.append(line)

    if not found:
        next_value = merge_platform_admin_email("", email)
        next_lines.append(f"PLATFORM_ADMIN_EMAILS={next_value}")

    next_text = "\n".join(next_lines).rstrip() + "\n"
    changed = next_text != existing_text
    if changed:
        env_path.write_text(next_text, encoding="utf-8")

    return {"changed": changed, "platformAdminEmails": next_value or ""}


def _transaction(engine_or_connection: Engine | Connection):
    if isinstance(engine_or_connection, Connection):
        return nullcontext(engine_or_connection)
    return engine_or_connection.begin()


def _validate_bootstrap_input(email: str, password: str) -> tuple[str, str]:
    normalized_email = email.strip().lower()
    if "@" not in normalized_email:
        raise PlatformAdminBootstrapError("邮箱格式无效")
    if len(password) < 8:
        raise PlatformAdminBootstrapError("密码至少需要 8 位")
    return normalized_email, password


def ensure_platform_admin_user(
    engine: Engine | Connection,
    *,
    email: str,
    password: str,
    admin_emails: str | None = None,
    reset_password: bool = False,
) -> dict[str, Any]:
    normalized_email, password = _validate_bootstrap_input(email, password)
    if not is_platform_admin_email(normalized_email, admin_emails):
        raise PlatformAdminBootstrapError(
            "邮箱未配置为平台管理员，请先设置 PLATFORM_ADMIN_EMAILS 或使用 --write-env"
        )

    now = datetime.now(UTC)
    with _transaction(engine) as conn:
        row = conn.execute(
            text(
                """
                SELECT id, email, password_hash, status
                FROM users
                WHERE email = :email
                """
            ),
            {"email": normalized_email},
        ).fetchone()

        if not row:
            result = conn.execute(
                text(
                    """
                    INSERT INTO users (
                        user_key,
                        email,
                        password_hash,
                        is_verified,
                        status,
                        created_at,
                        updated_at
                    ) VALUES (
                        :user_key,
                        :email,
                        :password_hash,
                        :is_verified,
                        :status,
                        :created_at,
                        :updated_at
                    )
                    """
                ),
                {
                    "user_key": secrets.token_hex(16),
                    "email": normalized_email,
                    "password_hash": hash_password(password),
                    "is_verified": True,
                    "status": "active",
                    "created_at": now,
                    "updated_at": now,
                },
            )
            return {"action": "created", "email": normalized_email, "userId": result.lastrowid}

        user_id, user_email, _password_hash, status = row
        if status in {"inactive", "suspended"}:
            raise PlatformAdminBootstrapError(f"账号状态为 {status}，请人工审查后再处理")

        if status == "pending_activation":
            conn.execute(
                text(
                    """
                    UPDATE users SET
                        password_hash = :password_hash,
                        is_verified = :is_verified,
                        status = :status,
                        updated_at = :updated_at
                    WHERE id = :user_id
                    """
                ),
                {
                    "password_hash": hash_password(password),
                    "is_verified": True,
                    "status": "active",
                    "updated_at": now,
                    "user_id": user_id,
                },
            )
            return {"action": "activated", "email": user_email, "userId": user_id}

        if reset_password:
            conn.execute(
                text(
                    """
                    UPDATE users SET
                        password_hash = :password_hash,
                        is_verified = :is_verified,
                        updated_at = :updated_at
                    WHERE id = :user_id
                    """
                ),
                {
                    "password_hash": hash_password(password),
                    "is_verified": True,
                    "updated_at": now,
                    "user_id": user_id,
                },
            )
            return {"action": "password_reset", "email": user_email, "userId": user_id}

        return {"action": "exists", "email": user_email, "userId": user_id}
