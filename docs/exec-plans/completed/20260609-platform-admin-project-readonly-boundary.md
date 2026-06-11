# 平台管理员项目只读边界 ExecPlan

## 目标

将平台管理员在租户项目页面中的定位收敛为“查看、排障、体验客户视角”，不提供创建、编辑、归档或删除租户项目的管理能力。

## 范围

- 保持 `/platform/tenants/:tenantKey` 的项目区为只读“项目概览”。
- 保持平台管理员无租户 membership 时只能调用项目 GET/read API。
- 在 `/projects/:tenantKey`、`/projects/:tenantKey/:projectId` 和 `/projects/:tenantKey/:projectId/quality` 中为平台只读访问显示明确提示。
- 不新增平台项目创建、编辑、归档、删除 API。
- 同步产品规格、安全文档、changelog 和测试。

## 非目标

- 不实现租户管理员项目创建、编辑或归档。
- 不把平台管理员加入客户租户 membership。
- 不改变 `user_tenants` 角色模型。
- 不调整 legacy dashboard、任务状态页或执行器权限。

## 任务拆解

| Task | 状态 | 验收 |
|------|------|------|
| 建立任务和门控 | complete | `TASKS.md`、临时计划文件和本 ExecPlan 可见 |
| 文档同步 | complete | 产品规格、安全文档和 changelog 明确平台项目只读边界 |
| 前端契约测试 | complete | 项目列表、详情、数据质量页测试覆盖只读提示 |
| 前端实现 | complete | 平台只读访问项目页时显示统一提示 |
| 验证归档 | complete | 定向测试、构建、文档验证通过，ExecPlan 移入 completed，临时任务文件删除 |

## 决策记录

| 决策 | 原因 |
|------|------|
| 不新增平台项目写接口 | 平台管理员是平台域身份，不是租户管理员代理。 |
| 租户项目工作台只显示只读提示 | 平台管理员需要体验客户视角，但不能让用户误以为平台身份可改客户配置。 |
| 复用 `isPlatformReadonlyTenantAccess` | 该 helper 已用于数据质量页隐藏重算按钮，语义与本次需求一致。 |
| 新建轻量提示组件 | 三个项目页都需要相同说明，复用组件可避免文案漂移。 |

## 验证计划

| Gate | 命令 | 状态 |
|------|------|------|
| 前端项目页契约测试 | `npm --prefix web test -- src/components/projects/__tests__/projectListPage.test.js src/components/projects/__tests__/projectDetailPage.test.js src/components/projects/__tests__/projectDataQualityPage.test.js src/components/platform/__tests__/platformTenantDetailPage.test.js` | passed |
| 后端项目权限回归 | `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_projects_api.py -q` | passed |
| 前端构建 | `npm --prefix web run build` | passed |
| 文档结构 | `python scripts/validate_agents_docs.py --level ERROR` | passed |
| Diff 检查 | `git diff --check` | passed |
| 页面烟测 | Playwright + 本机 Chrome 访问 `/projects/tn_6e1f78442bae?...` | passed |

## 进度记录

- 2026-06-09：用户确认平台管理员不应拥有租户项目创建、编辑、归档等操作；开始按只读边界修改。
- 2026-06-09：新增前端契约测试后先运行失败，确认缺少项目页只读提示；补齐 `PlatformReadonlyNotice` 后同一组测试通过（13 passed）。
- 2026-06-09：后端项目 API 权限回归通过（16 passed），确认平台管理员无 membership 仍不能创建项目或配置项目。
- 2026-06-09：前端全量测试通过（106 passed）；前端生产构建通过，输出仅含既有 Browserslist 数据偏旧提示。
- 2026-06-09：调整临时 `TASKS.md` 为标准区段后，文档结构验证通过（0 errors / 0 warnings）。
- 2026-06-09：使用本机 Chrome + Playwright 对项目列表页做平台只读访问烟测；只读提示、边界文案和项目卡片可见，4xx 响应和 console error 均为 0。
- 2026-06-09：归档 ExecPlan 到 completed，删除临时 `TASKS.md`、`task_plan.md`、`findings.md` 和 `progress.md`。
- 2026-06-09：最终文档结构验证通过（0 errors / 0 warnings）；`git diff --check` 通过，仅输出既有 Windows 换行转换提示。

## 错误记录

| 错误 | 处理 |
|------|------|
| Playwright bundled Chromium 未安装，启动时报 executable missing | 改用本机 `C:/Program Files/Google/Chrome/Application/chrome.exe` 执行页面烟测。 |
| PowerShell 管道中的中文正则被替换为问号 | 烟测脚本改用 Unicode 转义匹配中文文案。 |
| 页面烟测初次出现 `/api/v1/dashboard/available-dates` 401 | 该接口来自布局日期控件，补充 mock 拦截后烟测无 4xx 和 console error。 |
