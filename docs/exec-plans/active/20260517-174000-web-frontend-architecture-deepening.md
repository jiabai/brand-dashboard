# Web 前端架构深化 ExecPlan

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

通过 5 个架构深化重构，将 `web/` 前端从"能跑"提升到"好维护、好测试、AI 友好"。
完成后：新增功能只需改 1-2 个文件而非 3-5 个；每个模块有清晰的 interface 和 implementation 边界；
测试可以独立运行而不需要渲染完整组件树。

## Progress

- [x] 候选 #4：拆分 `src/utils/index.js` God Object（2026-05-17）
- [x] 候选 #1：创建 `src/api/` Adapter 层（2026-05-17）
- [ ] 候选 #2：拆分 `DashboardLayout` 职责（2026-05-17）
- [ ] 候选 #3：消除 Prop Drilling（2026-05-17）
- [ ] 候选 #5：统一路由配置（2026-05-17）
- [x] 运行文档结构验证（2026-05-17）

## Surprises & Discoveries

- 项目已有完整的产品规范、设计决策和 ExecPlan 历史文档体系，说明之前团队重视文档治理
- 已有 5 个单元测试文件在 `src/utils/__tests__/`，但测试覆盖率集中在工具函数，组件层无测试
- `src/utils/routing.js` 没有任何测试覆盖路由构建的边界情况（如空 tenantKey、特殊字符）

## Decision Log

| Decision | Rationale | Date | Author |
|----------|-----------|------|--------|
| 按 #4 → #1 → #2 → #3 → #5 顺序执行 | #4 是基础，拆分后 #1 的 API 层可以引用更清晰的 utils 模块；#2 和 #3 互相依赖，先做 #2 再做 #3；#5 最独立放最后 | 2026-05-17 | AI Agent |
| 不引入 TypeScript | 项目核心信念明确"无聊技术优先"，现有代码库全部是 JSX，引入 TS 会改变边界 | 2026-05-17 | AI Agent |
| 使用 JSDoc 类型注解 | 在不引入 TS 的前提下提供 IDE 自动补全和类型检查能力 | 2026-05-17 | AI Agent |
| 现有组件暂不迁移到 API Adapter 层 | Batch 1-2 只创建基础架构，组件迁移放在 Batch 3-5 中随重构一并执行，避免单次变更范围过大 | 2026-05-17 | AI Agent |

## Outcomes & Retrospective

### Batch 1+2 完成记录（2026-05-17）

**Passed:**

- `npm --prefix web run build` — 构建成功（10.73s，0 errors，0 warnings）
- `node --test src/utils/__tests__/*.test.js` — 8/8 测试通过（88.6ms）
- `python scripts/validate_agents_docs.py --level ERROR` — 0 errors，0 warnings
- `python scripts/validate_agents_docs.py --level WARN` — 0 errors，0 warnings

**Not run:**

- 手动浏览器验证 UI 渲染 — 未变更任何组件代码，风险低
- `npm --prefix web test` — 项目无 vitest 配置，使用 node --test 替代

**Residual risk:**

- 现有 9 个业务组件仍通过 `src/utils/index.js` re-export 引用工具函数，未迁移到新路径
- API Adapter 层已创建但未被任何组件引用，需要 Batch 3-5 中逐步迁移

**回顾:**

- utils 拆分顺利，re-export 模式保证了零破坏性变更
- API Adapter 层覆盖了项目中全部 17 个 API 端点
- 命名参数解构 + `buildQueryString` 封装使得 API 调用签名更清晰

## Context and Orientation

### 当前状态

`web/` 是一个 React 18 + Ant Design + Tailwind + Vite 的前端项目，包含：
- 9 个业务组件（HomeView、TrendAnalysis、SourceAnalysis 等）
- 1 个布局组件（DashboardLayout）
- 1 个路由工具模块（routing.js）
- 1 个 God Object 工具模块（utils/index.js，252 行）
- 5 个单元测试文件

### 关键文件

| 文件 | 职责 |
|------|------|
| `src/App.jsx` | 路由定义、全局主题配置 |
| `src/components/DashboardLayout.jsx` | 布局 + 时间范围管理 + Outlet context |
| `src/utils/routing.js` | 路由路径构建和 search 参数管理 |
| `src/utils/index.js` | 工具函数 re-export 入口（已拆分为 6 个子模块） |
| `src/api/index.js` | API Adapter re-export 入口（覆盖全部 17 个端点） |
| `src/hooks/useDashboardParams.js` | 从 URL 参数提取业务上下文 |
| `src/config.js` | 全局配置和默认值 |

### 相关规范

- `docs/DESIGN.md` — 前端设计规范
- `docs/ARCHITECTURE.md` — 系统架构
- `docs/EXECUTION_GATES.md` — 门禁规范
- `AGENTS.md` — 核心信念：前后端分离、多租户隔离、共享工具优于手写 helper

## Plan of Work

按依赖关系排序执行：

1. **Batch 1**: 拆分 `src/utils/index.js` → 6 个子模块 ✅
2. **Batch 2**: 创建 `src/api/` 目录，按业务域组织 API 调用 ✅
3. **Batch 3**: 提取 `useTimeframeManager` hook，简化 `DashboardLayout`
4. **Batch 4**: 消除 Prop Drilling，组件直接调用 hook 获取参数
5. **Batch 5**: 统一路由配置为单一真相源

## Concrete Steps

### Batch 1: 拆分 utils/index.js ✅

**工作目录**: `d:\Github\brand-dashboard\web`

1. 创建以下文件：

```
src/utils/format.js        — formatPercentage, formatDateParam, formatDateDisplay, parseDateInput
src/utils/number.js        — toPercent, toFraction, clampPercent, roundTwoDecimals
src/utils/url.js           — getQueryParam, updateQueryParams, buildQueryString
src/utils/http.js          — fetchJson, postJson
src/utils/config.js        — DEFAULT_BRAND_DATA, DEFAULT_PLATFORM_DATA, DEFAULT_REFERENCES_DATA, PLATFORM_COLORS, getPlatformColor
src/utils/validate.js      — validateBrandData, validatePlatformData, validateReferencesData, buildQueryJobStatusRowKey, getRangeByTimeframe, normalizeListValue
```

2. 更新 `src/utils/index.js` 为 re-export 入口

3. 现有 import 无需修改（re-export 保证了向后兼容）

4. 验证：`npm --prefix web run build` 成功，8/8 测试通过

### Batch 2: 创建 src/api/ Adapter 层 ✅

**工作目录**: `d:\Github\brand-dashboard\web`

1. 创建以下文件：

```
src/api/client.js          — 基础请求函数 fetchJson / postJson
src/api/dashboard.js       — 10 个 /api/v1/dashboard/* 端点
src/api/queryJobs.js       — 2 个 /api/v1/query-jobs/* 端点
src/api/auth.js            — 5 个认证/用户端点
src/api/index.js           — re-export 所有 API 模块
```

2. 覆盖项目中全部 17 个 API 端点

3. 验证：`npm --prefix web run build` 成功

### Batch 3: 拆分 DashboardLayout 职责

**工作目录**: `d:\Github\brand-dashboard\web`

1. 创建 `src/hooks/useTimeframeManager.js`：

```js
// 封装所有时间范围管理逻辑：
// - timeframe 解析和校验
// - startDate/endDate 的 fallback 逻辑
// - 可用日期查询
// - 日期参数同步
```

2. 简化 `DashboardLayout.jsx`：

```js
const DashboardLayout = () => {
  const dashboardParams = useDashboardParams();
  const timeframeManager = useTimeframeManager(dashboardParams);
  // ... 只负责布局和 context 传递
};
```

3. 验证：`npm --prefix web run dev` 启动后时间筛选功能正常工作

### Batch 4: 消除 Prop Drilling

**工作目录**: `d:\Github\brand-dashboard\web`

1. 更新 `src/hooks/useDashboardParams.js`，增加 JSDoc 类型注解：

```js
/**
 * @returns {{
 *   tenantKey: string,
 *   jobId: string,
 *   brand: string,
 *   timeframe: string,
 *   startDateParam: string,
 *   endDateParam: string,
 *   selectedPlatform: string,
 *   executorId: string,
 *   includeDeleted: string,
 *   searchParams: URLSearchParams,
 *   updateParams: function
 * }}
 */
```

2. 更新业务组件，直接从 hook 获取参数而非通过 props 传递

3. 简化 `HomeView.jsx` 等中间层组件

4. 验证：`npm --prefix web run build` 应成功

### Batch 5: 统一路由配置

**工作目录**: `d:\Github\brand-dashboard\web`

1. 创建 `src/config/routes.js`：

```js
export const ROUTES = {
  home: {
    path: '/dashboard/:tenantKey/:jobId',
    viewKey: 'home',
    menuLabel: '首页',
    menuIcon: 'HomeOutlined',
    requiresJobId: true,
  },
  trend: {
    path: '/trend/:tenantKey/:jobId',
    viewKey: 'trend',
    menuLabel: '趋势分析',
    menuIcon: 'LineChartOutlined',
    requiresJobId: true,
  },
  // ... 其他路由
};
```

2. 更新 `src/utils/routing.js` 使用统一配置

3. 更新 `src/App.jsx` 从配置生成路由

4. 更新 `src/components/Sidebar.jsx` 从配置生成菜单

5. 验证：`npm --prefix web run build` 应成功，所有路由正常工作

## Validation and Acceptance

### 启动方式

```bash
npm --prefix web run dev
```

### 可观察行为

- 浏览器打开 `http://localhost:3000` 应自动跳转到 dashboard 页面
- 侧边栏菜单点击应正确切换页面
- 时间筛选功能应正常工作
- 所有分析页面应正常加载数据

### 测试命令

```bash
# 构建验证
npm --prefix web run build

# 单元测试
node --test web/src/utils/__tests__/*.test.js

# 文档结构验证
python scripts/validate_agents_docs.py --level ERROR
python scripts/validate_agents_docs.py --level WARN
```

### 门禁检查

| Gate | 状态 | 命令 / 说明 |
|------|------|------------|
| 受影响代码已 inspect | ✅ | Batch 1-2 只新增文件 + 修改 index.js re-export，无现有逻辑变更 |
| 最小有效测试通过 | ✅ | `node --test` 8/8 通过 |
| 文档结构验证 ERROR | ✅ | `validate_agents_docs.py --level ERROR` 0 errors |
| 文档结构验证 WARN | ✅ | `validate_agents_docs.py --level WARN` 0 warnings |
| ExecPlan Progress 已更新 | ✅ | 本文件 Progress 章节已反映 Batch 1-2 完成 |
| durable docs 已同步 | ✅ | 无架构/安全/契约变更，仅内部模块组织变化 |
| 前端构建 | ✅ | `npm --prefix web run build` 0 errors |
| 手动浏览器验证 | ⏭️ | 跳过 — 未变更任何组件代码，向后兼容已通过构建验证 |
| 更广范围回归测试 | ⏭️ | 跳过 — 现有测试覆盖了工具函数间接依赖路径 |