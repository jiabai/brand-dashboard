# SaaS 多租户系统完整注册流程详细说明

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
   - 通过邮件激活账号（管理员收到邮件激活账号）
   - 负责管理本企业内的员工和配置

3. **租户员工（客户方）**
   - 客户企业的普通员工
   - 通过邀请码自助注册
   - 注册后自动归属到对应租户
   - 默认角色为"普通员工"

### 1.2 核心概念

**tenant_key（租户唯一标识）**
- 格式：`tn_` + 12位随机字符（如 `tn_a8f3k9m2x7p1`）
- 用途：数据隔离的核心字段，所有业务表都关联此字段
- 生成时机：创建租户时自动生成
- 不可修改：一旦生成永久不变

**邀请码（Invitation Code）**
- 格式：6位大写字母+数字（如 `ABC123`）
- 用途：员工注册时验证身份
- 有效期：1个月有效期
- 使用限制：可设置最大使用次数

**激活令牌（Activation Token）**
- 格式：JWT Token
- 用途：租户管理员首次激活账号
- 有效期：7天
- 单次使用：激活后失效

---

## 二、阶段一：平台操作员创建租户

### 流程概述
```
平台操作员填写表单
    ↓
后端验证唯一性
    ↓
生成 tenant_key
    ↓
INSERT tenants（创建租户）
    ↓
INSERT users（创建管理员用户，status=pending_activation）
    ↓
INSERT user_tenants（关联管理员到租户，role=admin）
    ↓
生成激活令牌
    ↓
INSERT invitation_codes（生成企业邀请码）
    ↓
发送激活邮件给管理员
    ↓
返回成功响应
```

### 2.1 触发场景

**销售签约后，运营人员需要为客户开通账号：**
- 前提条件：已签订服务合同
- 操作者：平台操作员（已登录平台后台）
- 操作入口：平台管理后台 → 租户管理 → 创建租户

### 2.2 详细步骤

#### 步骤 1：操作员填写租户信息

操作员在平台后台填写以下信息：

**必填字段：**
```
企业信息：
- 企业名称（tenantName）："阿里巴巴集团"
- 企业法定名称（companyLegalName）："阿里巴巴（中国）网络技术有限公司"
- 统一社会信用代码（registrationNo）："91330000748833471G"
- 行业（industry）："互联网/电子商务"
- 企业类型（companyType）："有限责任公司"

管理员信息：
- 管理员姓名（adminName）："张三"
- 管理员邮箱（adminEmail）："zhangsan@alibaba.com"
- 管理员手机（adminPhone）："13800138000"

订阅信息：
- 订阅计划（planType）："enterprise"（可选：trial/basic/pro/enterprise）
- 计费周期（billingCycle）："yearly"（可选：monthly/yearly）
- 合同开始日期（contractStartDate）："2025-01-20"
- 合同结束日期（contractEndDate）："2026-01-19"
- 最大用户数（maxUsers）：200（可覆盖默认值）
```

**可选字段：**
```
- 期望的子域名（preferredSubdomain）："alibaba"
- 销售人员ID（salesPersonId）："SALES_001"
- 备注（remarks）："重要客户，优先支持"
```

#### 步骤 2：前端提交请求

前端发送 HTTP 请求：

```http
POST /api/v1/platform/tenants HTTP/1.1
Host: admin.rushlink.click
Content-Type: application/json
Authorization: Bearer eyJhbGc...（平台操作员的JWT Token）

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
  "contractStartDate": "2025-01-20",
  "contractEndDate": "2026-01-19",
  "maxUsers": 200,
  "preferredSubdomain": "alibaba",
  "salesPersonId": "SALES_001"
}
```

#### 步骤 3：后端验证唯一性

后端接收到请求后，首先验证数据唯一性：

**验证项：**
1. 检查企业名称是否已存在
   ```sql
   SELECT COUNT(*) FROM tenants WHERE tenant_name = '阿里巴巴集团';
   ```
   - 如果存在 → 返回错误："企业名称已被使用"

2. 检查管理员邮箱是否已注册
   ```sql
   SELECT COUNT(*) FROM users WHERE email = 'zhangsan@alibaba.com';
   ```
   - 如果存在 → 返回错误："该邮箱已注册"

3. 检查子域名是否已被占用（如果用户指定了）
   ```sql
   SELECT COUNT(*) FROM tenants WHERE subdomain = 'alibaba';
   ```
   - 如果存在 → 返回错误："子域名已被占用"

4. 检查统一社会信用代码是否重复（如果提供了）
   ```sql
   SELECT COUNT(*) FROM tenants WHERE registration_no = '91330000748833471G';
   ```
   - 如果存在 → 返回错误："该企业已注册"

**如果任何一项验证失败，立即返回 400 Bad Request，终止流程。**

#### 步骤 4：生成 tenant_key

如果验证通过，系统生成租户的唯一标识：

**生成逻辑：**
```python
import uuid

# 生成12位随机字符串
raw_uuid = str(uuid.uuid4()).replace("-", "")
short_uuid = raw_uuid[:12]  # 取前12位
tenant_key = f"tn_{short_uuid}"  # 添加前缀

# 结果示例：tn_a8f3k9m2x7p1
```

**冲突检查：**
虽然 UUID 冲突概率极低，但仍需检查：
```sql
SELECT COUNT(*) FROM tenants WHERE tenant_key = 'tn_a8f3k9m2x7p1';
```
- 如果已存在（极罕见），重新生成
- 最多重试5次，失败则抛出异常

#### 步骤 5：生成子域名

**两种情况：**

**情况A：用户指定了子域名（preferredSubdomain = "alibaba"）**
- 直接使用："alibaba"
- 前面已验证过唯一性，此处无需再查

**情况B：用户未指定子域名**
- 从企业名称自动生成：
  ```python
  import re

  # 转换为小写，替换非字母数字字符为连字符，合并连续连字符，去除首尾连字符
  subdomain = re.sub(r"[^a-z0-9]", "-", tenant_name.lower())
  subdomain = re.sub(r"-+", "-", subdomain).strip("-")
  
  # 如果结果为空或太短，使用tenant_key：
  if len(subdomain) < 3:
      subdomain = tenant_key  # "tn_a8f3k9m2x7p1"
  ```

- 检查唯一性，如果冲突则添加数字后缀：
  ```python
  final_subdomain = subdomain
  suffix = 1
  
  while subdomain_exists(final_subdomain):
      final_subdomain = f"{subdomain}-{suffix}"  # "alibaba-1", "alibaba-2"...
      suffix += 1
  
  # 最终结果：如 "alibaba-3"
  ```

#### 步骤 6：创建租户记录

在数据库 `tenants` 表中插入一条记录：

```sql
INSERT INTO tenants (
    tenant_key,
    tenant_name,
    subdomain,
    company_legal_name,
    company_type,
    registration_no,
    industry,
    contact_name,
    contact_email,
    contact_phone,
    status,
    plan_type,
    max_users,
    billing_cycle,
    contract_start_date,
    contract_end_date,
    created_by,
    created_at,
    updated_at
) VALUES (
    'tn_a8f3k9m2x7p1',
    '阿里巴巴集团',
    'alibaba',
    '阿里巴巴（中国）网络技术有限公司',
    '有限责任公司',
    '91330000748833471G',
    '互联网/电子商务',
    '张三',
    'zhangsan@alibaba.com',
    '13800138000',
    'active',
    'enterprise',
    200,
    'yearly',
    '2025-01-20',
    '2026-01-19',
    'usr_b9g4l0n3y8q2',  -- 平台操作员的 user_key
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 获取自增ID
-- tenant_id = 100
```

**插入后获取自增ID：**
```python
tenant_id = 12345  # 数据库返回的自增主键
```

#### 步骤 7：创建管理员账号（未激活状态）

先检查该邮箱的用户是否已存在：
```sql
SELECT id FROM users WHERE email = 'zhangsan@alibaba.com';
```

情况1：用户不存在（首次注册），在数据库 `users` 表中插入管理员记录：

```sql
INSERT INTO users (
    user_key,
    email,
    password_hash,
    first_name,
    last_name,
    phone_number,
    is_verified,
    status,  -- ⚠️ pending_activation
    created_at,
    updated_at
) VALUES (
    'usr_b9g4l0n3y8q2',  -- 生成的 user_key（UUID）
    'zhangsan@alibaba.com',
    NULL,  -- ⚠️ 密码为空，待激活
    '张三',
    NULL,
    '13800138000',
    FALSE,
    'pending_activation',  -- ⚠️ 待激活状态
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- 获取自增ID
-- user_id = 67890
```
情况2：用户已存在（该邮箱在其他租户已注册）
```sql
-- 跳过创建用户，直接使用已有的 user_id
-- 示例：user_id = 67890（已存在）
```

关联管理员到租户（核心）

插入 user_tenants 关系：
```sql
INSERT INTO user_tenants (
    user_id,
    tenant_id,
    role,
    status,
    created_at
) VALUES (
    67890,      -- 管理员的 user_id
    100,        -- 租户的 tenant_id
    'admin',    -- 角色：管理员
    'active',   -- 在该租户下的状态
    CURRENT_TIMESTAMP
);
```

#### 步骤 8：生成激活令牌（JWT Token）

为管理员生成一个激活令牌，用于激活账号：

**使用 JWT 生成：**
```java
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import java.util.Date;

String activationToken = Jwts.builder()
    .setSubject("67890")                    // 用户ID
    .claim("type", "activation")            // 令牌类型
    .claim("tenant_key", "tn_a8f3k9m2x7p1") // 租户标识
    .claim("email", "zhangsan@alibaba.com") // 邮箱（用于验证）
    .setIssuedAt(new Date())                // 签发时间
    .setExpiration(new Date(System.currentTimeMillis() + 7 * 24 * 60 * 60 * 1000)) // 7天后过期
    .signWith(SignatureAlgorithm.HS256, "your-secret-key-min-256-bits")
    .compact();

// 生成的Token示例：
// eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI2Nzg5MCIsInR5cGUiOiJhY3RpdmF0aW9uIiwidGVuYW50X2tleSI6InRuX2E4ZjNrOW0yeDdwMSIsImVtYWlsIjoiemhhbmdzYW5AYWxpYmFiYS5jb20iLCJpYXQiOjE3MDU3MjgwMDAsImV4cCI6MTcwNjMzMjgwMH0.Xk7Y9mJ3nP2qL5wR8tV4cZ1aB6dF0eH9gI3jK7lM8nO
```

**Token 内容解析：**
```json
{
  "sub": "67890",                    // 用户ID
  "type": "activation",              // 令牌类型
  "tenant_key": "tn_a8f3k9m2x7p1",   // 租户标识
  "email": "zhangsan@alibaba.com",   // 邮箱
  "iat": 1705728000,                 // 签发时间（Unix时间戳）
  "exp": 1706332800                  // 过期时间（7天后）
}
```

#### 步骤 9：生成企业邀请码

生成一个6位的邀请码，供员工注册时使用：

**生成逻辑：**
```java
import org.apache.commons.lang3.RandomStringUtils;

String inviteCode;
int maxRetries = 10;

for (int i = 0; i < maxRetries; i++) {
    // 生成6位大写字母+数字
    inviteCode = RandomStringUtils.randomAlphanumeric(6).toUpperCase();
    // 示例：AB3K9M
    
    // 检查唯一性
    boolean exists = invitationCodeRepository.existsByCode(inviteCode);
    
    if (!exists) {
        break;  // 找到唯一的邀请码
    }
}

// 最终邀请码：AB3K9M
```

**插入邀请码记录：**
```sql
INSERT INTO invitation_codes (
    tenant_key,
    code,
    status,
    max_uses,
    usage_count,
    expires_at,
    created_by,
    created_at
) VALUES (
    'tn_a8f3k9m2x7p1',                     -- 关联租户
    'AB3K9M',                              -- 邀请码
    'active',                              -- 状态：激活
    NULL,                                  -- 最大使用次数（NULL=无限制）
    0,                                     -- 已使用次数
    '2026-01-20 00:00:00',                 -- 过期时间（1年后）
    'SYSTEM',                              -- 创建人
    CURRENT_TIMESTAMP                      -- 创建时间
);
```

#### 步骤 10：初始化租户数据

为新租户创建一些默认数据：

**A. 创建默认角色：**
```sql
INSERT INTO roles (tenant_key, role_code, role_name, description) VALUES
('tn_a8f3k9m2x7p1', 'TENANT_ADMIN', '租户管理员', '拥有所有权限'),
('tn_a8f3k9m2x7p1', 'MANAGER', '部门经理', '管理部门和员工'),
('tn_a8f3k9m2x7p1', 'EMPLOYEE', '普通员工', '基础使用权限');
```

**B. 创建默认部门：**
```sql
INSERT INTO departments (tenant_key, name, description) VALUES
('tn_a8f3k9m2x7p1', '默认部门', '系统自动创建');
```

**C. 初始化系统配置：**
```sql
INSERT INTO system_settings (tenant_key, setting_key, setting_value) VALUES
('tn_a8f3k9m2x7p1', 'timezone', 'Asia/Shanghai'),
('tn_a8f3k9m2x7p1', 'language', 'zh_CN'),
('tn_a8f3k9m2x7p1', 'date_format', 'yyyy-MM-dd'),
('tn_a8f3k9m2x7p1', 'currency', 'CNY');
```

**D. 创建欢迎通知：**
```sql
INSERT INTO notifications (tenant_key, title, content, type) VALUES
('tn_a8f3k9m2x7p1', 
 '欢迎使用系统', 
 '您的企业账号已创建成功，管理员激活后即可开始使用...', 
 'SYSTEM');
```

#### 步骤 11：发送激活邮件

向管理员邮箱发送激活邮件：

**邮件内容：**
```
收件人：zhangsan@alibaba.com
主题：欢迎使用 - 请激活您的管理员账号

尊敬的 张三，您好！

您的企业"阿里巴巴集团"已在我们平台成功创建账号。

请点击下方链接激活您的管理员账号并设置密码：
https://alibaba.yourplatform.com/activate?token=eyJhbGciOiJIUzI1NiJ9...

【重要信息】
- 企业名称：阿里巴巴集团
- 登录地址：https://alibaba.yourplatform.com
- 您的邮箱：zhangsan@alibaba.com
- 企业邀请码：AB3K9M（供员工注册使用）

激活链接将在7天后失效，请尽快完成激活。

如有疑问，请联系我们的客服团队。

此致
您的平台团队
```

**发送方式：**
- 使用异步发送（不阻塞主流程）
- 记录发送日志
- 发送失败时重试3次

#### 步骤 12：返回创建结果

后端返回成功响应：

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "tenantKey": "tn_a8f3k9m2x7p1",
  "tenantName": "阿里巴巴集团",
  "subdomain": "alibaba",
  "adminEmail": "zhangsan@alibaba.com",
  "activationToken": "eyJhbGciOiJIUzI1NiJ9...",
  "activationUrl": "https://alibaba.yourplatform.com/activate?token=eyJhbGciOiJIUzI1NiJ9...",
  "inviteCode": "AB3K9M",
  "createdAt": "2025-01-20T10:30:00Z",
  "createdBy": "operator_001",
  "message": "租户创建成功，激活邮件已发送至 zhangsan@alibaba.com"
}
```

**前端显示：**
- 弹窗提示创建成功
- 显示邀请码（可复制）
- 显示激活链接（可发送给管理员）
- 跳转回租户列表页

### 2.3 数据库变化总结

**此阶段共插入以下记录：**

| 表名 | 记录数 | 关键字段 |
|------|--------|---------|
| tenants | 1 | tenant_key, subdomain, status=active |
| users | 1 | tenant_key, status=pending_activation, password=NULL |
| invitation_codes | 1 | tenant_key, code, status=active |
| roles | 3 | tenant_key, 三个默认角色 |
| departments | 1 | tenant_key, 默认部门 |
| system_settings | 4 | tenant_key, 四个配置项 |
| notifications | 1 | tenant_key, 欢迎通知 |

**事务保证：**
- 以上所有操作在一个数据库事务内完成
- 任何步骤失败，全部回滚
- 确保数据一致性

---

## 三、阶段二：租户管理员激活账号

### 流程概述
```
管理员点击激活链接
    ↓
前端加载激活页面
    ↓
填写密码并提交
    ↓
后端验证 Token
    ↓
UPDATE users（设置密码，status=active，activated_at=now）
    ↓
返回成功（包含租户列表，因为用户可能属于多个租户）
    ↓
前端跳转到租户选择页 或 直接进入该租户
```

### 3.1 触发场景

**管理员收到激活邮件后：**
- 管理员打开邮箱，看到激活邮件
- 点击激活链接：`https://alibaba.yourplatform.com/activate?token=eyJ...`
- 浏览器跳转到激活页面

### 3.2 详细步骤

#### 步骤 1：前端加载激活页面

浏览器访问激活URL：

```
GET https://alibaba.yourplatform.com/activate?token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI2Nzg5MCIsInR5cGUiOiJhY3RpdmF0aW9uIiwidGVuYW50X2tleSI6InRuX2E4ZjNrOW0yeDdwMSIsImVtYWlsIjoiemhhbmdzYW5AYWxpYmFiYS5jb20iLCJpYXQiOjE3MDU3MjgwMDAsImV4cCI6MTcwNjMzMjgwMH0.Xk7Y9mJ3nP2qL5wR8tV4cZ1aB6dF0eH9gI3jK7lM8nO
```

**前端行为：**
1. 提取URL参数中的 `token`
2. 解码Token获取基本信息（不验证签名，仅展示）：
   ```javascript
   const tokenParts = token.split('.');
   const payload = JSON.parse(atob(tokenParts[1]));
   
   // 解析结果：
   {
     "sub": "67890",
     "email": "zhangsan@alibaba.com",
     "tenant_key": "tn_a8f3k9m2x7p1"
   }
   ```
3. 显示欢迎信息："欢迎，zhangsan@alibaba.com"
4. 展示密码设置表单

#### 步骤 2：管理员填写密码

管理员在激活页面填写：

```
【激活管理员账号】

欢迎，zhangsan@alibaba.com

请设置您的登录密码：
┌─────────────────────────────┐
│ 密码：     [************]   │  ← 输入：Admin@123456
│ 确认密码：  [************]   │  ← 输入：Admin@123456
└─────────────────────────────┘

密码要求：
✓ 至少8位字符
✓ 包含大写字母
✓ 包含小写字母
✓ 包含数字

[ 激活账号 ]  按钮
```

**前端验证：**
1. 检查两次密码是否一致
2. 检查密码长度 ≥ 8
3. 检查密码复杂度（正则表达式）
4. 验证通过后，发送激活请求

#### 步骤 3：提交激活请求

前端发送POST请求：

```http
POST /api/v1/public/auth/activate HTTP/1.1
Host: alibaba.yourplatform.com
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI2Nzg5MCIsInR5cGUiOiJhY3RpdmF0aW9uIiwidGVuYW50X2tleSI6InRuX2E4ZjNrOW0yeDdwMSIsImVtYWlsIjoiemhhbmdzYW5AYWxpYmFiYS5jb20iLCJpYXQiOjE3MDU3MjgwMDAsImV4cCI6MTcwNjMzMjgwMH0.Xk7Y9mJ3nP2qL5wR8tV4cZ1aB6dF0eH9gI3jK7lM8nO",
  "password": "Admin@123456",
  "confirmPassword": "Admin@123456"
}
```

#### 步骤 4：后端验证Token

后端收到请求后，首先验证激活令牌：

**A. 验证两次密码一致性：**
```java
if (!request.getPassword().equals(request.getConfirmPassword())) {
    throw new BusinessException("两次密码不一致");
}
```

**B. 解析并验证JWT Token：**
```java
Claims claims;
try {
    claims = Jwts.parser()
        .setSigningKey("your-secret-key-min-256-bits")
        .parseClaimsJws(request.getToken())
        .getBody();
} catch (ExpiredJwtException e) {
    throw new BusinessException("激活链接已过期，请联系客服重新发送");
} catch (JwtException e) {
    throw new BusinessException("激活链接无效");
}

// 解析成功，获取内容：
String userId = claims.getSubject();              // "67890"
String tokenType = claims.get("type", String.class);  // "activation"
String tenantKey = claims.get("tenant_key", String.class);  // "tn_a8f3k9m2x7p1"
String email = claims.get("email", String.class);  // "zhangsan@alibaba.com"
```

**C. 验证Token类型：**
```java
if (!"activation".equals(tokenType)) {
    throw new BusinessException("无效的激活令牌");
}
```

#### 步骤 5：查询用户并验证状态

根据Token中的用户ID查询数据库：

```sql
SELECT * FROM users WHERE id = 67890;
```

**查询结果：**
```
id: 67890
tenant_key: tn_a8f3k9m2x7p1
username: zhangsan@alibaba.com
email: zhangsan@alibaba.com
real_name: 张三
phone: 13800138000
password: NULL                    ← 密码为空
role: TENANT_ADMIN
status: pending_activation        ← 待激活状态
is_owner: true
created_at: 2025-01-20 10:30:00
updated_at: 2025-01-20 10:30:00
activated_at: NULL
```

**验证状态：**
```java
// 1. 检查用户是否存在
if (user == null) {
    throw new NotFoundException("用户不存在");
}

// 2. 检查是否已激活
if (user.getStatus() == UserStatus.ACTIVE) {
    throw new BusinessException("账号已激活，请直接登录");
}

// 3. 检查状态是否正确
if (user.getStatus() != UserStatus.PENDING_ACTIVATION) {
    throw new BusinessException("账号状态异常，请联系管理员");
}

// 4. 验证邮箱是否匹配（防止Token被篡改）
if (!user.getEmail().equals(email)) {
    throw new BusinessException("激活令牌与账号不匹配");
}
```

#### 步骤 6：加密密码并更新用户

验证通过后，更新用户信息：

**A. 加密密码：**
```java
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
String hashedPassword = encoder.encode("Admin@123456");

// 加密结果示例：
// $2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy
```

**B. 更新数据库：**
```sql
UPDATE users SET
    password = '$2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy',
    status = 'active',
    activated_at = CURRENT_TIMESTAMP,
    updated_at = CURRENT_TIMESTAMP
WHERE id = 67890;
```

**更新后的记录：**
```
id: 67890
tenant_key: tn_a8f3k9m2x7p1
username: zhangsan@alibaba.com
email: zhangsan@alibaba.com
real_name: 张三
phone: 13800138000
password: $2a$10$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy  ← 已加密
role: TENANT_ADMIN
status: active                     ← 已激活
is_owner: true
created_at: 2025-01-20 10:30:00
updated_at: 2025-01-20 11:15:00
activated_at: 2025-01-20 11:15:00  ← 激活时间
```

#### 步骤 7：记录操作日志（可选）

在审计日志表中记录激活操作：

```sql
INSERT INTO audit_logs (
    tenant_key,
    user_id,
    action,
    description,
    ip_address,
    created_at
) VALUES (
    'tn_a8f3k9m2x7p1',
    67890,
    'ACCOUNT_ACTIVATION',
    '管理员账号激活成功',
    '192.168.1.100',
    CURRENT_TIMESTAMP
);
```

#### 步骤 8：返回激活成功响应

后端返回成功响应：

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "message": "账号激活成功！",
  "tenantKey": "tn_a8f3k9m2x7p1",
  "loginUrl": "https://alibaba.yourplatform.com/login",
  "user": {
    "id": 67890,
    "username": "zhangsan@alibaba.com",
    "realName": "张三",
    "email": "zhangsan@alibaba.com",
    "role": "TENANT_ADMIN",
    "isOwner": true
  }
}
```

#### 步骤 9：前端跳转到登录页

前端收到成功响应后：

```javascript
// 1. 显示成功提示
alert('账号激活成功！即将跳转到登录页...');

// 2. 3秒后自动跳转
setTimeout(() => {
    window.location.href = 'https://alibaba.yourplatform.com/login';
}, 3000);

// 或直接跳转
window.location.href = response.loginUrl;
```

### 3.3 数据库变化总结

**此阶段修改的记录：**

| 表名 | 操作 | 变化 |
|------|------|------|
| users | UPDATE | status: pending_activation → active |
|  |  | password: NULL → 加密后的密码 |
|  |  | activated_at: NULL → 当前时间 |
| audit_logs | INSERT | 记录激活操作日志 |

---

## 四、阶段三：租户员工自助注册

### 4.1 触发场景

**员工获得邀请码后：**
- 管理员将邀请码（`AB3K9M`）分享给员工
- 员工访问注册页面：`https://alibaba.yourplatform.com/register`
- 或访问统一注册入口：`https://yourplatform.com/register`

### 4.2 详细步骤

#### 步骤 1：员工访问注册页面

浏览器加载注册表单：

```
【员工注册】

欢迎加入我们的平台

┌─────────────────────────────┐
│ 企业邀请码：  [______]  验证   │  ← 输入：AB3K9M
└─────────────────────────────┘

企业信息：（验证邀请码后显示）
企业名称：阿里巴巴集团
邀请码有效期：2026-01-20

您的信息：
┌─────────────────────────────┐
│ 真实姓名：  [____________]   │  ← 输入：李四
│ 邮箱：     [____________]   │  ← 输入：lisi@example.com
│ 手机号：    [____________]   │  ← 输入：13900139000
│ 密码：     [____________]   │  ← 输入：User@123456
│ 职位：     [____________]   │  ← 输入：软件工程师（可选）
└─────────────────────────────┘

[ 立即注册 ]  按钮
```

#### 步骤 2：实时验证邀请码

员工输入邀请码后，前端实时调用验证接口：

**A. 前端发送验证请求：**
```http
POST /api/v1/public/users/verify-invite-code?code=AB3K9M HTTP/1.1
Host: yourplatform.com
```

**B. 后端验证逻辑：**
```sql
SELECT 
    ic.*,
    t.tenant_name
FROM invitation_codes ic
LEFT JOIN tenants t ON ic.tenant_key = t.tenant_key
WHERE ic.code = 'AB3K9M';
```

**查询结果：**
```
id: 1
tenant_key: tn_a8f3k9m2x7p1
code: AB3K9M
status: active
max_uses: NULL
usage_count: 0
expires_at: 2026-01-20 00:00:00
created_by: SYSTEM
created_at: 2025-01-20 10:30:00
tenant_name: 阿里巴巴集团
```

**C. 验证检查：**
```java
// 1. 检查邀请码是否存在
if (invitationCode == null) {
    return new InviteCodeVerification(false, "邀请码不存在", null, null);
}

// 2. 检查状态
if (invitationCode.getStatus() != InvitationStatus.ACTIVE) {
    return new InviteCodeVerification(false, "邀请码已失效", null, null);
}

// 3. 检查是否过期
if (invitationCode.getExpiresAt() != null && 
    invitationCode.getExpiresAt().isBefore(LocalDateTime.now())) {
    return new InviteCodeVerification(false, "邀请码已过期", null, null);
}

// 4. 检查使用次数（如果有限制）
if (invitationCode.getMaxUses() != null && 
    invitationCode.getUsageCount() >= invitationCode.getMaxUses()) {
    return new InviteCodeVerification(false, "邀请码已达使用上限", null, null);
}

// 验证通过
return new InviteCodeVerification(
    true, 
    "邀请码有效",
    "阿里巴巴集团",
    LocalDateTime.of(2026, 1, 20, 0, 0)
);
```

**D. 返回验证结果：**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "valid": true,
  "message": "邀请码有效",
  "tenantName": "阿里巴巴集团",
  "expiresAt": "2026-01-20T00:00:00"
}
```

**E. 前端显示企业信息：**
```javascript
if (result.valid) {
    // 显示成功提示
    document.getElementById('tenant-info').innerHTML = `
        <div class="success">
            ✓ 邀请码有效
            <p>企业名称：${result.tenantName}</p>
            <p>有效期至：${result.expiresAt}</p>
        </div>
    `;
    
    // 启用注册按钮
    document.getElementById('register-btn').disabled = false;
} else {
    // 显示错误提示
    alert(result.message);
}
```

#### 步骤 3：员工填写完整信息

员工继续填写个人信息：

```
真实姓名：李四
邮箱：lisi@example.com
手机号：13900139000
密码：User@123456
职位：软件工程师
```

#### 步骤 4：提交注册请求

前端发送注册请求：

```http
POST /api/v1/public/users/register HTTP/1.1
Host: yourplatform.com
Content-Type: application/json

{
  "inviteCode": "AB3K9M",
  "realName": "李四",
  "email": "lisi@example.com",
  "phone": "13900139000",
  "password": "User@123456",
  "jobTitle": "软件工程师"
}
```

#### 步骤 5：后端验证邀请码（再次验证）

虽然前端已验证，但后端仍需再次验证（防止绕过前端验证）：

```java
InvitationCode invitation = validateInviteCode("AB3K9M");

// 验证逻辑与步骤2相同，此处省略
// 验证通过后，获取 tenant_key
String tenantKey = invitation.getTenantKey();  // "tn_a8f3k9m2x7p1"
```

#### 步骤 6：验证邮箱唯一性

检查邮箱是否已被注册：

```sql
SELECT COUNT(*) FROM users WHERE email = 'lisi@example.com';
```

**结果：**
- 如果 COUNT > 0 → 返回错误："该邮箱已注册"
- 如果 COUNT = 0 → 继续下一步

#### 步骤 7：检查租户用户数限制

查询租户的最大用户数限制和当前用户数：

**A. 查询租户信息：**
```sql
SELECT * FROM tenants WHERE tenant_key = 'tn_a8f3k9m2x7p1';
```

**结果：**
```
max_users: 200
status: active
```

**B. 统计当前用户数：**
```sql
SELECT COUNT(*) FROM users 
WHERE tenant_key = 'tn_a8f3k9m2x7p1' 
  AND status IN ('active', 'pending_activation');
```

**结果：**
```
current_count: 1  （只有管理员1人）
```

**C. 验证是否可以注册：**
```java
if (tenant.getStatus() != TenantStatus.ACTIVE) {
    throw new BusinessException("企业账号已停用，无法注册");
}

if (currentUserCount >= tenant.getMaxUsers()) {
    throw new BusinessException(
        String.format("企业用户数已达上限（%d人），请联系管理员", 
                      tenant.getMaxUsers())
    );
}

// 当前1人 < 上限200人，可以注册
```

#### 步骤 8：创建用户记录

在数据库中插入新用户：

**A. 加密密码：**
```java
BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
String hashedPassword = encoder.encode("User@123456");

// 结果：$2a$10$Vb5lPJK8mN3oP2qR4tU6vO7wX8yZ0aB1cD2eF3gH4iJ5kL6mN7oP8
```

**B. 插入用户记录：**
```sql
INSERT INTO users (
    tenant_key,
    username,
    email,
    real_name,
    phone,
    password,
    job_title,
    role,
    status,
    is_owner,
    created_at,
    updated_at
) VALUES (
    'tn_a8f3k9m2x7p1',                                           -- 关联租户
    'lisi@example.com',                                          -- 用户名（邮箱）
    'lisi@example.com',                                          -- 邮箱
    '李四',                                                       -- 真实姓名
    '13900139000',                                               -- 手机
    '$2a$10$Vb5lPJK8mN3oP2qR4tU6vO7wX8yZ0aB1cD2eF3gH4iJ5kL6mN7oP8',  -- 加密密码
    '软件工程师',                                                 -- 职位
    'EMPLOYEE',                                                  -- 角色：普通员工
    'active',                                                    -- 状态：直接激活
    FALSE,                                                       -- 不是所有者
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

**插入后获取用户ID：**
```java
Long newUserId = 67891;
```

**关键点：**
- `tenant_key` 从邀请码获取，确保加入正确的租户
- `status` 直接设为 `active`（员工注册后立即可用，无需激活）
- `role` 默认为 `EMPLOYEE`（普通员工）
- `is_owner` 为 `FALSE`（非所有者）

#### 步骤 9：更新邀请码使用次数

增加邀请码的使用计数：

```sql
UPDATE invitation_codes SET
    usage_count = usage_count + 1,
    updated_at = CURRENT_TIMESTAMP
WHERE code = 'AB3K9M';
```

**更新后：**
```
code: AB3K9M
usage_count: 1  （从0变为1）
```

#### 步骤 10：发送欢迎邮件（可选）

向新员工发送欢迎邮件：

```
收件人：lisi@example.com
主题：欢迎加入 阿里巴巴集团

亲爱的 李四，您好！

欢迎加入"阿里巴巴集团"！

您的账号已创建成功，现在可以登录系统了。

【登录信息】
- 登录地址：https://alibaba.yourplatform.com/login
- 用户名：lisi@example.com
- 密码：您刚才设置的密码

如需帮助，请联系您的管理员或我们的客服团队。

祝您工作愉快！

此致
您的平台团队
```

#### 步骤 11：返回注册成功响应

后端返回成功响应：

```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "status": "success",
  "message": "注册成功！",
  "userId": 67891,
  "username": "lisi@example.com",
  "tenantKey": "tn_a8f3k9m2x7p1",
  "tenantName": "阿里巴巴集团",
  "loginUrl": "https://alibaba.yourplatform.com/login",
  "createdAt": "2025-01-20T14:30:00Z"
}
```

#### 步骤 12：前端跳转到登录页

前端收到成功响应后：

```javascript
// 显示成功提示
alert(`注册成功！欢迎加入 ${response.tenantName}`);

// 跳转到登录页
setTimeout(() => {
    window.location.href = response.loginUrl;
}, 2000);
```

### 4.3 数据库变化总结

**此阶段的数据库变化：**

| 表名 | 操作 | 变化 |
|------|------|------|
| users | INSERT | 新增1条员工记录，status=active |
| invitation_codes | UPDATE | usage_count: 0 → 1 |
| audit_logs | INSERT | 记录注册操作日志（可选）|

---

## 五、技术实现细节

### 5.1 数据隔离机制

**所有业务表都包含 tenant_key 字段：**

```sql
-- 示例：订单表
CREATE TABLE orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    tenant_key VARCHAR(255) NOT NULL,  -- ← 租户标识
    order_no VARCHAR(100),
    customer_name VARCHAR(100),
    amount DECIMAL(10, 2),
    created_at TIMESTAMP,
    
    INDEX idx_tenant_key (tenant_key)
);

-- 查询时必须带上 tenant_key
SELECT * FROM orders 
WHERE tenant_key = 'tn_a8f3k9m2x7p1'  -- ← 自动添加
  AND status = 'pending';
```

**MyBatis 拦截器自动添加过滤条件：**

```java
@Intercepts({
    @Signature(type = Executor.class, method = "query", ...)
})
public class TenantSqlInterceptor implements Interceptor {
    
    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        // 从上下文获取当前租户
        String tenantKey = TenantContext.getCurrentTenantKey();
        
        if (tenantKey == null) {
            throw new RuntimeException("Tenant context not set");
        }
        
        // 修改SQL，自动添加 WHERE tenant_key = 'xxx'
        // ...（省略SQL解析逻辑）
        
        return invocation.proceed();
    }
}
```

### 5.2 安全机制

**A. 密码加密（BCrypt）：**
```java
// 注册时加密
String hashedPassword = new BCryptPasswordEncoder().encode("plainPassword");

// 登录时验证
boolean matches = new BCryptPasswordEncoder().matches("plainPassword", hashedPassword);
```

**B. JWT Token 防篡改：**
```java
// 使用HMAC-SHA256签名
String token = Jwts.builder()
    .setSubject(userId)
    .signWith(SignatureAlgorithm.HS256, SECRET_KEY)  // ← 签名
    .compact();

// 验证时会自动检查签名
Jwts.parser().setSigningKey(SECRET_KEY).parseClaimsJws(token);  // ← 签名不匹配会抛异常
```

**C. 防止跨租户访问：**
```java
// 拦截器验证用户是否属于当前租户
String tenantKeyFromHeader = request.getHeader("X-Tenant-Key");
Long userId = getUserIdFromToken(request);

User user = userRepository.findById(userId);

if (!user.getTenantKey().equals(tenantKeyFromHeader)) {
    throw new ForbiddenException("User does not belong to this tenant");
}
```

### 5.3 事务管理

**使用 Spring 声明式事务：**

```java
@Service
@Transactional(rollbackFor = Exception.class)
public class PlatformTenantService {
    
    public TenantCreationResponse createTenantByPlatform(...) {
        // 所有数据库操作在同一事务内
        createTenant(...);          // ← 步骤1
        createAdminUser(...);       // ← 步骤2
        generateInviteCode(...);    // ← 步骤3
        initializeTenantData(...);  // ← 步骤4
        
        // 任何步骤抛异常，全部回滚
    }
}
```

**传播行为示例：**
```java
@Transactional(propagation = Propagation.REQUIRED)  // 加入已有事务
public void createRoles(String tenantKey) {
    // ...
}

@Transactional(propagation = Propagation.REQUIRES_NEW)  // 新事务（发邮件等）
public void sendEmail(...) {
    // 即使主事务回滚，邮件也会发送
}
```

### 5.4 异常处理

**统一异常处理器：**

```java
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ErrorResponse> handleBusinessException(BusinessException e) {
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(new ErrorResponse("BUSINESS_ERROR", e.getMessage()));
    }
    
    @ExceptionHandler(NotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFoundException(NotFoundException e) {
        return ResponseEntity
            .status(HttpStatus.NOT_FOUND)
            .body(new ErrorResponse("NOT_FOUND", e.getMessage()));
    }
    
    @ExceptionHandler(JwtException.class)
    public ResponseEntity<ErrorResponse> handleJwtException(JwtException e) {
        return ResponseEntity
            .status(HttpStatus.UNAUTHORIZED)
            .body(new ErrorResponse("INVALID_TOKEN", "令牌无效或已过期"));
    }
}
```

---

## 六、流程总结

### 6.1 三个阶段对比

| 阶段 | 操作者 | 触发方式 | 核心操作 | 状态变化 |
|------|--------|---------|---------|---------|
| **阶段1** | 平台操作员 | 手动创建 | 创建tenant + admin（未激活） | tenant: active<br>admin: pending_activation |
| **阶段2** | 租户管理员 | 点击邮件链接 | 设置密码 + 激活账号 | admin: pending_activation → active |
| **阶段3** | 租户员工 | 输入邀请码 | 自助注册 + 立即激活 | user: active（直接） |

### 6.2 关键数据流转

```
平台操作员创建租户
    ↓
生成 tenant_key = "tn_a8f3k9m2x7p1"
    ↓
生成 activation_token（管理员用）
生成 invite_code = "AB3K9M"（员工用）
    ↓
管理员收到邮件 → 激活账号
    ↓
员工获得邀请码 → 自助注册
    ↓
所有用户通过 tenant_key 关联到同一租户
    ↓
数据查询时自动过滤 WHERE tenant_key = 'tn_a8f3k9m2x7p1'
```

### 6.3 安全要点

1. ✅ **密码加密存储**：使用 BCrypt，不可逆
2. ✅ **Token 防篡改**：JWT 签名验证
3. ✅ **邀请码验证**：前后端双重验证
4. ✅ **用户数限制**：防止超额注册
5. ✅ **租户隔离**：SQL 自动添加 tenant_key 过滤
6. ✅ **权限控制**：@PreAuthorize 注解
7. ✅ **激活链接过期**：7天自动失效
8. ✅ **审计日志**：记录关键操作

这样，整个流程逻辑清晰、细节完备、安全可靠！