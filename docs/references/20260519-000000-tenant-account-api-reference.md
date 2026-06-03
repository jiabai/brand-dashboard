# 租户、账号、登录与权限 API 参考

> 状态：已按 Phase 1-5 落地，2026-05-20 修订
>
> 本文档记录多租户管理和登录功能的当前 API 契约，并保留后续增强事项。产品流程见 `docs/product-specs/20260519-000000-multi-tenant-registration-flow.md`，平台运营后台契约见 `docs/references/20260520-010000-platform-operations-console-reference.md`，首个平台管理员初始化见 `docs/references/20260520-020000-platform-admin-bootstrap-reference.md`，架构设计见 `docs/ARCHITECTURE_MULTITENANT.md`。

## 1. 通用约定

### 1.1 响应外壳

成功响应：

```json
{
  "status": "success",
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

错误响应：

```json
{
  "status": "error",
  "code": 400,
  "message": "请求参数无效"
}
```

HTTP 状态与业务 `code` 必须一致。认证失败使用 401，权限不足使用 403，资源不存在使用 404，参数错误使用 400。

### 1.2 认证 Header

用户态受保护 API：

```http
Authorization: Bearer <access_token>
X-Tenant-Key: tn_1a2b3c4d5e6f
```

执行器 API：

```http
X-Executor-Key: ek_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

执行器 ID 继续通过 query 参数 `executor_id` 传入，保持当前实现兼容。

### 1.3 令牌格式

| 令牌 | 当前实现 | 后续 |
|---|---|---|
| Activation Token | 自定义 HMAC `payload.signature` | 本阶段保持现状，7 天有效，单次使用 |
| Access Token | 标准 JWT `header.payload.signature`，12 小时有效 | 结束兼容期后移除旧 access token 验证回退 |

目标 access token payload：

```json
{
  "sub": "123",
  "type": "access",
  "iat": 1779235200,
  "exp": 1779278400
}
```

### 1.4 角色字段

API 对外返回产品角色：

| API 角色 | 数据库角色 |
|---|---|
| `platform_admin` | 平台管理员白名单或平台管理员表 |
| `tenant_admin` | `user_tenants.role = admin` |
| `tenant_member` | `user_tenants.role = member` |
| `tenant_viewer` | `user_tenants.role = viewer` |

## 2. 创建租户

### `POST /api/v1/platform/tenants`

平台管理员为客户企业创建租户和首个管理员账号。

正式 Web 入口应位于 `/platform/tenants` 平台运营后台，而不是租户工作台内的账户管理页。

鉴权：

- 必须携带 `Authorization: Bearer <access_token>`，且当前用户是 `platform_admin`。
- 当前实现：已接入 `require_platform_admin`，MVP 通过 `PLATFORM_ADMIN_EMAILS` 白名单识别平台管理员。
- 如果还没有平台管理员账号，先通过 `api/scripts/bootstrap_platform_admin.py` 创建或激活首个平台管理员用户；不要通过公开 API 初始化平台管理员。

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `tenantName` | string | 是 | 企业显示名称 |
| `companyLegalName` | string | 否 | 企业法定名称 |
| `registrationNo` | string | 否 | 统一社会信用代码 |
| `industry` | string | 是 | 行业 |
| `companyType` | string | 否 | 企业类型 |
| `adminName` | string | 是 | 租户管理员姓名 |
| `adminEmail` | string | 是 | 租户管理员邮箱 |
| `adminPhone` | string | 否 | 租户管理员手机号 |
| `planType` | string | 否 | `trial`、`basic`、`pro`、`enterprise` |
| `billingCycle` | string | 否 | `monthly`、`yearly` |
| `contractStartDate` | string | 否 | `YYYY-MM-DD` |
| `contractEndDate` | string | 否 | `YYYY-MM-DD` |
| `maxUsers` | int | 否 | 最大用户数 |
| `preferredSubdomain` | string | 否 | 期望子域名 |
| `salesPersonId` | string | 否 | 销售或交付人员 ID |

请求示例：

```bash
curl -X POST "http://localhost:8000/api/v1/platform/tenants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <platform_access_token>" \
  -d '{
    "tenantName": "阿里巴巴集团",
    "companyLegalName": "阿里巴巴（中国）网络技术有限公司",
    "registrationNo": "91330000748833471G",
    "industry": "互联网/电子商务",
    "companyType": "有限责任公司",
    "adminName": "张三",
    "adminEmail": "zhangsan@alibaba.com",
    "adminPhone": "13800138000",
    "planType": "enterprise",
    "billingCycle": "yearly",
    "contractStartDate": "2026-05-20",
    "contractEndDate": "2027-05-19",
    "maxUsers": 200,
    "preferredSubdomain": "alibaba",
    "salesPersonId": "SALES_001"
  }'
```

成功响应：

```json
{
  "status": "success",
  "code": 200,
  "message": "租户创建成功",
  "data": {
    "tenantKey": "tn_1a2b3c4d5e6f",
    "tenantName": "阿里巴巴集团",
    "adminEmail": "zhangsan@alibaba.com",
    "activationToken": "eyJ1c2VyX2lkIjoxMjN9.xxxxx",
    "activationUrl": "https://alibaba.yourplatform.com/activate?token=xxxxx",
    "loginUrl": "https://alibaba.yourplatform.com/login",
    "inviteCode": "ABC123",
    "emailDelivery": {
      "status": "sent",
      "to": "zhangsan@alibaba.com",
      "message": "激活邮件已发送"
    }
  }
}
```

邮件发送状态：

| status | 说明 |
|---|---|
| `sent` | SMTP 已配置且激活邮件已发送 |
| `not_configured` | SMTP 配置不完整，未自动发送；平台操作员需复制激活链接人工发送 |
| `failed` | SMTP 发送失败；平台操作员需复制激活链接人工发送 |

SMTP 通过 `api/.env` 配置，示例：

```dotenv
SMTP_HOST=smtp.example.com
SMTP_PORT=465
SMTP_USERNAME=sender@example.com
SMTP_PASSWORD=<smtp_authorization_code>
SMTP_FROM=sender@example.com
SMTP_USE_TLS=true
```

安全要求：`.env` 不提交到 Git；`SMTP_PASSWORD` 不得写入文档、日志或错误响应。邮件发送失败不影响租户创建成功。

错误：

| HTTP | message | 场景 |
|---:|---|---|
| 401 | 未提供有效的认证令牌 | 缺少或无效 token |
| 403 | 需要平台管理员权限 | 非平台管理员 |
| 400 | 企业名称已被使用 | 租户名称重复 |
| 400 | 子域名已被占用 | 子域名重复 |
| 400 | 账号状态异常 | 管理员邮箱对应用户停用或暂停 |

## 3. 激活管理员账号

### `POST /api/v1/public/auth/activate`

租户管理员通过激活链接设置密码。

鉴权：公开接口，依赖 activation token。

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `token` | string | 是 | 激活令牌 |
| `password` | string | 是 | 新密码，至少 8 位 |
| `confirmPassword` | string | 是 | 确认密码 |

请求示例：

```bash
curl -X POST "http://localhost:8000/api/v1/public/auth/activate" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<activation_token>",
    "password": "SecurePass123!",
    "confirmPassword": "SecurePass123!"
  }'
```

成功响应：

```json
{
  "status": "success",
  "code": 200,
  "message": "账号激活成功",
  "data": {
    "userId": 123,
    "email": "zhangsan@alibaba.com",
    "tenantKey": "tn_1a2b3c4d5e6f",
    "loginUrl": "https://alibaba.yourplatform.com/login"
  }
}
```

错误：

| HTTP | message | 场景 |
|---:|---|---|
| 400 | 两次密码不一致 | 密码确认失败 |
| 400 | 激活链接无效或已过期 | token 无效、过期、类型错误 |
| 400 | 用户不存在 | 激活令牌有效但对应用户已被删除 |
| 400 | 账号已激活 | 重复激活 |

## 4. 验证邀请码

### `POST /api/v1/public/users/verify-invite-code`

员工注册前验证邀请码。

鉴权：公开接口。

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `code` | string | 是 | 6 位邀请码 |

成功响应：

```json
{
  "status": "success",
  "code": 200,
  "message": "邀请码有效",
  "data": {
    "tenantKey": "tn_1a2b3c4d5e6f",
    "tenantName": "阿里巴巴集团",
    "expiresAt": "2026-06-19T00:00:00Z"
  }
}
```

安全要求：

- 不返回联系人、计划、成员数量、管理员邮箱等敏感字段。
- 无效、过期、停用、超限统一返回 400。

## 5. 员工注册

### `POST /api/v1/public/users/register`

员工通过邀请码加入租户。

鉴权：公开接口，依赖邀请码。

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `inviteCode` | string | 是 | 邀请码 |
| `realName` | string | 是 | 姓名 |
| `email` | string | 是 | 邮箱 |
| `password` | string | 是 | 密码，至少 8 位 |
| `phoneNumber` | string | 否 | 手机号 |

成功响应：

```json
{
  "status": "success",
  "code": 200,
  "message": "注册成功",
  "data": {
    "userId": 456,
    "tenantKey": "tn_1a2b3c4d5e6f",
    "tenantName": "阿里巴巴集团"
  }
}
```

错误：

| HTTP | message | 场景 |
|---:|---|---|
| 400 | 邀请码无效或已过期 | 邀请码不存在、停用、过期或超限 |
| 400 | 用户已加入该租户 | 已存在同租户成员关系 |

## 6. 用户登录

### `POST /api/v1/public/auth/login`

用户登录系统。

鉴权：公开接口。

请求体：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---:|---|
| `email` | string | 是 | 登录邮箱 |
| `password` | string | 是 | 登录密码 |

请求示例：

```bash
curl -X POST "http://localhost:8000/api/v1/public/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "zhangsan@alibaba.com",
    "password": "SecurePass123!"
  }'
```

成功响应：

```json
{
  "status": "success",
  "code": 200,
  "message": "登录成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "tokenType": "Bearer",
    "expiresIn": 43200,
    "user": {
      "userId": 123,
      "email": "zhangsan@alibaba.com",
      "tenants": [
        {
          "tenantKey": "tn_1a2b3c4d5e6f",
          "tenantName": "阿里巴巴集团",
          "role": "tenant_admin",
          "status": "active"
        }
      ],
      "platformRoles": []
    }
  }
}
```

后续增强：

- 当前错误 HTTP 状态使用 400，目标应调整为 401。

错误：

| HTTP | message | 场景 |
|---:|---|---|
| 400 | 账号或密码错误 | 邮箱不存在或密码错误 |
| 400 | 账号未激活 | 用户状态不是 active |

## 7. 当前用户信息

### `GET /api/v1/auth/me`

用于前端刷新页面后恢复登录态。

鉴权：`Authorization: Bearer <access_token>`。

成功响应：

```json
{
  "status": "success",
  "code": 200,
  "message": "获取当前用户成功",
  "data": {
    "user": {
      "userId": 123,
      "email": "zhangsan@alibaba.com",
      "tenants": [
        {
          "tenantKey": "tn_1a2b3c4d5e6f",
          "tenantName": "阿里巴巴集团",
          "role": "tenant_admin",
          "status": "active",
          "tenantStatus": "active"
        }
      ],
      "platformRoles": []
    }
  }
}
```

## 8. 受保护租户 API 约定

Dashboard、任务状态、任务加载等用户态 API 必须遵循：

```http
Authorization: Bearer <access_token>
X-Tenant-Key: tn_1a2b3c4d5e6f
```

过渡期兼容：

- 现有 query/body 中的 `tenant_key` 可保留。
- 服务端必须校验 query/body `tenant_key` 与 `X-Tenant-Key` 一致。
- 如果缺少 `X-Tenant-Key`，可在兼容期从 query/body 读取，但仍必须校验用户成员关系。

典型错误：

| HTTP | message | 场景 |
|---:|---|---|
| 401 | 未提供有效的认证令牌 | 缺少或无效 access token |
| 403 | 无权访问该租户 | 用户不属于该租户 |
| 403 | 需要租户管理员权限 | 角色不足 |
| 403 | 租户不可用 | 租户 inactive 或 suspended |
| 400 | 租户上下文不一致 | header 与 body/query tenant_key 不一致 |

## 9. 执行器 API 约定

执行器接口继续使用机器身份：

```http
GET /api/v1/query-jobs/fetch?executor_id=exec_xxx
X-Executor-Key: ek_xxx
```

当前约定：

- `/api/v1/query-jobs/fetch` 和 `/api/v1/query-jobs/report` 保持按 `executor_id` 过滤任务。
- `/api/v1/conversation/load` 已校验 `tenant_key + job_id + executor_id` 有匹配任务。
- `/api/v1/query-jobs/load` 不是执行器接口，当前要求租户管理员调用。

## 10. 数据模型摘要

| 表 | 关键字段 | 说明 |
|---|---|---|
| `tenants` | `id`、`tenant_key`、`tenant_name`、`subdomain`、`status`、`plan_type`、`max_users` | 企业租户 |
| `users` | `id`、`user_key`、`email`、`password_hash`、`is_verified`、`status` | 全局用户 |
| `user_tenants` | `user_id`、`tenant_id`、`role`、`status` | 用户与租户成员关系 |
| `invitation_codes` | `tenant_id`、`code`、`status`、`max_uses`、`usage_count`、`expires_at` | 邀请码 |
| `executors` | `executor_id`、`api_key`、`status`、`ip_address` | 执行器凭据 |
