"""Create or prepare the first platform administrator user.

This is a local/deployment bootstrap script, not a public HTTP API.
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
    parser = argparse.ArgumentParser(description="Bootstrap a platform administrator user.")
    parser.add_argument("--email", default=os.getenv("PLATFORM_BOOTSTRAP_ADMIN_EMAIL"))
    parser.add_argument("--password", default=os.getenv("PLATFORM_BOOTSTRAP_ADMIN_PASSWORD"))
    parser.add_argument(
        "--write-env",
        action="store_true",
        help="Add the email to api/.env PLATFORM_ADMIN_EMAILS if it is missing.",
    )
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Reset password when the active user already exists.",
    )
    parser.add_argument(
        "--env-file",
        default=str(_api_env_path()),
        help="Path to the API .env file. Defaults to api/.env.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    env_file = Path(args.env_file)
    load_dotenv(dotenv_path=env_file)

    if not args.email:
        print("ERROR: 缺少 --email 或 PLATFORM_BOOTSTRAP_ADMIN_EMAIL", file=sys.stderr)
        return 2
    if not args.password:
        print("ERROR: 缺少 --password 或 PLATFORM_BOOTSTRAP_ADMIN_PASSWORD", file=sys.stderr)
        return 2

    if str(_project_root()) not in sys.path:
        sys.path.insert(0, str(_project_root()))

    from api.v1.repositories.connection import get_engine
    from api.v1.repositories.platform_admins import (
        PlatformAdminBootstrapError,
        ensure_platform_admin_user,
        is_platform_admin_email,
        update_platform_admin_env_file,
    )

    normalized_email = args.email.strip().lower()
    env_changed = False

    if args.write_env and not is_platform_admin_email(normalized_email):
        env_result = update_platform_admin_env_file(env_file, normalized_email)
        os.environ["PLATFORM_ADMIN_EMAILS"] = env_result["platformAdminEmails"]
        env_changed = bool(env_result["changed"])

    try:
        result = ensure_platform_admin_user(
            get_engine(),
            email=normalized_email,
            password=args.password,
            reset_password=args.reset_password,
        )
    except PlatformAdminBootstrapError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    action_labels = {
        "created": "已创建平台管理员用户",
        "exists": "平台管理员用户已存在，未修改密码",
        "activated": "已激活平台管理员用户",
        "password_reset": "已重置平台管理员用户密码",
    }
    print(action_labels.get(result["action"], result["action"]))
    print(f"email={result['email']}")
    if env_changed:
        print("api/.env 已更新 PLATFORM_ADMIN_EMAILS，请重启后端服务使配置生效")
    else:
        print("PLATFORM_ADMIN_EMAILS 已包含该邮箱")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
