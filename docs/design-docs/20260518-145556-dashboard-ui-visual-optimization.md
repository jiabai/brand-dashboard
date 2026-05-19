# 仪表板 UI 视觉优化设计记录

## 背景

shadcn/ui 迁移解决了组件源码可控和 Ant Design/G2 依赖移除问题，但迁移后的界面仍存在明显视觉债：

- 全局深紫背景与品牌分析仪表板的运营场景不匹配，长时间使用压迫感强。
- 页面信息密度低，空状态和卡片高度过大，首屏像失败态而非工作台。
- 顶部栏、侧栏、卡片、表格和图表之间缺少统一的视觉节奏。
- 当前主题更像技术迁移后的默认壳层，不像有明确设计系统的产品界面。

`DESIGN-TOKENS.md` 的 cream canvas、warm ink、coral primary、dark product surface、低阴影体系适合成为参考，但该文件面向 Claude/Anthropic 营销与产品展示界面。本项目应吸收其色彩和层级原则，转换为更克制、更高密度的运营仪表板语言。

## 决策

1. 采用“暖色浅底运营仪表板”作为默认视觉方向：浅奶油 canvas、暖黑正文、低饱和 coral 主强调、teal/amber 作为数据辅助色。
2. 不继续使用深紫作为全局页面底色。深色 surface 只用于侧栏、局部高对比面板或需要承载复杂数据的局部模块。
3. 将 `DESIGN-TOKENS.md` 中的营销页 display typography 收敛为仪表板层级：页面标题、区域标题、卡片标题、表格正文、caption，不使用超大 hero 字号。
4. 仪表板卡片采用 1px warm hairline border、低阴影或无阴影、8px 默认圆角，避免浮夸卡片堆叠。
5. 空状态从“整张大卡片中央展示”改为“局部轻量状态”：降低高度、减少图标装饰、保留行动按钮。
6. 图表颜色从单一紫色体系改为 warm ink + coral + teal + amber + semantic 状态色，强调可读性和数据区分。

## 主题 Token 映射

| 语义 | 参考来源 | Brand Dashboard 目标 |
|------|----------|----------------------|
| `background` | `canvas #faf9f5` | 页面主背景，浅奶油色 |
| `foreground` | `ink #141413` | 标题和高优先级文本 |
| `muted` | `surface-soft #f5f0e8` | 次级区域、筛选条、轻量状态背景 |
| `muted-foreground` | `muted #6c6a64` | 次级说明、表格辅助文本 |
| `card` | `canvas / surface-card` | 数据卡片和表格容器 |
| `border` | `hairline #e6dfd8` | 卡片、输入、表格分隔线 |
| `primary` | `coral #cc785c` | 主按钮、active 标记、关键强调 |
| `primary-hover` | `coral active #a9583e` | 主按钮 hover/active |
| `sidebar` | `surface-dark #181715` 或暖浅底变体 | 桌面侧栏按最终实现选择，但必须与内容区形成清晰边界 |
| `success` | `#5db872` | 正向状态、增长 |
| `warning` | `#d4a017` | 注意状态 |
| `destructive` | `#c64545` | 错误状态 |
| `chart-1` | coral | 品牌主序列 |
| `chart-2` | teal | 平台或来源辅助序列 |
| `chart-3` | amber | 排名或警示类辅助序列 |

## 版式与密度

### App Shell

- 桌面侧栏宽度保持稳定，不因 active 文案或图标造成跳动。
- 顶部栏高度控制在 64px 左右，左侧展示任务上下文，右侧展示更新时间和时间筛选。
- 顶部筛选按钮使用 segmented/tabs 样式，不使用过小的幽灵按钮堆叠。
- 移动端使用抽屉或折叠导航，内容区不被侧栏覆盖。

### 内容区域

- 页面内边距桌面建议 24px，移动端 16px。
- 首页优先展示“品牌排名 + 平台提及率 + 引用详情”三类核心信息。
- 卡片标题区高度收敛，标题、描述和动作一行或两行内完成。
- 数据卡片不使用大面积深色背景，除非该模块需要突出高对比数据摘要。

### 表格

- 表头使用 muted 背景和 12-13px caption 级文字。
- 行高保持 44-52px，适合扫描。
- 排序、筛选、分页控件与表格边界对齐。
- 空表格只占据表格内容区的最小有效高度。

### 图表

- 图表容器保持浅底，网格线使用 hairline-soft。
- 坐标、legend、tooltip 使用 warm ink/muted，避免纯白/纯黑跳变。
- 图表颜色最多使用 3-5 个稳定 token，不按页面随意生成。

## 组件规则

| 组件 | 规则 |
|------|------|
| Button | primary 使用 coral；outline/ghost 必须显式设置前景色；icon button 优先用 Lucide 图标 |
| Card | 默认 8px radius、warm hairline border、无重阴影；不要卡片套卡片 |
| Badge | 使用浅 warm surface 或 semantic 色，避免大面积高饱和填充 |
| EmptyState | 默认低高度、少文案、单一行动；错误态保留重试按钮 |
| LoadingSpinner | 尺寸与所在容器匹配，不用整屏大 loading 覆盖局部内容 |
| Sidebar | active 状态应清楚但克制，可使用 coral 左边线或浅底高亮 |
| Header | 更新时间、数据更新至、时间筛选应成为同一控制组，不分散在页面边缘 |

## 禁止项

1. 不使用当前深紫/紫蓝作为主视觉系统。
2. 不使用营销页 hero、大字号价值主张或装饰性背景。
3. 不使用离散渐变球、bokeh、无业务意义插画作为仪表板装饰。
4. 不在业务组件中直接散落新增 hex 色值。
5. 不通过增加新 UI 库解决视觉问题。
6. 不牺牲现有业务行为来换取视觉重排。

## 执行影响

主要影响 `web/src/index.css`、`web/src/components/ui/*`、`DashboardLayout.jsx`、`Sidebar.jsx`、首页和分析页展示组件。后端 API、数据库、认证、多租户逻辑不受影响。

## 验证

- 自动验证：`npm --prefix web test`、`npm --prefix web run build`、`python scripts/validate_agents_docs.py --level ERROR`。
- 视觉验证：启动 Vite 后检查桌面和移动端首页截图，确认侧栏、顶部栏、内容卡片、空状态和表格无重叠。
- 设计验证：新增或修改的颜色应优先来自 semantic token；空状态高度、卡片密度和首屏可读性应明显优于迁移后的临时主题。
