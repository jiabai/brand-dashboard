# Web 前端架构深化设计记录

## 背景

`web/` 前端已经完成 URL 路由改造和初步 API Adapter 搭建，但剩余问题仍集中在三个方向：

- `DashboardLayout.jsx` 同时承担布局、时间范围、可用日期请求和 URL 参数修正职责
- `App.jsx` / `HomeView.jsx` 通过中间组件传递 tenant、job、brand、date 等页面参数
- 路由路径、侧栏菜单、任务入口分别维护，新增页面需要改多个文件

## 决策

1. 新增 `useTimeframeManager`，封装 timeframe、日期范围归一化、available-dates 请求、禁用日期和 URL 日期参数同步。`DashboardLayout.jsx` 保留 Header、Sidebar、Content 和 Outlet context 渲染。
2. 扩展 `useDashboardParams`，增加 JSDoc 返回说明，并新增 `useDashboardRequestParams` 作为业务组件读取 dashboard 请求上下文的统一入口。业务组件不再依赖 `App.jsx` 或 `HomeView.jsx` 透传 tenant/job/brand/date props。
3. 新增 `web/src/config/routes.js`，将 App route、Sidebar 菜单项、任务菜单项和路由元数据统一为单一配置源。`web/src/utils/routing.js` 只负责路径构建、路径识别和 search 参数清理。
4. 将业务组件中手写的 dashboard/query-jobs/auth URL 调用迁移到 `web/src/api/` Adapter，组件只传业务参数。

## 验证

- 新增 `web/src/hooks/__tests__/useTimeframeManager.test.js` 覆盖日期范围归一化、specific_day 参数输出和 available-dates 归一化。
- 新增 `web/src/config/__tests__/routes.test.js` 覆盖路由配置、菜单分组和 App 可路由条目。
- 保留并通过原有 routing/utils 测试，确保旧入口行为兼容。

## 结果

新增功能时，路由、菜单和 API 调用的改动入口更集中；组件层不再复制查询字符串拼装逻辑，也减少了从 route wrapper 到业务组件的参数透传。
