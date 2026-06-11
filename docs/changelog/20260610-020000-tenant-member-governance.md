# 租户成员治理与角色变更审计

## 变更

- 新增租户成员列表 API：`GET /api/v1/tenants/{tenant_key}/members`，仅租户 active admin 可访问。
- 新增租户成员更新 API：`PATCH /api/v1/tenants/{tenant_key}/members/{user_id}`，支持更新 `role` / `status` 并写入审计。
- 新增平台应急成员更新 API：`PATCH /api/v1/platform/tenants/{tenant_key}/members/{user_id}`，要求 `platform_admin` 且 `reason` 必填。
- 新增 `tenant_role_audit_logs` schema 与 MySQL migration，用于记录角色/状态变更。
- 增加最后 active admin 保护，禁止降级或停用租户最后一个 active admin。
- `grant_tenant_access.py` 增加 `--actor-email` / `--reason`，并让既有成员角色更新/恢复写入审计、拒绝降级最后 active admin。

## 验证

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_member_governance.py -q`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_access_grant.py -q`
