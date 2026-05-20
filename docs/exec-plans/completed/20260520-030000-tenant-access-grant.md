# 租户访问授权 CLI 实施计划

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

本计划解决“平台管理员登录后访问已有租户 dashboard 拿不到数据”的根因：目标租户和业务数据存在，但当前用户缺少 `user_tenants` 显式成员关系。完成后，运维人员可以通过本地 CLI 为已有用户授予已有租户的访问角色；dashboard 仍走 `get_current_tenant`，不绕过多租户隔离。

## Progress

- [x] Phase 0: 根因确认 — 本地库存在租户和 job 数据，但 `user_tenants` 无目标成员关系（2026-05-20）
- [x] Phase 1: 文档规格 — 新增产品规格、运行参考、active ExecPlan 和 TASKS（2026-05-20）
- [x] Phase 2: 测试先行 — 覆盖创建、幂等、更新、恢复和拒绝非法授权（2026-05-20，RED：缺少 `tenant_access` 模块）
- [x] Phase 3: 仓储函数与 CLI — 实现参数校验、事务写入和安全输出（2026-05-20）
- [x] Phase 4: 本地数据修复 — 为当前平台管理员补 `tn_6e1f78442bae` 的 viewer 访问（2026-05-20）
- [x] Phase 5: 验证与归档 — 后端测试、ruff、文档校验、ExecPlan 归档并删除 TASKS（2026-05-20）

## Surprises & Discoveries

- 2026-05-20：`data/geo_csv/geo.db` 中 `tn_6e1f78442bae` 和 `job_20260209_123550_e9ba00f6` 的业务数据存在，但没有任何用户 membership。
- 2026-05-20：URL 日期参数 `20260212` 与前后端约定一致，不是本次无数据的根因。

## Decision Log

| Decision | Rationale | Date/Author |
|---|---|---|
| 使用显式 `user_tenants` 授权 | 保持平台权限和租户业务数据权限隔离，避免平台管理员自动跨租户读数据 | 2026-05-20 / agent |
| 首版只提供本地/部署 CLI | 授权能力高危，公开 HTTP API 需要审计、审批、操作者记录，本次不扩大攻击面 | 2026-05-20 / agent |
| 默认角色为 `viewer` | 排障和查看 dashboard 应遵循最小权限原则 | 2026-05-20 / agent |

## Context and Orientation

相关文件：

| 类型 | 文件 |
|---|---|
| 新增 | `docs/product-specs/20260520-030000-tenant-access-grant.md` |
| 新增 | `docs/references/20260520-030000-tenant-access-grant-reference.md` |
| 新增 | `api/tests/test_tenant_access_grant.py` |
| 新增 | `api/v1/repositories/tenant_access.py` |
| 新增 | `api/scripts/grant_tenant_access.py` |
| 修改 | `docs/ARCHITECTURE_MULTITENANT.md` |
| 修改 | `docs/SECURITY.md` |

当前请求链路：

1. 前端 dashboard API 请求携带 `Authorization` 和目标 `tenant_key`。
2. `api/v1/routes/dashboard.py` 路由组依赖 `get_current_tenant`。
3. `get_current_tenant` 通过 `get_user_tenant_membership` 查询 `user_tenants`。
4. 无成员关系时返回 403 `"无权访问该租户"`。

## Plan of Work

### Phase 1: 文档规格

1. 新增租户访问授权产品规格。
2. 新增 CLI 运行参考。
3. 更新架构、安全和索引文档。
4. 创建 `TASKS.md`。

验证：

```powershell
python scripts/validate_agents_docs.py --level ERROR
```

### Phase 2: 测试先行

1. 新增 `api/tests/test_tenant_access_grant.py`。
2. 先写失败测试：
   - 新建 viewer membership。
   - 已有相同 membership 幂等返回。
   - 已有不同角色可更新。
   - 已停用 membership 可恢复。
   - 未知用户、未知租户、停用用户/租户、非法角色拒绝。
   - 授权后 `get_user_tenant_membership` 可解析。
3. 运行目标测试，确认因实现缺失失败。

验证：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_access_grant.py -q
```

### Phase 3: 仓储函数与 CLI

1. 新增 `api/v1/repositories/tenant_access.py`。
2. 新增 `api/scripts/grant_tenant_access.py`。
3. 使用 SQLAlchemy 参数绑定和事务，不拼接用户输入 SQL。
4. CLI 输出只包含动作、邮箱、租户和角色。

验证：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_access_grant.py -q
uv run --project api ruff check api
```

### Phase 4: 本地数据修复

1. 运行 CLI 为当前本地用户授予 `tn_6e1f78442bae` 的 `viewer`。
2. 直接查询 `user_tenants` 确认记录存在。

验证：

```powershell
uv run --project api python api/scripts/grant_tenant_access.py --email lantianye@163.com --tenant-key tn_6e1f78442bae --role viewer
```

### Phase 5: 收尾

1. 更新 ExecPlan Progress、Outcomes 和验证记录。
2. 运行相关后端测试、ruff 和文档 ERROR/WARN 校验。
3. 归档 ExecPlan 到 completed，更新 completed index，删除 `TASKS.md`。

## Validation and Acceptance

- 当前 dashboard URL 对应的租户访问问题通过显式 membership 解决。
- 未授权用户仍不能访问目标租户。
- 新 CLI 可重复执行且不会制造重复 membership。
- 文档准确说明平台管理员不自动拥有租户业务数据访问权。

## Outcomes & Retrospective

已完成：

- 新增 `api/v1/repositories/tenant_access.py`，提供 `grant_tenant_access`，支持创建、幂等返回、角色更新、停用 membership 恢复，以及非法状态拒绝。
- 新增 `api/scripts/grant_tenant_access.py`，支持 `--email`、`--tenant-key`、`--role viewer/member/admin`，默认 `viewer`。
- 新增 `api/tests/test_tenant_access_grant.py`，覆盖 9 个目标行为。
- 已通过 CLI 为本地用户 `lantianye@163.com` 授予 `tn_6e1f78442bae` 的 `viewer` 成员关系。
- 已用真实 dashboard API 验证：`available-dates`、`filter-metadata`、`brand-metrics`、`keyword-platform-brand-rates` 在目标租户/job/日期下返回 200。

验证记录：

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_tenant_access_grant.py -q`：9 passed，存在既有 SQLite datetime 警告。
- `uv run --project api ruff check api`：All checks passed。
- `uv run --project api python api/scripts/grant_tenant_access.py --help`：正常输出 CLI 参数说明。
- `uv run --project api python api/scripts/grant_tenant_access.py --email lantianye@163.com --tenant-key tn_6e1f78442bae --role viewer`：已创建租户访问授权。
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：71 passed，存在既有 Pydantic/SQLite 警告。
- `python scripts/validate_agents_docs.py --level ERROR`：0 errors，0 warnings。
- `python scripts/validate_agents_docs.py --level WARN`：0 errors，0 warnings。
