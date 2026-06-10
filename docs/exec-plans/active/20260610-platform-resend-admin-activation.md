# 平台重发租户管理员激活邮件实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 平台管理员可在租户详情页对「待激活」管理员重新签发 7 天激活令牌并重发激活邮件（含人工兜底链接）。

**Architecture:** 后端在 `api/v1/repositories/auth.py` 新增只读仓储函数重签令牌，新路由 `POST /api/v1/platform/tenants/{tenant_key}/resend-activation` 复用 `send_admin_activation_email`；前端在 `web/src/api/platform.js` 加适配器，详情页管理员卡片加按钮与结果区，复用 `getEmailDeliveryMeta`。不写数据库、不存发送历史。

**Tech Stack:** FastAPI + SQLAlchemy（text SQL）、pytest（内存 SQLite + TestClient）、React 18 + shadcn/ui、node:test 源码契约测试。

**Spec:** `docs/product-specs/20260610-platform-resend-admin-activation.md`

**约定与上下文（执行者必读）：**

- 测试命令（PowerShell，仓库根目录）：
  - 后端单文件：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_resend_activation.py -q`
  - 后端全量：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
  - 后端 lint：`uv run --project api ruff check api`
  - 前端测试：`npm --prefix web test`；前端构建：`npm --prefix web run build`
  - 文档验证：`python scripts/validate_agents_docs.py --level ERROR`
- 工作区有大量他人在途改动：**每次 commit 只 `git add` 本计划点名的文件，严禁 `git add -A` / `git add .`**。`docs/product-specs/index.md`、`docs/exec-plans/active/index.md` 带有他人未提交改动，不要提交它们。
- 错误信封：业务错误统一 `JSONResponse(status_code=4xx, content={"status":"error","message":...,"code":4xx})`。
- 仓储错误约定：租户不存在抛 `LookupError`（路由映射 404）；业务拒绝抛 `ValueError`（路由映射 400）。
- 管理员定位规则（与详情页展示一致，见 `api/v1/repositories/tenants.py:145`）：`user_tenants` 中 `role='admin'` 按 `created_at ASC` 第一条。

---

### Task 1: 仓储函数 `regenerate_admin_activation`

**Files:**
- Create: `api/tests/test_resend_activation.py`
- Modify: `api/v1/repositories/auth.py`（在 `activate_admin_account` 之后新增函数）

- [ ] **Step 1: 写失败的仓储测试**

创建 `api/tests/test_resend_activation.py`：

```python
from datetime import UTC, datetime, timedelta

import pytest
from api.v1.repositories import auth as auth_repository
from api.v1.utils.security import verify_token
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def memory_engine(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-with-at-least-32-bytes")
    monkeypatch.setenv("AUTH_BASE_URL", "https://example.com")
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE tenants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_key VARCHAR(255) NOT NULL UNIQUE,
                    tenant_name VARCHAR(255) NOT NULL UNIQUE,
                    subdomain VARCHAR(100),
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_key VARCHAR(36) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    first_name VARCHAR(100),
                    phone_number VARCHAR(50),
                    is_verified BOOLEAN NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE user_tenants (
                    user_id INTEGER NOT NULL,
                    tenant_id INTEGER NOT NULL,
                    role VARCHAR(50) NOT NULL DEFAULT 'member',
                    status VARCHAR(20) NOT NULL DEFAULT 'active',
                    created_at TIMESTAMP,
                    PRIMARY KEY (user_id, tenant_id)
                )
                """
            )
        )
    return engine


def _seed_tenant(engine, *, tenant_key="tn_demo", subdomain=None):
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO tenants (tenant_key, tenant_name, subdomain, created_at, updated_at)
                VALUES (:tenant_key, :tenant_name, :subdomain, :now, :now)
                """
            ),
            {
                "tenant_key": tenant_key,
                "tenant_name": f"企业{tenant_key}",
                "subdomain": subdomain,
                "now": now,
            },
        )
        return conn.execute(
            text("SELECT id FROM tenants WHERE tenant_key = :tenant_key"),
            {"tenant_key": tenant_key},
        ).fetchone()[0]


def _seed_admin(
    engine,
    tenant_id,
    *,
    email,
    user_status="pending_activation",
    membership_created_at=None,
):
    now = datetime.now(UTC)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO users (
                    user_key, email, password_hash, is_verified, status, created_at, updated_at
                ) VALUES (:user_key, :email, 'x', 0, :status, :now, :now)
                """
            ),
            {
                "user_key": f"uk_{email}",
                "email": email,
                "status": user_status,
                "now": now,
            },
        )
        user_id = conn.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()[0]
        conn.execute(
            text(
                """
                INSERT INTO user_tenants (user_id, tenant_id, role, status, created_at)
                VALUES (:user_id, :tenant_id, 'admin', 'active', :created_at)
                """
            ),
            {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "created_at": membership_created_at or now,
            },
        )
    return user_id


def test_regenerate_returns_new_activation_payload(memory_engine):
    tenant_id = _seed_tenant(memory_engine)
    user_id = _seed_admin(memory_engine, tenant_id, email="admin@demo.test")

    result = auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")

    assert result["tenantKey"] == "tn_demo"
    assert result["tenantName"] == "企业tn_demo"
    assert result["adminEmail"] == "admin@demo.test"
    assert result["activationUrl"].startswith("https://example.com/activate?token=")
    assert result["loginUrl"] == "https://example.com/login"

    payload = verify_token(
        result["activationToken"], "test-secret-with-at-least-32-bytes"
    )
    assert payload["type"] == "activation"
    assert payload["user_id"] == user_id
    assert payload["tenant_key"] == "tn_demo"
    assert payload["email"] == "admin@demo.test"
    expected_exp = (datetime.now(UTC) + timedelta(days=7)).timestamp()
    assert abs(payload["exp"] - expected_exp) < 60


def test_regenerate_targets_earliest_admin(memory_engine):
    tenant_id = _seed_tenant(memory_engine)
    early = datetime(2026, 1, 1, tzinfo=UTC)
    late = datetime(2026, 5, 1, tzinfo=UTC)
    _seed_admin(
        memory_engine,
        tenant_id,
        email="late-admin@demo.test",
        membership_created_at=late,
    )
    _seed_admin(
        memory_engine,
        tenant_id,
        email="first-admin@demo.test",
        membership_created_at=early,
    )

    result = auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")

    assert result["adminEmail"] == "first-admin@demo.test"


def test_regenerate_rejects_unknown_tenant(memory_engine):
    with pytest.raises(LookupError, match="租户不存在"):
        auth_repository.regenerate_admin_activation(memory_engine, "tn_missing")


def test_regenerate_rejects_tenant_without_admin(memory_engine):
    _seed_tenant(memory_engine)
    with pytest.raises(ValueError, match="该租户未设置管理员"):
        auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")


def test_regenerate_rejects_active_admin(memory_engine):
    tenant_id = _seed_tenant(memory_engine)
    _seed_admin(memory_engine, tenant_id, email="admin@demo.test", user_status="active")
    with pytest.raises(ValueError, match="账号已激活"):
        auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")


def test_regenerate_rejects_abnormal_admin(memory_engine):
    tenant_id = _seed_tenant(memory_engine)
    _seed_admin(
        memory_engine, tenant_id, email="admin@demo.test", user_status="suspended"
    )
    with pytest.raises(ValueError, match="账号状态异常"):
        auth_repository.regenerate_admin_activation(memory_engine, "tn_demo")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_resend_activation.py -q`
Expected: FAIL，报 `AttributeError: ... has no attribute 'regenerate_admin_activation'`

- [ ] **Step 3: 实现仓储函数**

在 `api/v1/repositories/auth.py` 的 `activate_admin_account` 函数之后（约 360 行附近）新增：

```python
def regenerate_admin_activation(engine: Engine, tenant_key: str) -> Dict[str, Any]:
    now = datetime.now(UTC)
    with engine.connect() as conn:
        tenant_row = conn.execute(
            text(
                "SELECT id, tenant_name, subdomain FROM tenants"
                " WHERE tenant_key = :tenant_key"
            ),
            {"tenant_key": tenant_key},
        ).fetchone()
        if not tenant_row:
            raise LookupError("租户不存在")
        tenant_id, tenant_name, subdomain = tenant_row

        admin_row = conn.execute(
            text(
                """
                SELECT u.id, u.email, u.status
                FROM user_tenants ut
                JOIN users u ON u.id = ut.user_id
                WHERE ut.tenant_id = :tenant_id
                  AND ut.role = 'admin'
                ORDER BY ut.created_at ASC
                LIMIT 1
                """
            ),
            {"tenant_id": tenant_id},
        ).fetchone()
        if not admin_row:
            raise ValueError("该租户未设置管理员")
        user_id, admin_email, user_status = admin_row
        if user_status == "active":
            raise ValueError("账号已激活")
        if user_status != "pending_activation":
            raise ValueError("账号状态异常")

    activation_token = sign_token(
        {
            "user_id": user_id,
            "tenant_key": tenant_key,
            "email": admin_email,
            "type": "activation",
            "exp": int((now + timedelta(days=7)).timestamp()),
        },
        _get_auth_secret(),
    )
    tenant_base_url = _build_tenant_base_url(subdomain)
    return {
        "tenantKey": tenant_key,
        "tenantName": tenant_name,
        "adminEmail": admin_email,
        "activationToken": activation_token,
        "activationUrl": f"{tenant_base_url}/activate?token={activation_token}",
        "loginUrl": f"{tenant_base_url}/login",
    }
```

说明：`Engine`、`Dict`、`Any`、`datetime`、`UTC`、`timedelta`、`text`、`sign_token` 在该文件均已导入，无需新增 import。

- [ ] **Step 4: 运行测试确认通过**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_resend_activation.py -q`
Expected: 6 passed

- [ ] **Step 5: Commit**

```powershell
git add api/tests/test_resend_activation.py api/v1/repositories/auth.py
git commit -m @'
feat: 新增平台重发激活令牌仓储函数

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 2: 路由 `POST /platform/tenants/{tenant_key}/resend-activation`

**Files:**
- Modify: `api/tests/test_resend_activation.py`（追加路由测试）
- Modify: `api/v1/routes/auth.py`（导入 + 新路由）

- [ ] **Step 1: 追加失败的路由测试**

在 `api/tests/test_resend_activation.py` 顶部 import 区追加：

```python
from unittest.mock import patch

from api.v1.dependencies.auth import CurrentUser, require_platform_admin
from api.v1.routes import auth as auth_routes
from fastapi import FastAPI
from fastapi.testclient import TestClient
```

文件末尾追加：

```python
@pytest.fixture()
def platform_client():
    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/api/v1")
    app.dependency_overrides[require_platform_admin] = lambda: CurrentUser(
        user_id=1,
        email="platform@example.com",
        status="active",
    )
    return TestClient(app)


_REPO_RESULT = {
    "tenantKey": "tn_demo",
    "tenantName": "示例企业",
    "adminEmail": "admin@demo.test",
    "activationToken": "new-token",
    "activationUrl": "https://example.com/activate?token=new-token",
    "loginUrl": "https://example.com/login",
}


def test_resend_route_returns_payload_with_email_delivery(platform_client):
    with patch(
        "api.v1.routes.auth.regenerate_admin_activation",
        return_value=dict(_REPO_RESULT),
    ) as regenerate, patch(
        "api.v1.routes.auth.send_admin_activation_email",
        return_value={
            "status": "sent",
            "to": "admin@demo.test",
            "message": "激活邮件已发送",
        },
    ) as send_email:
        response = platform_client.post(
            "/api/v1/platform/tenants/tn_demo/resend-activation"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["message"] == "激活令牌已重新签发"
    assert body["data"]["adminEmail"] == "admin@demo.test"
    assert body["data"]["activationUrl"].startswith("https://example.com/activate")
    assert body["data"]["emailDelivery"]["status"] == "sent"
    regenerate.assert_called_once()
    assert regenerate.call_args.args[1] == "tn_demo"
    send_email.assert_called_once_with(dict(_REPO_RESULT))


def test_resend_route_maps_lookup_error_to_404(platform_client):
    with patch(
        "api.v1.routes.auth.regenerate_admin_activation",
        side_effect=LookupError("租户不存在"),
    ):
        response = platform_client.post(
            "/api/v1/platform/tenants/tn_missing/resend-activation"
        )

    assert response.status_code == 404
    body = response.json()
    assert body["status"] == "error"
    assert body["message"] == "租户不存在"
    assert body["code"] == 404


def test_resend_route_maps_value_error_to_400(platform_client):
    with patch(
        "api.v1.routes.auth.regenerate_admin_activation",
        side_effect=ValueError("账号已激活"),
    ):
        response = platform_client.post(
            "/api/v1/platform/tenants/tn_demo/resend-activation"
        )

    assert response.status_code == 400
    body = response.json()
    assert body["status"] == "error"
    assert body["message"] == "账号已激活"
    assert body["code"] == 400


def test_resend_route_keeps_success_when_email_raises(platform_client):
    with patch(
        "api.v1.routes.auth.regenerate_admin_activation",
        return_value=dict(_REPO_RESULT),
    ), patch(
        "api.v1.routes.auth.send_admin_activation_email",
        side_effect=RuntimeError("smtp-secret leaked in raw exception"),
    ):
        response = platform_client.post(
            "/api/v1/platform/tenants/tn_demo/resend-activation"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["emailDelivery"]["status"] == "failed"
    assert (
        body["data"]["emailDelivery"]["message"]
        == "激活邮件发送失败，请复制激活链接人工发送"
    )
    assert "smtp-secret" not in response.text


def test_resend_route_requires_platform_admin():
    app = FastAPI()
    app.include_router(auth_routes.router, prefix="/api/v1")
    client = TestClient(app)

    response = client.post("/api/v1/platform/tenants/tn_demo/resend-activation")

    assert response.status_code == 401
```

- [ ] **Step 2: 运行测试确认失败**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_resend_activation.py -q`
Expected: 新增 5 个路由测试 FAIL（404 Not Found：路由不存在 / patch 目标缺失报 `AttributeError`），原 6 个仓储测试 PASS

- [ ] **Step 3: 实现路由**

`api/v1/routes/auth.py` 修改一：`from api.v1.repositories.auth import (...)` 导入块（第 16-22 行）按字母序加入 `regenerate_admin_activation`：

```python
from api.v1.repositories.auth import (
    activate_admin_account,
    authenticate_user,
    create_tenant_with_admin,
    regenerate_admin_activation,
    register_employee,
    verify_invite_code,
)
```

修改二：在 `get_platform_tenant_detail`（`@router.get("/platform/tenants/{tenant_key}")`）函数体之后、`get_platform_collection_health` 之前新增路由：

```python
@router.post("/platform/tenants/{tenant_key}/resend-activation")
def resend_tenant_activation(
    tenant_key: str,
    engine: Engine = Depends(get_engine),
    _platform_admin: CurrentUser = Depends(require_platform_admin),
):
    try:
        result = regenerate_admin_activation(engine, tenant_key)
    except LookupError as exc:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": str(exc), "code": 404},
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    try:
        email_delivery = send_admin_activation_email(result)
    except Exception:
        email_delivery = {
            "status": "failed",
            "to": result.get("adminEmail"),
            "message": EMAIL_FAILED_MESSAGE,
        }
    result = {**result, "emailDelivery": email_delivery}
    return {
        "status": "success",
        "data": result,
        "message": "激活令牌已重新签发",
        "code": 200,
    }
```

说明：`Engine`、`Depends`、`JSONResponse`、`get_engine`、`require_platform_admin`、`send_admin_activation_email`、`EMAIL_FAILED_MESSAGE` 该文件均已导入。

- [ ] **Step 4: 运行测试确认通过**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_resend_activation.py -q`
Expected: 11 passed

- [ ] **Step 5: 后端回归与 lint**

Run: `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
Expected: 全部通过（数量以当前主干为准，不得新增失败）

Run: `uv run --project api ruff check api`
Expected: All checks passed!

- [ ] **Step 6: Commit**

```powershell
git add api/tests/test_resend_activation.py api/v1/routes/auth.py
git commit -m @'
feat: 新增平台重发管理员激活邮件接口

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 3: 前端 API 适配器 `resendPlatformTenantActivation`

**Files:**
- Modify: `web/src/api/__tests__/platform.test.js`
- Modify: `web/src/api/platform.js`

- [ ] **Step 1: 写失败的适配器测试**

`web/src/api/__tests__/platform.test.js` 的 import 块中（`fetchPlatformTenants,` 之后、`updatePlatformTenantMember,` 之前，保持字母序）加入 `resendPlatformTenantActivation`：

```js
import {
  createPlatformTenant,
  fetchPlatformCollectionHealth,
  fetchPlatformTenantMembers,
  fetchPlatformTenantDetail,
  fetchPlatformTenants,
  resendPlatformTenantActivation,
  updatePlatformTenantMember,
} from '../platform.js';
```

文件末尾追加测试：

```js
test('resendPlatformTenantActivation posts to the resend endpoint', async () => {
  let requestedUrl;
  let requestedOptions;
  globalThis.fetch = async (url, options) => {
    requestedUrl = url;
    requestedOptions = options;
    return jsonResponse({
      data: {
        tenantKey: 'tn_demo',
        activationUrl: 'https://example.com/activate?token=new',
        emailDelivery: { status: 'sent' },
      },
    });
  };

  const result = await resendPlatformTenantActivation('tn_demo');

  const parsed = new URL(requestedUrl, 'http://localhost');
  assert.equal(
    parsed.pathname,
    '/api/v1/platform/tenants/tn_demo/resend-activation',
  );
  assert.equal(requestedOptions.method, 'POST');
  assert.equal(result.data.emailDelivery.status, 'sent');
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix web test`
Expected: FAIL，报 `resendPlatformTenantActivation` 未从 `../platform.js` 导出（SyntaxError）

- [ ] **Step 3: 实现适配器**

`web/src/api/platform.js` 在 `createPlatformTenant` 之后新增：

```js
export const resendPlatformTenantActivation = (tenantKey, options) => {
  return post(
    `/api/v1/platform/tenants/${encodePathSegment(tenantKey)}/resend-activation`,
    undefined,
    platformOptions(options),
  );
};
```

- [ ] **Step 4: 运行测试确认通过**

Run: `npm --prefix web test`
Expected: 全部通过

- [ ] **Step 5: Commit**

```powershell
git add web/src/api/__tests__/platform.test.js web/src/api/platform.js
git commit -m @'
feat: 前端新增平台重发激活邮件 API 适配器

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 4: 详情页「重发激活邮件」按钮与结果区

**Files:**
- Modify: `web/src/components/platform/__tests__/platformTenantDetailPage.test.js`
- Modify: `web/src/components/platform/PlatformTenantDetailPage.jsx`

- [ ] **Step 1: 写失败的源码契约测试**

`platformTenantDetailPage.test.js` 文件末尾追加：

```js
describe('PlatformTenantDetailPage resend activation contract', () => {
  it('exposes a resend activation entry for pending admins', () => {
    assert.match(source, /resendPlatformTenantActivation/);
    assert.match(source, /adminStatus === 'pending_activation'/);
    assert.match(source, /重发激活邮件/);
    assert.match(source, /getEmailDeliveryMeta/);
    assert.match(source, /新激活链接/);
    assert.match(source, /复制激活链接/);
  });

  it('keeps resend result presentation consistent with create tenant panel', () => {
    assert.match(source, /resendResult\.activationUrl/);
    assert.match(source, /AlertTitle>\{resendDeliveryMeta\.title\}/);
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix web test`
Expected: 新增 2 个用例 FAIL（regex 不匹配）

- [ ] **Step 3: 实现页面改动**

`web/src/components/platform/PlatformTenantDetailPage.jsx` 共 5 处修改：

修改一，lucide-react 导入（第 2-14 行）按字母序加入 `Check`、`Copy`、`MailPlus`：

```jsx
import {
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Building2,
  Check,
  Copy,
  FolderKanban,
  Gauge,
  ListChecks,
  MailPlus,
  RefreshCw,
  ShieldCheck,
  UserRound,
  Users,
} from 'lucide-react';
```

修改二，平台 API 导入（第 17-21 行）加入 `resendPlatformTenantActivation`：

```jsx
import {
  fetchPlatformTenantDetail,
  fetchPlatformTenantMembers,
  resendPlatformTenantActivation,
  updatePlatformTenantMember,
} from '../../api/platform.js';
```

修改三，tenantPresentation 导入（第 67-77 行）按字母序加入 `getEmailDeliveryMeta`：

```jsx
import {
  buildTenantDashboardPath,
  buildTenantTaskStatusPath,
  formatDate,
  getAdminStatusLabel,
  getBillingCycleLabel,
  getEmailDeliveryMeta,
  getPlanTypeLabel,
  getQueryJobStatusMeta,
  getTenantStatusMeta,
  normalizeTenantDetailResponse,
} from './tenantPresentation.js';
```

修改四，state 与 handler。在 `const [memberActionMessage, setMemberActionMessage] = useState('');`（第 107 行）之后追加 state：

```jsx
  const [isResendingActivation, setIsResendingActivation] = useState(false);
  const [resendError, setResendError] = useState('');
  const [resendResult, setResendResult] = useState(null);
  const [copiedActivation, setCopiedActivation] = useState(false);
```

在组件内现有成员提交 handler（`handleSubmitMemberUpdate`，定义于约 255 行起）的函数体结束之后追加：

```jsx
  const resendDeliveryMeta = resendResult
    ? getEmailDeliveryMeta(resendResult.emailDelivery)
    : null;

  const handleResendActivation = async () => {
    setIsResendingActivation(true);
    setResendError('');
    try {
      const response = await resendPlatformTenantActivation(tenantKey);
      setResendResult(response?.data || response || null);
    } catch (submitError) {
      setResendResult(null);
      setResendError(submitError.message || '激活邮件重发失败');
    } finally {
      setIsResendingActivation(false);
    }
  };

  const handleCopyActivationUrl = async () => {
    if (!navigator?.clipboard || !resendResult?.activationUrl) return;
    await navigator.clipboard.writeText(resendResult.activationUrl);
    setCopiedActivation(true);
    window.setTimeout(() => setCopiedActivation(false), 1600);
  };
```

修改五，租户管理员卡片（`id="tenant-admin"` 区块，约 444-471 行）。把 CardHeader 中原单个按钮包进按钮组，并在 CardContent 末尾追加结果区——整块替换为：

```jsx
              <div id="tenant-admin" ref={tenantAdminRef}>
                <Card>
                  <CardHeader className="gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="grid gap-1">
                      <CardTitle className="flex items-center gap-2">
                        <UserRound className="size-4" aria-hidden="true" />
                        租户管理员
                      </CardTitle>
                      <CardDescription>平台只读查看，用于客户识别、联络和排障交接。</CardDescription>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      {tenant.adminStatus === 'pending_activation' ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={isResendingActivation}
                          onClick={handleResendActivation}
                        >
                          <MailPlus className="size-3.5" />
                          {isResendingActivation ? '重发中...' : '重发激活邮件'}
                        </Button>
                      ) : null}
                      <Button
                        type="button"
                        size="sm"
                        disabled={!canOpenTenantTools}
                        onClick={handleOpenMemberSheet}
                      >
                        <ShieldCheck className="size-3.5" />
                        {adminActionLabel}
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="grid gap-4 sm:grid-cols-2">
                    <DetailField label="管理员姓名" value={tenant.adminName} />
                    <DetailField label="管理员邮箱" value={tenant.adminEmail} />
                    <DetailField label="管理员手机号" value={tenant.adminPhone} />
                    <DetailField label="管理员状态" value={getAdminStatusLabel(tenant.adminStatus)} />
                    {resendError ? (
                      <Alert variant="destructive" className="sm:col-span-2">
                        <AlertTitle>激活邮件重发失败</AlertTitle>
                        <AlertDescription>{resendError}</AlertDescription>
                      </Alert>
                    ) : null}
                    {resendResult ? (
                      <div className="grid gap-3 sm:col-span-2">
                        {resendDeliveryMeta ? (
                          <Alert variant={resendDeliveryMeta.variant}>
                            <AlertTitle>{resendDeliveryMeta.title}</AlertTitle>
                            <AlertDescription>{resendDeliveryMeta.description}</AlertDescription>
                          </Alert>
                        ) : null}
                        <div className="grid gap-1">
                          <span className="text-xs font-medium text-muted-foreground">新激活链接</span>
                          <div className="flex min-w-0 items-center gap-2">
                            <code className="min-w-0 flex-1 truncate text-xs text-foreground">
                              {resendResult.activationUrl || '未返回'}
                            </code>
                            {resendResult.activationUrl ? (
                              <Button
                                type="button"
                                variant="outline"
                                size="icon-sm"
                                onClick={handleCopyActivationUrl}
                                title="复制激活链接"
                              >
                                {copiedActivation ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
                              </Button>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </CardContent>
                </Card>
              </div>
```

说明：`Alert/AlertTitle/AlertDescription`、`Button` 已在该文件导入；`canOpenTenantTools`、`adminActionLabel`、`handleOpenMemberSheet` 为既有标识符，原样保留。

- [ ] **Step 4: 运行测试与构建确认通过**

Run: `npm --prefix web test`
Expected: 全部通过

Run: `npm --prefix web run build`
Expected: 构建成功，无报错

- [ ] **Step 5: Commit**

```powershell
git add web/src/components/platform/__tests__/platformTenantDetailPage.test.js web/src/components/platform/PlatformTenantDetailPage.jsx
git commit -m @'
feat: 平台租户详情页新增重发激活邮件入口

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

---

### Task 5: 全量门禁与文档收尾

**Files:**
- Create: `docs/changelog/20260610-050000-platform-resend-admin-activation.md`
- Move: `docs/exec-plans/active/20260610-platform-resend-admin-activation.md` → `docs/exec-plans/completed/`

- [ ] **Step 1: 运行全部门禁**

```powershell
uv run --project api ruff check api
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
```

Expected: 全部通过。任何失败都必须先修复再继续，不得跳过。

- [ ] **Step 2: 写 changelog 记录**

创建 `docs/changelog/20260610-050000-platform-resend-admin-activation.md`：

```markdown
# 平台重发租户管理员激活邮件

## 变更

- 新增 `POST /api/v1/platform/tenants/{tenant_key}/resend-activation`：平台管理员对「待激活」租户管理员重签 7 天激活令牌并重发激活邮件。
- 新增仓储函数 `regenerate_admin_activation`：按详情页同款规则（role='admin' 按 created_at 最早）定位管理员，校验 `pending_activation` 状态，只读不写库。
- 复用 `send_admin_activation_email`；SMTP 未配置/失败时接口仍返回 200，`emailDelivery` 区分状态，响应携带新激活链接供人工兜底。
- 前端新增 `resendPlatformTenantActivation` 适配器；租户详情页管理员卡片在待激活时显示「重发激活邮件」按钮，结果区展示邮件状态与可复制激活链接。

## 边界

- 不支持修改管理员邮箱；不提供自助重发；不保存发送历史；不做频率限制。
- 不主动作废历史令牌；任一令牌激活成功后其余令牌全部失效。
- 仅平台管理员可触发；激活链接只出现在本次响应与邮件中。

## 验证

- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `npm --prefix web test`
- `npm --prefix web run build`
- `python scripts/validate_agents_docs.py --level ERROR`
```

注意：若实际执行的验证命令或结果与上述有出入，按真实情况修改后再提交。

- [ ] **Step 3: 归档 ExecPlan**

```powershell
git mv docs/exec-plans/active/20260610-platform-resend-admin-activation.md docs/exec-plans/completed/20260610-platform-resend-admin-activation.md
```

同时检查计划内所有 checkbox 已勾选（`- [x]`）。

不更新 `docs/exec-plans/active/index.md` 与 `docs/exec-plans/completed/index.md` 中他人未提交的行；只把本计划自己的行从 active 索引移到 completed 索引（若 active 索引中本计划的行尚未提交，则连同该行的增删一并留在工作区，由仓库维护者随批次提交，本次提交不包含两个 index 文件）。

- [ ] **Step 4: Commit**

```powershell
git add docs/changelog/20260610-050000-platform-resend-admin-activation.md docs/exec-plans/active/20260610-platform-resend-admin-activation.md docs/exec-plans/completed/20260610-platform-resend-admin-activation.md
git commit -m @'
docs: 平台重发激活邮件功能 changelog 与计划归档

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
'@
```

说明：`git mv` 后旧路径的删除已在暂存区，`git add` 旧路径是为确保删除被纳入提交（路径不存在时该参数等价于记录删除）。

---

## 验收对照（Spec → Task）

| Spec 要求 | 覆盖 Task |
|---|---|
| 目标 1：详情页待激活入口 | Task 4 |
| 目标 2：重签 7 天令牌 + 复用邮件 | Task 1、2 |
| 目标 3：响应含链接与 emailDelivery、人工兜底 | Task 2、4 |
| 目标 4：定位首个 admin（created_at 最早） | Task 1（test_regenerate_targets_earliest_admin） |
| 目标 5：仅 pending_activation 可重发 | Task 1（三个拒绝用例）、Task 4（按钮条件渲染） |
| API 错误表（404/400/401） | Task 2（四个错误用例） |
| 安全：不泄露 SMTP 细节 | Task 2（test_resend_route_keeps_success_when_email_raises） |
| 安全：仅平台管理员 | Task 2（test_resend_route_requires_platform_admin） |
| 验收门禁 | Task 2 Step 5、Task 4 Step 4、Task 5 Step 1 |
