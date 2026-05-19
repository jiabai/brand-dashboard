# Web UI shadcn 迁移 ExecPlan

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must be kept up to date as work proceeds.

## Purpose / Big Picture

将 `web/` 前端从 Ant Design 5.x + G2 迁移到 shadcn/ui + Tailwind v4 semantic tokens + React/SVG/CSS 轻量图表。迁移完成后，UI 原语源码进入项目，主题由 CSS variables 和 Tailwind `@theme inline` 驱动，Ant Design、Ant Design Icons 和 G2 依赖被移除；现有路由、API Adapter、租户隔离和用户可见业务行为保持不变。

## Progress

- [x] 设计方案审查与修订完成，结论为“有条件适合，分阶段执行”（2026-05-18）
- [x] 产品 Spec 已创建：`docs/product-specs/20260518-003119-migrate-web-ui-to-shadcn.md`（2026-05-18）
- [x] ExecPlan 已创建并等待用户批准（2026-05-18）
- [x] 用户批准开始编码（2026-05-18）
- [x] Phase 0：基线验证与依赖现状记录（2026-05-18）
- [x] Phase 1：shadcn 基础设施与主题 token（2026-05-18）
- [x] Phase 2：应用壳层和低风险组件迁移（2026-05-18）
- [x] Phase 3：展示类业务组件迁移（2026-05-18）
- [x] Phase 4：表格组件迁移（2026-05-18）
- [x] Phase 5：表单、日期与通知迁移（2026-05-18）
- [x] Phase 6：图表迁移（2026-05-18）
- [x] Phase 7：依赖清理、文档同步和最终验证（2026-05-18）

## Surprises & Discoveries

- `npx shadcn@latest info --json` 显示当前项目尚未初始化 shadcn：`config: null`，`components: []`。
- `web/src/index.css` 已有 Tailwind v4 `@theme inline`，但语义 token 仍主要映射到 `--ant-*`，这会让主题迁移成为单独风险点。
- `docs/exec-plans/active/index.md` 曾引用已移动到 completed 的 `20260517-174000-web-frontend-architecture-deepening.md`，本次准备文档时会顺手修正 active index。
- `web/src/components/ui/` 当前没有 shadcn UI 原语文件，不能假设已有 Button/Card 等组件。
- shadcn CLI 当前没有 `radix-nova` preset；实际命令使用 `--base radix --preset nova`，生成的 `components.json` style 为 `radix-nova`。
- shadcn CLI 生成了 `web/src/lib/utils.js`，但项目既有共享入口是 `web/src/lib/cn.js`；已将组件导入统一改回 `@/lib/cn` 并删除重复 helper。
- 移除 Ant Design 后暴露出 `dayjs` 曾是隐式传递依赖；已将 `dayjs` 加为前端显式依赖。
- 用户实际启动页面后发现桌面侧栏消失、按钮文字发黑。根因是 `web/src/index.css` 仍使用 Tailwind 旧入口 `@tailwind base/components/utilities`，Tailwind v4 没有生成 `md:`/`sm:` 响应式工具类；同时移除 Ant Design reset 后，原生 button 文字色不再被继承。已改为 `@import "tailwindcss";` 并补充 shadcn Button variant 的显式前景色。

## Decision Log

| Decision | Rationale | Date/Author |
|----------|-----------|-------------|
| 采用分阶段迁移，不采用一次性整体替换 | Ant Design 覆盖布局、表单、表格、图表和主题，整体替换难以验证和回滚 | 2026-05-18 / agent |
| 允许短期双栈，但最终移除 Ant Design | 阶段性交付需要可运行状态；长期双栈会增加维护成本 | 2026-05-18 / agent |
| 不引入 TypeScript | 当前项目是 JSX/JS，语言迁移会扩大任务范围 | 2026-05-18 / agent |
| 暂不引入 TanStack Table | 新依赖需单独评审；先按现有表格功能等价迁移 | 2026-05-18 / agent |
| 先创建 Spec + ExecPlan，等待用户批准后编码 | 任务改变前端技术栈，属于非平凡任务 | 2026-05-18 / agent |
| 不引入 Recharts/sonner/react-hook-form | 当前图表和表单可用 shadcn 原语、原生 SVG/CSS 与受控表单完成，减少新运行时依赖和迁移面 | 2026-05-18 / agent |
| 保留 `dayjs` 并写入直接依赖 | 项目已有时间工具和日期参数逻辑使用 dayjs，移除会扩大范围 | 2026-05-18 / agent |

## Context and Orientation

### 当前项目状态

| 项 | 状态 |
|----|------|
| 前端框架 | React 18 + Vite |
| UI 现状 | Ant Design 5.x + Tailwind v4 |
| 图表 | `@antv/g2` 动态加载 |
| 图标 | `@ant-design/icons` + `lucide-react` |
| shadcn | 未初始化 |
| 路由 | `react-router-dom` v6，配置在 `web/src/config/routes.js` |
| API | `web/src/api/` Adapter，前端不直接访问数据库 |
| 共享工具 | `web/src/lib/cn.js`, `web/src/utils/` |

### 关键文件

| 文件 | 迁移职责 |
|------|----------|
| `web/package.json`, `web/package-lock.json` | 依赖新增与移除 |
| `web/src/index.css` | Tailwind v4 token 与 Ant Design token 清理 |
| `web/src/main.jsx` | 移除 `antd/dist/reset.css` |
| `web/src/App.jsx` | 移除 `ConfigProvider`、`Spin` 和 Ant Design theme |
| `web/src/components/DashboardLayout.jsx` | 布局、时间筛选、DatePicker/Segmented 迁移 |
| `web/src/components/Sidebar.jsx` | `Layout.Sider`、`Menu`、Ant icons 迁移 |
| `web/src/components/CreateQueryJob.jsx` | Ant Design Form/DatePicker/message 迁移 |
| `web/src/components/AccountManagement.jsx` | 多表单迁移 |
| `web/src/components/*Table*.jsx`, `QueryJobStatus.jsx`, `ReferencesTable.jsx` | 表格功能迁移 |
| `web/src/components/TrendAnalysis.jsx`, `SourceAnalysis.jsx`, `SentimentAnalysis.jsx` | 图表迁移 |
| `web/src/utils/loadG2Chart.js` | 迁移完成后删除 |
| `web/vite.config.js` | 移除 Ant Design/G2 manualChunks |
| `docs/DESIGN.md` | 实现完成后同步真实 UI 技术栈 |

## Plan of Work

### Phase 0: 基线验证与准备

1. 读取 active ExecPlan，确认用户已批准。
2. 运行当前基线：

```powershell
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
```

3. 记录 Ant Design/G2 当前引用：

```powershell
rg -n "antd|@ant-design/icons|@antv/g2|theme\\.useToken|ConfigProvider|message\\.useMessage" web/src web/package.json web/vite.config.js
```

4. 若基线失败，先记录失败并判断是否属于本迁移前置修复；不直接掩盖既有失败。

### Phase 1: shadcn 基础设施与主题 token

工作目录：`web/`

1. 初始化 shadcn：

```powershell
npx shadcn@latest init --template vite --base radix --preset radix-nova --css-variables
```

2. 检查 `components.json`、`web/src/index.css`、alias 配置和生成文件扩展名。
3. 安装基础组件：

```powershell
npx shadcn@latest add button card badge separator alert skeleton spinner tooltip popover dropdown-menu
```

4. 调整 `web/src/index.css`，建立独立 semantic tokens，保留临时 Ant Design 兼容变量直到 Phase 7。
5. 验证：

```powershell
npm --prefix web run build
```

### Phase 2: 应用壳层和低风险组件迁移

1. 修改 `web/src/App.jsx`：移除 `ConfigProvider`、`theme.darkAlgorithm` 和 Ant Design `Spin` fallback。
2. 修改 `web/src/components/LoadingSpinner.jsx`：替换为 shadcn `Spinner`。
3. 修改 `web/src/components/EmptyState.jsx`：替换 Ant Design `Empty`/`Button`。
4. 修改 `web/src/components/ErrorBoundary.jsx`：替换 Ant Design `Result`/`Typography`/`Button`。
5. 安装并迁移 Sidebar：

```powershell
npx shadcn@latest add sidebar
```

6. 修改 `DashboardLayout.jsx` 和 `Sidebar.jsx`，保留 `useDashboardParams`、`useTimeframeManager` 和 `routes.js`。
7. 验证构建和浏览器入口。

### Phase 3: 展示类业务组件迁移

1. 迁移低风险展示组件：`HomeView.jsx`、`KeywordSection.jsx`、`PlatformMentionRates.jsx`、`SubmissionSuccess.jsx`、`TaskName.jsx`。
2. 替换 `Card`、`Badge/Tag`、`Progress`、`Tooltip`、`Button`、`Typography`。
3. 遵守 shadcn 组合规则：`CardHeader/CardTitle/CardDescription/CardContent` 完整组合，按钮图标使用项目图标库，条件 class 使用 `cn()`。
4. 每批修改后运行：

```powershell
npm --prefix web run build
```

### Phase 4: 表格组件迁移

1. 安装表格相关组件：

```powershell
npx shadcn@latest add table select checkbox scroll-area
```

2. 逐个迁移：
   - `BrandShareOfVoiceTable.jsx`
   - `BrandMentionRate.jsx`
   - `ReferencesTable.jsx`
   - `QueryJobStatus.jsx`
   - `PlatformDetail.jsx`
   - `SourceAnalysis.jsx` 的表格部分
3. 对每个表格保留行 key、排序、筛选、分页、loading、empty 和列格式化。
4. 若发现手写表格状态复杂度过高，暂停并新增 design decision，不在本阶段直接引入 TanStack Table。

### Phase 5: 表单、日期与通知迁移

1. 使用 shadcn `Input`、`Textarea`、`Select`、`Tabs`、`Calendar`、`Popover` 与原生 `date` / `datetime-local` 输入迁移表单。
2. 数字输入使用 shadcn `Input` + number parsing，不新增第三方组件。
3. 迁移 `CreateQueryJob.jsx`，确保提交 payload 与迁移前一致。
4. 迁移 `AccountManagement.jsx`，覆盖租户创建、管理员激活、邀请码验证、员工注册、登录等表单。
5. 将 Ant Design `message.useMessage()` 改为页面内 `Alert`/结果面板反馈。
6. 验证表单必填、日期格式和错误提示。

### Phase 6: 图表迁移

1. 不引入新的图表库，使用 React/SVG/CSS 原生轻量图表完成当前视图。
2. 迁移 `TrendAnalysis.jsx`：SVG 折线图、点位、坐标网格和空状态。
3. 迁移 `SourceAnalysis.jsx`：CSS 横向堆叠比例条。
4. 迁移 `SentimentAnalysis.jsx`：CSS conic-gradient 环形图和文字云。
5. 保留 `web/src/utils/trendChartConfig.js` 数据预处理职责。
6. 删除 `web/src/utils/loadG2Chart.js`。
7. 验证颜色、空数据和 loading。

### Phase 7: 清理、文档同步和最终验证

1. 从 `web/src/main.jsx` 移除 `antd/dist/reset.css`。
2. 从 `web/package.json` 移除 `antd`、`@ant-design/icons`、`@antv/g2`。
3. 更新 `web/vite.config.js`，移除 Ant Design/G2 manualChunks。
4. 清理 `web/src/index.css` 和 `web/src/styles/` 中 Ant Design 专用变量和选择器。
5. 更新 `docs/DESIGN.md`，将 UI 规范同步为 shadcn/ui + Tailwind v4。
6. 更新本 ExecPlan 的 Outcomes & Retrospective。
7. 将本文件移动到 `docs/exec-plans/completed/`，更新 active/completed index。

## Validation and Acceptance

### 阶段验证

每个 Phase 至少运行：

```powershell
npm --prefix web run build
```

表单、路由、时间工具或数据转换有变更时运行：

```powershell
npm --prefix web test
```

### 最终验证

```powershell
npm --prefix web test
npm --prefix web run build
python scripts/validate_agents_docs.py --level ERROR
python scripts/validate_agents_docs.py --level WARN
rg -n "antd|@ant-design/icons|@antv/g2|theme\\.useToken|ConfigProvider|message\\.useMessage" web/src web/package.json web/vite.config.js
```

最终 `rg` 命令预期没有业务源码命中 Ant Design/G2 残留。

### 浏览器验证

启动前端：

```powershell
npm --prefix web run dev
```

验证：

1. `/dashboard/:tenantKey/:jobId` 首页可渲染。
2. 侧栏可切换趋势、分平台、信源、情感、账户、新建任务、任务状态。
3. 时间筛选和 specific day 日期选择更新 URL 参数。
4. 表格排序、筛选、分页和空状态可用。
5. 新建任务表单负向校验和成功提交反馈可用。
6. 图表 tooltip、legend、颜色和空数据状态可用。
7. 浏览器 console 无新增 error。

## Outcomes & Retrospective

### Passed

- `npm --prefix web test`：18 个测试全部通过。
- `npm --prefix web run build`：构建通过，产物不再包含 Ant Design/G2 vendor chunk。
- `rg -n "antd|@ant-design/icons|@antv/g2|theme\\.useToken|ConfigProvider|message\\.useMessage|loadG2Chart" web/src web/package.json web/vite.config.js`：无命中。
- 本地 Vite dev server + Edge CDP smoke：`/dashboard`、`/trend`、`/platforms`、`/sources`、`/sentiment`、`/accounts`、`/tasks/new`、`/tasks/status` 均可渲染有效 DOM，并成功生成页面截图。
- 用户反馈后的回归修复：补充 `tailwind v4 entrypoint is used so responsive shadcn classes are generated` 测试，重新验证 `npm --prefix web test` 19 个测试全部通过；桌面截图确认侧栏恢复为 256px，主内容从侧栏右侧开始渲染，按钮文字恢复为前景色。

### Notes

- 图表迁移实际采用原生 SVG/CSS，而非引入 Recharts；原因是当前图表复杂度可控，减少依赖更符合本项目“无聊技术优先”的约束。
- 表单迁移实际采用受控表单和页面内 Alert 反馈，而非引入 react-hook-form/zod/sonner；后续若表单规则继续扩展，可单独评审是否引入 schema/form 库。
- `dayjs` 已从隐式依赖改为显式依赖。
