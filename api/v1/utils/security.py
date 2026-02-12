import base64
import hashlib
import hmac
import json
import secrets
import time


def generate_executor_id(prefix: str = "exec_") -> str:
    """
    生成执行器唯一标识符。
    格式: exec_ + 8位随机十六进制字符
    """
    # 使用 secrets 生成 4 字节的随机数并转换为十六进制 (8位)
    random_suffix = secrets.token_hex(4)
    return f"{prefix}{random_suffix}"


def generate_api_key(prefix: str = "ek_") -> str:
    """
    生成高熵的 API Key。
    格式: ek_ + 32位随机十六进制字符
    """
    # 使用 secrets 生成 16 字节的随机数并转换为十六进制 (32位)
    random_key = secrets.token_hex(16)
    return f"{prefix}{random_key}"


def hash_password(password: str, iterations: int = 260000) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    parts = stored_hash.split("$", 3)
    if len(parts) != 4:
        return False
    algorithm, iterations, salt, digest = parts
    if algorithm != "pbkdf2_sha256":
        return False
    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(computed, digest)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def sign_token(payload: dict, secret: str) -> str:
    body = _base64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signature = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return f"{body}.{_base64url_encode(signature)}"


def verify_token(token: str, secret: str) -> dict:
    if "." not in token:
        raise ValueError("令牌无效")
    body, signature = token.split(".", 1)
    expected = hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(_base64url_encode(expected), signature):
        raise ValueError("令牌无效")
    payload = json.loads(_base64url_decode(body))
    exp = payload.get("exp")
    if exp and time.time() > exp:
        raise ValueError("令牌已过期")
    return payload
