# 租户分析看板上下文二级导航 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 让租户成员在按采集（`jobId`）取数的 6 个 legacy 分析页（首页/趋势/分平台/信源/情感/问答快照）之间自由导航，方式是在分析路由内加一条顶部水平标签栏，主侧边栏保持项目优先不变。

**Architecture:** `routing.js` 新增 `getAnalysisNavRoutes()`（复用既有 `isAnalysisView` 谓词）；新增极薄 `AnalysisNav`（NavLink 标签栏）+ `AnalysisLayout`（`AnalysisNav` + `Outlet`）；`App.jsx` 把 `getRoutableRoutes()` 按 `isAnalysisView` 一分为二，6 个分析路由包进 pathless 的 `<Route element={<AnalysisLayout/>}>`。纯前端、后端零改动。

**Tech Stack:** React 18 + react-router-dom v6 + Tailwind + lucide-react；`node:test` 源码契约 + 纯函数测试（无 jsdom，组件测试读 `.jsx` 文本 `assert.match`）。

**Spec:** `docs/design-docs/20260611-tenant-analysis-navigation.md`

**约定与上下文（执行者必读）：**

- 门禁命令（仓库根目录）：
  - 前端测试：`npm --prefix web test`（当前基线 **139 pass / 0 fail**）
  - 前端构建：`npm --prefix web run build`
  - 前端 lint：`npm --prefix web run lint`
  - 文档验证：`python scripts/validate_agents_docs.py --level ERROR`（输出 GBK 乱码，看「0 个错误」计数即可）
  - 后端门禁本次**无关**（无后端改动）。
- **暂存纪律**：本分支为多 agent 共享脏分支，工作区有他人未提交在途改动。每次 commit **只 `git add` 任务点名文件，严禁 `git add -A` / `git add .`**。每个任务前用 `git status --porcelain -- <file>` 复核。
  - 本计划所有目标文件在 HEAD 均为 **clean**（正常 add，无需 blob 构造）：`web/src/utils/routing.js`、`web/src/utils/__tests__/routing.test.js`、`web/src/App.jsx`、`web/src/components/HomeView.jsx`，以及 3 个新建文件。
  - ⚠️ **刻意不碰** `web/src/config/routes.js` 与 `web/src/config/__tests__/routes.test.js`：它们当前有他人在途改动（`accounts` 菜单名 `账户管理`→`加入团队`）。本计划把 `getAnalysisNavRoutes` 放在 clean 的 `routing.js`，正是为了避开并发改同一文件。
  - 文档收尾若遇 DIRTY 索引文件（如 `docs/exec-plans/completed/index.md`、`docs/design-docs/20260608-legacy-compatibility-boundary.md`），**只改工作区不提交**，随用户批次入库。
- **顺序要求（保证每次提交都能构建/通过）**：Task 1 先落 `getAnalysisNavRoutes`（被组件依赖）；Task 2 建 `AnalysisNav`/`AnalysisLayout`（依赖 Task 1）；Task 3 才在 `App.jsx` 引用 `AnalysisLayout` 并接线 + 清理 HomeView 面包屑；Task 4 文档收尾。
- **可见范围**：不加任何角色门禁——分析页对所有租户成员可见（与重构前一致），平台「客户视角」只读模式照常可见。

---

### Task 1: routing.js 新增 `getAnalysisNavRoutes()` 选择器

**Files（均 clean，正常 add）:**
- Modify: `web/src/utils/routing.js`
- Modify: `web/src/utils/__tests__/routing.test.js`

- [x] **Step 1: 写失败的测试**

`web/src/utils/__tests__/routing.test.js`：把顶部 import 中加入 `getAnalysisNavRoutes`，整块替换为：

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  buildRouteSearch,
  buildViewPath,
  getAnalysisNavRoutes,
  getViewKeyFromPath,
} from '../routing.js';
```

并在文件**末尾追加**两个用例：

```js
test('getAnalysisNavRoutes returns the six job-scoped analysis routes in order', () => {
  assert.deepEqual(
    getAnalysisNavRoutes().map((route) => route.viewKey),
    ['home', 'trend', 'platforms', 'sources', 'sentiment', 'snapshots'],
  );
});

test('getAnalysisNavRoutes entries are all legacy job-scoped routes', () => {
  const routes = getAnalysisNavRoutes();
  assert.equal(routes.length, 6);
  for (const route of routes) {
    assert.equal(route.requiresJobId, true);
    assert.equal(route.menuSection, 'legacy');
    assert.ok(route.path);
  }
});
```

- [x] **Step 2: 运行确认失败**

Run: `npm --prefix web test`
Expected: 新用例 FAIL（`getAnalysisNavRoutes` 未导出 → `undefined is not a function`）。

- [x] **Step 3: 实现选择器**

`web/src/utils/routing.js`：把顶部 import 块加入 `ROUTE_DEFINITIONS`：

```js
import {
  DEFAULT_VIEW_KEY,
  ROUTE_DEFINITIONS,
  getRouteByPathSegment,
  getRouteByTaskAction,
  getRouteByViewKey,
} from '../config/routes.js';
```

在 `isAnalysisView` 定义之后（紧接其右花括号下一行）追加：

```js
export const getAnalysisNavRoutes = () =>
  ROUTE_DEFINITIONS.filter((route) => isAnalysisView(route.viewKey));
```

- [x] **Step 4: 运行确认通过**

Run: `npm --prefix web test`
Expected: 全绿（139 + 2 = **141 pass**）。

- [x] **Step 5: Commit**（两文件 clean）

```bash
git add web/src/utils/routing.js web/src/utils/__tests__/routing.test.js
git commit -m "feat: routing 新增 getAnalysisNavRoutes 选择器

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: 新增 `AnalysisNav` 标签栏与 `AnalysisLayout` 布局

**Files（均新建，clean）:**
- Create: `web/src/components/AnalysisNav.jsx`
- Create: `web/src/components/AnalysisLayout.jsx`
- Create: `web/src/components/__tests__/analysisNav.test.js`

- [x] **Step 1: 写失败的测试**

创建 `web/src/components/__tests__/analysisNav.test.js`（源码契约风格，对照 `Sidebar.test.js`）：

```js
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';

const analysisNavSource = () =>
  readFileSync(join(import.meta.dirname, '..', 'AnalysisNav.jsx'), 'utf8');

test('analysis nav renders tabs from the shared analysis route source', () => {
  const source = analysisNavSource();
  assert.match(source, /getAnalysisNavRoutes/);
  assert.match(source, /useDashboardParams/);
  assert.match(source, /buildViewPath/);
  assert.match(source, /buildRouteSearch/);
  assert.match(source, /getViewKeyFromPath/);
  assert.match(source, /NavLink/);
});
```

- [x] **Step 2: 运行确认失败**

Run: `npm --prefix web test`
Expected: 该用例 FAIL（`readFileSync` 抛 ENOENT，`AnalysisNav.jsx` 尚不存在）。

- [x] **Step 3: 创建 `AnalysisNav.jsx`**

`web/src/components/AnalysisNav.jsx`：

```jsx
import React, { useMemo } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

import { useDashboardParams } from '@/hooks/useDashboardParams';
import {
  buildRouteSearch,
  buildViewPath,
  getAnalysisNavRoutes,
  getViewKeyFromPath,
} from '@/utils/routing';

const ANALYSIS_NAV_ITEMS = getAnalysisNavRoutes();

const AnalysisNav = () => {
  const location = useLocation();
  const { tenantKey, jobId } = useDashboardParams();
  const selectedKey = useMemo(
    () => getViewKeyFromPath(location.pathname),
    [location.pathname],
  );

  return (
    <nav
      aria-label="分析看板导航"
      className="flex items-center gap-1 overflow-x-auto border-b border-border pb-2"
    >
      {ANALYSIS_NAV_ITEMS.map((item) => {
        const pathname = buildViewPath(item.viewKey, { tenantKey, jobId });
        const search = buildRouteSearch({
          search: location.search,
          nextViewKey: item.viewKey,
        });
        const isActive = selectedKey === item.viewKey;
        return (
          <NavLink
            key={item.viewKey}
            to={`${pathname}${search}`}
            className={[
              'inline-flex shrink-0 items-center rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'text-muted-foreground hover:bg-muted hover:text-foreground',
            ].join(' ')}
          >
            {item.menuLabel}
          </NavLink>
        );
      })}
    </nav>
  );
};

export default React.memo(AnalysisNav);
```

- [x] **Step 4: 创建 `AnalysisLayout.jsx`**

`web/src/components/AnalysisLayout.jsx`：

```jsx
import React from 'react';
import { Outlet } from 'react-router-dom';

import AnalysisNav from './AnalysisNav.jsx';

const AnalysisLayout = () => (
  <div className="flex min-w-0 flex-col gap-4">
    <AnalysisNav />
    <Outlet />
  </div>
);

export default AnalysisLayout;
```

- [x] **Step 5: 运行确认通过 + 构建**

Run: `npm --prefix web test`
Expected: 全绿（141 + 1 = **142 pass**）。

Run: `npm --prefix web run build`
Expected: 构建成功（两个新组件此时尚未被 import，不进 bundle 但语法被解析；若有 JSX/import 错误会在 Task 3 接线后暴露，这里先确保无语法错误）。

- [x] **Step 6: Commit**（三文件新建 clean）

```bash
git add web/src/components/AnalysisNav.jsx web/src/components/AnalysisLayout.jsx web/src/components/__tests__/analysisNav.test.js
git commit -m "feat: 新增分析看板二级导航 AnalysisNav 与 AnalysisLayout

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: App.jsx 接线 + HomeView 面包屑清理

**Files（均 clean，正常 add）:**
- Modify: `web/src/App.jsx`
- Modify: `web/src/components/HomeView.jsx`

- [x] **Step 1: 确认无测试断言将被破坏**

Run: `npm --prefix web test`（基线应为 142 pass）。
检查没有测试依赖 HomeView 面包屑：

Run: `grep -rn "面包屑" web/src`
Expected: 仅 `web/src/components/HomeView.jsx` 命中（即将删除）；若有测试文件命中，停下评估。

- [x] **Step 2: 改 `App.jsx` —— 加导入**

(a) 在 `import DashboardLayout ...` 之后加一行：

```jsx
import DashboardLayout from './components/DashboardLayout.jsx';
import AnalysisLayout from './components/AnalysisLayout.jsx';
```

(b) 给 routing 导入加入 `isAnalysisView`：

```jsx
import { buildViewPath, isAnalysisView } from './utils/routing.js';
```

- [x] **Step 3: 改 `App.jsx` —— 路由拆分**

在 `AppRoutes` 组件体内、`defaultPath` 定义之后、`return (` 之前插入：

```jsx
  const routableRoutes = getRoutableRoutes();
  const standaloneRoutes = routableRoutes.filter((route) => !isAnalysisView(route.viewKey));
  const analysisRoutes = routableRoutes.filter((route) => isAnalysisView(route.viewKey));
```

把 DashboardLayout 那段路由块整体替换为：

```jsx
      <Route element={<ProtectedRoute><DashboardLayout /></ProtectedRoute>}>
        {standaloneRoutes.map((route) => (
          <Route
            key={route.viewKey}
            path={route.path}
            element={<RouteShell>{ROUTE_ELEMENT_FACTORIES[route.viewKey]?.()}</RouteShell>}
          />
        ))}
        <Route element={<AnalysisLayout />}>
          {analysisRoutes.map((route) => (
            <Route
              key={route.viewKey}
              path={route.path}
              element={<RouteShell>{ROUTE_ELEMENT_FACTORIES[route.viewKey]?.()}</RouteShell>}
            />
          ))}
        </Route>
      </Route>
```

- [x] **Step 4: 改 `HomeView.jsx` —— 删重复面包屑**

(a) 删除 `ChevronRight` 导入。把开头：

```jsx
import React from 'react';
import { ChevronRight } from 'lucide-react';

import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
```

改为：

```jsx
import React from 'react';

import { useDashboardRequestParams } from '@/hooks/useDashboardParams';
```

(b) 删除面包屑 `<nav>` 块，保留 h1。把：

```jsx
            <nav aria-label="面包屑导航" className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span>仪表板</span>
              <ChevronRight className="size-3" aria-hidden="true" />
              <span className="font-medium text-foreground">首页概览</span>
            </nav>
            <h1 className="text-2xl font-medium text-foreground">首页概览</h1>
```

改为：

```jsx
            <h1 className="text-2xl font-medium text-foreground">首页概览</h1>
```

- [x] **Step 5: 测试 + lint + 构建**

```bash
npm --prefix web test
npm --prefix web run lint
npm --prefix web run build
```

Expected: 测试 142 pass；lint 通过（`ChevronRight` 已无未用引用）；构建成功。

- [x] **Step 6: 手动验证（关键 —— node:test 无法渲染路由）**

Run: `npm --prefix web run dev`，浏览器走一遍：租户登录 → 监测项目 → 项目详情 → 进入看板 → 选一次采集 → 落地 `/dashboard/:tenantKey/:jobId`。确认：
- 内容区顶部出现 6 个标签（首页/趋势/分平台/信源/情感/问答快照），「首页」高亮。
- 点击各标签能切换页面，URL 段切换且 `tenantKey/jobId` 保留；时间范围等参数不丢。
- 左侧主侧边栏仍只有「监测项目 / 加入团队」（未回灌分析项）。

- [x] **Step 7: Commit**（两文件 clean）

```bash
git add web/src/App.jsx web/src/components/HomeView.jsx
git commit -m "feat: 分析路由接入二级导航布局并清理 HomeView 重复面包屑

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: 文档收尾

**Files:**
- Create: `docs/changelog/20260611-093000-tenant-analysis-navigation.md`
- Modify: `docs/design-docs/20260611-tenant-analysis-navigation.md`（状态行）
- Move: `docs/exec-plans/active/20260611-tenant-analysis-navigation.md` → `completed/`
- Modify: `docs/exec-plans/active/index.md`（恢复空态）
- Modify（DIRTY，按需仅改工作区）: `docs/exec-plans/completed/index.md`

- [x] **Step 1: 全量门禁复跑**

```bash
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
```

Expected: 前端 142 pass；构建成功；文档 0 错误。失败先排查；本功能问题修复，他人在途问题报告 BLOCKED。

- [x] **Step 2: changelog**

创建 `docs/changelog/20260611-093000-tenant-analysis-navigation.md`（若该文件名已存在则把 `093000` 递增为当前时间）：

```markdown
# 租户分析看板上下文二级导航

## 变更

- `web/src/utils/routing.js` 新增 `getAnalysisNavRoutes()`，复用既有 `isAnalysisView` 谓词，返回 6 个按采集取数的 legacy 分析路由（首页/趋势/分平台/信源/情感/问答快照）。
- 新增 `AnalysisNav`（NavLink 水平标签栏）与 `AnalysisLayout`（`AnalysisNav` + `Outlet`）。
- `App.jsx` 把 `getRoutableRoutes()` 按 `isAnalysisView` 一分为二，6 个分析路由包进 pathless 的 `<Route element={<AnalysisLayout/>}>`；其余路由不变。
- 删除 `HomeView` 与标签栏重复的「仪表板 › 首页概览」面包屑。

## 边界

- 主侧边栏保持项目优先（`getSidebarMenuRoutes()` 仍只有项目/加入团队），不回灌 legacy 分析项，符合 Legacy 兼容边界。
- 纯前端：不改路由 path、不动后端取数、不加角色门禁。

## 验证

- `npm --prefix web test`（142 pass）
- `npm --prefix web run build`
- `npm --prefix web run lint`
- 手动走查：进入看板后 6 标签可切换、参数保留、主侧栏不变。
- `python scripts/validate_agents_docs.py --level ERROR`
```

按 Step 1 真实结果核对验证小节。

- [x] **Step 3: 规格状态 + 计划归档**

1. `docs/design-docs/20260611-tenant-analysis-navigation.md` 状态行 `状态：设计中（待 ExecPlan 与实现），2026-06-11` → `状态：已实现，2026-06-11`。
2. 本计划所有 `- [x]` → `- [x]`（确认每步真的完成）。
3. `git mv docs/exec-plans/active/20260611-tenant-analysis-navigation.md docs/exec-plans/completed/20260611-tenant-analysis-navigation.md`，随后 `git add` 该 completed 路径（确保勾选后内容入暂存）。
4. `docs/exec-plans/active/index.md`（clean）→ 恢复 `# Active ExecPlans\n\n当前无进行中的 ExecPlan。`，一并提交。
5. `docs/exec-plans/completed/index.md`：先 `git status --porcelain -- docs/exec-plans/completed/index.md`。
   - 表头后插入：`| [20260611-tenant-analysis-navigation.md](20260611-tenant-analysis-navigation.md) | 租户分析看板上下文二级导航：legacy 分析页随采集上下文出现的标签栏 | 2026-06-11 |`
   - 若该文件 **DIRTY（带他人在途行）→ 只改工作区不提交**；若 clean → 可一并提交。

- [x] **Step 4: 复跑文档验证**

Run: `python scripts/validate_agents_docs.py --level ERROR` → 0 错误。

- [x] **Step 5: Commit**（按 clean/DIRTY 结论组织）

```bash
git add docs/changelog/20260611-093000-tenant-analysis-navigation.md docs/design-docs/20260611-tenant-analysis-navigation.md docs/exec-plans/active/20260611-tenant-analysis-navigation.md docs/exec-plans/completed/20260611-tenant-analysis-navigation.md docs/exec-plans/active/index.md
git commit -m "docs: 分析看板二级导航实现完成，计划归档与 changelog

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

提交后核对：commit 含 changelog（A）、design-doc 状态（M）、计划 rename（R）、active/index.md（M）；**不含** `completed/index.md`（若其 DIRTY）。

---

## 范围外 / 后续

- **Legacy 边界文档交叉引用**：spec「文档一致性」提到给 `docs/design-docs/20260608-legacy-compatibility-boundary.md` §3 补一句「允许上下文二级导航」。该文档当前有他人在途改动，为避免 blob 构造**本计划不动它**；边界解释已记录在本设计文档，交叉引用留待后续 clean 批次补。
- **「最近一次分析」快捷入口**（项目列表/详情深链到最近成功采集的看板）：按 YAGNI 不做，已在 spec 登记为将来增强。
- **项目级聚合分析**：后端数据建模改动，非本次导航范畴。

## 验收对照（Spec → Task）

| Spec 要求 | 覆盖 Task |
|---|---|
| `getAnalysisNavRoutes()` 选择器（复用 isAnalysisView，6 页按序） | Task 1 |
| `AnalysisNav` 标签栏（active 态 / 参数保留 / NavLink） | Task 2 + Task 3 Step 6 手动验证 |
| `AnalysisLayout` 极薄布局 | Task 2 |
| `App.jsx` 按 isAnalysisView 拆分、分析路由包 AnalysisLayout | Task 3 |
| 主侧边栏不变量（仍只项目/加入团队） | 既有 `routes.test.js` 锁定（不触碰）+ Task 3 Step 6 手动验证 |
| 删 HomeView 重复面包屑 | Task 3 |
| 路由测试（6 页顺序 / requiresJobId / legacy） | Task 1 |
| AnalysisNav 源码契约测试 | Task 2 |
| 纯前端、后端零改动、不加角色门禁 | 全计划（无后端/无权限文件） |
