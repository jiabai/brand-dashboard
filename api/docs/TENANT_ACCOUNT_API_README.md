# 租户与账号管理 API 文档

## 创建租户 API

---------------------

### 接口信息
- **路径**: `/api/v1/platform/tenants`
- **方法**: `POST`
- **描述**: 平台操作员为客户创建租户账号
- **角色**: 平台操作员

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| tenantName | string | 是 | 企业名称 |
| companyLegalName | string | 否 | 企业法定名称 |
| registrationNo | string | 否 | 统一社会信用代码 |
| industry | string | 是 | 行业 |
| companyType | string | 否 | 企业类型 |
| adminName | string | 是 | 管理员姓名 |
| adminEmail | string | 是 | 管理员邮箱 |
| adminPhone | string | 否 | 管理员手机 |
| planType | string | 否 | 订阅计划（trial/basic/pro/enterprise） |
| billingCycle | string | 否 | 计费周期（monthly/yearly） |
| contractStartDate | string | 否 | 合同开始日期 |
| contractEndDate | string | 否 | 合同结束日期 |
| maxUsers | int | 否 | 最大用户数 |
| preferredSubdomain | string | 否 | 期望的子域名 |
| salesPersonId | string | 否 | 销售人员ID |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/platform/tenants" \
  -H "Content-Type: application/json" \
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
    "contractStartDate": "2025-01-20",
    "contractEndDate": "2026-01-19",
    "maxUsers": 200,
    "preferredSubdomain": "alibaba",
    "salesPersonId": "SALES_001"
  }'
```

### 响应格式

```json
{
  "status": "success",
  "code": 200,
  "message": "租户创建成功",
  "data": {
    "tenantKey": "tn_a8f3k9m2x7p1",
    "tenantName": "阿里巴巴集团",
    "adminEmail": "zhangsan@alibaba.com",
    "activationToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "activationUrl": "https://alibaba.yourplatform.com/activate?token=xxx",
    "loginUrl": "https://alibaba.yourplatform.com/login",
    "inviteCode": "ABC123"
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| code | int | 业务状态码 |
| message | string | 响应消息 |
| data | object | 响应数据 |
| data.tenantKey | string | 租户唯一标识 |
| data.tenantName | string | 租户名称 |
| data.adminEmail | string | 管理员邮箱 |
| data.activationToken | string | 激活令牌 |
| data.activationUrl | string | 激活链接 |
| data.loginUrl | string | 登录链接 |
| data.inviteCode | string | 邀请码 |

### 错误响应

```json
{
  "status": "error",
  "code": 400,
  "message": "企业名称已被使用"
}
```

---------------------

## 激活管理员账号 API

---------------------

### 接口信息
- **路径**: `/api/v1/public/auth/activate`
- **方法**: `POST`
- **描述**: 租户管理员通过邮件中的激活链接激活账号
- **角色**: 租户管理员

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| token | string | 是 | 激活令牌（来自邮件链接） |
| password | string | 是 | 密码（至少8位） |
| confirmPassword | string | 是 | 确认密码 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/public/auth/activate" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "password": "SecurePass123!",
    "confirmPassword": "SecurePass123!"
  }'
```

### 响应格式

```json
{
  "status": "success",
  "code": 200,
  "message": "账号激活成功",
  "data": {
    "userId": 123,
    "email": "zhangsan@alibaba.com",
    "tenantKey": "tn_a8f3k9m2x7p1",
    "loginUrl": "https://alibaba.yourplatform.com/login"
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| code | int | 业务状态码 |
| message | string | 响应消息 |
| data | object | 响应数据 |
| data.userId | int | 用户ID |
| data.email | string | 邮箱 |
| data.tenantKey | string | 租户唯一标识 |
| data.loginUrl | string | 登录链接 |

### 错误响应

```json
{
  "status": "error",
  "code": 400,
  "message": "两次密码不一致"
}
```

---------------------

## 验证邀请码 API

---------------------

### 接口信息
- **路径**: `/api/v1/public/users/verify-invite-code`
- **方法**: `POST`
- **描述**: 员工注册前验证邀请码有效性
- **角色**: 租户员工

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| code | string | 是 | 6位邀请码 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/public/users/verify-invite-code" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "ABC123"
  }'
```

### 响应格式

```json
{
  "status": "success",
  "code": 200,
  "message": "邀请码有效",
  "data": {
    "tenantKey": "tn_a8f3k9m2x7p1",
    "tenantName": "阿里巴巴集团",
    "expiresAt": "2025-02-14T00:00:00Z"
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| code | int | 业务状态码 |
| message | string | 响应消息 |
| data | object | 响应数据 |
| data.tenantKey | string | 租户唯一标识 |
| data.tenantName | string | 租户名称 |
| data.expiresAt | string | 过期时间（ISO 8601格式） |

### 错误响应

```json
{
  "status": "error",
  "code": 400,
  "message": "邀请码无效或已过期"
}
```

---------------------

## 员工注册 API

---------------------

### 接口信息
- **路径**: `/api/v1/public/users/register`
- **方法**: `POST`
- **描述**: 租户员工通过邀请码自助注册
- **角色**: 租户员工

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| inviteCode | string | 是 | 邀请码 |
| realName | string | 是 | 真实姓名 |
| email | string | 是 | 邮箱 |
| password | string | 是 | 密码（至少8位） |
| phoneNumber | string | 否 | 手机号 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/public/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "inviteCode": "ABC123",
    "realName": "李四",
    "email": "lisi@alibaba.com",
    "password": "SecurePass123!",
    "phoneNumber": "13900139000"
  }'
```

### 响应格式

```json
{
  "status": "success",
  "code": 200,
  "message": "注册成功",
  "data": {
    "userId": 123,
    "tenantKey": "tn_a8f3k9m2x7p1",
    "tenantName": "阿里巴巴集团"
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| code | int | 业务状态码 |
| message | string | 响应消息 |
| data | object | 响应数据 |
| data.userId | int | 用户ID |
| data.tenantKey | string | 租户唯一标识 |
| data.tenantName | string | 租户名称 |

### 错误响应

```json
{
  "status": "error",
  "code": 400,
  "message": "该邮箱已注册"
}
```

---------------------

## 用户登录 API

---------------------

### 接口信息
- **路径**: `/api/v1/public/auth/login`
- **方法**: `POST`
- **描述**: 用户登录系统
- **角色**: 所有用户

### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| email | string | 是 | 登录邮箱 |
| password | string | 是 | 密码 |

### 请求示例

```bash
curl -X POST "http://your-api.com/api/v1/public/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "zhangsan@alibaba.com",
    "password": "SecurePass123!"
  }'
```

### 响应格式

```json
{
  "status": "success",
  "code": 200,
  "message": "登录成功",
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "userId": 123,
      "email": "zhangsan@alibaba.com",
      "tenants": [
        {
          "tenantKey": "tn_a8f3k9m2x7p1",
          "tenantName": "阿里巴巴集团"
        }
      ]
    }
  }
}
```

### 响应字段说明

| 字段名 | 类型 | 描述 |
|--------|------|------|
| status | string | 响应状态，"success" 或 "error" |
| code | int | 业务状态码 |
| message | string | 响应消息 |
| data | object | 响应数据 |
| data.accessToken | string | 访问令牌（JWT），有效期12小时 |
| data.user | object | 用户信息 |
| data.user.userId | int | 用户ID |
| data.user.email | string | 邮箱 |
| data.user.tenants | array | 所属租户列表 |
| data.user.tenants[].tenantKey | string | 租户唯一标识 |
| data.user.tenants[].tenantName | string | 租户名称 |

### 错误响应

```json
{
  "status": "error",
  "code": 400,
  "message": "邮箱或密码错误"
}
```

---------------------

## 核心概念

### tenant_key（租户唯一标识）

- 格式：`tn_` + 12位随机字符（如 `tn_a8f3k9m2x7p1`）
- 用途：数据隔离的核心字段，所有业务表都关联此字段
- 生成时机：创建租户时自动生成
- 特性：一旦生成永久不变

### 邀请码（Invitation Code）

- 格式：6位大写字母+数字（如 `ABC123`）
- 用途：员工注册时验证身份
- 有效期：1个月
- 使用限制：可设置最大使用次数

### 激活令牌（Activation Token）

- 格式：JWT Token
- 用途：租户管理员首次激活账号
- 有效期：7天
- 特性：单次使用，激活后失效

### 访问令牌（Access Token）

- 格式：JWT Token
- 用途：登录后访问受保护的API
- 有效期：12小时

---

## 用户状态说明

| 状态 | 说明 |
|------|------|
| pending_activation | 待激活（新创建的管理员） |
| active | 正常使用 |
| inactive | 未激活/停用 |
| suspended | 已暂停 |

---

## 租户状态说明

| 状态 | 说明 |
|------|------|
| active | 正常使用 |
| inactive | 已停用 |
| suspended | 已暂停 |

---

## 完整注册流程

```
平台操作员创建租户
        │
        ▼
┌─────────────────────────┐
│  生成 tenant_key        │
│  创建管理员用户         │
│  生成激活令牌           │
│  生成邀请码             │
│  发送激活邮件           │
└─────────────────────────┘
        │
        ▼
管理员收到邮件 → 点击激活链接 → 设置密码 → 激活成功
        │
        ▼
管理员分发邀请码给员工
        │
        ▼
员工验证邀请码 → 填写注册信息 → 注册成功
```

---

## 数据库表结构

### tenants（租户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 租户ID |
| tenant_key | VARCHAR(255) | 租户唯一标识 |
| tenant_name | VARCHAR(255) | 租户显示名称 |
| subdomain | VARCHAR(100) | 租户子域名 |
| company_legal_name | VARCHAR(255) | 企业法定名称 |
| industry | VARCHAR(100) | 行业 |
| status | ENUM | 租户状态（active/inactive/suspended） |
| plan_type | VARCHAR(50) | 订阅计划类型 |
| max_users | INT | 最大用户数 |

### users（用户表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 用户ID |
| user_key | VARCHAR(36) | 用户全局唯一标识 |
| email | VARCHAR(255) | 登录邮箱 |
| password_hash | VARCHAR(255) | 密码哈希 |
| status | ENUM | 用户状态 |

### user_tenants（用户-租户关系表）

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | BIGINT | 关联 users.id |
| tenant_id | BIGINT | 关联 tenants.id |
| role | VARCHAR(50) | 租户内角色（admin/member/viewer） |
| status | ENUM | 在该租户下的状态 |

### invitation_codes（邀请码表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 邀请码ID |
| tenant_id | BIGINT | 所属租户ID |
| code | VARCHAR(20) | 邀请码（6位） |
| status | ENUM | 邀请码状态（active/inactive/expired） |
| max_uses | INT | 最大使用次数 |
| usage_count | INT | 已使用次数 |
| expires_at | TIMESTAMP | 过期时间 |

---

## 角色定义

| 角色 | 说明 | 操作路径 |
|------|------|----------|
| 平台操作员 | 乙方销售/运营人员，负责创建租户 | `/api/v1/platform/*` |
| 租户管理员 | 客户企业负责人，通过邮件激活账号 | `/api/v1/public/auth/*` |
| 租户员工 | 客户企业普通员工，通过邀请码注册 | `/api/v1/public/users/*` |

---

## 相关文件

- 路由定义：[v1/routes/auth.py](../v1/routes/auth.py)
- 数据仓库：[v1/repositories/auth.py](../v1/repositories/auth.py)
- 数据库结构：[database/schema_auth.sql](../database/schema_auth.sql)
- 详细流程说明：[SaaS 多租户系统完整注册流程详细说明.md](./SaaS%20多租户系统完整注册流程详细说明.md)
