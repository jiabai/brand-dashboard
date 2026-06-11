# 平台只读项目工作台身份上下文

## 背景

平台管理员从租户详情页点击“进入项目工作台”后，登录态仍然保留，但项目工作台顶部没有直接展示当前账号。由于平台管理员通常没有客户租户 membership，租户选择器也不会出现，容易误判为当前登录账户信息丢失。

## 变更

- 项目工作台顶部显示当前登录账号邮箱。
- 平台只读客户视角下额外显示“客户视角”和当前路由 `tenantKey`。
- 不改变 AuthContext、token 存储、`/auth/me` 刷新逻辑，也不把平台管理员加入客户租户 membership。

## 验证

- `npm --prefix web test -- src/components/__tests__/DashboardLayout.test.js`
