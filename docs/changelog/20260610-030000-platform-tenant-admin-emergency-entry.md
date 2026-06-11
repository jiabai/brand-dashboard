# 平台租户管理员应急设置入口

## 变更

- 在平台租户详情页的租户管理员卡片增加“设置管理员 / 应急设置”入口。
- 新增 `GET /api/v1/platform/tenants/{tenant_key}/members`，平台管理员可读取目标租户现有成员作为应急设置候选。
- 新增前端平台成员 API adapter：`fetchPlatformTenantMembers`、`updatePlatformTenantMember`。
- Sheet 表单固定提交 `role=admin`、`status=active`，并要求填写 reason；角色变更继续写入 `tenant_role_audit_logs`。
- Quickcep 快牛智营本地开发库已通过页面入口将 `lantianye@163.com` 从 active viewer 设置为 active admin，并写入平台范围审计记录。

## 边界

- 不创建或邀请新用户。
- 不自动降级其他 admin。
- 不在平台租户列表页放置写操作入口。
- 不把平台管理员写入客户租户 membership。

## 验证

- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `npm --prefix web test`
- `npm --prefix web run build`
- `python scripts/validate_agents_docs.py --level ERROR`
- Playwright local smoke：打开 Quickcep 租户详情页，通过租户管理员卡片设置 `lantianye@163.com` 为管理员，PATCH 返回 200，审计表记录 `actor_scope=platform`。
