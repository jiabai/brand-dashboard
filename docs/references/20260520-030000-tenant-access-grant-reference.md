# 租户访问授权 CLI 参考

> 状态：已实现，2026-05-20 创建
>
> 本文档记录已有用户访问已有租户的本地/部署授权命令。产品边界见 `docs/product-specs/20260520-030000-tenant-access-grant.md`。

## 1. 使用场景

当已有租户和业务数据存在，但当前非平台用户无法访问租户工作台，或某用户需要真实租户 membership 时，先检查 `user_tenants` 是否存在目标成员关系。如果缺失，使用本 CLI 显式补授权。

典型表现：

- 登录成功，且当前用户不是走平台管理员 dashboard 只读旁路。
- 访问 `/dashboard/<tenantKey>/<jobId>` 后页面无数据或 API 返回 403。
- 数据库业务表中确认有该 `tenant_key` 和 `job_id` 的数据。
- `user_tenants` 中没有该用户与目标租户的记录。

## 2. 命令

```powershell
uv run --project api python api/scripts/grant_tenant_access.py `
  --email <user@example.com> `
  --tenant-key <tn_xxxxxxxxxxxx> `
  --role viewer
```

参数：

| 参数 | 必填 | 默认值 | 说明 |
|---|---:|---|---|
| `--email` | 是 | 无 | 已存在用户邮箱 |
| `--tenant-key` | 是 | 无 | 已存在租户 `tenant_key` |
| `--role` | 否 | `viewer` | 可选 `viewer`、`member`、`admin` |

## 3. 当前问题的本地修复命令

针对本地 SQLite 数据库 `data/geo_csv/geo.db` 中的 `tn_6e1f78442bae`：

```powershell
uv run --project api python api/scripts/grant_tenant_access.py `
  --email lantianye@163.com `
  --tenant-key tn_6e1f78442bae `
  --role viewer
```

授权后无需修改 URL。若后端服务已经在运行，数据库 membership 变更通常不需要重启后端；如果此前登录态中租户列表为空，建议退出并重新登录，以便前端拿到最新租户列表。

## 4. 输出

成功时 CLI 输出动作、邮箱、租户和角色，例如：

```text
已创建租户访问授权
email=user@example.com
tenant_key=tn_xxxxxxxxxxxx
role=viewer
```

失败时返回非 0 退出码，并输出错误原因：

| 错误 | 说明 |
|---|---|
| 用户不存在 | 邮箱未对应 `users` 记录 |
| 账号状态不可授权 | 用户不是 active |
| 租户不存在 | `tenant_key` 不存在 |
| 租户状态不可授权 | 租户不是 active |
| 角色无效 | 角色不在 `viewer/member/admin` |

## 5. 安全注意事项

- 该能力只提供本地/部署 CLI，不提供公开 HTTP API。
- 平台管理员 dashboard 只读访问不需要写入 `user_tenants`；本 CLI 用于非平台用户或需要真实租户成员关系的场景。
- 排障和只读查看优先授予 `viewer`，需要代操作时才授予 `admin`。
- CLI 不读取或输出用户密码、access token、executor key。
