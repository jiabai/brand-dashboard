# 平台租户管理员应急设置入口

## 背景

平台租户详情页已经能展示租户管理员信息，但当历史导入或数据修复后的租户没有 active admin 时，平台运营只能通过 CLI 或后端接口处理。Quickcep 快牛智营当前已有 active 成员 `lantianye@163.com`，但租户管理员显示为未设置，因此需要在产品入口中补齐受审计的应急设置能力。

## 目标

1. 平台管理员在 `/platform/tenants/:tenantKey#tenant-admin` 能从现有租户成员中选择一人设为 active admin。
2. 平台应急设置必须填写 reason，并继续写入 `tenant_role_audit_logs`。
3. 提交成功后刷新租户详情，管理员卡片不再显示未设置。
4. 保持平台身份与租户身份分离，不把平台管理员加入客户租户 membership。

## 非目标

- 本次不实现完整前端成员管理页。
- 本次不创建或邀请新用户；只处理已有 `user_tenants` 成员。
- 本次不自动降级其他 admin；设置管理员表示把选中成员提升或恢复为 active admin。
- 本次不在平台租户列表承载写操作，列表继续只提供查看入口。

## API 行为

- `GET /api/v1/platform/tenants/{tenant_key}/members`
  - 权限：`platform_admin`
  - 行为：读取指定租户现有成员，不要求平台管理员拥有该租户 membership。
  - 响应：`data.members[]`，字段与租户侧成员列表保持一致。
- `PATCH /api/v1/platform/tenants/{tenant_key}/members/{user_id}`
  - 沿用既有平台应急接口。
  - 页面提交固定传入 `role=admin`、`status=active` 和用户填写的 `reason`。

## 页面行为

- 租户管理员卡片右上角显示操作按钮：
  - 无管理员时显示“设置管理员”。
  - 已有管理员时显示“应急设置”。
- 点击后打开右侧 Sheet，加载现有成员列表。
- Sheet 表单包含成员选择和应急原因；原因为空时不能提交。
- 提交成功后关闭或保留结果反馈，并刷新成员列表与租户详情。
- 成员列表为空时展示空状态，不提供创建/邀请入口。

## 验收标准

- 平台管理员可读取目标租户成员列表，即使自己不是该租户成员。
- 非平台用户不能调用平台成员读取 API。
- 详情页存在租户管理员设置入口、成员选择、reason 输入和平台应急 API 调用。
- Quickcep 可通过页面把现有成员 `lantianye@163.com` 设为 active admin。
- 所有变更通过后端、前端、文档和浏览器门控。
