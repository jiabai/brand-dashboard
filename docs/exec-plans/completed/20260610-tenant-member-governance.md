# Tenant Member Governance Completed ExecPlan

## Intent

补齐租户成员管理 API、平台应急/客服角色修改审计，以及最后一个 active admin 保护。

## Current Finding

当前不满足全部需求：

- `create_tenant_with_admin` 已能创建首个租户管理员。
- `grant_tenant_access.py` 是本地/部署脚本，不是正式 HTTP API。
- `grant_tenant_access` 没有审计日志，也没有最后管理员保护。
- `/api/v1` 下没有租户成员列表和角色修改 API。

## Implementation Tasks

1. 写失败测试：租户 admin 成员列表与角色修改。
2. 写失败测试：非 admin 拒绝、平台应急修改必须带 reason。
3. 写失败测试：最后一个 active admin 不能降级或停用。
4. 新增 `tenant_role_audit_logs` schema 与 MySQL migration。
5. 新增租户成员 repository，集中处理列表、更新、审计和最后 admin 校验。
6. 在 `auth.py` 增加租户成员 API 与平台应急成员 API。
7. 同步安全文档、changelog 和本计划验证记录。

## Gate Checklist

- [x] 定向成员治理测试先失败后通过
- [x] `ruff check api`
- [x] `python scripts/validate_agents_docs.py --level ERROR`
- [x] 本 ExecPlan 的 Progress / Decision Log / Verification 更新

## Decision Log

- 2026-06-10：保持平台角色与租户角色分离；本次只为平台管理员提供带 reason 的应急/客服修改入口，不让平台管理员天然获得租户写权限。
- 2026-06-10：角色变更审计放在独立表 `tenant_role_audit_logs`，不复用应用日志，便于按租户、目标用户、操作者查询。
- 2026-06-10：最后 active admin 保护在 repository 内集中执行，HTTP API 和 CLI 后续都应复用同一入口。

## Progress

- 2026-06-10：已 inspect 当前 schema、route、`grant_tenant_access` 和测试；确认需求未全部满足。
- 2026-06-10：新增 `api/tests/test_tenant_member_governance.py`，RED 验证为 7 failed，均因目标成员治理路由返回 404。
- 2026-06-10：新增 `tenant_members` repository、租户成员 API、平台应急成员 API、审计表 schema 与 MySQL migration；定向测试 GREEN。
- 2026-06-10：同步本地 SQLite `data/geo_csv/geo_migrated.db`，创建 `tenant_role_audit_logs` 表和索引，保证开发服务器当前数据库可直接使用新 API。
- 2026-06-10：完成全量后端测试、ruff 和文档 ERROR 门控；计划归档到 completed。
- 2026-06-10：补齐 `grant_tenant_access.py` 写路径保护；既有成员更新/恢复现在写审计，并拒绝降级最后 active admin，CLI 支持 `--actor-email` / `--reason`。

## Verification

- RED：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_member_governance.py -q` -> 7 failed，目标路由 404。
- Note：裸 `pytest` 不在 PATH；使用项目历史命令 `uv run --project api --extra dev pytest ...`。
- GREEN：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_member_governance.py -q` -> 7 passed, 77 warnings。
- Impacted regression：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_member_governance.py api/tests/test_auth_dependencies.py api/tests/test_platform_tenants.py -q` -> 20 passed, 170 warnings。
- CLI access grant：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_access_grant.py -q` -> 10 passed, 40 warnings。
- Combined tenant governance：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_member_governance.py api/tests/test_tenant_access_grant.py -q` -> 17 passed, 117 warnings。
- Backend full regression：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` -> 178 passed, 1645 warnings。
- Lint：`uv run --project api ruff check api` -> All checks passed。
- Docs：`python scripts/validate_agents_docs.py --level ERROR` -> 0 errors, 0 warnings。
