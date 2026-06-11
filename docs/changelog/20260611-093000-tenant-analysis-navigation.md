# 租户分析看板上下文二级导航

## 变更

- `web/src/utils/routing.js` 新增 `getAnalysisNavRoutes()`，复用既有 `isAnalysisView` 谓词，返回 6 个按采集取数的 legacy 分析路由（首页/趋势/分平台/信源/情感/问答快照），按 ROUTES 声明序。
- 新增 `web/src/components/AnalysisNav.jsx`（NavLink 水平标签栏，active 态用 `getViewKeyFromPath`，链接用 `buildViewPath` + `buildRouteSearch` 保留 `tenantKey/jobId/` 查询参数）与 `web/src/components/AnalysisLayout.jsx`（`AnalysisNav` + `Outlet`）。
- `web/src/App.jsx` 把 `getRoutableRoutes()` 按 `isAnalysisView` 一分为二，6 个分析路由包进 pathless 的 `<Route element={<AnalysisLayout/>}>`；其余路由不变。
- 删除 `web/src/components/HomeView.jsx` 与标签栏重复的「仪表板 › 首页概览」面包屑及随之无用的 `ChevronRight` 导入。

## 边界

- 主侧边栏保持项目优先（`getSidebarMenuRoutes()` 仍只项目/加入团队）；`Sidebar.jsx`、`config/routes.js`、`useDashboardParams.js` 未改动，Legacy 兼容边界与既有 `routes.test.js` 不变量保持。
- 纯前端：不改路由 path、不动后端取数、不加角色门禁。

## 验证

- `npm --prefix web test` → 142 pass / 0 fail（含新增 `getAnalysisNavRoutes` 2 例 + `analysisNav` 源码契约 1 例）。
- `npm --prefix web run build` → 成功（`✓ built`）。
- `npm --prefix web run lint` → 0 error（功能文件 0 warning；既有 8 warning 均在未改文件）。
- `python scripts/validate_agents_docs.py --level ERROR` → 0 错误。
- React Router pathless 嵌套的 param 流：经既有 `DashboardLayout`（同为 pathless 父路由，已读 `useParams` 取 `tenantKey/jobId`）佐证安全。
- 交互走查（登录→监测项目→项目详情→进入看板→选采集→6 标签切换、参数保留、主侧栏不变）：**待人工验收**（无 jsdom，单测不覆盖；结构性已论证）。

## 后续

- 其余分析页（如 `AnswerSnapshotsPage`）可能自带页内面包屑，与新标签栏视觉重复，可作合并后视觉收尾（spec 已将「其余 5 页仅在视觉冲突时微调」列为范围内的可选项）。
