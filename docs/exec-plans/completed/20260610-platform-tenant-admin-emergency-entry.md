# 平台租户管理员应急设置入口 ExecPlan

## Intent

在平台租户详情页补齐受审计的租户管理员设置入口，用于处理已有成员但没有 active admin 的历史租户。

## Scope

- 新增平台域成员读取 API：`GET /api/v1/platform/tenants/{tenant_key}/members`。
- 新增前端平台成员 API adapter。
- 在 `PlatformTenantDetailPage` 的租户管理员卡片中新增设置入口和 Sheet 表单。
- 继续复用既有平台应急 `PATCH`、`tenant_role_audit_logs` 和最后 active admin 保护。

## Non-Goals

- 不做完整成员管理页。
- 不创建或邀请新成员。
- 不自动降级其他 admin。
- 不在租户列表页新增写操作。

## Tasks

| Task | Status | Validation |
|------|--------|------------|
| 建立任务和门控 | complete | `TASKS.md`、本 ExecPlan 和产品 Spec 可见；文档 ERROR 校验通过 |
| 红灯测试 | complete | 后端平台成员读取、前端 API adapter、详情页入口契约测试先失败 |
| 后端实现 | complete | 平台成员读取 API 通过定向后端测试 |
| 前端实现 | complete | 平台 API adapter 和详情页入口通过定向前端测试 |
| 全量门控 | complete | ruff、pytest、web test、web build、docs ERROR、浏览器烟测通过 |
| 归档收尾 | complete | changelog 完成，ExecPlan 移到 completed，`TASKS.md` 删除 |

## Decision Log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-06-10 | 设置对象仅限现有租户成员 | Quickcep 当前问题可闭环，避免把账号创建/邀请流程混入应急设置 |
| 2026-06-10 | 设置管理员不自动降级其他 admin | 降低误伤和锁定风险，最后 active admin 保护由后端统一兜底 |
| 2026-06-10 | 入口放在租户详情页管理员卡片 | 高风险写操作不放在租户列表密集表格中，保留清晰上下文 |

## Progress

- 2026-06-10：创建 `TASKS.md`、产品 Spec 和 active ExecPlan；文档 ERROR 门控通过。
- 2026-06-10：红灯测试完成；后端平台成员读取接口返回 404，前端 adapter 未导出，详情页入口契约缺失。
- 2026-06-10：新增平台成员读取路由、平台成员 API adapter 和详情页 Sheet 入口；后端/前端定向测试转绿。
- 2026-06-10：全量自动化门控通过；本地浏览器烟测通过并将 Quickcep 的 `lantianye@163.com` 设置为 active admin，审计表已记录平台操作。
- 2026-06-10：写入 changelog，准备归档 ExecPlan 并删除临时 `TASKS.md`。

## Verification

- Docs setup：`python scripts/validate_agents_docs.py --level ERROR` -> 0 errors, 0 warnings.
- RED backend：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_member_governance.py -q` -> 2 failed, 7 passed; missing platform members GET route returns 404.
- RED frontend：`npm --prefix web test -- src/api/__tests__/platform.test.js src/components/platform/__tests__/platformTenantDetailPage.test.js` -> failed; missing adapter export and missing detail-page emergency entry.
- GREEN backend scoped：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_member_governance.py api/tests/test_platform_tenants.py -q` -> 18 passed, 174 warnings.
- GREEN frontend scoped：`npm --prefix web test -- src/api/__tests__/platform.test.js src/components/platform/__tests__/platformTenantDetailPage.test.js src/components/platform/__tests__/tenantPresentation.test.js` -> 23 passed.
- Lint：`uv run --project api ruff check api` -> All checks passed.
- Backend full regression：`$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q` -> 180 passed, 1669 warnings.
- Frontend full test：`npm --prefix web test` -> 116 passed.
- Frontend build：`npm --prefix web run build` -> built in 4.13s.
- Docs：`python scripts/validate_agents_docs.py --level ERROR` -> 0 errors, 0 warnings.
- Browser smoke：Playwright opened `/platform/tenants/tn_6e1f78442bae#tenant-admin`, loaded members, submitted platform PATCH for user 1 with reason, received 200, and refreshed tenant detail.
- Local SQLite verification：Quickcep `lantianye@163.com` is now `role=admin,status=active`; latest audit log has `actor_scope=platform`, `old_role=viewer`, `new_role=admin`.
