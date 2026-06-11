# 租户加入团队入口收敛

## 变更内容

- 将租户工作台侧边栏“账户管理”入口调整为“加入团队”。
- 平台管理员只读客户视角下隐藏“加入团队”入口。
- 登录后的 `/accounts/:tenantKey` 页面收敛为邀请码核验与员工注册，不再展示账户登录表单。
- 租户开通入口继续只保留在平台后台，不在租户工作台内展示。

## 边界

- 不实现成员列表、角色管理或邀请码生成。
- 不新增后端 API。
- 不改变公开登录、注册、激活流程。

## 验证

- `npm --prefix web test -- src/components/__tests__/Sidebar.test.js src/components/__tests__/AccountManagement.test.js src/config/__tests__/routes.test.js`
- `npm --prefix web test`
- `npm --prefix web run build`
- `python scripts/validate_agents_docs.py --level ERROR`
