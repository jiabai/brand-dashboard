from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from api.v1.utils.security import verify_token

ACCESS_TOKEN_EXPIRES_IN_SECONDS = 12 * 60 * 60


def create_access_token(
    user_id: int,
    secret: str,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    now = datetime.now(UTC)
    expires_at = now + (expires_delta or timedelta(seconds=ACCESS_TOKEN_EXPIRES_IN_SECONDS))
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_access_token(token: str, secret: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return verify_token(token, secret)

