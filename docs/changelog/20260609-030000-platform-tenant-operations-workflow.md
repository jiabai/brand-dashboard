# 平台租户运营中转页

## 变更内容

- 新增 `GET /api/v1/platform/tenants/{tenant_key}`，平台管理员可读取租户运营详情和监测项目摘要。
- 新增 `/platform/tenants/:tenantKey` 平台租户详情页，展示客户资料、项目摘要、项目工作台主入口和排障入口。
- 租户列表只保留“详情”主入口；“看板”和“任务状态”不在列表行展示。
- 租户详情页主按钮为“进入项目工作台”，跳转 `/projects/:tenantKey`。
- 平台管理员通过租户详情进入项目工作台后，项目工作台顶部显示“返回租户详情”，跳回 `/platform/tenants/:tenantKey`。
- 租户详情页项目区改为“项目概览”，项目工作台页标题改为“项目工作台”，避免两个页面都叫“监测项目”。
- 租户详情页项目行增加“打开项目”和“数据质量”，分别跳转 `/projects/:tenantKey/:projectId` 和 `/projects/:tenantKey/:projectId/quality`。
- 从租户详情“项目概览”进入项目详情或数据质量时携带 `from=platform-tenant-detail`，项目详情页返回 `/platform/tenants/:tenantKey#project-overview`；从项目工作台进入项目详情时仍返回项目工作台。
- “最新看板”改名为“最新任务看板”，与“任务状态”一起放在“排障入口”区。
- 项目 GET 接口补齐平台管理员只读能力：`platform_admin` 无 membership 时可读取 active 租户项目列表、项目详情、数据质量、报告列表和告警。
- 更新平台 API adapter、展示工具函数和前后端回归测试。

## 边界

- 不放开平台管理员的租户写权限。
- 不把平台管理员加入客户租户 membership。
- 项目摘要通过平台 API 只读返回；进入项目工作台后，GET 读取使用平台只读租户上下文。
- 平台管理员仍不能创建项目、配置品牌、配置问题集或加载查询任务，除非同时拥有该租户 admin membership。

## 验证

- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_tenants.py -q`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_projects_api.py -q`
- `npm --prefix web test -- src/api/__tests__/platform.test.js src/components/platform/__tests__/tenantPresentation.test.js src/components/projects/__tests__/projectPresentation.test.js`
