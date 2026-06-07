import os
import re
from typing import Any, Dict, Mapping, Optional
from urllib.parse import quote_plus


class DatabaseConfigError(ValueError):
    """Raised when database configuration is missing or invalid."""


_ENV_PLACEHOLDER_PATTERN = re.compile(
    r"^\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?::-(?P<default>.*))?\}$"
)


def _resolve_env_placeholder(
    value: Any, environ: Optional[Mapping[str, str]] = None
) -> Any:
    if not isinstance(value, str):
        return value

    text = value.strip()
    match = _ENV_PLACEHOLDER_PATTERN.match(text)
    if not match:
        return text

    env = os.environ if environ is None else environ
    name = match.group("name")
    env_value = env.get(name)
    if env_value:
        return env_value

    default = match.group("default")
    if default is not None:
        return default

    raise DatabaseConfigError(
        f"Missing required environment variable `{name}` for database config"
    )


def _required_string(db_cfg: Dict[str, Any], key: str) -> str:
    value = db_cfg.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DatabaseConfigError(f"Missing or invalid `brand_analysis.database.{key}`")
    return value.strip()


def _coerce_port(value: Any) -> int:
    if isinstance(value, str):
        if not value.isdigit():
            raise DatabaseConfigError("Invalid `brand_analysis.database.port`")
        value = int(value)
    if not isinstance(value, int) or not (1 <= value <= 65535):
        raise DatabaseConfigError("Invalid `brand_analysis.database.port`")
    return value


def resolve_database_config(
    db_cfg: Any, environ: Optional[Mapping[str, str]] = None
) -> Dict[str, Any]:
    if not isinstance(db_cfg, dict):
        raise DatabaseConfigError("Missing or invalid `brand_analysis.database` object")

    resolved = {
        key: _resolve_env_placeholder(value, environ)
        for key, value in db_cfg.items()
    }

    return {
        "host": _required_string(resolved, "host"),
        "port": _coerce_port(resolved.get("port", 3306)),
        "user": _required_string(resolved, "user"),
        "password": _required_string(resolved, "password"),
        "name": _required_string(resolved, "name"),
    }


def build_mysql_database_url(db_cfg: Any) -> str:
    resolved = resolve_database_config(db_cfg)
    user = quote_plus(resolved["user"])
    password = quote_plus(resolved["password"])
    host = resolved["host"]
    port = resolved["port"]
    name = quote_plus(resolved["name"])
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"
