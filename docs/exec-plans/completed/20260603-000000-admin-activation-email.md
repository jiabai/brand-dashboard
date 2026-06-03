# 管理员激活邮件发送 ExecPlan

> 完成日期：2026-06-03

## 目标

在平台管理员创建租户成功后，后端基于 `api/.env` 的 SMTP 配置自动发送首个租户管理员激活邮件，并把发送状态返回给前端展示。邮件发送失败不影响租户创建成功。

## 架构

- `api/v1/repositories/auth.py` 继续只负责租户、用户、邀请码和激活链接生成。
- `api/v1/services/email_sender.py` 负责读取 SMTP 配置、构造激活邮件和发送。
- `api/v1/routes/auth.py` 在 `create_tenant_with_admin()` 成功后调用邮件服务，并把结果合并到响应 `data.emailDelivery`。
- `web/src/components/platform/CreateTenantPanel.jsx` 展示邮件发送状态，保留激活链接复制。
- `web/src/components/LoginView.jsx` 从 `/activate?token=...` 自动填入激活令牌。

## 文件清单

- 新增：`api/v1/services/email_sender.py`
- 新增：`api/tests/test_email_sender.py`
- 修改：`api/v1/routes/auth.py`
- 修改：`api/tests/test_auth.py`
- 修改：`web/src/components/platform/tenantPresentation.js`
- 修改：`web/src/components/platform/__tests__/tenantPresentation.test.js`
- 修改：`web/src/components/platform/CreateTenantPanel.jsx`
- 新增：`web/src/auth/activation.js`
- 新增：`web/src/auth/__tests__/activation.test.js`
- 修改：`web/src/components/LoginView.jsx`
- 修改：`docs/product-specs/index.md`
- 新增：`docs/product-specs/20260603-000000-admin-activation-email.md`
- 新增：`docs/changelog/20260603-000000-admin-activation-email.md`

## 任务完成

### Task 1：后端邮件服务测试

- [x] 新增 `api/tests/test_email_sender.py`。
- [x] 覆盖 SMTP 配置缺失时返回 `not_configured`。
- [x] 覆盖 `SMTP_PORT=465` + `SMTP_USE_TLS=true` 时使用 `smtplib.SMTP_SSL`。
- [x] 覆盖邮件正文包含租户名称、管理员邮箱、激活链接和 7 天有效期提示。

### Task 2：后端邮件服务实现

- [x] 新增 `api/v1/services/email_sender.py`。
- [x] 使用标准库 `smtplib`、`ssl`、`email.message.EmailMessage`，不引入新依赖。
- [x] SMTP 配置不完整时不发送邮件，返回 `not_configured`。
- [x] SMTP 失败时返回 `failed`，不抛出包含敏感信息的错误给路由。

### Task 3：租户创建路由集成

- [x] 在 `api/tests/test_auth.py` 中新增路由测试：创建租户成功后调用邮件服务，并返回 `emailDelivery`。
- [x] 新增路由测试：邮件服务抛异常时创建租户仍返回 200，`emailDelivery.status = "failed"`。
- [x] 修改 `api/v1/routes/auth.py`：仓储成功后调用 `send_admin_activation_email(result)`。

### Task 4：前端状态展示

- [x] 在 `tenantPresentation.js` 新增 `getEmailDeliveryMeta()`。
- [x] 在 `tenantPresentation.test.js` 覆盖 `sent`、`not_configured`、`failed` 和未知状态。
- [x] 在 `CreateTenantPanel.jsx` 展示邮件状态提示，失败/未配置时提醒复制激活链接人工发送。

### Task 5：激活链接自动填充、文档与验证

- [x] 新增 URL token 解析 helper 和测试。
- [x] 修改 `LoginView.jsx`，让 `/activate?token=...` 自动填入激活令牌。
- [x] 新增 changelog。
- [x] 运行后端目标测试。
- [x] 运行前端目标测试。
- [x] 运行前端构建。
- [x] 运行文档结构验证。

## 验证结果

```powershell
.\api\.venv\Scripts\python.exe -m pytest -p no:cacheprovider api\tests\test_email_sender.py api\tests\test_auth.py -q
# 14 passed, 6 warnings

npm.cmd --prefix web run test -- src/components/platform/__tests__/tenantPresentation.test.js src/auth/__tests__/activation.test.js src/api/__tests__/platform.test.js
# 12 passed

npm.cmd --prefix web run build
# built successfully

ruff check api\v1\services\email_sender.py api\v1\routes\auth.py api\tests\test_email_sender.py api\tests\test_auth.py
# All checks passed

.\api\.venv\Scripts\python.exe scripts\validate_agents_docs.py --level ERROR
# 0 errors, 0 warnings
```

## 风险与缓解

- SMTP 连接失败：不阻断租户创建，返回 `failed` 并展示人工兜底。
- 密钥泄露：不提交 `.env`，不在错误响应中包含 SMTP 异常细节。
- 邮件先发但事务回滚：邮件发送只在仓储函数返回后执行。
- 页面误以为必须重建租户才能重发：本阶段不做重发功能，明确提示人工复制激活链接发送。
