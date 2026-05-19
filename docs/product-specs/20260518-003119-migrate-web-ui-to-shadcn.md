# Web UI 组件系统迁移到 shadcn/ui

## 背景

当前 `web/` 前端使用 React 18 + Ant Design 5.x + Tailwind v4。Ant Design 覆盖应用入口、布局、表单、表格、图表周边、通知、加载和空状态；图表引擎使用 `@antv/g2` 动态加载；图标同时使用 `@ant-design/icons` 与 `lucide-react`。

项目已经有 Tailwind v4 和 `web/src/lib/cn.js`，但 shadcn/ui 尚未初始化：没有 `components.json`，`web/src/components/ui/` 中没有 shadcn 组件源码，`web/src/index.css` 的语义 token 仍主要映射到 `--ant-*` 变量。

## 用户价值

迁移完成后，前端 UI 组件源码进入项目，样式系统收敛到 Tailwind semantic tokens，减少 Ant Design CSS-in-JS 与 Tailwind 双轨维护成本。仪表板页面在保持现有功能的前提下，获得更可控的组件组合、主题 token 和图表样式。

## 目标

1. 将前端 UI 组件系统迁移到 shadcn/ui + Tailwind v4 semantic tokens。
2. 移除 Ant Design、Ant Design Icons 和 G2 运行时依赖。
3. 保留现有路由、页面结构、API Adapter、租户参数、任务参数和时间筛选语义。
4. 迁移表单、表格、图表时保持用户可见行为等价。
5. 迁移完成后同步 `docs/DESIGN.md` 和相关执行文档。

## 非目标

1. 不修改后端 API、数据库、多租户隔离和认证逻辑。
2. 不改变 `web/src/api/` 的请求契约。
3. 不引入 TypeScript。
4. 不引入全局状态管理库。
5. 不重新设计导航信息架构。
6. 不在本轮直接引入 TanStack Table，除非执行中单独完成设计评审并获得批准。

## 使用场景

1. 用户打开仪表板首页，侧栏、顶部时间筛选、KPI 卡片、平台指标和引用表格正常展示。
2. 用户在侧栏切换趋势、分平台、信源、情感等页面，路由与页面状态保持现有行为。
3. 用户切换 `yesterday`、`7days`、`30days`、`specific_day`，URL 查询参数和数据刷新逻辑不变。
4. 用户创建查询任务，表单字段、日期选择、校验错误和提交结果与现有 Ant Design 表单语义一致。
5. 用户查看表格，排序、筛选、分页、加载、空状态、行 key 行为保持等价。
6. 用户查看趋势、信源、情感图表，tooltip、颜色、空数据和加载状态可用。

## 功能要求

| 编号 | 要求 |
|------|------|
| FR-1 | 初始化 shadcn/ui 配置，并将 UI 原语源码放入 `web/src/components/ui/` |
| FR-2 | 建立独立于 `--ant-*` 的 Tailwind v4 semantic tokens |
| FR-3 | 迁移应用壳层、侧栏、加载、空状态、错误边界和基础展示组件 |
| FR-4 | 迁移表格组件并保持排序、筛选、分页、加载、空状态行为 |
| FR-5 | 迁移表单组件并保持字段校验和提交 payload |
| FR-6 | 将通知从 `message` 迁移到页面内 Alert/状态反馈 |
| FR-7 | 将日期选择从 Ant Design DatePicker 迁移到 shadcn Calendar 组合 |
| FR-8 | 将 G2 图表迁移到 React/SVG/CSS 原生轻量图表 |
| FR-9 | 移除 Ant Design、Ant Design Icons 和 G2 依赖与源码引用 |
| FR-10 | 更新 durable docs 和 ExecPlan 验证记录 |

## 非功能要求

| 类别 | 要求 |
|------|------|
| 可维护性 | 不新增第二套 API client、routing helper 或 `cn()` helper |
| 可回滚性 | 每个阶段保持构建通过，阶段边界清晰 |
| 兼容性 | 保持 React 18、Vite、Tailwind v4、JSX 项目形态 |
| 安全 | 不改 API 认证、租户隔离和敏感配置读取 |
| 性能 | 移除 Ant Design 后不引入明显更大的 UI/charts bundle |
| 可访问性 | Dialog、Sheet、Popover、Tooltip、Form control 使用 shadcn/Radix 推荐组合和标题/aria 属性 |

## 约束

1. 必须先获得用户批准再编码。
2. 必须遵守 `docs/EXECUTION_GATES.md`。
3. 必须将 active ExecPlan 的 Progress、Decision Log 和验证记录保持最新。
4. 必须优先使用 `web/src/lib/cn.js`、`web/src/utils/`、`web/src/api/`。
5. 新依赖必须记录到 ExecPlan，最终提交前锁定到 `web/package-lock.json`。

## 验收标准

1. `npm --prefix web test` 通过。
2. `npm --prefix web run build` 通过。
3. `python scripts/validate_agents_docs.py --level ERROR` 通过。
4. `rg "antd|@ant-design/icons|@antv/g2" web/src web/package.json web/vite.config.js` 无业务残留。
5. 浏览器验证首页、趋势、分平台、信源、情感、账户、新建任务、任务状态页面可访问。
6. 表单提交 payload 与迁移前保持一致。
7. 时间筛选和日期格式保持 `YYYYMMDD` API 参数语义。
8. `docs/DESIGN.md` 反映迁移完成后的实际技术栈。
