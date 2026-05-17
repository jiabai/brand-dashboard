# 前端 URL 路由改造

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

用户访问 dashboard 时，URL 从 `/?view=home&tenant_key=...&job_id=...` 变为 `/dashboard/tn_xxx/job_xxx?brand=QuickCEP`，路径表达"哪个页面/资源"，查询参数表达"怎么过滤"。分析类页面携带 `tenantKey + jobId`，租户级页面只携带 `tenantKey`，侧边栏点击导航到不同路径，浏览器前进/后退正常工作，旧书签自动重定向。

## Progress

- [x] Phase 1: 基础设施 — 安装 react-router-dom，main.jsx 包裹 BrowserRouter（2026-05-17）
- [x] Phase 2: 布局提取 — 创建 useDashboardParams hook、DashboardLayout、HomeView（2026-05-17）
- [x] Phase 3: 路由替换 — 重写 App.jsx 为 Routes 定义，修改 Sidebar 使用 useNavigate（2026-05-17）
- [x] Phase 4: 组件清理 — TrendAnalysis、QueryJobStatus、CreateQueryJob 去掉直接读 URL（2026-05-17）
- [x] Phase 5: 兼容与验证 — 创建 LegacyRedirect，构建验证，浏览器手动验证（2026-05-17）

## Surprises & Discoveries

- 2026-05-17：代码检查发现 `task-load`、`task-status`、`accounts` 是租户级页面；原计划把所有页面都强制建成 `/:tenantKey/:jobId` 路径会让 `job_id` 语义过载。已修正为分析页使用 `jobId` 路径，任务状态页用 `job_id` 查询参数做可选筛选。
- 2026-05-17：浏览器验证发现从趋势页进入任务状态会携带 `trend_platform/trend_keyword`，已通过路由查询清理规则修正为离开趋势页时删除趋势专属筛选。
- 2026-05-17：浏览器日志中出现 AntD `Card bodyStyle` deprecation warning，定位到 `QueryJobStatus` 并改为 `styles.body`。

## Decision Log

| Decision | Rationale | Date/Author |
|----------|-----------|-------------|
| 使用 react-router-dom v6 | 项目已有 React 18，v6 是标准搭配；嵌套路由 + Outlet 天然支持 Layout 模式 | 2026-05-17 / agent |
| tenantKey/jobId 放入路径参数 | 它们是资源定位符（必填、层级关系），符合 RESTful 路径设计 | 2026-05-17 / agent |
| 保留 start_date/end_date，去掉 date | API 层使用 start_date/end_date，前端应与之对齐；date 是历史遗留 | 2026-05-17 / agent |
| 日期格式保持 YYYYMMDD | 与 API 的 `date` 参数格式一致，不引入格式转换层 | 2026-05-17 / agent |
| 不引入状态管理库 | 项目当前无全局状态库，URL 作为单一数据源已足够；引入新库增加复杂度 | 2026-05-17 / agent |
| 旧 URL 兼容已移除 | 旧式 `?view=...&tenant_key=...&job_id=...` 查询参数 URL 不再支持；`/` 和 `*` 路由直接重定向到默认 dashboard | 2026-05-17 / agent |
| 租户级页面不强制携带 jobId | 新建任务、任务状态、账户管理不是具体分析任务资源；任务状态的 job_id 是筛选条件，应保留在 query 中 | 2026-05-17 / agent |
| 趋势筛选仅保留在趋势页 | `trend_platform`、`trend_keyword` 只影响趋势分析，跨页携带会污染任务状态等租户级 URL | 2026-05-17 / agent |

## Outcomes & Retrospective

完成了前端路由改造：`App.jsx` 现在只负责主题和 Routes，`DashboardLayout` 承接原有壳层与时间筛选，`useDashboardParams` 统一读取路径/查询参数。旧 URL 兼容（`LegacyRedirect`）已移除，`/` 和 `*` 路由直接重定向到默认 dashboard。旧 `date` 参数不再写入新 URL；任务状态页保留 `job_id` 作为筛选查询参数；趋势专属筛选离开趋势页时会被清理。

验证记录：

- `npm --prefix web test`：10 tests passed
- `npm --prefix web run build`：Vite build passed
- `python scripts/validate_agents_docs.py --level ERROR`：0 errors, 0 warnings
- 浏览器验证（`http://127.0.0.1:3001`）：旧 dashboard URL 重定向、侧边栏趋势导航、任务状态租户级路径、浏览器前进/后退、时间筛选 URL 同步、旧任务状态 URL 兼容、平台下钻返回清除 `platform` 均通过

## Context and Orientation

### 当前状态

- 前端无路由库，所有页面通过 `/?view=home&...` 查询参数驱动
- `App.jsx`（461 行）承担路由分发、状态管理、URL 同步、日期逻辑
- 部分组件（TrendAnalysis、QueryJobStatus、CreateQueryJob）跨层直接读 URL
- 参数冗余：`start_date` 和 `date` 同时存在

### 关键文件

| 文件 | 重要性 |
|------|--------|
| `web/src/App.jsx` | 主入口，需拆分为 Routes + DashboardLayout |
| `web/src/components/Sidebar.jsx` | 导航组件，需改用 useNavigate |
| `web/src/components/TrendAnalysis.jsx` | 跨层读 URL，需清理 |
| `web/src/components/QueryJobStatus.jsx` | 跨层读 URL，需清理 |
| `web/src/components/CreateQueryJob.jsx` | 跨层读 URL，需清理 |
| `web/src/utils/index.js` | getQueryParam/updateQueryParams 定义处 |
| `web/package.json` | 需新增 react-router-dom 依赖 |
| `web/vite.config.js` | 需确认 SPA fallback 配置 |

### 术语

- **路径参数**：URL 路径中的动态段，如 `/dashboard/:tenantKey/:jobId`
- **查询参数**：URL `?` 后的键值对，如 `?brand=QuickCEP&timeframe=30days`
- **Outlet**：React Router v6 的嵌套路由渲染占位符

### 路由矩阵

| View key | 新路径 | 参数来源 |
|----------|--------|----------|
| `home` | `/dashboard/:tenantKey/:jobId` | `tenant_key`、`job_id` 进入路径 |
| `trend` | `/trend/:tenantKey/:jobId` | `tenant_key`、`job_id` 进入路径 |
| `platforms` | `/platforms/:tenantKey/:jobId` | `tenant_key`、`job_id` 进入路径 |
| `sources` | `/sources/:tenantKey/:jobId` | `tenant_key`、`job_id` 进入路径 |
| `sentiment` | `/sentiment/:tenantKey/:jobId` | `tenant_key`、`job_id` 进入路径 |
| `accounts` | `/accounts/:tenantKey` | `tenant_key` 进入路径 |
| `task-load` | `/tasks/:tenantKey/new` | `tenant_key` 进入路径，`executor_id` 保留 query |
| `task-status` | `/tasks/:tenantKey/status` | `tenant_key` 进入路径，`job_id`、`include_deleted` 保留 query |

## Plan of Work

### Phase 1: 基础设施

安装 `react-router-dom`，在 `main.jsx` 中包裹 `BrowserRouter`。改动最小，风险最低，为后续所有工作提供基础。

### Phase 2: 布局提取

从 `App.jsx` 中提取 Header + Sidebar + 时间筛选器到 `DashboardLayout.jsx`，创建 `useDashboardParams.js` hook 统一参数读取，创建 `HomeView.jsx` 薄包装组件。这是改动量最大的阶段，但逻辑从现有代码提取，不引入新行为。

### Phase 3: 路由替换

重写 `App.jsx` 为纯 Routes 定义，修改 `Sidebar.jsx` 使用 `useNavigate`。此时新旧路由并存，旧 `renderContent()` 逻辑仍可工作。

### Phase 4: 组件清理

修改 `TrendAnalysis`、`QueryJobStatus`、`CreateQueryJob`，去掉 `getQueryParam` 直接调用，改用 `useSearchParams` 或 props。

### Phase 5: 兼容与验证

创建 `LegacyRedirect.jsx` 处理旧 URL，运行构建验证，浏览器手动测试全部路由。

## Concrete Steps

### Phase 1: 基础设施

工作目录：`web/`

```powershell
npm --prefix web install react-router-dom
```

预期输出：`package.json` 中新增 `"react-router-dom": "^6.x"`，`node_modules/react-router-dom` 目录存在。

修改 `web/src/main.jsx`：
- 新增 `import { BrowserRouter } from 'react-router-dom'`
- 用 `<BrowserRouter>` 包裹 `<App />`

验证：
```powershell
npm --prefix web run build
```
预期：构建通过，无报错。

### Phase 2: 布局提取

工作目录：`web/src/`

创建 `web/src/hooks/useDashboardParams.js`：
- 从 `useParams()` 读取 `tenantKey`、`jobId`
- 从 `useSearchParams()` 读取 `timeframe`、`brand`、`start_date`、`end_date`、`platform`
- 提供 `updateParams` 增量合并方法

创建 `web/src/components/DashboardLayout.jsx`：
- 从 `App.jsx` 提取 Header（TaskName + 时间筛选 Segmented + DatePicker）
- 从 `App.jsx` 提取 Sidebar
- 使用 `<Outlet />` 渲染子路由
- 保留 `availableDates` 加载逻辑
- 保留 `handleFilterChange` 逻辑

创建 `web/src/components/HomeView.jsx`：
- 薄包装组件，组合 BrandMentionRate + PlatformMentionRates + ReferencesTable
- 通过 `useDashboardParams()` 获取参数并传递给子组件

验证：
```powershell
npm --prefix web run build
```
预期：构建通过。此时新组件尚未被引用，不影响现有功能。

### Phase 3: 路由替换

工作目录：`web/src/`

重写 `web/src/App.jsx`：
- 删除 `Dashboard()` 函数（路由 + 状态 + 布局逻辑）
- 删除 `renderContent()` if/else 链
- 删除 `useEffect` URL 同步逻辑
- 保留 `App()` 的 ConfigProvider 包裹
- 新增 `<Routes>` 定义

修改 `web/src/components/Sidebar.jsx`：
- 新增 `import { useNavigate, useLocation } from 'react-router-dom'`
- `handleMenuClick` 改用 `navigate()`
- `selectedKey` 从 `location.pathname` 推导
- 移除 `onMenuClick` 和 `selectedKey` props
- 使用路由矩阵生成目标路径；分析页保留当前 `jobId`，租户级页面只保留 `tenantKey`

验证：
```powershell
npm --prefix web run build
```
预期：构建通过。

### Phase 4: 组件清理

工作目录：`web/src/components/`

修改 `TrendAnalysis.jsx`：
- 去掉 `getQueryParam('tenant_key', ...)` 和 `getQueryParam('job_id', ...)` 调用
- 直接使用 props 中的 `tenantKey`、`jobId`
- `trend_platform`、`trend_keyword` 改用 `useSearchParams`

修改 `QueryJobStatus.jsx`：
- 去掉 `getQueryParam` 调用
- 改用 `useSearchParams` 读取可选筛选 `job_id`、`include_deleted`，`tenantKey` 从路由 props/context 进入

修改 `CreateQueryJob.jsx`：
- 去掉 `getQueryParam` 调用
- 改用 `useSearchParams` 读取 `executor_id`、`tenant_key`

验证：
```powershell
npm --prefix web run build
```
预期：构建通过。

### Phase 5: 兼容与验证

工作目录：`web/src/components/`

创建 `LegacyRedirect.jsx`：
- 读取当前 URL 的 `view` 查询参数
- 映射 `view` 值到新路径
- 将 `tenant_key` → `tenantKey`；分析页将 `job_id` → `jobId` 路径参数，租户级页面按路由矩阵处理
- 其余查询参数保留（去掉 `view`、`date`）
- 使用 `<Navigate to={newUrl} replace />` 重定向

在 `App.jsx` 的 `<Routes>` 末尾添加：
```jsx
<Route path="*" element={<LegacyRedirect />} />
```

验证：
```powershell
npm --prefix web run build
```
预期：构建通过。

浏览器手动验证：
1. 访问 `http://localhost:3000/?view=home&tenant_key=tn_xxx&job_id=job_xxx` → 自动跳转到 `/dashboard/tn_xxx/job_xxx`
2. 点击侧边栏各菜单项 → URL 正确变化，页面正确渲染
3. 切换时间筛选 → URL 查询参数同步
4. 浏览器前进/后退 → 行为正确

## Validation and Acceptance

### 构建验证

```powershell
npm --prefix web run build
```

预期：无 error，无 warning（与改造前一致）。

### 运行时验证

启动前端开发服务器后：

1. **旧 URL 兼容**：浏览器访问 `/?view=home&tenant_key=tn_6e1f78442bae&job_id=job_20260209_123550_e9ba00f6&brand=QuickCEP&timeframe=specific_day&start_date=20260212&end_date=20260212&date=20260212`，自动跳转到 `/dashboard/tn_6e1f78442bae/job_20260209_123550_e9ba00f6?brand=QuickCEP&timeframe=specific_day&start_date=20260212&end_date=20260212`
2. **侧边栏导航**：依次点击首页、趋势分析、分平台分析、信源分析、情感分析、账户管理、新建查询任务、查询任务状态，URL 正确变化
3. **时间筛选**：切换 yesterday / 7days / 30days / specific_day，URL 查询参数同步，数据正确刷新
4. **平台下钻**：在首页点击平台卡片，URL 出现 `?platform=xxx`，点击返回后清除
5. **浏览器导航**：前进/后退按钮行为正确，页面状态与 URL 一致
6. **直接访问新 URL**：在新标签页直接访问 `/trend/tn_xxx/job_xxx?timeframe=30days`，页面正确渲染
7. **租户级页面**：访问 `/?view=task-status&tenant_key=tn_xxx&job_id=job_xxx&include_deleted=true`，自动跳转到 `/tasks/tn_xxx/status?job_id=job_xxx&include_deleted=true`
