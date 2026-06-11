# 租户分析看板上下文二级导航

> 状态：设计中（待 ExecPlan 与实现），2026-06-11
>
> 关联：Legacy 兼容边界见 `docs/design-docs/20260608-legacy-compatibility-boundary.md`；路由策略源 `web/src/config/routes.js`；分析页判定 `web/src/utils/routing.js`（`isAnalysisView`）；主侧边栏 `web/src/components/Sidebar.jsx`；App 路由 `web/src/App.jsx`。

## 背景

`599a978 feat: make project navigation primary` 把产品形态改为「项目优先」，并按 `docs/design-docs/20260608-legacy-compatibility-boundary.md` 将 6 个分析页（首页 `home`、趋势 `trend`、分平台 `platforms`、信源 `sources`、情感 `sentiment`、问答快照 `snapshots`）从 `menuSection: 'main'` 降级为 `menuSection: 'legacy'`。

主侧边栏 `Sidebar.jsx` 只渲染 `getSidebarMenuRoutes()`（`menuSection==='main'` → 仅「监测项目 + 加入团队」）与 `getTaskMenuRoutes()`（`menuSection==='task'` → 空）。因此这 6 个分析页**在主导航里没有任何入口**。

用户可见现象：租户管理员在「监测项目 / 项目详情页」点「进入看板」，在右侧 Sheet 选一次采集后，`ProjectDetailPage` 经 `buildProjectDashboardPath` 跳到 `/dashboard/:tenantKey/:jobId`（legacy `home` 视图），落地页是 `HomeView`（标题「首页概览」）。此时侧边栏只有项目优先菜单，**趋势/分平台/信源/情感/问答快照都没有导航入口**——看起来「仪表板只剩一个首页概览」。

这些页面并未删除：`App.jsx` 用 `getRoutableRoutes()` 注册全部带 `path` 的路由（含 6 个分析页），仍可凭 URL 直达，只是丢了菜单入口。

## 需求

- 租户成员（含拥有最高权限的租户管理员）日常需查看本租户分析数据，必须能在 6 个分析页之间自由导航。
- 必须守住 Legacy 兼容边界：legacy 路由**不得回到主侧边栏菜单**（`docs/design-docs/20260608-legacy-compatibility-boundary.md` §3、回归测试 `web/src/config/__tests__/routes.test.js`）。
- 纯前端改动：不改路由 `path`、不动后端取数、不新增角色门禁。
- 可见范围与重构前一致：分析页对租户成员本就全部可见，从未按角色收窄；平台管理员「客户视角」只读模式同样可见。

## 决策

在**按采集（`jobId`）取数的分析路由内**，于内容区顶部渲染一条**水平标签栏**（上下文二级导航），在 6 个分析页之间切换，并保留 `tenantKey / jobId / 查询参数`。主侧边栏保持项目优先不变。

二级导航是一个「随采集上下文出现」的新层，**不是主侧边栏菜单**，因此不违反 Legacy 边界。

不选的两个方向及理由：

- **全局侧边栏新增「分析」分区**：要把 legacy 路由塞回主侧边栏，直接违反刚落地的 Legacy 边界文档与其回归测试；属于刚定架构即自我推翻。
- **重构为项目级聚合分析**：方向最贴合「项目中心」模型，但 6 个分析页当前数据全部按单次采集 `job_id` 取（`/trend/:tenantKey/:jobId` 等），上移到项目维度是后端聚合口径的大改，超出「导航」范畴。登记为将来演进（见「范围外」）。

## 信息架构与版式

天然层级为 `项目 → 某次采集 → 该次采集的分析`。二级导航挂在「采集看板」这一层，正好承接这一钻取链。

```
┌─────────────────────────────────────────────────────────┐
│ [全局 Header：账号 / 租户选择 / 时间范围 / 退出]            │  ← DashboardLayout（不变）
├──────────┬──────────────────────────────────────────────┤
│          │ 仪表板 ›  [首页] 趋势 分平台 信源 情感 问答快照  │  ← 新增 AnalysisNav（标签栏）
│ 主侧栏    ├──────────────────────────────────────────────┤
│ 监测项目  │                                              │
│ 加入团队  │            ← 当前分析页内容（Outlet）           │
│（不变）   │                                              │
└──────────┴──────────────────────────────────────────────┘
```

- 采用**顶部水平标签栏**，不另加竖直侧栏（主侧栏已是左侧竖栏，再加一条会变双竖栏、视觉过重）。
- 标签栏用 `web/src/components/platform/PlatformLayout.jsx` 已验证的 `NavLink` 行写法（语义化、自带 active 态）。`web/src/components/ui/tabs.jsx` 那个 primitive 面向「面板切换（value/TabsContent）」，与路由驱动的 `Outlet` 模型不搭，不采用。
- 标签栏只在 `isAnalysisView` 路由内出现；切换标签保留当前参数。

## 组件与接线（4 处，全前端）

1. **`web/src/config/routes.js`**：抽出单一谓词并新增选择器，与现有 `isAnalysisView` 收口为同一来源，消除重复：
   - `export const isAnalysisRoute = (route) => Boolean(route?.requiresJobId && route?.path && !route?.disabled);`
   - `export const getAnalysisNavRoutes = () => ROUTE_DEFINITIONS.filter(isAnalysisRoute);` → 按 ROUTES 声明序返回 `[home, trend, platforms, sources, sentiment, snapshots]`（即标签顺序）。
   - `settings`（disabled、无 path）与 `task-load/task-status`（无 jobId）天然被排除。
2. **`web/src/utils/routing.js`**：`isAnalysisView` 改为复用 `isAnalysisRoute`：`isAnalysisView = (viewKey) => isAnalysisRoute(getRouteByViewKey(viewKey));`（行为不变，DashboardLayout 的 brand 解析等既有调用不受影响）。
3. **新增 `web/src/components/AnalysisNav.jsx`**：从 `getAnalysisNavRoutes()` 渲染标签；active 态用 `getViewKeyFromPath(location.pathname)`；每个标签目标地址用 `buildViewPath(viewKey, { tenantKey, jobId })` + `buildRouteSearch({ search, nextViewKey })`——与 `Sidebar` 的 `handleMenuSelect` 完全一致（`buildRouteSearch` 会按目标页清理无关参数，必须逐标签计算）。`tenantKey/jobId` 取自 `useDashboardParams()`。
4. **新增 `web/src/components/AnalysisLayout.jsx`**：极薄布局 `<><AnalysisNav /><Outlet /></>`。
5. **`web/src/App.jsx`**：把 `getRoutableRoutes()` 按 `isAnalysisRoute` 一分为二；6 个分析路由包进一个 pathless 的 `<Route element={<AnalysisLayout/>}>`，其余路由（项目族、加入团队、任务页）保持原样直接挂在 `DashboardLayout` 下。每个分析路由元素仍各自包 `RouteShell`（ErrorBoundary + Suspense）。

## 数据流

`AnalysisNav` 仅读 `useDashboardParams()` 取 `tenantKey/jobId`、读 `location` 算 active，**不发任何请求**；各分析页继续按 `jobId` 自取数据。**后端零改动**。

## 顺带清理（在已要触碰的范围内）

`web/src/components/HomeView.jsx` 顶部「仪表板 › 首页概览」面包屑会与标签栏重复：删除该面包屑行，保留 h1 标题与描述。其余 5 页实现时核对、仅在视觉冲突时微调，不做无关重构。

## 测试边界

- `web/src/config/__tests__/routes.test.js`：
  - 断言 `getAnalysisNavRoutes()` 精确返回 `[home, trend, platforms, sources, sentiment, snapshots]`、顺序正确、全部 `requiresJobId`。
  - **复测主侧边栏不变量**：`getSidebarMenuRoutes()` 仍只返回 `[projects, accounts]`——锁住「二级导航未泄漏进主侧边栏」。
- 新增 `AnalysisNav` 组件测试：给定 location → 渲染 6 个标签、标对 active、目标地址带对 `tenantKey/jobId` 且保留参数。沿用仓库现有 `node:test` 风格。

## 文档一致性

- 在 `docs/design-docs/20260608-legacy-compatibility-boundary.md` §3 补一条：**允许**一个「随采集上下文出现」的分析二级导航，它与被禁止的「主侧边栏菜单」是两回事，避免将来误判其违规。
- 把「最近一次分析」快捷入口登记为将来增强（见下）。

## 范围外与残余风险

- **项目级聚合分析**：把分析从单次采集上移到项目维度，是后端数据建模改动，本次不做；作为「项目中心」模型的将来演进方向。
- **「最近一次分析」快捷入口**：可在项目列表/项目详情加「查看最近分析」按钮，深链到该项目最近一次成功采集的看板，缩短日常访问路径。本次按 YAGNI 不做，仅登记。
- **钻取深度**：当前日常访问需经「项目 → 项目详情 → 进入看板 → 选采集 → 分析」。考虑到分析数据本就按单次采集划分，先以二级导航满足「可达全部分析页」的核心诉求；若日常摩擦确实偏高，再评估上面的快捷入口。
