# 平台管理员 Bootstrap 运行参考

> 状态：MVP 已落地参考，2026-05-20
>
> 本文档说明如何创建首个平台管理员登录账号。平台运营后台见 `docs/product-specs/20260520-010000-platform-operations-console.md`。

## 1. 背景说明

`PLATFORM_ADMIN_EMAILS` 只是授权白名单，不会自动创建用户。平台管理员登录需要同时满足：

1. `users.email` 中存在该邮箱，用户状态为 `active`。
2. 该邮箱存在于后端环境变量 `PLATFORM_ADMIN_EMAILS`。
3. 用户使用正确密码调用 `/api/v1/public/auth/login`。

## 2. 推荐命令

开发环境从仓库根目录运行：

```powershell
uv run --project api python api/scripts/bootstrap_platform_admin.py `
  --email ops@example.com `
  --password "ChangeMe-Strong-Password-123" `
  --write-env
```

如果账号已存在且需要重置密码：

```powershell
uv run --project api python api/scripts/bootstrap_platform_admin.py `
  --email ops@example.com `
  --password "New-Strong-Password-123" `
  --write-env `
  --reset-password
```

也可以通过环境变量传入，避免命令历史记录密码：

```powershell
$env:PLATFORM_BOOTSTRAP_ADMIN_EMAIL="ops@example.com"
$env:PLATFORM_BOOTSTRAP_ADMIN_PASSWORD="ChangeMe-Strong-Password-123"
uv run --project api python api/scripts/bootstrap_platform_admin.py --write-env
```

## 3. `.env` 行为

`--write-env` 会创建或更新 `api/.env` 中的：

```env
PLATFORM_ADMIN_EMAILS=ops@example.com
```

如果已有多个邮箱，脚本会保留原值并追加新邮箱：

```env
PLATFORM_ADMIN_EMAILS=admin1@example.com,ops@example.com
```

脚本不会写入 `PLATFORM_BOOTSTRAP_ADMIN_PASSWORD`，也不会把密码打印到终端。

## 4. 服务重启

如果脚本更新了 `api/.env`，正在运行的后端进程通常已经读取过旧环境变量。需要重启后端：

```powershell
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

前端一般不需要因为 bootstrap 脚本重启；如果前端 dev server 仍是旧代码，再重启：

```powershell
npm --prefix web run dev
```

## 5. 预期结果

脚本成功后，用创建的邮箱和密码在 `/login` 登录，再访问：

```text
http://127.0.0.1:3000/platform/tenants
```

登录响应中的用户对象应包含：

```json
{
  "platformRoles": ["platform_admin"]
}
```

## 6. 常见错误

| 错误 | 原因 | 处理 |
|---|---|---|
| `邮箱未配置为平台管理员` | 未设置 `PLATFORM_ADMIN_EMAILS` 且未传 `--write-env` | 加 `--write-env` 或手工编辑 `api/.env` |
| `账号状态为 inactive/suspended` | 已存在账号被停用或封禁 | 人工审查账号状态后再处理 |
| 登录后仍跳 `/login` | 后端未运行、token 恢复失败、密码错误 | 重启后端并重新登录 |
| 登录后显示 403 | 邮箱未进入 `PLATFORM_ADMIN_EMAILS` 或后端未重启 | 检查 `api/.env` 并重启后端 |
