# Ant Design 到 shadcn/ui 迁移设计评审与修订

> 状态：执行前设计，待项目负责人批准
> 日期：2026-05-18
> 版本：v1.1
>
> 本文档修订 2026-05-17 的 Ant Design 到 shadcn/ui 迁移方案。修订依据包括
> `AGENTS.md`、`docs/ARCHITECTURE.md`、`docs/DESIGN.md`、`docs/SECURITY.md`、
> `WORKFLOW.md`、`docs/EXECUTION_GATES.md`、当前 `web/` 代码、`package.json` 和
> `npx shadcn@latest info --json` 输出。

## 1. 评审结论

结论：迁移方向有条件合适，但原 v1.0 文档中“完全可行，且需要整体替换，不是渐进式迁移”的判断过于激进。更合适的方案是：

1. 将本迁移视为一次明确的前端架构决策，而不是普通 UI 组件替换。
2. 执行时允许短期 Ant Design 与 shadcn/ui 在不同页面或不同批次共存，避免单次大爆炸式改造。
3. 不允许长期双栈；最终验收必须移除 `antd`、`@ant-design/icons`、`@antv/g2` 及 Ant Design 专用 CSS。
4. 每个阶段都必须可构建、可测试、可回滚，并在 active ExecPlan 中记录进度、决策和验证结果。

该方案目前只完成设计与执行准备。未经用户明确批准，不进入编码实现。

## 2. 为什么需要修订原方案

### 2.1 与当前项目约束冲突

`AGENTS.md` 当前核心技术栈声明是：

```text
React 18 + Ant Design + Tailwind + FastAPI + SQLAlchemy
```

迁移到 shadcn/ui 会改变前端 UI 技术栈，并新增 Radix primitives、Recharts、React Hook Form、Zod、Sonner、React Day Picker 等依赖。因此这不是“无边界”改动，必须先有产品 Spec、设计记录和 ExecPlan。

### 2.2 当前代码不是“shadcn 已初始化”状态

`npx shadcn@latest info --json` 显示：

| 项 | 当前值 |
|----|--------|
| Framework | Vite |
| React Server Components | false |
| TypeScript | false |
| Tailwind | v4 |
| Tailwind CSS file | `src/index.css` |
| import alias | `@` |
| shadcn config | null |
| installed shadcn components | none |

这意味着执行时需要先创建 shadcn 配置和 UI 原语源码，不能假设已有 `components.json` 或 `web/src/components/ui/*`。

### 2.3 当前 Ant Design 覆盖面较大

代码审计确认 Ant Design 不只出现在布局层，还覆盖应用入口、表单、表格、图表、通知、空状态、加载、主题 token 和图标。

主要受影响文件包括：

| 区域 | 文件 |
|------|------|
| 应用入口 | `web/src/App.jsx`, `web/src/main.jsx` |
| 布局导航 | `web/src/components/DashboardLayout.jsx`, `web/src/components/Sidebar.jsx` |
| 表单 | `web/src/components/CreateQueryJob.jsx`, `web/src/components/AccountManagement.jsx` |
| 表格 | `BrandShareOfVoiceTable.jsx`, `BrandMentionRate.jsx`, `ReferencesTable.jsx`, `QueryJobStatus.jsx`, `PlatformDetail.jsx`, `SourceAnalysis.jsx` |
| 图表 | `TrendAnalysis.jsx`, `SourceAnalysis.jsx`, `SentimentAnalysis.jsx`, `web/src/utils/loadG2Chart.js` |
| 通用展示 | `HomeView.jsx`, `KeywordSection.jsx`, `EmptyState.jsx`, `LoadingSpinner.jsx`, `ErrorBoundary.jsx`, `PlatformMentionRates.jsx`, `SubmissionSuccess.jsx`, `TaskName.jsx` |
| 样式主题 | `web/src/index.css`, `web/src/styles/app-shell.css`, `web/vite.config.js` |

因此原方案的整体替换会把布局、表单、表格和图表四类高风险改动绑在一起，不利于验证和回滚。

### 2.4 “shadcn 零额外依赖”表述不准确

shadcn/ui 的组件源码会进入项目，但它仍会按组件引入 Radix primitives、`class-variance-authority` 等依赖。表单、日期、Toast、图表还会引入额外库。设计文档和 ExecPlan 必须显式记录依赖增量。

## 3. 修订后的设计原则

### 3.1 短期可共存，长期必须收敛

迁移过程中允许：

- App shell 或单个页面先迁移到 shadcn/ui。
- 尚未迁移的页面继续使用 Ant Design。
- 每个阶段保持构建通过，避免长时间停留在不可运行状态。

迁移过程中不允许：

- 同一个交互控件同时混用 Ant Design 与 shadcn/ui。
- 为兼容迁移复制一套业务状态或 API 调用。
- 在完成验收后继续保留 Ant Design 主题、图标或表格依赖。

### 3.2 前后端边界不变

迁移只影响 `web/` UI 层：

- 不修改后端 API。
- 不修改租户隔离逻辑。
- 不修改 `web/src/api/` Adapter 的契约。
- 不让 UI 组件跨层访问数据库或绕过 REST API。

### 3.3 保持 JavaScript 项目形态

当前项目是 JSX + JS 配置，不引入 TypeScript。执行时若 shadcn CLI 生成 TSX，需要在落地时转为 JSX 或配置生成 JS 组件，避免把 UI 迁移扩大为语言迁移。

### 3.4 主题 token 一次打底，页面分批迁移

`web/src/index.css` 当前已经有 Tailwind v4 `@theme inline`，但基础变量仍映射到 `--ant-*`。迁移时应先建立独立的 shadcn 语义 token，再逐步删除 Ant Design token 兼容层。

Tailwind v4 下应维护：

- `--background`, `--foreground`, `--card`, `--popover`
- `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`
- `--border`, `--input`, `--ring`
- `--chart-1` 到 `--chart-5`
- `--sidebar-*`
- `@theme inline` 中的 `--color-*` 映射

不要直接照搬 Tailwind v3 的 HSL-only 示例而不验证当前 v4 输出。

## 4. 目标与非目标

### 4.1 目标

1. 将前端组件系统从 Ant Design 5.x 迁移到 shadcn/ui + Tailwind v4 semantic tokens。
2. 移除 `antd`、`@ant-design/icons`、`@antv/g2` 依赖。
3. 图表从 G2 迁移到 Recharts，并通过 shadcn Chart wrapper 保持统一主题。
4. 表单迁移到 React Hook Form + Zod，保留现有必填、格式和业务校验语义。
5. 保留现有路由、API Adapter、tenant/job 参数和时间筛选行为。
6. 迁移完成后同步 `docs/DESIGN.md`、相关 design doc、active ExecPlan 和必要索引。

### 4.2 非目标

1. 不重写后端。
2. 不改 API response shape。
3. 不引入全局状态库。
4. 不引入 TypeScript。
5. 不重新设计信息架构、菜单结构或路由矩阵。
6. 不在第一轮引入 TanStack Table；如表格功能手写成本过高，另起设计决策评审。

## 5. 技术方案

### 5.1 shadcn 初始化

执行时建议在 `web/` 下初始化：

```powershell
npx shadcn@latest init --template vite --base radix --preset radix-nova --css-variables
```

执行前必须确认：

- `components.json` 将 aliases 指向 `@/components`、`@/lib`。
- 组件输出与当前 JavaScript 项目兼容。
- `tailwindCss` 指向 `src/index.css`。
- 不覆盖未评审的现有样式。

### 5.2 组件源码位置

| 类型 | 目标位置 |
|------|----------|
| shadcn UI 原语 | `web/src/components/ui/` |
| 项目业务组件 | `web/src/components/` |
| 共享工具 | `web/src/lib/cn.js`, `web/src/utils/` |
| API 调用 | `web/src/api/` |
| 主题 CSS | `web/src/index.css`, `web/src/styles/` |

不新增第二套 `cn()`，继续使用 `web/src/lib/cn.js`。

### 5.3 组件映射

| 当前 Ant Design | 目标实现 | 风险 |
|-----------------|----------|------|
| `ConfigProvider`, `theme.useToken` | CSS variables + Tailwind semantic classes | 中 |
| `Layout`, `Sider`, `Menu` | shadcn `Sidebar` + Tailwind layout | 中 |
| `Spin` | `Spinner` / `Skeleton` | 低 |
| `Empty` | shadcn `Empty` 或项目级 empty state | 低 |
| `Card`, `Tag`, `Badge`, `Divider`, `Tooltip`, `Popover` | shadcn 对应组件 | 低到中 |
| `Segmented` | `ToggleGroup` | 中 |
| `DatePicker` | `Calendar` + `Popover` + `react-day-picker` | 高 |
| `Form` | React Hook Form + Zod + shadcn Form | 高 |
| `Table` | shadcn Table + 当前功能逐项重建 | 高 |
| `message` | `sonner` toast | 中 |
| `@ant-design/icons` | `lucide-react` | 低 |
| G2 图表 | Recharts + shadcn Chart | 高 |

### 5.4 依赖策略

计划移除：

```json
"antd": "^5.27.1",
"@ant-design/icons": "^5.6.1",
"@antv/g2": "^5.4.8"
```

计划新增：

```json
"recharts": "由 npm 解析并锁定到 package-lock.json",
"react-hook-form": "由 npm 解析并锁定到 package-lock.json",
"@hookform/resolvers": "由 npm 解析并锁定到 package-lock.json",
"zod": "由 npm 解析并锁定到 package-lock.json",
"sonner": "由 npm 解析并锁定到 package-lock.json",
"react-day-picker": "由 npm 解析并锁定到 package-lock.json",
"date-fns": "由 npm 解析并锁定到 package-lock.json",
"class-variance-authority": "由 shadcn CLI 按需加入",
"@radix-ui/*": "由 shadcn CLI 按组件按需加入"
```

版本以 `package-lock.json` 为准，执行后需要在 ExecPlan 中记录实际新增依赖。

## 6. 分阶段迁移方案

### Phase 0：批准与基线

- 用户批准后再开始编码。
- 运行基线验证：`npm --prefix web test`、`npm --prefix web run build`、`python scripts/validate_agents_docs.py --level ERROR`。
- 记录当前 bundle chunk 和 Ant Design 使用面。

### Phase 1：shadcn 基础设施

- 初始化 `components.json`。
- 安装基础 UI 原语：`button`, `card`, `badge`, `separator`, `alert`, `skeleton`, `spinner`, `tooltip`, `popover`, `dropdown-menu`。
- 修正 `web/src/index.css` token，不破坏现有页面。
- 保持 Ant Design 页面仍可运行。

### Phase 2：应用壳层和低风险组件

- 迁移 `App.jsx` loading fallback、`LoadingSpinner.jsx`、`EmptyState.jsx`、`ErrorBoundary.jsx`。
- 迁移 `DashboardLayout.jsx` 和 `Sidebar.jsx`。
- 保留现有 `useDashboardParams`、`useTimeframeManager`、`routes.js`。

### Phase 3：展示类业务组件

- 迁移 `HomeView.jsx`、`KeywordSection.jsx`、`PlatformMentionRates.jsx`、`PlatformDetail.jsx`、`SubmissionSuccess.jsx`、`TaskName.jsx`。
- 替换 `Card`、`Badge/Tag`、`Progress`、`Tooltip`、`Button`、`Typography` 等低到中风险调用。

### Phase 4：表格组件

- 迁移 `BrandShareOfVoiceTable.jsx`、`BrandMentionRate.jsx`、`ReferencesTable.jsx`、`QueryJobStatus.jsx` 和 `SourceAnalysis.jsx` 的表格部分。
- 对排序、筛选、分页、空状态、行 key、加载态逐项写验证。
- 若手写表格状态超过合理复杂度，暂停并记录 TanStack Table 评审，不直接引入。

### Phase 5：表单、日期与通知

- 迁移 `CreateQueryJob.jsx` 和 `AccountManagement.jsx`。
- 使用 React Hook Form + Zod 保留现有字段校验。
- 使用 `react-day-picker` + `date-fns` 处理日期，不改变 API 需要的日期格式。
- 将 `message.useMessage()` 改为 `sonner`。

### Phase 6：图表迁移

- 安装 shadcn Chart 和 Recharts。
- 迁移 `TrendAnalysis.jsx`、`SourceAnalysis.jsx`、`SentimentAnalysis.jsx`。
- 保留 `web/src/utils/trendChartConfig.js` 的数据预处理职责，只替换渲染层。
- 删除 `web/src/utils/loadG2Chart.js`。

### Phase 7：收敛与文档同步

- 移除 `antd/dist/reset.css`。
- 移除 `antd`、`@ant-design/icons`、`@antv/g2`。
- 更新 `web/vite.config.js` manualChunks。
- 清理 `--ant-*` token 和 Ant Design 专用 CSS。
- 更新 `docs/DESIGN.md` 为实际迁移完成状态。
- 将 active ExecPlan 移动到 completed，并记录验证。

## 7. 验收标准

迁移完成必须满足：

1. `rg "antd|@ant-design/icons|@antv/g2|ant-" web/src web/package.json web/vite.config.js` 无业务残留，允许历史文档命中。
2. `npm --prefix web test` 通过。
3. `npm --prefix web run build` 通过。
4. `python scripts/validate_agents_docs.py --level ERROR` 通过。
5. 浏览器验证首页、趋势、分平台、信源、情感、账户、新建任务、任务状态页面可渲染。
6. 时间筛选、日期选择、侧栏导航、任务创建表单、表格排序/筛选、图表 tooltip 行为可用。
7. active ExecPlan 的 Progress、Decision Log、Outcomes、验证记录完整。
8. `docs/DESIGN.md` 与实际 UI 技术栈一致。

## 8. 主要风险与缓解

| 风险 | 等级 | 缓解 |
|------|------|------|
| 表格高级功能丢失 | 高 | 表格单独成阶段，逐项列出排序、筛选、分页、加载和空状态验收 |
| 表单校验语义变化 | 高 | Zod schema 按现有 Ant Design rules 逐字段映射，提交前做负向校验 |
| 日期格式回归 | 高 | 保持 `YYYYMMDD` API 参数，UI 日期对象只在组件边界转换 |
| 图表视觉与 tooltip 不一致 | 中高 | Recharts 每个图表单独验收，保留数据预处理工具函数 |
| Tailwind v4 token 配置错误 | 中 | Phase 1 单独验证 tokens，不与页面迁移混在一起 |
| 长期双栈残留 | 中 | 最终 `rg` 门禁检查 Ant Design 残留 |
| 新依赖过多 | 中 | 依赖由阶段按需引入，ExecPlan 记录实际增量 |

## 9. 决策记录

| 决策 | 理由 | 日期 |
|------|------|------|
| 采用分阶段迁移，不采用一次性整体替换 | 当前 Ant Design 覆盖入口、表单、表格、图表和主题，整体替换风险过高 | 2026-05-18 |
| 迁移过程中允许短期双栈 | 保证每个阶段都可构建、可验证、可回滚 | 2026-05-18 |
| 最终必须移除 Ant Design 依赖 | 避免长期维护两套设计系统 | 2026-05-18 |
| 不引入 TypeScript | 当前项目为 JSX/JS，语言迁移不属于本任务目标 | 2026-05-18 |
| 暂不引入 TanStack Table | 新依赖需要单独评估；先以现有表格功能等价迁移为目标 | 2026-05-18 |
| `docs/DESIGN.md` 在实现完成后更新 | 当前只是执行前设计，不能把项目现状提前写成已迁移 | 2026-05-18 |

