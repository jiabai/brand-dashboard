# 平台管理员 Membership 只读边界修正

## 背景

真实账号 `lantianye@163.com` 同时具备 `platform_admin` 角色和 `tn_6e1f78442bae` 的 active viewer membership。旧前端判断把该 membership 视为租户成员访问，因此项目工作台左侧栏仍显示“加入团队”。

## 变更

- 平台管理员进入租户项目工作台时始终按平台客户视角处理。
- 即使平台管理员账号拥有目标租户 membership，也隐藏“加入团队”等租户侧入口。
- 保留 `hasTenantMembership` 作为独立 helper，不删除数据库 membership。

## 验证

- `npm --prefix web test -- src/auth/__tests__/platformAccess.test.js src/components/__tests__/Sidebar.test.js`
