# 平台租户管理员信息入口 ExecPlan

## 目标

平台管理员在租户管理页面能明确进入并查看租户管理员信息，包括姓名、邮箱、手机号和账号状态。

## 范围

- 平台租户列表和详情 API 返回管理员姓名、邮箱、手机号和状态。
- 租户管理列表的管理员列增加“查看”入口，进入租户详情页管理员信息区。
- 租户详情页增加“租户管理员”信息卡片。
- 同步测试、产品规格和 changelog。

## 非目标

- 不实现租户管理员编辑、重置密码、重新发送激活邮件等写操作。
- 不新增后端路由；沿用平台租户列表和详情 API。
- 不暴露 password hash、activation token、API key 等敏感字段。

## 任务拆解

| Task | 状态 | 验收 |
|------|------|------|
| 建立任务和门禁 | complete | `TASKS.md` 和本 ExecPlan 可见 |
| 失败测试 | complete | 后端和前端定向测试先失败 |
| API 实现 | complete | 平台租户列表/详情返回管理员姓名和手机号 |
| 前端实现 | complete | 列表管理员列有查看入口，详情有租户管理员信息卡片 |
| 文档同步 | complete | 产品规格、API 参考和 changelog 已更新 |
| 验证归档 | complete | 门禁完成，ExecPlan 移入 completed，临时任务清单删除 |

## 决策记录

| 决策 | 原因 |
|------|------|
| 使用详情页锚点作为入口 | 租户管理员信息属于租户详情的一部分，不需要单独页面或新路由。 |
| 只读展示管理员信息 | 平台管理员当前职责是查看、排障和运营，不在此阶段新增账号写操作。 |
| 返回姓名、邮箱、手机号、状态 | 这些是租户创建时已采集的管理员基础信息，满足运营识别和联系需求。 |
| 使用 SQL 列别名映射平台租户响应 | 新增字段后避免依赖易错的 `row[index]` 顺序。 |

## 验证记录

| Gate | 命令 | 状态 |
|------|------|------|
| 后端定向测试 | `api\.venv\Scripts\python.exe -m pytest api/tests/test_platform_tenants.py -q` | passed，9 tests |
| 后端 scoped ruff | `uv run --project api --extra dev ruff check api/v1/repositories/tenants.py api/v1/routes/auth.py api/tests/test_platform_tenants.py` | passed |
| 后端全量 ruff | `uv run --project api --extra dev ruff check api` | blocked，未触达文件 `api/tests/test_legacy_geo_migration.py` import 排序已有问题 |
| 前端定向测试 | `npm --prefix web test -- src/components/platform/__tests__/platformTenantsPage.test.js src/components/platform/__tests__/platformTenantDetailPage.test.js src/components/platform/__tests__/tenantPresentation.test.js` | passed，16 tests |
| 前端全量测试 | `npm --prefix web test` | passed，113 tests |
| 前端构建 | `npm --prefix web run build` | passed |
| 本地浏览器烟测 | Playwright + 系统 Chrome，拦截平台租户 API，点击管理员列“查看”进入 `#tenant-admin` | passed |
| 文档结构 | `python scripts/validate_agents_docs.py --level ERROR` | passed |
| Diff 检查 | `git diff --check` | passed |

## 进度记录

- 2026-06-09：用户指出平台租户管理缺少查看租户管理员信息的机制；创建任务清单和 ExecPlan。
- 2026-06-09：补齐后端失败测试和前端源码契约测试，确认功能缺口。
- 2026-06-09：平台租户列表和详情 API 返回 `adminName`、`adminEmail`、`adminPhone`、`adminStatus`，后端定向测试 9 passed。
- 2026-06-09：租户列表新增管理员信息入口，租户详情新增 `#tenant-admin` 信息区，前端定向测试 16 passed。
- 2026-06-09：同步产品规格、API 参考和 changelog。
- 2026-06-09：前端全量测试 113 passed，构建通过；本地 Playwright 烟测确认列表入口跳转到 `/platform/tenants/tn_demo#tenant-admin`。
- 2026-06-10：根据产品审视，将操作列中的“租户管理员”按钮收敛为管理员列内的“查看”轻量入口，操作列只保留“详情”。

## 错误记录

| 错误 | 处理 |
|------|------|
| 默认 `python -m pytest` 使用的解释器未安装 pytest | 改用后端虚拟环境 `api\.venv\Scripts\python.exe -m pytest ...`。 |
| Playwright 自带 Chromium 未下载 | 使用本机 Chrome 可执行文件完成烟测。 |
| 全量 ruff 命中未触达文件 `api/tests/test_legacy_geo_migration.py` import 排序问题 | 未修改该无关文件；改用本次触达后端文件的 scoped ruff 验证新增范围。 |
