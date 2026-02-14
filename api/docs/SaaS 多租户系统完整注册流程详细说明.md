# SaaS 多租户系统完整注册流程详细说明 (Python/FastAPI 实现版)

---

## 一、业务背景与角色定义

### 1.1 系统角色

**三类角色：**

1. **平台操作员（乙方）**
   - 公司的销售、运营人员
   - 负责为客户创建租户账号
   - 拥有平台后台管理权限
   - 操作路径：`/api/v1/platform/*`

2. **租户管理员（客户方）**
   - 客户企业的主要负责人
   - 由平台操作员创建，状态为"待激活"
   - 通过激活链接设置密码（目前未集成邮件发送）
   - 负责管理本企业内的员工和配置

3. **租户员工（客户方）**
   - 客户企业的普通员工
   - 通过邀请码自助注册
   - 注册后自动归属到对应租户
   - 默认角色为 `member` (普通员工)

### 1.2 核心概念

**tenant_key（租户唯一标识）**
- 格式：`tn_` + 12位十六进制字符（如 `tn_1a2b3c4d5e6f`）
- 用途：数据隔离的核心字段，所有业务表都关联此字段
- 生成时机：创建租户时自动生成
- 不可修改：一旦生成永久不变

**邀请码（Invitation Code）**
- 格式：6位大写字母+数字（如 `ABC123`）
- 用途：员工注册时验证身份
- 有效期：默认 30 天
- 使用限制：可设置最大使用次数

**激活令牌（Activation Token）**
- 格式：自定义签名 JSON (Custom Signed Token)
- 用途：租户管理员首次激活账号
- 有效期：7天
- 机制：HMAC-SHA256 签名

---

## 二、阶段一：平台操作员创建租户

### 流程概述
```
平台操作员提交请求
    ↓
后端开启事务 (Transaction)
    ↓
验证唯一性 (Tenant Name, Email, Subdomain)
    ↓
生成 tenant_key (tn_hex)
    ↓
INSERT tenants
    ↓
INSERT users (status=pending_activation, password=hash(temp))
    ↓
INSERT user_tenants (role=admin)
    ↓
INSERT invitation_codes (生成默认邀请码)
    ↓
生成激活 Token (Activation Token)
    ↓
返回成功响应 (包含激活链接、邀请码)
```

### 2.1 触发场景

**操作入口**：`POST /api/v1/platform/tenants`

### 2.2 详细步骤

#### 步骤 1：前端提交请求

```http
POST /api/v1/platform/tenants HTTP/1.1
Content-Type: application/json

{
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
  "maxUsers": 200,
  "preferredSubdomain": "alibaba"
}
```

#### 步骤 2：后端处理逻辑 (Python)

后端接收请求后，在 `api.v1.repositories.auth.create_tenant_with_admin` 中处理：

1.  **生成标识**：
    ```python
    def _generate_tenant_key() -> str:
        return f"tn_{secrets.token_hex(6)}"  # 12位 Hex
    ```

2.  **事务处理与验证**：
    ```python
    with engine.begin() as conn:
        # 1. 验证企业名称唯一性
        existing_tenant = conn.execute(
            text("SELECT id FROM tenants WHERE tenant_name = :tenant_name"),
            {"tenant_name": tenant_name}
        ).fetchone()
        if existing_tenant:
            raise ValueError("企业名称已被使用")

        # 2. 验证邮箱状态
        existing_email = conn.execute(
            text("SELECT id, status FROM users WHERE email = :email"),
            {"email": admin_email}
        ).fetchone()
        if existing_email and existing_email.status in {"inactive", "suspended"}:
            raise ValueError("账号状态异常")
        
        # 3. 验证子域名
        if preferred_subdomain:
            # ... 查询 validation ...
    ```

3.  **数据插入**：
    *   **Tenants 表**: 插入租户基本信息。
    *   **Users 表**: 创建管理员用户，状态为 `pending_activation`。
    *   **User_Tenants 表**: 关联用户与租户，角色为 `admin`。
    *   **Invitation_Codes 表**: 生成初始邀请码，有效期 30 天。

4.  **生成激活令牌**：
    ```python
    activation_token = sign_token(
        {
            "user_id": user_id,
            "tenant_key": tenant_key,
            "email": admin_email,
            "type": "activation",
            "exp": int((now + timedelta(days=7)).timestamp()),
        },
        secret,
    )
    ```

#### 步骤 3：返回结果

```json
{
  "status": "success",
  "data": {
    "tenantKey": "tn_1a2b3c...",
    "tenantName": "阿里巴巴集团",
    "adminEmail": "zhangsan@alibaba.com",
    "activationToken": "eyJh... (Token)",
    "activationUrl": "https://alibaba.yourplatform.com/activate?token=...",
    "loginUrl": "https://alibaba.yourplatform.com/login",
    "inviteCode": "AB3K9M"
  },
  "message": "租户创建成功",
  "code": 200
}
```

> **注意**：当前实现未集成邮件发送服务，操作员需手动复制 `activationUrl` 发送给客户管理员。

---

## 三、阶段二：租户管理员激活账号

### 3.1 触发场景

管理员访问激活链接：`POST /api/v1/public/auth/activate`

### 3.2 详细步骤

#### 步骤 1：提交激活请求

```http
POST /api/v1/public/auth/activate HTTP/1.1
Content-Type: application/json

{
  "token": "...",
  "password": "NewPassword123!",
  "confirmPassword": "NewPassword123!"
}
```

#### 步骤 2：后端验证与更新

在 `api.v1.repositories.auth.activate_admin_account` 中：

1.  **验证 Token**：
    *   校验签名 (HMAC-SHA256)。
    *   校验过期时间 (`exp`)。
    *   校验类型 (`type == "activation"`).

2.  **更新用户状态**：
    ```python
    conn.execute(
        text("""
            UPDATE users SET
                password_hash = :password_hash,
                status = 'active',
                is_verified = 1,
                updated_at = :now
            WHERE id = :user_id
        """),
        {...}
    )
    ```

#### 步骤 3：返回结果

返回登录地址，前端引导跳转。

---

## 四、阶段三：租户员工自助注册

### 4.1 触发场景

员工使用邀请码注册：`POST /api/v1/public/users/register`

### 4.2 详细步骤

#### 步骤 1：验证邀请码 (可选预验证)

调用 `POST /api/v1/public/users/verify-invite-code` 检查邀请码有效性并获取租户信息。

#### 步骤 2：提交注册信息

```http
POST /api/v1/public/users/register HTTP/1.1
Content-Type: application/json

{
  "inviteCode": "AB3K9M",
  "realName": "李四",
  "email": "lisi@example.com",
  "password": "UserPassword123",
  "phoneNumber": "13900139000"
}
```

#### 步骤 3：后端处理

在 `api.v1.repositories.auth.register_employee` 中：

1.  **验证邀请码**：检查 `invitation_codes` 表状态、过期时间、使用次数。
2.  **创建/查询用户**：
    *   如果邮箱已存在，复用 User ID。
    *   如果不存在，创建新用户 (`status=active`)。
3.  **关联租户**：
    *   检查是否已加入该租户。
    *   插入 `user_tenants` 表，角色为 `member`。
4.  **更新邀请码**：使用次数 +1。

---

## 五、技术实现细节与安全审计

### 5.1 技术栈
- **语言框架**: Python 3.10+, FastAPI
- **数据库**: SQLAlchemy (Raw SQL approach)
- **认证**: 自定义 HMAC-SHA256 Token (非标准 JWT)
- **加密**: PBKDF2-SHA256 (260,000 iterations)

### 5.2 已知安全漏洞与设计缺陷 (Audit Findings)

⚠️ **1. 缺乏接口鉴权 (Critical)**
- **问题**: Dashboard 接口 (`api/v1/routes/dashboard.py`) 和管理接口 (`/platform/tenants`) **没有任何身份验证**。
- **风险**: 任何人只要知道 `tenant_key` 即可查询所有敏感业务数据；任何人均可创建租户。
- **建议**: 立即引入 `Depends(get_current_user)` 中间件，并在所有敏感路由上强制校验。

⚠️ **2. 数据隔离依赖客户端 (High)**
- **问题**: Dashboard 接口完全依赖前端传递的 `tenant_key` 参数来过滤数据。
- **风险**: 恶意用户可以修改 URL 中的 `tenant_key` 访问其他租户的数据（因为没有后端校验当前用户是否属于该 `tenant_key`）。
- **建议**: 后端应从 `access_token` 中解析用户所属的 `tenant_key`，或校验请求参数与 Token 中的权限是否一致。

⚠️ **3. Token 格式非标准 (Medium)**
- **问题**: 使用了自定义的 `Payload.Signature` 格式，而非标准的 `Header.Payload.Signature` JWT 格式。
- **风险**: 无法使用标准 JWT 库解析，互操作性差。
- **建议**: 迁移至 `PyJWT` 或 `python-jose` 库生成标准 JWT。

⚠️ **4. 缺乏邮件服务 (Low)**
- **问题**: 激活流程依赖人工传递链接。
- **建议**: 集成 SMTP 服务实现自动化邮件发送。

### 5.3 数据库模式映射

| 概念 | 数据库表 | 关键字段 | Python 实现差异 |
| :--- | :--- | :--- | :--- |
| 租户 | `tenants` | `tenant_key`, `subdomain` | Key 为 Hex 格式 |
| 用户 | `users` | `email`, `password_hash` | Hash 使用 PBKDF2 |
| 关系 | `user_tenants` | `role` | 角色名为 `admin`/`member` |
| 邀请 | `invitation_codes` | `code` | 有效期默认 30 天 |

