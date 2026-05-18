# 仪表板 UI 视觉优化 ExecPlan

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

将 shadcn/ui 迁移后的 Brand Dashboard 从“可运行但粗糙”的临时深色界面，优化为暖色浅底、信息密度更高、适合品牌分析运营场景的专业仪表板。实现过程中保持现有路由、API Adapter、租户参数、时间筛选和数据契约不变，只调整视觉系统、布局密度和组件表现。

## Progress

- [x] 用户确认 UI 需要优化，并要求先完成设计文档（2026-05-18）
- [x] 已读取 `AGENTS.md`、`docs/ARCHITECTURE.md`、`docs/DESIGN.md`、`DESIGN-TOKENS.md`（2026-05-18）
- [x] 产品 Spec 已创建：`docs/product-specs/20260518-145556-optimize-dashboard-ui-visual-design.md`（2026-05-18）
- [x] 设计记录已创建：`docs/design-docs/20260518-145556-dashboard-ui-visual-optimization.md`（2026-05-18）
- [x] ExecPlan 已创建，等待用户批准后编码（2026-05-18）
- [x] 用户确认开始执行 UI 优化编码（2026-05-18）
- [x] Phase 0：基线验证与当前截图确认（2026-05-18）
- [x] Phase 1：全局主题 token 切换为 warm canvas/coral（2026-05-18）
- [x] Phase 2：App shell、顶部栏和侧栏优化（2026-05-18）
- [x] Phase 3：Button/Card/Table/EmptyState 基础组件视觉统一（2026-05-18）
- [x] Phase 4：首页布局和数据组件密度优化（2026-05-18）
- [x] Phase 5：最终验证、浏览器截图和文档收尾（2026-05-18）

## Surprises & Discoveries

- `DESIGN-TOKENS.md` 面向 Claude/Anthropic 营销与产品展示界面，色彩和层级可参考，但不能照搬 hero、pricing、CTA band 和大字号 editorial 结构。
- 当前项目 `docs/DESIGN.md` 已同步为 shadcn/ui + Tailwind v4，但缺少具体视觉方向、token 映射和仪表板密度规则。
- 用户反馈的“丑”主要不是组件库问题，而是主题 token、布局密度、空状态策略和 App shell 视觉层级未完成。
- `App.jsx` 仍强制给 `document.documentElement` 添加 `dark` class，导致浅色 token 初次实现后实际页面仍显示为深色模式；已移除并新增测试防回归。
- 本地后端未提供有效业务数据时，首页会展示 500/空状态；本轮按视觉优化处理容器、密度和错误态，不改变 API 行为。
- 复查 `web/.env` 后确认默认 tenant/job/brand 均指向真实数据集。此前使用 `/dashboard/default/latest` 和默认 `30days` 做验证是错误上下文；真实数据最新可用日期为 `2026-02-12`。
- shadcn/Radix Popover 日历在顶部栏中曾被定位到视口外，导致用户无法点击日期；已改为原生 `input type="date"`，避免弹层定位风险。
- 首页无显式 `timeframe` 时仍按当前日期计算 `30days`，会请求 `20260419-20260518` 并得到空数据；已改为根据 `available-dates` 自动回填最新可用日。
- 兼容此前误给出的 `/dashboard/default/latest` 链接：前端会将 `default` / `latest` 路由占位值映射为 `web/.env` 中的默认 tenant/job。
- 宽屏桌面适配不能简单让所有内容等比铺满：趋势图需要限定高度，表格需要更高行距和更宽关键列，否则会分别出现图表过高和表格拥挤的问题。

## Decision Log

| Decision | Rationale | Date/Author |
|----------|-----------|-------------|
| 采用暖色浅底运营仪表板风格 | 与 `DESIGN-TOKENS.md` 的 warm canvas/coral/ink 一致，同时比深紫主题更适合长时间业务使用 | 2026-05-18 / agent |
| 不照搬 Claude 营销页结构 | 本项目是数据仪表板，需要高密度扫描，不需要 hero、footer、pricing 或大面积 CTA | 2026-05-18 / agent |
| 先文档、获批后编码 | 用户明确要求先完成设计文档，待确认后再执行 UI 优化 | 2026-05-18 / agent |
| 不引入新 UI/图表库 | 当前问题是设计系统和 CSS/布局问题，不需要扩大依赖面 | 2026-05-18 / agent |
| 移除默认强制 dark mode | 默认视觉方向是浅色 warm canvas，暗色模式只能作为显式扩展，不能启动时强制启用 | 2026-05-18 / agent |
| 默认首页使用后端最新可用日期 | 项目数据可能是历史批次；无显式 timeframe 时按当前日期计算 30days 会错过真实数据 | 2026-05-18 / agent |
| 顶部日期控件改为原生 date input | Radix Popover 在 sticky header 中出现视口外定位，原生日期输入更稳定且保持 URL 参数契约 | 2026-05-18 / agent |
| 兼容 `default/latest` 占位路由 | 之前调试时给过错误链接，兼容后可避免用户继续访问该链接时请求错误 tenant/job | 2026-05-18 / agent |
| 宽屏图表限高、表格增密度留白 | 图表和表格的信息形态不同；图表横向铺开但高度应封顶，表格需要通过行高、列宽和单元格 padding 保持可读 | 2026-05-18 / agent |

## Context and Orientation

### 当前状态

| 项 | 状态 |
|----|------|
| 前端 | React 18 + Vite + shadcn/ui + Tailwind v4 |
| UI 问题 | 深紫临时主题、卡片稀疏、空状态过重、顶部栏和侧栏层级粗糙 |
| 参考风格 | `DESIGN-TOKENS.md` 的 warm canvas、coral primary、warm ink、dark surface |
| 约束 | 不改 API、不改路由语义、不引入新库、不新增业务页面 |

### 关键文件

| 文件 | 职责 |
|------|------|
| `web/src/index.css` | 全局 shadcn/Tailwind semantic tokens 和基础排版 |
| `web/src/components/ui/button.jsx` | Button variants 的颜色、状态和前景色 |
| `web/src/components/ui/card.jsx` | Card 基础间距、边框和圆角 |
| `web/src/components/DashboardLayout.jsx` | App shell、顶部栏、时间筛选和内容区域密度 |
| `web/src/components/Sidebar.jsx` | 品牌区、导航项、active 状态和响应式侧栏 |
| `web/src/components/EmptyState.jsx` | 空状态高度、图标、文案和行动按钮 |
| `web/src/components/DataTable.jsx` | 表格密度、表头、分页和空表格状态 |
| `web/src/components/HomeView.jsx` | 首页首屏内容组织 |
| `web/src/components/*Analysis.jsx` | 图表和分析卡片视觉一致性 |

## Plan of Work

### Phase 0: 基线和截图确认

1. 运行基线验证：

```powershell
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
```

2. 启动前端并截取当前首页桌面/移动端，用作视觉对比。
3. 记录当前 console error 与后端 500/空数据情况，区分数据问题和视觉问题。

### Phase 1: 全局主题 Token

1. 修改 `web/src/index.css` 的 semantic tokens。
2. 建立 warm canvas、warm ink、coral primary、hairline border、muted surface、chart tokens。
3. 检查 Button、Card、Input、Table 等 shadcn 原语在浅色主题下的默认可读性。
4. 增加主题入口测试，确保 Tailwind v4 与 shadcn CSS 入口仍保留。

### Phase 2: App Shell 优化

1. 优化 `DashboardLayout.jsx` 顶部栏：任务标题、更新时间、数据日期、时间筛选组成清晰控制组。
2. 优化内容区域最大宽度、padding、section gap。
3. 优化移动端折叠表现，避免筛选按钮和标题挤压。
4. 优化 `Sidebar.jsx`：品牌区、导航 active、分组和 icon 对齐。

### Phase 3: 基础组件视觉统一

1. 优化 Button variants，确保 primary/outline/ghost/destructive 均有明确前景色。
2. 优化 Card 基础风格，减少厚重边框和过高 padding。
3. 优化 Badge、Progress、Skeleton、LoadingSpinner 的暖色主题表现。
4. 优化 EmptyState：降低默认高度，错误态保留重试按钮。

### Phase 4: 页面和数据组件密度优化

1. 优化 `HomeView.jsx` 首屏：品牌排名、平台提及率、引用详情的布局节奏。
2. 优化表格密度和空数据状态，保持排序、筛选、分页行为。
3. 优化图表卡片、legend、tooltip、空数据和颜色。
4. 检查账户、任务创建、任务状态页面的表单和状态反馈一致性。

### Phase 5: 视觉验证和文档收尾

1. 运行最终验证：

```powershell
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
python scripts/validate_agents_docs.py --level WARN
```

2. 浏览器验证桌面和移动端截图。
3. 检查新增硬编码色值：

```powershell
rg -n "#[0-9a-fA-F]{3,8}" web/src
```

4. 更新 `docs/DESIGN.md` 和本 ExecPlan 的结果记录。
5. 完成后将本 ExecPlan 移动到 `docs/exec-plans/completed/` 并更新索引。

## Validation and Acceptance

### 自动验证

```powershell
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
python scripts/validate_agents_docs.py --level WARN
```

### 浏览器验证

1. `/dashboard/:tenantKey/:jobId` 桌面首页渲染正常。
2. 移动端宽度下侧栏、顶部栏、筛选控件无重叠。
3. 首页、趋势、分平台、信源、情感、账户、新建任务、任务状态页面可访问。
4. 空数据和后端错误状态不再占据异常大面积。
5. 浏览器 console 无新增前端渲染错误。

## Outcomes & Retrospective

### Passed

- `npm --prefix web test`：22 个测试全部通过。
- `npm --prefix web run build`：构建通过。
- `python scripts\validate_agents_docs.py --level ERROR`：0 个错误，0 个警告。
- 浏览器截图：已生成 `ui-optimized-desktop-final.png` 和 `ui-optimized-mobile-final.png`，确认默认页面为 warm canvas 浅色主题，侧栏恢复稳定显示，顶部栏和内容区无明显重叠。
- `rg -n "#[0-9a-fA-F]{3,8}" web\src`：新增视觉色值集中在 `web/src/index.css` semantic tokens；平台和信源图表颜色已改为 CSS token 引用。剩余命中为 token 定义与测试 fixture。
- 用户反馈后的数据链路验证：从 `/` 进入会跳转到 `tn_6e1f78442bae/job_20260209_123550_e9ba00f6?timeframe=specific_day&start_date=20260212&end_date=20260212`，首页显示 `deepseek`、`udesk.cn` 和引用详情表。
- 用户反馈后的兼容验证：访问 `/dashboard/default/latest` 也会使用 `.env` 的真实默认 tenant/job，并显示 `deepseek`、`udesk.cn` 和引用详情表。
- 用户反馈后的回归验证：`npm --prefix web test` 更新为 26 个测试全部通过；`npm --prefix web run build` 通过。
- 宽屏适配验证：2560px 桌面下主内容区铺满侧栏后的可用宽度；趋势图容器高度控制在 420/460px 档位；分平台表格首行高度约 51px，分页与横向溢出正常。

### Notes

- 本轮没有修改后端 API、租户参数、路由语义或数据请求契约。
- 默认首页依赖 `available-dates` 作为历史任务的数据锚点；用户显式选择昨天、过去 7 天、过去 30 天或指定日期后，不再被自动回填覆盖。
