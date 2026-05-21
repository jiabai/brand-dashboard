# 平台管理员 Bootstrap 产品规格

> 状态：MVP 已落地，2026-05-20
>
> 本文档定义 Brand Dashboard 首个平台管理员账号的初始化方案。它补齐 `/platform` 平台运营后台已经完成后暴露出的启动缺口：系统能识别 `PLATFORM_ADMIN_EMAILS` 白名单，但不会自动创建该邮箱对应的可登录用户。

## 1. 背景

平台运营后台 `/platform/tenants` 已经通过 `PlatformRoute` 和后端 `require_platform_admin` 保护。平台管理员身份当前由 `PLATFORM_ADMIN_EMAILS` 派生：

1. 用户必须先能通过 `/api/v1/public/auth/login` 登录。
2. 登录响应或 `/api/v1/auth/me` 根据当前用户邮箱匹配 `PLATFORM_ADMIN_EMAILS`。
3. 匹配后前端得到 `platformRoles: ["platform_admin"]`，后端平台 API 放行。

当前缺口是：如果系统还没有任何用户账号，或者 `api/.env` 没有配置 `PLATFORM_ADMIN_EMAILS`，平台运营后台会正确跳转登录页，但没有办法登录成平台管理员。

## 2. 目标

1. 提供一个受控的本地/部署初始化命令，用于创建第一个平台管理员登录账号。
2. 初始化命令创建或激活 `users` 表中的平台管理员用户，密码只以哈希形式入库。
3. 初始化命令可显式把邮箱加入 `api/.env` 的 `PLATFORM_ADMIN_EMAILS`，但不得写入明文密码。
4. 初始化命令必须幂等：已有账号时不重复创建；需要重置密码时必须显式传参。
5. 不新增公开 HTTP bootstrap API，避免生产环境暴露高危初始化入口。

## 3. 非目标

1. 不实现平台管理员自助邀请、审批或多级权限。
2. 不新增 `platform_admins` 数据表；MVP 仍沿用 `PLATFORM_ADMIN_EMAILS`。
3. 不在仓库提交真实平台管理员邮箱或密码。
4. 不创建租户成员关系；平台管理员可以没有任何客户租户 membership。

## 4. 方案

新增 CLI：

```powershell
uv run --project api python api/scripts/bootstrap_platform_admin.py `
  --email ops@example.com `
  --password "ChangeMe-Strong-Password-123" `
  --write-env
```

命令行为：

| 场景 | 行为 |
|---|---|
| 邮箱不在 `PLATFORM_ADMIN_EMAILS` 且未传 `--write-env` | 失败并提示配置白名单 |
| 邮箱不在 `PLATFORM_ADMIN_EMAILS` 且传 `--write-env` | 更新 `api/.env` 的 `PLATFORM_ADMIN_EMAILS`，并提示重启后端 |
| 用户不存在 | 创建 `users` 记录，`status=active`、`is_verified=true` |
| 用户已存在且 `status=active` | 默认不改密码；传 `--reset-password` 才重置密码 |
| 用户已存在且 `status=pending_activation` | 激活账号；传入密码写入哈希 |
| 用户已存在且 `status=inactive/suspended` | 失败，要求人工处理账号风险 |

## 5. 安全要求

1. 命令不得输出明文密码。
2. 命令不得把密码写入 `.env`、文档、日志或响应。
3. 密码使用现有 `api/v1/utils/security.py::hash_password` 哈希。
4. 所有 SQL 使用 SQLAlchemy `text()` 参数绑定。
5. `--write-env` 只允许写邮箱白名单，不写任何凭据。
6. 命令完成后如更新 `.env`，必须提示重启后端服务使环境变量生效。

## 6. 验收标准

- 可以创建一个无租户 membership 的 active 用户。
- 登录该用户后，响应包含 `platformRoles: ["platform_admin"]`。
- 邮箱未进白名单时脚本失败，或在显式 `--write-env` 时补齐白名单。
- 再次运行脚本不会重复创建用户。
- 已存在 active 用户默认不重置密码，显式 `--reset-password` 才更新。
- 文档说明清楚本地运行命令和后端重启要求。
