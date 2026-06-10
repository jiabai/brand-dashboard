# 自助密码重置与修改密码实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 租户用户可经登录页申请重置邮件并凭 1 小时一次性令牌设置新密码；已登录用户可在账户管理页验证当前密码后修改密码。

**Architecture:** 后端在 `api/v1/repositories/auth.py` 新增三个仓储函数（申请重置/凭令牌重置/修改密码），一次性语义由密码哈希指纹实现（无新表）；`email_sender.py` 新增重置邮件；`routes/auth.py` 新增两个公开路由（防枚举统一响应）与一个认证路由。前端登录页加第 4 个「重置」标签并将 `?token=` 自动填充改为路由感知，账户管理页加「修改密码」表单。

**Tech Stack:** FastAPI + SQLAlchemy text SQL、HMAC 签名令牌（既有 `sign_token/verify_token`）、pytest（内存 SQLite + TestClient）、React 18 + shadcn/ui、node:test 源码契约测试。

**Spec:** `docs/product-specs/20260610-password-reset-and-change.md`

**约定与上下文（执行者必读）：**

- 测试命令（PowerShell，仓库根目录）：
  - 后端单文件：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_password_reset.py -q`
  - 后端全量：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`（当前基线 194 passed）
  - 后端 lint：`uv run --project api ruff check api`
  - 前端测试：`npm --prefix web test`（当前基线 122 pass）；构建：`npm --prefix web run build`
  - 文档验证：`python scripts/validate_agents_docs.py --level ERROR`
- **暂存纪律**：工作区有他人未提交在途改动。每次 commit 只准 add 任务点名的文件，**严禁 `git add -A` / `git add .`**。目前带在途改动的目标文件只有三个：`api/v1/routes/auth.py`、`web/src/components/AccountManagement.jsx`、`web/src/components/__tests__/AccountManagement.test.js`、外加 `docs/SECURITY.md`——涉及这些文件的任务必须按「提交 blob = `git show HEAD:<file>` + 仅本任务增量」构造提交版本（Node 脚本拼内容 → `git hash-object -w --no-filters` → `git update-index --cacheinfo 100644,<hash>,<path>`），提交版本不得引用在途标识符，提交后用临时 worktree 或 `git show <commit>:<file>` 验证自洽；磁盘文件保持「在途 + 本任务」完整集成。其余目标文件全部干净，正常 `git add`。
- 错误信封：业务错误统一 `JSONResponse(status_code=4xx, content={"status":"error","message":...,"code":4xx})`。
- 防枚举是本功能最高优先级安全要求：`forgot-password` 对所有输入返回完全一致的 200 响应体。

---

### Task 1: 仓储函数（申请重置 / 凭令牌重置 / 修改密码）

**Files:**
- Create: `api/tests/test_password_reset.py`
- Modify: `api/v1/repositories/auth.py`（顶部 import + 在 `regenerate_admin_activation` 之后、`verify_invite_code` 之前新增）

- [ ] **Step 1: 写失败的仓储测试**

创建 `api/tests/test_password_reset.py`：

```python
from datetime import UTC, datetime, timedelta

import pytest
from api.v1.repositories import auth as auth_repository
from api.v1.utils.security import hash_password, sign_token, verify_password
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def memory_engine(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    monkeypatch.setenv("AUTH_BASE_URL", "https://example.com")
    auth_repository._reset_email_last_sent.clear()
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key VARCHAR(36) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    is_verified BOOLEAN NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
    return engine


def _seed_user(engine, *, email="user@demo.test", password="OldPass12345", status="active"):
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO users (
                    user_key, email, password_hash, is_verified, status, created_at, updated_at
                ) VALUES (:user_key, :email, :password_hash, 1, :status, :now, :now)
                """
            ),
            {
                "user_key": f"uk_{email}",
                "email": email,
                "password_hash": hash_password(password),
                "status": status,
                "now": now,
            },
        )
        return conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()[0]


def _password_hash_of(engine, user_id):
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT password_hash FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        ).fetchone()[0]


def test_request_reset_returns_token_payload_for_active_user(memory_engine):
    user_id = _seed_user(memory_engine)

    result = auth_repository.request_password_reset(memory_engine, "user@demo.test")

    assert result is not None
    assert result["email"] == "user@demo.test"
    assert result["resetUrl"].startswith("https://example.com/reset-password?token=")
    activation = auth_repository.reset_password_with_token(
        memory_engine, result["resetToken"], "NewPass12345"
    )
    assert activation["userId"] == user_id
    assert verify_password("NewPass12345", _password_hash_of(memory_engine, user_id))


def test_request_reset_returns_none_for_unknown_and_inactive_users(memory_engine):
    _seed_user(memory_engine, email="pending@demo.test", status="pending_activation")
    _seed_user(memory_engine, email="suspended@demo.test", status="suspended")

    assert auth_repository.request_password_reset(memory_engine, "missing@demo.test") is None
    assert auth_repository.request_password_reset(memory_engine, "pending@demo.test") is None
    assert auth_repository.request_password_reset(memory_engine, "suspended@demo.test") is None


def test_request_reset_enforces_per_email_cooldown(memory_engine):
    _seed_user(memory_engine)

    first = auth_repository.request_password_reset(memory_engine, "user@demo.test")
    second = auth_repository.request_password_reset(memory_engine, "user@demo.test")

    assert first is not None
    assert second is None


def test_reset_token_is_single_use(memory_engine):
    _seed_user(memory_engine)
    result = auth_repository.request_password_reset(memory_engine, "user@demo.test")

    auth_repository.reset_password_with_token(memory_engine, result["resetToken"], "NewPass12345")
    with pytest.raises(ValueError, match="重置链接无效或已失效"):
        auth_repository.reset_password_with_token(
            memory_engine, result["resetToken"], "OtherPass12345"
        )


def test_password_change_invalidates_outstanding_reset_tokens(memory_engine):
    user_id = _seed_user(memory_engine)
    result = auth_repository.request_password_reset(memory_engine, "user@demo.test")

    auth_repository.change_password(memory_engine, user_id, "OldPass12345", "ChangedPass1")
    with pytest.raises(ValueError, match="重置链接无效或已失效"):
        auth_repository.reset_password_with_token(
            memory_engine, result["resetToken"], "NewPass12345"
        )


def test_reset_rejects_expired_token(memory_engine):
    user_id = _seed_user(memory_engine)
    password_hash = _password_hash_of(memory_engine, user_id)
    expired_token = sign_token(
        {
            "user_id": user_id,
            "email": "user@demo.test",
            "type": "password_reset",
            "pwd_fp": auth_repository._password_fingerprint(password_hash),
            "exp": int((datetime.now(UTC) - timedelta(minutes=1)).timestamp()),
        },
        "test-secret-with-at-least-32-bytes",
    )

    with pytest.raises(ValueError, match="重置链接无效或已失效"):
        auth_repository.reset_password_with_token(memory_engine, expired_token, "NewPass12345")


def test_reset_rejects_activation_token_type(memory_engine):
    user_id = _seed_user(memory_engine)
    activation_token = sign_token(
        {
            "user_id": user_id,
            "email": "user@demo.test",
            "type": "activation",
            "exp": int((datetime.now(UTC) + timedelta(days=7)).timestamp()),
        },
        "test-secret-with-at-least-32-bytes",
    )

    with pytest.raises(ValueError, match="重置链接无效或已失效"):
        auth_repository.reset_password_with_token(
            memory_engine, activation_token, "NewPass12345"
        )


def test_change_password_requires_correct_current_password(memory_engine):
    user_id = _seed_user(memory_engine)

    with pytest.raises(ValueError, match="当前密码错误"):
        auth_repository.change_password(memory_engine, user_id, "WrongPass123", "NewPass12345")

    auth_repository.change_password(memory_engine, user_id, "OldPass12345", "NewPass12345")
    assert verify_password("NewPass12345", _password_hash_of(memory_engine, user_id))
```

- [ ] **Step 2: 运行测试确认失败**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_password_reset.py -q`
Expected: FAIL，fixture 阶段报 `AttributeError: ... has no attribute '_reset_email_last_sent'`

- [ ] **Step 3: 实现仓储函数**

`api/v1/repositories/auth.py` 修改一：顶部 import 块（第 1-6 行区域）加入 `hashlib` 与 `time`：

```python
import hashlib
import os
import secrets
import string
import time
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List
from urllib.parse import urlparse
```

修改二：在 `regenerate_admin_activation` 函数之后、`verify_invite_code` 之前新增：

```python
RESET_TOKEN_TTL_SECONDS = 3600
_RESET_EMAIL_COOLDOWN_SECONDS = 60
_reset_email_last_sent: Dict[str, float] = {}


def _password_fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode("utf-8")).hexdigest()[:16]


def request_password_reset(engine: Engine, email: str) -> Dict[str, Any] | None:
    """为 active 账号签发 1 小时重置令牌。

    防枚举契约：邮箱不存在、账号非 active、冷却期内一律返回 None，
    调用方不得让响应体现任何差异。冷却为进程内存级，按邮箱 60 秒。
    """
    now = time.time()
    last_sent = _reset_email_last_sent.get(email)
    if last_sent is not None and now - last_sent < _RESET_EMAIL_COOLDOWN_SECONDS:
        return None

    with engine.connect() as conn:
        user_row = conn.execute(
            text(
                "SELECT id, email, password_hash, status FROM users"
                " WHERE email = :email"
            ),
            {"email": email},
        ).fetchone()
    if not user_row or user_row[3] != "active":
        return None

    user_id, user_email, password_hash, _status = user_row
    reset_token = sign_token(
        {
            "user_id": user_id,
            "email": user_email,
            "type": "password_reset",
            "pwd_fp": _password_fingerprint(password_hash),
            "exp": int(datetime.now(UTC).timestamp()) + RESET_TOKEN_TTL_SECONDS,
        },
        _get_auth_secret(),
    )
    _reset_email_last_sent[email] = now
    base_url = _build_tenant_base_url(None)
    return {
        "email": user_email,
        "resetToken": reset_token,
        "resetUrl": f"{base_url}/reset-password?token={reset_token}",
    }


def reset_password_with_token(engine: Engine, token: str, password: str) -> Dict[str, Any]:
    """凭重置令牌设置新密码。

    对外失败文案统一为「重置链接无效或已失效」，不区分签名错误、过期、
    类型不符与指纹不匹配（已使用或密码已变更），避免泄露令牌状态。
    """
    try:
        payload = verify_token(token, _get_auth_secret())
    except ValueError as exc:
        raise ValueError("重置链接无效或已失效") from exc
    if payload.get("type") != "password_reset":
        raise ValueError("重置链接无效或已失效")
    user_id = int(payload["user_id"])
    now = datetime.now(UTC)

    with engine.begin() as conn:
        user_row = conn.execute(
            text(
                "SELECT id, email, password_hash, status FROM users"
                " WHERE id = :user_id"
            ),
            {"user_id": user_id},
        ).fetchone()
        if (
            not user_row
            or user_row[3] != "active"
            or _password_fingerprint(user_row[2]) != payload.get("pwd_fp")
        ):
            raise ValueError("重置链接无效或已失效")
        conn.execute(
            text(
                """
                UPDATE users SET
                    password_hash = :password_hash,
                    updated_at = :updated_at
                WHERE id = :user_id
                """
            ),
            {
                "password_hash": hash_password(password),
                "updated_at": now,
                "user_id": user_id,
            },
        )
    return {"userId": user_id, "email": user_row[1]}


def change_password(
    engine: Engine, user_id: int, current_password: str, new_password: str
) -> Dict[str, Any]:
    now = datetime.now(UTC)
    with engine.begin() as conn:
        user_row = conn.execute(
            text("SELECT id, email, password_hash FROM users WHERE id = :user_id"),
            {"user_id": user_id},
        ).fetchone()
        if not user_row:
            raise ValueError("用户不存在")
        if not verify_password(current_password, user_row[2]):
            raise ValueError("当前密码错误")
        conn.execute(
            text(
                """
                UPDATE users SET
                    password_hash = :password_hash,
                    updated_at = :updated_at
                WHERE id = :user_id
                """
            ),
            {
                "password_hash": hash_password(new_password),
                "updated_at": now,
                "user_id": user_id,
            },
        )
    return {"userId": user_id, "email": user_row[1]}
```

说明：`Engine`、`Dict`、`Any`、`datetime`、`UTC`、`text`、`sign_token`、`verify_token`、`hash_password`、`verify_password`、`_get_auth_secret`、`_build_tenant_base_url` 均已存在；本任务新增 import 只有 `hashlib` 和 `time`。

- [ ] **Step 4: 运行测试确认通过**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_password_reset.py -q`
Expected: 8 passed

- [ ] **Step 5: Commit**（两文件均干净，正常 add）

```powershell
git add api/tests/test_password_reset.py api/v1/repositories/auth.py
git commit -m @'
feat: 新增密码重置与修改密码仓储函数

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 2: 重置邮件发送函数

**Files:**
- Modify: `api/v1/services/email_sender.py`（文件末尾新增）
- Modify: `api/tests/test_email_sender.py`（追加测试类）

- [ ] **Step 1: 写失败的测试**

`api/tests/test_email_sender.py` 顶部 import 行改为：

```python
from api.v1.services.email_sender import (
    send_admin_activation_email,
    send_password_reset_email,
)
```

文件末尾追加：

```python
class TestPasswordResetEmailSender(unittest.TestCase):
    def test_returns_not_configured_when_smtp_settings_are_missing(self):
        reset_result = {
            "email": "user@acme.test",
            "resetUrl": "https://example.com/reset-password?token=token",
        }

        with patch.dict(os.environ, {}, clear=True):
            result = send_password_reset_email(reset_result)

        self.assertEqual(result["status"], "not_configured")
        self.assertEqual(result["to"], "user@acme.test")
        self.assertEqual(result["message"], "SMTP 未配置，未发送重置邮件")

    def test_sends_reset_email_with_url_and_expiry_hint(self):
        reset_result = {
            "email": "user@acme.test",
            "resetUrl": "https://example.com/reset-password?token=token",
        }
        smtp_instance = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = smtp_instance
        smtp_context.__exit__.return_value = False

        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.163.com",
                "SMTP_PORT": "465",
                "SMTP_USERNAME": "sender@example.com",
                "SMTP_PASSWORD": "smtp-secret",
                "SMTP_FROM": "sender@example.com",
                "SMTP_USE_TLS": "true",
            },
            clear=True,
        ), patch(
            "api.v1.services.email_sender.smtplib.SMTP_SSL",
            return_value=smtp_context,
        ):
            result = send_password_reset_email(reset_result)

        self.assertEqual(result["status"], "sent")
        message = smtp_instance.send_message.call_args.args[0]
        self.assertEqual(message["To"], "user@acme.test")
        self.assertIn("密码重置", message["Subject"])
        body = message.get_content()
        self.assertIn("https://example.com/reset-password?token=token", body)
        self.assertIn("1 小时内", body)
        self.assertIn("请忽略此邮件", body)

    def test_returns_failed_without_leaking_smtp_exception_details(self):
        reset_result = {
            "email": "user@acme.test",
            "resetUrl": "https://example.com/reset-password?token=token",
        }

        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.163.com",
                "SMTP_PORT": "465",
                "SMTP_USERNAME": "sender@example.com",
                "SMTP_PASSWORD": "smtp-secret",
                "SMTP_FROM": "sender@example.com",
                "SMTP_USE_TLS": "true",
            },
            clear=True,
        ), patch(
            "api.v1.services.email_sender.smtplib.SMTP_SSL",
            side_effect=RuntimeError("smtp-secret leaked in raw exception"),
        ):
            result = send_password_reset_email(reset_result)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["message"], "重置邮件发送失败")
        self.assertNotIn("smtp-secret", str(result))
```

- [ ] **Step 2: 运行测试确认失败**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_email_sender.py -q`
Expected: FAIL，`ImportError: cannot import name 'send_password_reset_email'`

- [ ] **Step 3: 实现邮件函数**

`api/v1/services/email_sender.py` 常量区（第 8-10 行之后）追加：

```python
RESET_EMAIL_SENT_MESSAGE = "重置邮件已发送"
RESET_EMAIL_NOT_CONFIGURED_MESSAGE = "SMTP 未配置，未发送重置邮件"
RESET_EMAIL_FAILED_MESSAGE = "重置邮件发送失败"
```

文件末尾追加：

```python
def _build_password_reset_message(
    config: SmtpConfig, reset_result: Dict[str, Any]
) -> EmailMessage:
    email = reset_result.get("email") or ""
    reset_url = reset_result.get("resetUrl") or ""

    message = EmailMessage()
    message["From"] = config.sender
    message["To"] = email
    message["Subject"] = "Brand Dashboard 密码重置"
    message.set_content(
        "\n".join(
            [
                "您好，我们收到了此邮箱的密码重置申请。",
                "",
                "请在 1 小时内打开以下链接设置新密码：",
                reset_url,
                "",
                "如果不是您本人操作，请忽略此邮件，密码不会被修改。",
            ]
        )
    )
    return message


def send_password_reset_email(reset_result: Dict[str, Any]) -> Dict[str, str | None]:
    """发送密码重置邮件。返回值仅用于服务端观测与测试；

    防枚举要求公开接口的响应不得包含本函数的任何返回内容。
    """
    email = reset_result.get("email")
    try:
        config = _load_smtp_config()
        if not config:
            return {
                "status": "not_configured",
                "to": email,
                "message": RESET_EMAIL_NOT_CONFIGURED_MESSAGE,
            }

        message = _build_password_reset_message(config, reset_result)
        _send_message(config, message)
        return {
            "status": "sent",
            "to": email,
            "message": RESET_EMAIL_SENT_MESSAGE,
        }
    except Exception:
        return {
            "status": "failed",
            "to": email,
            "message": RESET_EMAIL_FAILED_MESSAGE,
        }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_email_sender.py -q`
Expected: 6 passed（原 3 + 新 3）

- [ ] **Step 5: Commit**（两文件均干净）

```powershell
git add api/v1/services/email_sender.py api/tests/test_email_sender.py
git commit -m @'
feat: 新增密码重置邮件发送函数

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 3: 三个密码路由（含防枚举集成测试）

**Files:**
- Modify: `api/tests/test_password_reset.py`（追加路由测试）
- Modify: `api/v1/routes/auth.py`（⚠️ 带在途改动，过滤暂存）

- [ ] **Step 1: 追加失败的路由测试**

`api/tests/test_password_reset.py` 顶部 import 区追加：

```python
from unittest.mock import patch

from api.v1.dependencies.auth import CurrentUser, get_current_user
from api.v1.repositories.connection import get_engine
from api.v1.routes import auth as auth_routes
from fastapi import FastAPI
from fastapi.testclient import TestClient
```

文件末尾追加：

```python
def _public_client(memory_engine):
    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/api/v1")
    app.dependency_overrides[get_engine] = lambda: memory_engine
    return TestClient(app)


def _authed_client(memory_engine, user_id):
    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/api/v1")
    app.dependency_overrides[get_engine] = lambda: memory_engine
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id,
        email="user@demo.test",
        status="active",
    )
    return TestClient(app)


def test_forgot_password_responses_are_byte_identical(memory_engine):
    _seed_user(memory_engine)
    _seed_user(memory_engine, email="pending@demo.test", status="pending_activation")
    client = _public_client(memory_engine)

    responses = []
    with patch(
        "api.v1.routes.auth.send_password_reset_email",
        return_value={"status": "sent", "to": None, "message": ""},
    ):
        for email in [
            "user@demo.test",
            "missing@demo.test",
            "pending@demo.test",
            "user@demo.test",
        ]:
            responses.append(client.post(
                "/api/v1/public/auth/forgot-password", json={"email": email}
            ))

    assert {r.status_code for r in responses} == {200}
    assert len({r.text for r in responses}) == 1
    body = responses[0].json()
    assert body["message"] == "如果该邮箱已注册并激活，重置邮件已发送"
    assert body["data"] is None


def test_forgot_password_sends_email_only_for_active_user(memory_engine):
    _seed_user(memory_engine)
    client = _public_client(memory_engine)

    with patch(
        "api.v1.routes.auth.send_password_reset_email",
        return_value={"status": "sent", "to": None, "message": ""},
    ) as send_email:
        client.post("/api/v1/public/auth/forgot-password", json={"email": "user@demo.test"})
        client.post("/api/v1/public/auth/forgot-password", json={"email": "missing@demo.test"})

    send_email.assert_called_once()
    sent_payload = send_email.call_args.args[0]
    assert sent_payload["email"] == "user@demo.test"
    assert sent_payload["resetUrl"].startswith("https://example.com/reset-password?token=")


def test_forgot_password_swallows_email_exceptions(memory_engine):
    _seed_user(memory_engine)
    client = _public_client(memory_engine)

    with patch(
        "api.v1.routes.auth.send_password_reset_email",
        side_effect=RuntimeError("smtp-secret leaked"),
    ):
        response = client.post(
            "/api/v1/public/auth/forgot-password", json={"email": "user@demo.test"}
        )

    assert response.status_code == 200
    assert "smtp-secret" not in response.text


def test_reset_password_route_roundtrip(memory_engine):
    _seed_user(memory_engine)
    client = _public_client(memory_engine)

    with patch(
        "api.v1.routes.auth.send_password_reset_email",
        return_value={"status": "sent", "to": None, "message": ""},
    ) as send_email:
        client.post("/api/v1/public/auth/forgot-password", json={"email": "user@demo.test"})
    token = send_email.call_args.args[0]["resetToken"]

    response = client.post(
        "/api/v1/public/auth/reset-password",
        json={"token": token, "password": "NewPass12345", "confirmPassword": "NewPass12345"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "密码已重置"

    login = client.post(
        "/api/v1/public/auth/login",
        json={"email": "user@demo.test", "password": "NewPass12345"},
    )
    assert login.status_code == 200


def test_reset_password_route_rejects_mismatch_and_bad_token(memory_engine):
    client = _public_client(memory_engine)

    mismatch = client.post(
        "/api/v1/public/auth/reset-password",
        json={"token": "x.y", "password": "NewPass12345", "confirmPassword": "Different123"},
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["message"] == "两次密码不一致"

    bad_token = client.post(
        "/api/v1/public/auth/reset-password",
        json={"token": "x.y", "password": "NewPass12345", "confirmPassword": "NewPass12345"},
    )
    assert bad_token.status_code == 400
    assert bad_token.json()["message"] == "重置链接无效或已失效"


def test_change_password_route_requires_auth_and_current_password(memory_engine):
    user_id = _seed_user(memory_engine)

    unauthed = _public_client(memory_engine).post(
        "/api/v1/auth/change-password",
        json={
            "currentPassword": "OldPass12345",
            "newPassword": "NewPass12345",
            "confirmPassword": "NewPass12345",
        },
    )
    assert unauthed.status_code == 401

    client = _authed_client(memory_engine, user_id)
    wrong = client.post(
        "/api/v1/auth/change-password",
        json={
            "currentPassword": "WrongPass123",
            "newPassword": "NewPass12345",
            "confirmPassword": "NewPass12345",
        },
    )
    assert wrong.status_code == 400
    assert wrong.json()["message"] == "当前密码错误"

    ok = client.post(
        "/api/v1/auth/change-password",
        json={
            "currentPassword": "OldPass12345",
            "newPassword": "NewPass12345",
            "confirmPassword": "NewPass12345",
        },
    )
    assert ok.status_code == 200
    assert ok.json()["message"] == "密码已修改"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_password_reset.py -q`
Expected: 新增 6 个路由测试 FAIL（patch 目标缺失报 `AttributeError` / 路由不存在 404），原 8 个仓储测试 PASS

- [ ] **Step 3: 实现路由**

`api/v1/routes/auth.py` 修改一：repositories.auth 导入块按字母序加入三个函数：

```python
from api.v1.repositories.auth import (
    activate_admin_account,
    authenticate_user,
    change_password,
    create_tenant_with_admin,
    regenerate_admin_activation,
    register_employee,
    request_password_reset,
    reset_password_with_token,
    verify_invite_code,
)
```

修改二：email_sender 导入块加入 `send_password_reset_email`：

```python
from api.v1.services.email_sender import (
    EMAIL_FAILED_MESSAGE,
    send_admin_activation_email,
    send_password_reset_email,
)
```

修改三：Pydantic 模型区（`VerifyInviteCodeRequest` 之后）追加：

```python
class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=1)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    confirmPassword: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(..., min_length=1)
    newPassword: str = Field(..., min_length=8)
    confirmPassword: str = Field(..., min_length=8)
```

修改四：在 `login_handler`（`@router.post("/public/auth/login")`）函数体之后、`get_me_handler` 之前追加三个路由：

```python
FORGOT_PASSWORD_MESSAGE = "如果该邮箱已注册并激活，重置邮件已发送"


@router.post("/public/auth/forgot-password")
def forgot_password_handler(
    request: ForgotPasswordRequest, engine: Engine = Depends(get_engine)
):
    reset_payload = request_password_reset(engine, request.email)
    if reset_payload is not None:
        try:
            send_password_reset_email(reset_payload)
        except Exception:
            pass
    return {
        "status": "success",
        "data": None,
        "message": FORGOT_PASSWORD_MESSAGE,
        "code": 200,
    }


@router.post("/public/auth/reset-password")
def reset_password_handler(
    request: ResetPasswordRequest, engine: Engine = Depends(get_engine)
):
    if request.password != request.confirmPassword:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "两次密码不一致", "code": 400},
        )
    try:
        reset_password_with_token(engine, request.token, request.password)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    return {"status": "success", "data": None, "message": "密码已重置", "code": 200}


@router.post("/auth/change-password")
def change_password_handler(
    request: ChangePasswordRequest,
    engine: Engine = Depends(get_engine),
    current_user: CurrentUser = Depends(get_current_user),
):
    if request.newPassword != request.confirmPassword:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "两次密码不一致", "code": 400},
        )
    try:
        change_password(
            engine, current_user.user_id, request.currentPassword, request.newPassword
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    return {"status": "success", "data": None, "message": "密码已修改", "code": 200}
```

说明：`Engine`、`Depends`、`JSONResponse`、`BaseModel`、`Field`、`get_engine`、`get_current_user`、`CurrentUser` 均已导入。`forgot-password` 的防枚举要求：响应字面量三处路径完全一致，不携带 `emailDelivery`。

- [ ] **Step 4: 运行测试确认通过**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_password_reset.py -q`
Expected: 14 passed（8 仓储 + 6 路由）

- [ ] **Step 5: 后端回归与 lint**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
Expected: 约 211 passed（194 基线 + Task 1 的 8 + Task 2 的 3 + 本任务的 6），0 失败

Run: `uv run --project api ruff check api`
Expected: All checks passed!

- [ ] **Step 6: ⚠️ 过滤暂存与提交**

`api/v1/routes/auth.py` 带他人在途改动（成员治理路由，引用未跟踪文件 `api/v1/repositories/tenant_members.py`）。提交 blob = `git show HEAD:api/v1/routes/auth.py` + 仅本任务四处修改（导入两处、模型、路由），不得包含任何 `tenant_members` / `TenantMemberGovernance` / `/members` 内容。构造后静态核对提交版本所有 import 在提交树存在，并用临时 worktree 跑 `pytest api/tests/test_password_reset.py`（标准做法见 Task 2 of 前序功能 commit 12c8519）。测试文件干净，正常 add。

```powershell
git add api/tests/test_password_reset.py
# routes/auth.py 经 hash-object/update-index 注入后：
git commit -m @'
feat: 新增忘记密码、重置密码与修改密码接口

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

提交后核对：`git show --stat HEAD` 恰好 2 个文件；`git diff HEAD -- api/v1/routes/auth.py` 残留只含在途治理 hunk。

---

### Task 4: 前端 API 适配器

**Files:**
- Modify: `web/src/api/auth.js`（干净）
- Modify: `web/src/api/index.js`（先核对：若该 barrel 文件存在且 re-export auth.js，确认新函数随之导出；若需显式列出则补；该文件当前干净）
- Create: `web/src/api/__tests__/auth.test.js`

- [ ] **Step 1: 写失败的适配器测试**

创建 `web/src/api/__tests__/auth.test.js`：

```js
import test from 'node:test';
import assert from 'node:assert/strict';

import { changePassword, forgotPassword, resetPassword } from '../auth.js';
import { clearAuthSession, writeAuthSession } from '../../auth/storage.js';

class MemoryStorage {
  constructor() {
    this.map = new Map();
  }

  getItem(key) {
    return this.map.has(key) ? this.map.get(key) : null;
  }

  setItem(key, value) {
    this.map.set(key, String(value));
  }

  removeItem(key) {
    this.map.delete(key);
  }
}

const jsonResponse = (payload) => ({
  ok: true,
  status: 200,
  json: async () => payload,
  text: async () => JSON.stringify(payload),
});

test.beforeEach(() => {
  globalThis.localStorage = new MemoryStorage();
});

test.afterEach(() => {
  clearAuthSession();
  delete globalThis.localStorage;
  delete globalThis.fetch;
});

test('forgotPassword posts email to the public endpoint', async () => {
  let requestedUrl;
  let requestedOptions;
  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestedOptions = options;
    return jsonResponse({ status: 'success', message: '如果该邮箱已注册并激活，重置邮件已发送' });
  };

  await forgotPassword({ email: 'user@demo.test' });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/public/auth/forgot-password');
  assert.equal(requestedOptions.method, 'POST');
  assert.equal(JSON.parse(requestedOptions.body).email, 'user@demo.test');
});

test('resetPassword posts token and passwords', async () => {
  let requestedUrl;
  let requestedOptions;
  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestedOptions = options;
    return jsonResponse({ status: 'success', message: '密码已重置' });
  };

  await resetPassword({ token: 't.t', password: 'NewPass12345', confirmPassword: 'NewPass12345' });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/public/auth/reset-password');
  assert.equal(requestedOptions.method, 'POST');
  assert.equal(JSON.parse(requestedOptions.body).token, 't.t');
});

test('changePassword posts with authorization header', async () => {
  writeAuthSession({
    accessToken: 'user-token',
    currentTenantKey: 'tn_demo',
    user: { tenants: [{ tenantKey: 'tn_demo', status: 'active' }] },
  });

  let requestedUrl;
  let requestedOptions;
  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestedOptions = options;
    return jsonResponse({ status: 'success', message: '密码已修改' });
  };

  await changePassword({
    currentPassword: 'OldPass12345',
    newPassword: 'NewPass12345',
    confirmPassword: 'NewPass12345',
  });

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(parsed.pathname, '/api/v1/auth/change-password');
  assert.equal(requestedOptions.method, 'POST');
  assert.equal(requestedOptions.headers.Authorization, 'Bearer user-token');
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix web test`
Expected: FAIL，`does not provide an export named 'changePassword'`（或 forgotPassword）

- [ ] **Step 3: 实现适配器**

`web/src/api/auth.js` 在 `login` 之后、`getMe` 之前追加：

```js
export const forgotPassword = (payload, options) => {
  return post('/api/v1/public/auth/forgot-password', payload, options);
};

export const resetPassword = (payload, options) => {
  return post('/api/v1/public/auth/reset-password', payload, options);
};

export const changePassword = (payload, options) => {
  return post('/api/v1/auth/change-password', payload, options);
};
```

随后核对 `web/src/api/index.js`：若 barrel 用 `export * from './auth.js'` 则无需改动；若逐名导出则按字母序补三个名字。

- [ ] **Step 4: 运行测试确认通过**

Run: `npm --prefix web test`
Expected: 全部通过（基线 122 + 新增 3 = 125 pass）

- [ ] **Step 5: Commit**（涉及文件均干净；index.js 未改动则不加）

```powershell
git add web/src/api/auth.js web/src/api/__tests__/auth.test.js
# 若改了 barrel：git add web/src/api/index.js
git commit -m @'
feat: 前端新增密码重置与修改密码 API 适配器

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 5: 登录页「重置」标签与路由感知令牌填充

**Files:**
- Create: `web/src/components/__tests__/loginView.test.js`
- Modify: `web/src/components/LoginView.jsx`（干净）
- Modify: `web/src/App.jsx`（干净）

- [ ] **Step 1: 写失败的契约测试**

创建 `web/src/components/__tests__/loginView.test.js`：

```js
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const loginViewSource = readFileSync(resolve(__dirname, '../LoginView.jsx'), 'utf8');
const appSource = readFileSync(resolve(__dirname, '../../App.jsx'), 'utf8');

describe('LoginView password reset contract', () => {
  it('exposes a forgot password entry and a reset tab', () => {
    assert.match(loginViewSource, /忘记密码？/);
    assert.match(loginViewSource, /value="reset"/);
    assert.match(loginViewSource, /grid-cols-4/);
    assert.match(loginViewSource, /forgotPassword/);
    assert.match(loginViewSource, /resetPassword/);
    assert.match(loginViewSource, /发送重置邮件/);
    assert.match(loginViewSource, /重置密码/);
  });

  it('keeps token autofill route-aware for activate and reset', () => {
    assert.match(loginViewSource, /location\.pathname === '\/reset-password'/);
    assert.match(loginViewSource, /location\.pathname === '\/activate'/);
  });
});

describe('App reset-password route contract', () => {
  it('routes /reset-password to the login view reset tab', () => {
    assert.match(appSource, /path="\/reset-password"/);
    assert.match(appSource, /defaultTab="reset"/);
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix web test`
Expected: 3 个新用例 FAIL（regex 不匹配）

- [ ] **Step 3: 实现页面改动**

`web/src/App.jsx`：在 `/register` 路由行之后新增：

```jsx
      <Route path="/reset-password" element={<LoginView defaultTab="reset" />} />
```

`web/src/components/LoginView.jsx` 共 6 处修改：

修改一，api 导入加入两个函数：

```jsx
import { activateAuth, forgotPassword, registerUser, resetPassword, verifyInviteCode } from '../api/auth.js';
```

修改二，lucide 导入按字母序加入 `MailQuestion`（用于重置按钮图标）：

```jsx
import { CheckCircle2, KeyRound, Lock, MailQuestion, UserPlus } from 'lucide-react';
```

修改三，`initialForms` 增加两个表单：

```jsx
  forgot: {
    email: '',
  },
  reset: {
    token: '',
    password: '',
    confirmPassword: '',
  },
```

修改四，替换 `?token=` 自动填充 effect（原 66-80 行）为路由感知版本：

```jsx
  useEffect(() => {
    const token = readActivationTokenFromSearch(location.search);
    if (!token) return;
    if (location.pathname === '/reset-password') {
      setActiveTab('reset');
      setForms((current) => {
        if (current.reset.token === token) return current;
        return {
          ...current,
          reset: {
            ...current.reset,
            token,
          },
        };
      });
      return;
    }
    if (location.pathname === '/activate') {
      setActiveTab('activate');
      setForms((current) => {
        if (current.activate.token === token) return current;
        return {
          ...current,
          activate: {
            ...current.activate,
            token,
          },
        };
      });
    }
  }, [location.pathname, location.search]);
```

修改五，在 `handleRegister` 之后追加两个 handler：

```jsx
  const handleForgotPassword = async (event) => {
    event.preventDefault();
    setLoadingKey('forgot');
    setFeedback(null);
    try {
      const result = await forgotPassword(stripEmpty(forms.forgot));
      setResult('success', '重置邮件', result?.message || '如果该邮箱已注册并激活，重置邮件已发送');
    } catch (error) {
      setResult('error', '重置邮件', error.message);
    } finally {
      setLoadingKey('');
    }
  };

  const handleResetPassword = async (event) => {
    event.preventDefault();
    if (forms.reset.password !== forms.reset.confirmPassword) {
      setResult('error', '重置失败', '两次输入的密码不一致');
      return;
    }

    setLoadingKey('reset');
    setFeedback(null);
    try {
      const result = await resetPassword(stripEmpty(forms.reset));
      setResult('success', '密码已重置', result?.message || '请使用新密码登录');
      setActiveTab('login');
    } catch (error) {
      setResult('error', '重置失败', error.message);
    } finally {
      setLoadingKey('');
    }
  };
```

修改六，标签栏与内容。`TabsList` 改 4 列并加触发器：

```jsx
              <TabsList className="grid h-auto w-full grid-cols-4">
                <TabsTrigger value="login">登录</TabsTrigger>
                <TabsTrigger value="activate">激活</TabsTrigger>
                <TabsTrigger value="register">注册</TabsTrigger>
                <TabsTrigger value="reset">重置</TabsTrigger>
              </TabsList>
```

登录表单的提交按钮之后（`</form>` 之前）加入口链接：

```jsx
                  <div className="text-right">
                    <button
                      type="button"
                      className="text-sm font-medium text-primary hover:underline"
                      onClick={() => setActiveTab('reset')}
                    >
                      忘记密码？
                    </button>
                  </div>
```

`register` 的 `TabsContent` 之后追加重置标签内容（一页两表单，对照注册标签模式）：

```jsx
              <TabsContent value="reset" className="space-y-5 pt-4">
                <form className="flex flex-col gap-3 sm:flex-row" onSubmit={handleForgotPassword}>
                  <Input
                    required
                    type="email"
                    autoComplete="email"
                    value={forms.forgot.email}
                    onChange={(event) => updateForm('forgot', 'email', event.target.value)}
                    placeholder="注册邮箱"
                  />
                  <Button type="submit" variant="outline" disabled={loadingKey === 'forgot'}>
                    <MailQuestion className="size-4" />
                    {loadingKey === 'forgot' ? '发送中...' : '发送重置邮件'}
                  </Button>
                </form>

                <form className="space-y-4" onSubmit={handleResetPassword}>
                  <FormField label="重置令牌" required>
                    <Input
                      required
                      value={forms.reset.token}
                      onChange={(event) => updateForm('reset', 'token', event.target.value)}
                      placeholder="邮件中的重置令牌"
                    />
                  </FormField>
                  <FormField label="新密码" required>
                    <Input
                      required
                      type="password"
                      minLength="8"
                      autoComplete="new-password"
                      value={forms.reset.password}
                      onChange={(event) => updateForm('reset', 'password', event.target.value)}
                      placeholder="至少 8 位"
                    />
                  </FormField>
                  <FormField label="确认新密码" required>
                    <Input
                      required
                      type="password"
                      minLength="8"
                      autoComplete="new-password"
                      value={forms.reset.confirmPassword}
                      onChange={(event) => updateForm('reset', 'confirmPassword', event.target.value)}
                      placeholder="再次输入新密码"
                    />
                  </FormField>
                  <Button type="submit" className="w-full" disabled={loadingKey === 'reset'}>
                    <KeyRound className="size-4" />
                    {loadingKey === 'reset' ? '重置中...' : '重置密码'}
                  </Button>
                </form>
              </TabsContent>
```

同时把卡片描述行更新为涵盖重置：

```jsx
              <p className="text-sm text-muted-foreground">登录、激活管理员账号、邀请码注册或重置密码</p>
```

- [ ] **Step 4: 运行测试与构建确认通过**

Run: `npm --prefix web test`
Expected: 全部通过（约 128 pass）

Run: `npm --prefix web run build`
Expected: 构建成功

- [ ] **Step 5: Commit**（三个文件全部干净，正常 add）

```powershell
git add web/src/components/__tests__/loginView.test.js web/src/components/LoginView.jsx web/src/App.jsx
git commit -m @'
feat: 登录页新增密码重置标签与路由感知令牌填充

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 6: 账户管理页「修改密码」表单

**Files:**
- Modify: `web/src/components/__tests__/AccountManagement.test.js`（⚠️ 带在途改动，过滤暂存）
- Modify: `web/src/components/AccountManagement.jsx`（⚠️ 带在途改动，过滤暂存）

- [ ] **Step 1: 写失败的契约测试**

`AccountManagement.test.js` 文件末尾追加（先 Read 该文件确认 describe 风格与 `source` 变量名，与现有保持一致；若现有用其他变量名读取源码则沿用）：

```js
describe('AccountManagement change password contract', () => {
  it('exposes a change password form calling the authed endpoint', () => {
    assert.match(source, /changePassword/);
    assert.match(source, /修改密码/);
    assert.match(source, /currentPassword/);
    assert.match(source, /newPassword/);
    assert.match(source, /confirmPassword/);
    assert.match(source, /两次输入的新密码不一致/);
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix web test`
Expected: 新用例 FAIL（regex 不匹配）

- [ ] **Step 3: 实现页面改动**

`web/src/components/AccountManagement.jsx` 共 5 处修改（工作区版本）：

修改一，api 导入加入 `changePassword`（保持该文件从 `'@/api'` 导入的现状与排序）：

```jsx
import {
  changePassword,
  registerUser,
  verifyInviteCode,
} from '@/api';
```

若 Task 4 核对发现 `web/src/api/index.js` barrel 未导出 `changePassword`，回到 Task 4 的 barrel 步骤补上后再继续。

修改二，lucide 导入按字母序加入 `KeyRound`：

```jsx
import {
  Key,
  KeyRound,
  ShieldCheck,
  UserCheck,
  UserPlus,
} from 'lucide-react';
```

修改三，`initialForms` 增加：

```jsx
  password: {
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  },
```

`loadingMap` 初始值增加 `password: false`。

修改四，在 `handleOperation` 定义之后追加专用 handler（两次一致性校验需要前置拦截，不走 `handleOperation` 工厂）：

```jsx
  const handleChangePassword = async (event) => {
    event.preventDefault();
    if (forms.password.newPassword !== forms.password.confirmPassword) {
      setFeedback({ type: 'error', title: '修改密码', message: '两次输入的新密码不一致' });
      return;
    }
    setLoading('password', true);
    setFeedback(null);
    try {
      const result = await changePassword(stripEmpty(forms.password));
      pushResponse('修改密码', 'success', result);
      setForms((current) => ({
        ...current,
        password: { currentPassword: '', newPassword: '', confirmPassword: '' },
      }));
    } catch (error) {
      pushResponse('修改密码', 'error', { message: error.message });
    } finally {
      setLoading('password', false);
    }
  };
```

修改五，主卡片 `CardContent` 内、员工注册 `</form>` 之后追加修改密码表单：

```jsx
            <form className="account-form space-y-4" onSubmit={handleChangePassword}>
              <div>
                <div className="account-section-title">修改密码</div>
                <p className="mt-1 text-sm text-muted-foreground">
                  验证当前密码后设置新密码；修改成功后下次登录使用新密码。
                </p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <FormField label="当前密码" required>
                  <Input required type="password" autoComplete="current-password" value={forms.password.currentPassword} onChange={(event) => updateForm('password', 'currentPassword', event.target.value)} placeholder="输入当前密码" />
                </FormField>
                <FormField label="新密码" required>
                  <Input required type="password" minLength="8" autoComplete="new-password" value={forms.password.newPassword} onChange={(event) => updateForm('password', 'newPassword', event.target.value)} placeholder="至少 8 位" />
                </FormField>
                <FormField label="确认新密码" required>
                  <Input required type="password" minLength="8" autoComplete="new-password" value={forms.password.confirmPassword} onChange={(event) => updateForm('password', 'confirmPassword', event.target.value)} placeholder="再次输入新密码" />
                </FormField>
              </div>
              <Button type="submit" disabled={loadingMap.password}>
                <KeyRound className="size-4" />
                {loadingMap.password ? '提交中...' : '修改密码'}
              </Button>
            </form>
```

- [ ] **Step 4: 运行测试与构建确认通过**

Run: `npm --prefix web test`
Expected: 全部通过（约 129 pass）

Run: `npm --prefix web run build`
Expected: 构建成功

- [ ] **Step 5: ⚠️ 过滤暂存与提交**

两个文件都带在途改动（加入团队边界相关）。提交 blob = `git show HEAD:<file>` + 仅本任务增量，适配 HEAD 上下文：若 HEAD 版本的导入块、表单区与工作区不同，提交版本以 HEAD 实际内容为基底只加本任务内容；提交版本不得引用 HEAD 中不存在且非本任务新增的标识符。构造后用临时 worktree 跑 `node --test <worktree>/web/src/components/__tests__/AccountManagement.test.js` 验证提交版本自洽（该测试只读源码文件，不需要 node_modules）。

```powershell
# 两文件经 hash-object/update-index 注入后：
git commit -m @'
feat: 账户管理页新增修改密码表单

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

提交后核对：`git show --stat HEAD` 恰好 2 个文件；残留 diff 只含在途 hunk，无 changePassword 相关行。

---

### Task 7: SECURITY.md 限流清单、changelog 与收尾

**Files:**
- Modify: `docs/SECURITY.md`（⚠️ 带在途改动，过滤暂存）
- Create: `docs/changelog/20260610-070000-password-reset-and-change.md`
- Move: `docs/exec-plans/active/20260610-password-reset-and-change.md` → `docs/exec-plans/completed/`

- [ ] **Step 1: 运行全部门禁（真实执行并记录结果）**

```powershell
uv run --project api ruff check api
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
```

Expected: 全部通过。失败先排查：本功能问题修复后重跑；他人在途问题报告 BLOCKED。

- [ ] **Step 2: SECURITY.md 限流清单补两个端点**

「API 安全」节的速率限制行改为（HEAD 与工作区该行内容一致，提交 blob 基于 HEAD 构造，只改这一行）：

```markdown
- 速率限制：登录、邀请码验证、员工注册、激活、忘记密码、重置密码、报告生成和重算类接口上线前必须纳入限流计划；忘记密码接口已内置按邮箱 60 秒进程级冷却。
```

- [ ] **Step 3: 写 changelog**

创建 `docs/changelog/20260610-070000-password-reset-and-change.md`：

```markdown
# 自助密码重置与修改密码

## 变更

- 新增 `POST /api/v1/public/auth/forgot-password`：对 active 账号签发 1 小时重置令牌并发送重置邮件；防枚举（全路径统一响应）+ 按邮箱 60 秒进程级冷却。
- 新增 `POST /api/v1/public/auth/reset-password`：校验令牌签名/类型/有效期/密码哈希指纹后更新密码；失败统一报「重置链接无效或已失效」。
- 新增 `POST /api/v1/auth/change-password`：已登录用户验证当前密码后修改密码。
- 一次性令牌语义：payload 携带 password_hash 的 SHA-256 指纹前 16 字符，密码变更后所有存量重置令牌自动失效；与激活令牌按 type 隔离。
- `email_sender` 新增 `send_password_reset_email`（复用 SMTP 基建，含 1 小时有效期与非本人操作提示）。
- 登录页新增「重置」标签（申请邮件 + 凭令牌设新密码）与「忘记密码？」入口；`?token=` 自动填充改为路由感知，修复 `/activate` 劫持任意路由 token 参数的缺陷；新增 `/reset-password` 路由。
- 账户管理页新增「修改密码」表单。
- `docs/SECURITY.md` 限流计划清单补充忘记密码与重置密码端点。

## 边界

- 不升级密码强度策略；不做密码历史/过期；不持久化重置令牌；不做短信重置。
- 重置/修改密码不失效已签发 JWT（无状态令牌已知局限，列为未来增强）。
- 平台侧代发重置邮件单独立项。

## 验证

- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `npm --prefix web test`
- `npm --prefix web run build`
- `python scripts/validate_agents_docs.py --level ERROR`
```

按 Step 1 真实结果核对验证小节，如有出入按实际改写（附 passed 数量）。

- [ ] **Step 4: 勾选并归档 ExecPlan**

1. 把本计划所有 `- [ ]` 勾成 `- [x]`。
2. `git mv docs/exec-plans/active/20260610-password-reset-and-change.md docs/exec-plans/completed/20260610-password-reset-and-change.md`
3. 索引处理：`docs/exec-plans/active/index.md` 是干净文件且本计划的行已随计划文档一起提交——归档时删除该行、恢复「当前无进行中的 ExecPlan。」形态，并把这个删除**一并提交**；`docs/exec-plans/completed/index.md` 带在途改动，只在工作区加行（3 列格式，Completed 填 2026-06-10），**不提交**。

- [ ] **Step 5: 复跑文档验证**

Run: `python scripts/validate_agents_docs.py --level ERROR`
Expected: 0 错误

- [ ] **Step 6: Commit**

```powershell
# docs/SECURITY.md 经 blob 构造注入（基于 HEAD 只改限流行）后：
git add docs/changelog/20260610-070000-password-reset-and-change.md docs/exec-plans/active/20260610-password-reset-and-change.md docs/exec-plans/completed/20260610-password-reset-and-change.md docs/exec-plans/active/index.md
git commit -m @'
docs: 自助密码重置功能 changelog、安全清单与计划归档

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

提交后核对：commit 不含 `docs/exec-plans/completed/index.md`；SECURITY.md 提交 diff 仅一行变化。

---

## 验收对照（Spec → Task）

| Spec 要求 | 覆盖 Task |
|---|---|
| 目标 1：登录页入口 + `/reset-password?token=` 自动填充 | Task 5 |
| 目标 2/3：1 小时令牌 + 指纹一次性 | Task 1（单次使用/改密失效/过期/类型隔离四个用例） |
| 目标 4：重置邮件复用 SMTP | Task 2 |
| 目标 5：防枚举统一响应 | Task 3（byte-identical 集成测试） |
| 目标 6：60 秒冷却 | Task 1（cooldown 用例）+ Task 3 |
| 目标 7：已登录修改密码 | Task 1、3、6 |
| 目标 8：路由感知填充修复 | Task 5（契约测试） |
| API 行为 5.1/5.2/5.3 错误表 | Task 3 路由测试 |
| 安全要求 7（JWT 已知局限） | 规格明示，无代码任务 |
| SECURITY.md 限流清单 | Task 7 |
| 验收门禁 | Task 3 Step 5、Task 5/6 Step 4、Task 7 Step 1 |
