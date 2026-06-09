# 平台租户运营中转页 ExecPlan

## 目标

将平台管理员进入 Brand Dashboard Platform 后的操作逻辑落地为清晰路径：租户列表负责发现客户，租户详情负责承接客户运营上下文，项目工作台负责主业务查看，旧 dashboard 和任务状态只作为排障入口保留。

## 范围

- 新增平台租户详情 API：`GET /api/v1/platform/tenants/{tenant_key}`。
- 新增平台租户详情页：`/platform/tenants/:tenantKey`。
- 调整租户列表操作入口：列表只保留详情入口，不再恢复看板和任务状态快速入口。
- 调整租户详情页操作入口：主按钮进入 `/projects/:tenantKey`，项目行进入 `/projects/:tenantKey/:projectId` 和 `/projects/:tenantKey/:projectId/quality`。
- 补齐项目 GET 接口平台管理员只读能力：`platform_admin` 无 membership 时可读取 active 租户项目列表、项目详情、数据质量、报告列表和告警。
- 保持平台后台不发送 `X-Tenant-Key`，继续使用 `platform_admin` 鉴权。
- 同步产品规格、设计文档、变更记录和测试。

## 非目标

- 不放开平台管理员的租户写权限。
- 不把平台管理员写入所有租户 membership。
- 不重做租户工作台、legacy dashboard 或执行器管理 CRUD。
- 不实现审计后台、平台管理员表或租户成员管理。

## 任务拆解

| Task | 状态 | 验收 |
|------|------|------|
| 建立任务和门控 | complete | `TASKS.md` 和本 ExecPlan 可见 |
| 平台租户详情 API | complete | 平台管理员可读取详情和项目摘要，非平台用户拒绝 |
| 平台租户详情页 | complete | `/platform/tenants/:tenantKey` 可渲染客户资料、项目摘要和排障入口 |
| 租户列表入口调整 | complete | 列表只保留“详情”主入口 |
| 项目工作台主入口收敛 | complete | 详情页主按钮跳 `/projects/:tenantKey`，项目行提供详情和数据质量入口 |
| 项目 GET 平台只读权限 | complete | 平台管理员无 membership 可读 active 租户项目 GET，写接口仍 403 |
| 文档同步 | complete | 产品规格、设计文档、changelog 和索引更新 |
| 验证归档 | complete | 门控通过，ExecPlan 移入 completed，active index 更新 |

## 决策记录

| 决策 | 原因 |
|------|------|
| 租户详情放在 `/platform/tenants/:tenantKey` | 平台管理员先处理客户运营上下文，再进入项目工作台或排障入口，避免从列表突然跳入 legacy dashboard。 |
| 详情数据走 `/api/v1/platform/*` | 平台后台属于平台域，不应伪装成租户 membership，也不应发送 `X-Tenant-Key`。 |
| 先返回项目摘要，不开放项目写操作 | 平台运营需要识别客户项目和排障入口，但本阶段不改变租户配置权限。 |
| 移除列表上的快速看板/任务入口 | 列表只负责客户发现；排障动作进入详情页后再选择，避免平台后台第一层导航分叉。 |
| 详情页主操作进入项目工作台 | 当前主业务入口是 `/projects/:tenantKey`；旧 `dashboard` 只保留兼容和排障价值。 |
| 项目 GET 使用平台只读租户上下文 | 平台管理员能读取 active 租户项目现状，但不写入 `user_tenants`，也不获得租户 admin 权限。 |

## 门控

| Gate | 命令 | 状态 |
|------|------|------|
| 后端定向测试 | `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_tenants.py api/tests/test_projects_api.py -q` | passed |
| 前端平台测试 | `npm --prefix web test -- src/api/__tests__/platform.test.js src/components/platform/__tests__/tenantPresentation.test.js src/components/projects/__tests__/projectPresentation.test.js` | passed |
| 前端构建 | `npm --prefix web run build` | passed |
| 文档结构 | `python scripts/validate_agents_docs.py --level ERROR` | passed |
| Diff 检查 | `git diff --check` | passed |

## 进度记录

- 2026-06-09：创建任务清单和 active ExecPlan。
- 2026-06-09：新增平台租户详情 API 和后端测试；后端定向测试 9 passed。
- 2026-06-09：新增平台租户详情页、租户列表详情入口、前端 API 和展示工具测试；平台定向前端测试 16 passed。
- 2026-06-09：同步产品规格、平台 API 参考、设计文档和 changelog。
- 2026-06-09：`npm --prefix web run build` 通过；Playwright 桌面和移动渲染检查通过，无 console error。
- 2026-06-09：`ruff check api/v1/repositories/tenants.py api/v1/routes/auth.py api/tests/test_platform_tenants.py` 通过。
- 2026-06-09：删除临时 `TASKS.md`，归档 ExecPlan；文档结构验证和 `git diff --check` 通过。
- 2026-06-09：按平台管理员项目工作台收敛方案追加实现：租户详情页主入口改为 `/projects/:tenantKey`，项目行增加详情与数据质量入口，旧 dashboard 文案改为“最新任务看板”并保留在排障入口；项目 GET 接口改用平台只读租户上下文，写接口保持原权限。
- 2026-06-09：补齐平台只读 UI 边界：平台管理员无目标租户 membership 时，数据质量页不展示“重新分析”写操作；新增 `platformAccess` helper 测试。最终门控通过：后端 25 passed，前端指定 21 passed，前端扩展 25 passed，构建、文档 ERROR、ruff 和 `git diff --check` 通过。

## 错误记录

| 错误 | 处理 |
|------|------|
| `npm --prefix web test -- platform` 把 `platform` 当作测试文件，返回 Could not find 'platform' | 改为传入具体平台测试文件路径。 |
| `python scripts/validate_agents_docs.py --level ERROR` 在任务进行中因临时 `TASKS.md` 不符合标准区段失败 | 任务完成后删除 `TASKS.md`，以 completed ExecPlan 承接长期记录。 |
| `ruff check api` 在未改动的 `api/tests/test_legacy_geo_migration.py` import 排序失败 | 未改无关文件；本次 touched Python 文件 ruff 通过。 |
