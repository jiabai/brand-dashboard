# 平台租户管理员信息入口

## 背景

平台管理员在租户管理页面只能看到管理员邮箱和账号状态，没有明确入口查看租户管理员的完整运营信息。排障或客户交接时，平台管理员需要快速确认首个租户管理员姓名、邮箱、手机号和账号状态。

## 变更

- 平台租户列表和详情 API 增加只读字段：`adminName`、`adminEmail`、`adminPhone`、`adminStatus`。
- 平台租户列表新增“租户管理员”入口，跳转到 `/platform/tenants/:tenantKey#tenant-admin`。
- 平台租户详情页新增“租户管理员”信息区，独立展示姓名、邮箱、手机号和账号状态。
- 保持平台管理员边界为查看、排障和客户视角体验，不新增租户管理员编辑、重置密码或重新发送激活邮件等写操作。

## 验证

- `api\.venv\Scripts\python.exe -m pytest api/tests/test_platform_tenants.py -q`
- `npm --prefix web test -- src/components/platform/__tests__/platformTenantsPage.test.js src/components/platform/__tests__/platformTenantDetailPage.test.js src/components/platform/__tests__/tenantPresentation.test.js`
