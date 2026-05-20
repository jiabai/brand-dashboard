# 平台管理员 Bootstrap 实施计划

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

本计划补齐平台运营后台的首个登录账号初始化能力。完成后，部署者可以通过本地 CLI 创建一个 active 的平台管理员用户，并确保该邮箱进入 `PLATFORM_ADMIN_EMAILS` 白名单；平台运营人员随后能正常登录 `/platform/tenants`。

## Progress

- [x] Phase 0: 文档规格 — 新增产品规格、运行参考、active ExecPlan 和 TASKS（2026-05-20）
- [x] Phase 1: Bootstrap 仓储函数与测试 — 创建/复用/重置平台管理员用户（2026-05-20）
- [x] Phase 2: CLI 脚本 — 参数、环境变量、`.env` 白名单写入和安全输出（2026-05-20）
- [x] Phase 3: 登录链路验证 — bootstrap 后登录返回 `platformRoles`（2026-05-20）
- [x] Phase 4: 文档收尾与归档（2026-05-20）

## Surprises & Discoveries

- 2026-05-20：`PLATFORM_ADMIN_EMAILS` 只做邮箱到 `platform_admin` 的角色映射，不创建用户。
- 2026-05-20：平台管理员可以没有租户 membership；`authenticate_user` 会返回空 `tenants` 和 `platformRoles`，这正适合平台域身份。
- 2026-05-20：额外 CLI E2E 验证时，不能用简单分号切分 `schema_sqlite.sql`，因为 trigger 内含 `BEGIN...END`；改用 SQLite `executescript` 后验证通过。

## Decision Log

| Decision | Rationale | Date/Author |
|---|---|---|
| 使用本地 CLI 而非公开 API | bootstrap 是高危初始化能力，公开 HTTP API 容易变成生产攻击面 | 2026-05-20 / agent |
| 继续沿用 `PLATFORM_ADMIN_EMAILS` | 当前 MVP 已围绕该白名单实现，新增表会扩大本次改动范围 | 2026-05-20 / agent |
| `--write-env` 只写邮箱不写密码 | 邮箱是授权配置，密码是凭据；凭据不得落入 `.env` 或日志 | 2026-05-20 / agent |
| 已停用/封禁账号不自动恢复 | 避免 bootstrap 绕过人工风控或运营处置 | 2026-05-20 / agent |

## Context and Orientation

相关文件：

| 类型 | 文件 |
|---|---|
| 新增 | `api/v1/repositories/platform_admins.py` |
| 新增 | `api/scripts/bootstrap_platform_admin.py` |
| 新增 | `api/tests/test_platform_admin_bootstrap.py` |
| 修改 | `docs/ARCHITECTURE_MULTITENANT.md` |
| 修改 | `docs/SECURITY.md` |
| 修改 | `docs/product-specs/index.md` |
| 修改 | `docs/references/index.md` |

当前登录链路：

1. `authenticate_user` 读取 `users` 表，要求 `status=active`。
2. `get_platform_roles_for_email` 从 `PLATFORM_ADMIN_EMAILS` 匹配当前 email。
3. 匹配后登录响应和 `/auth/me` 返回 `platformRoles: ["platform_admin"]`。

## Plan of Work

### Phase 1: Bootstrap 仓储函数与测试

1. 在 `api/tests/test_platform_admin_bootstrap.py` 先写失败测试：
   - 邮箱不在白名单时拒绝 bootstrap。
   - 用户不存在时创建 active/verified 用户，密码可验证。
   - 已存在 active 用户默认不重置密码。
   - 显式 `reset_password=True` 时更新密码。
   - inactive/suspended 用户拒绝自动恢复。
2. 新增 `api/v1/repositories/platform_admins.py`：
   - `ensure_platform_admin_user(engine, email, password, reset_password=False)`。
   - `is_platform_admin_email(email, admin_emails=None)`。
   - `merge_platform_admin_email(existing, email)`。
   - `update_platform_admin_env_file(path, email)`。

验证：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_admin_bootstrap.py -q
```

### Phase 2: CLI 脚本

1. 新增 `api/scripts/bootstrap_platform_admin.py`。
2. 支持 `--email` / `PLATFORM_BOOTSTRAP_ADMIN_EMAIL`。
3. 支持 `--password` / `PLATFORM_BOOTSTRAP_ADMIN_PASSWORD`。
4. 支持 `--write-env` 更新 `api/.env` 的 `PLATFORM_ADMIN_EMAILS`。
5. 支持 `--reset-password` 显式重置已有账号密码。
6. 输出只包含邮箱、动作、是否需要重启，不输出密码。

验证：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_admin_bootstrap.py -q
uv run --project api ruff check api
```

### Phase 3: 登录链路验证

1. 在测试中用 bootstrap 创建平台管理员。
2. 设置 `PLATFORM_ADMIN_EMAILS`。
3. 调用 `authenticate_user`，断言返回 `platformRoles=["platform_admin"]` 和空租户列表。

验证：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_admin_bootstrap.py api/tests/test_auth.py -q
```

### Phase 4: 文档收尾与归档

1. 更新架构、安全、reference、product spec 当前状态。
2. 更新本 ExecPlan 的 Progress/Outcomes。
3. 运行后端相关测试、ruff、文档 ERROR/WARN 校验。
4. 归档 ExecPlan 到 completed，更新 completed index，删除 `TASKS.md`。

验证：

```powershell
$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q
uv run --project api ruff check api
python scripts/validate_agents_docs.py --level ERROR
python scripts/validate_agents_docs.py --level WARN
```

## Validation and Acceptance

- Bootstrap 脚本可以创建首个平台管理员用户。
- 未白名单邮箱无法静默成为平台管理员。
- `--write-env` 能把邮箱加入 `api/.env`，且不写入密码。
- 已有 active 用户默认保持密码不变；显式 `--reset-password` 才修改。
- inactive/suspended 用户不会被自动恢复。
- 登录 bootstrap 用户后可获得 `platform_admin` 角色。

## Outcomes & Retrospective

已完成 Phase 1-3：

- 新增 `api/v1/repositories/platform_admins.py`，提供平台管理员邮箱白名单判断、`.env` 合并写入、用户创建/激活/重置密码能力。
- 新增 `api/scripts/bootstrap_platform_admin.py`，支持 `--email`、`--password`、`--write-env`、`--reset-password`、`--env-file`。
- 新增 `api/tests/test_platform_admin_bootstrap.py`，覆盖白名单拒绝、创建用户、保留已有密码、显式重置密码、拒绝 inactive/suspended、激活 pending 用户、登录返回 `platform_admin`、`.env` 白名单合并。
- 安全边界保持为本地/部署 CLI，没有新增公开 HTTP API。

验证记录：

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_admin_bootstrap.py -q`：10 passed，存在既有 SQLite datetime 警告。
- `uv run --project api ruff check api`：All checks passed。
- `uv run --project api python api/scripts/bootstrap_platform_admin.py --help`：正常输出 CLI 参数说明。

已完成 Phase 4 文档收尾与归档：

- 更新 `docs/ARCHITECTURE_MULTITENANT.md`，记录 bootstrap CLI 作为平台管理员白名单 MVP 的初始化路径。
- 更新 `docs/SECURITY.md`，明确 bootstrap 只能是本地/部署 CLI，不提供公开 API，不输出或落盘明文密码。
- 更新 `docs/references/20260519-000000-tenant-account-api-reference.md`，补充首个平台管理员初始化入口。
- 更新产品规格与运行参考状态为 MVP 已落地。

最终验证记录：

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：62 passed，存在既有 Pydantic/SQLite 警告。
- `uv run --project api ruff check api`：All checks passed。
- `python scripts/validate_agents_docs.py --level ERROR`：0 errors，0 warnings。
- `python scripts/validate_agents_docs.py --level WARN`：0 errors，0 warnings。
- 临时 SQLite CLI E2E：`bootstrap cli e2e ok`，覆盖 `--write-env`、用户创建、登录返回 `platform_admin`、密码不出现在输出中。
