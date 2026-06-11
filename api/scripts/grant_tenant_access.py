"""Grant an existing user access to an existing tenant.

This is a local/deployment operation script, not a public HTTP API.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _api_env_path() -> Path:
    return Path(__file__).resolve().parents[1] / ".env"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Grant tenant workspace access to a user.")
    parser.add_argument("--email", default=os.getenv("TENANT_ACCESS_GRANT_EMAIL"))
    parser.add_argument("--tenant-key", default=os.getenv("TENANT_ACCESS_GRANT_TENANT_KEY"))
    parser.add_argument(
        "--role",
        default=os.getenv("TENANT_ACCESS_GRANT_ROLE", "viewer"),
        choices=("viewer", "member", "admin"),
    )
    parser.add_argument("--actor-email", default=os.getenv("TENANT_ACCESS_GRANT_ACTOR_EMAIL"))
    parser.add_argument("--reason", default=os.getenv("TENANT_ACCESS_GRANT_REASON"))
    parser.add_argument(
        "--env-file",
        default=str(_api_env_path()),
        help="Path to the API .env file. Defaults to api/.env.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    load_dotenv(dotenv_path=Path(args.env_file))

    if not args.email:
        print("ERROR: 缺少 --email 或 TENANT_ACCESS_GRANT_EMAIL", file=sys.stderr)
        return 2
    if not args.tenant_key:
        print("ERROR: 缺少 --tenant-key 或 TENANT_ACCESS_GRANT_TENANT_KEY", file=sys.stderr)
        return 2

    if str(_project_root()) not in sys.path:
        sys.path.insert(0, str(_project_root()))

    from api.v1.repositories.connection import get_engine
    from api.v1.repositories.tenant_access import TenantAccessGrantError, grant_tenant_access

    try:
        result = grant_tenant_access(
            get_engine(),
            email=args.email,
            tenant_key=args.tenant_key,
            role=args.role,
            actor_email=args.actor_email,
            reason=args.reason,
        )
    except TenantAccessGrantError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    action_labels = {
        "created": "已创建租户访问授权",
        "exists": "租户访问授权已存在，未修改",
        "updated": "已更新租户访问角色",
        "reactivated": "已恢复租户访问授权",
    }
    print(action_labels.get(result["action"], result["action"]))
    print(f"email={result['email']}")
    print(f"tenant_key={result['tenant_key']}")
    print(f"role={result['role']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
