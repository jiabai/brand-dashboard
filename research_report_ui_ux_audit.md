# Brand Dashboard UI/UX 审查报告

## 摘要

基于 ui-ux-pro-max 设计审查框架，对 web/ 目录下所有页面进行了系统性审查。发现 17 个问题，按严重程度分为 CRITICAL（3 个）、HIGH（6 个）、MEDIUM（5 个）、LOW（3 个）。最突出的问题集中在无障碍访问（图表缺乏键盘可访问性、对比度不足）、数据可视化可用性（全零数据 Y 轴失真、图表无替代文本）、以及布局一致性（Card 内边距层级混乱、页面结构风格不统一）。

---

## 1. 无障碍访问 (Accessibility) — CRITICAL

### 1.1 SVG 图表无键盘可访问性 [CRITICAL]

`TrendSvgChart`（TrendAnalysis.jsx:90-163）使用原生 SVG 渲染折线图，数据点 `<circle>` 没有设置 `tabIndex`、`role` 或键盘事件处理器。屏幕阅读器用户无法通过 Tab 键遍历数据点，也无法获取单个数据点的值。

**违反规则**: `keyboard-nav`（完整键盘支持）、`focusable-elements`（交互图表元素必须键盘可导航）、`tooltip-keyboard`（tooltip 内容必须键盘可达）

**建议**: 为每个数据点 `<circle>` 添加 `tabIndex={0}`、`role="graphics-symbol"` 及 `aria-label`，并考虑在 focus 时显示 tooltip 信息。

### 1.2 色彩对比度不达标 [CRITICAL]

以下场景中前景色与背景色的对比度低于 WCAG AA 标准的 4.5:1：

| 位置 | 前景色 | 背景色 | 对比度 | 目标 |
|------|--------|--------|--------|------|
| `MetricCircle` 百分比文字（11px）| `text-foreground` on `bg-card` + `ring-1 ring-border` | `#141413` on `#fffdf8` | OK（12.8:1）| 4.5:1 |
| `MetricCircle` 标签文字（12px）| `text-muted-foreground` | `bg-transparent` | `#6c6a64` on `#faf9f5` ≈ 4.0:1 | 4.5:1 |
| `WordCloud` 彩色文字（14-40px）| 多种 chart 色 | `bg-muted/25` | 部分 < 3:1 | 3:1 (大字) |
| `SourceAnalysisChart` 图例文字 | `text-muted-foreground` | `hover:bg-muted` | `#6c6a64` on `#f5f0e8` ≈ 3.4:1 | 4.5:1 |

**违反规则**: `color-contrast`（正常文字最低 4.5:1）、`color-accessible-pairs`

**建议**: 将 `--muted-foreground` 从 `#6c6a64` 调深至至少 `#5a5852`（可达 5.2:1），或在关键信息处使用 `text-foreground` 替代 `text-muted-foreground`。

### 1.3 图表仅靠颜色区分数据 [CRITICAL]

`SourceAnalysisChart` 的堆叠条形图（SourceAnalysis.jsx:120-136）和 `SentimentDonut`（SentimentAnalysis.jsx:31-65）仅通过颜色区分不同类别，没有图案、纹理或形状辅助区分。红绿色盲用户无法区分正面（chart-2 绿色）和负面（destructive 红色）。

**违反规则**: `color-not-only`（不能仅靠颜色传达信息）、`pattern-texture`（用图案/纹理辅助区分）、`color-not-decorative-only`

**建议**: 在堆叠条形图中为每个段落添加不同的斜线纹理（SVG pattern）；在环形图旁的图例中添加不同形状图标（如圆形/方形/三角形）。

---

## 2. 数据可视化 (Charts & Data) — HIGH

### 2.1 趋势图全零数据时 Y 轴失真 [HIGH]

`TrendSvgChart`（TrendAnalysis.jsx:67-70）当所有数据为 0 时，`maxValue = Math.max(1, ...values)` 强制设为 1（即 1.00%），Y 轴刻度为 0%/0.25%/0.50%/0.75%/1.00%，数据线平贴底部。这导致 99% 的图表空间完全浪费，且用户可能误认为数据范围很大。

**违反规则**: `axis-readability`（刻度必须合理且不误导）、`empty-data-state`

**建议**: 当所有值为 0 时，显示空状态提示"当前周期内无品牌提及数据"而非绘制无意义的 0 值折线图；或使用 `maxValue = Math.max(maxValue * 1.2, 0.01)` 让 Y 轴范围更紧凑。

### 2.2 图表缺少屏幕阅读器文本摘要 [HIGH]

`TrendSvgChart` 的 SVG 有 `aria-label="品牌提及率趋势图"`（通用标签），但没有提供数据摘要。`SourceAnalysisChart` 的堆叠条完全没有 `aria-label` 或 `role="img"`。`SentimentDonut` 使用纯 CSS `conic-gradient` 实现，完全不可被屏幕阅读器读取。

**违反规则**: `screen-reader-summary`（提供文本摘要描述图表关键洞察）、`data-table`（为可访问性提供表格替代）

**建议**: 在每个图表卡片底部添加 `sr-only` 的文本摘要，如"2024年2月12日，品牌提及率为 0.00%，共 1 个数据点"；为 `SentimentDonut` 添加 `aria-label` 描述"正面 60%，负面 20%，中性 20%"。

### 2.3 图表无交互式 Tooltip [HIGH]

`TrendSvgChart` 的数据点仅使用 SVG 原生 `<title>` 元素提供 tooltip，在桌面端需要鼠标悬停触发，移动端完全不可用。`SourceAnalysisChart` 堆叠条使用 `title` 属性，同理。没有点击/tap 查看详情的能力。

**违反规则**: `tooltip-on-interact`（悬停或点击提供精确数值）、`touch-target-chart`（交互图表元素 ≥44pt 点击区域）、`tooltip-keyboard`

**建议**: 替换 `<title>` 为可交互的 Tooltip 组件（如 Radix Tooltip），支持键盘 focus 触发和触摸 tap 触发；扩大数据点点击区域至 44×44px。

### 2.4 环形图固定尺寸不响应式 [HIGH]

`SentimentDonut`（SentimentAnalysis.jsx:44）使用硬编码的 `size-64`（256px）外圆 + `size-36`（144px）内圆，在小屏设备上可能溢出或显得过大，大屏上又显得过小。

**违反规则**: `responsive-chart`（图表必须在小屏上重排或简化）

**建议**: 使用响应式尺寸如 `size-48 sm:size-56 lg:size-64`，或将环形图替换为水平堆叠条形图（移动端更好的替代方案）。

### 2.5 信源分析堆叠条缺少 Y 轴标注 [HIGH]

`SourceAnalysisChart` 的水平堆叠条（SourceAnalysis.jsx:120-136）只有图例，没有 Y 轴标签说明"百分比"单位，也没有 hover 显示精确值。用户无法知道 100% 代表什么。

**违反规则**: `axis-labels`（标注轴单位和可读刻度）、`direct-labeling`（小数据集直接在图表上标注值）

**建议**: 在堆叠条上方添加刻度线（0% / 25% / 50% / 75% / 100%），或在每个段落内直接标注百分比。

### 2.6 词云组件缺乏交互性和语义 [HIGH]

`WordCloud`（SentimentAnalysis.jsx:67-89）仅渲染静态 `<span>` 文字，没有交互能力（点击/悬停查看详情），没有语义标注（哪些是正面词、哪些是负面词），且颜色分配方式 `colors[index % colors.length]` 导致红色（`text-destructive`）随机出现在索引 2, 7, 12... 的词语上，可能误导用户以为这些是负面词。

**违反规则**: `color-not-only`、`trend-emphasis`（强调数据趋势而非装饰）

**建议**: 为词云添加分类标注（正面/负面/中性），使用对应颜色（正面绿、负面红、中性灰）；添加悬停效果显示具体数值。

---

## 3. 布局与响应式 (Layout & Responsive) — HIGH

### 3.1 Card 内边距层级混乱 [HIGH]

不同页面的 Card 内边距策略不一致：

| 页面 | Card > CardContent | 额外覆盖 | 实际效果 |
|------|---------------------|----------|----------|
| BrandMentionRate | CardContent（默认 px-5）| 无 | 统一 |
| TrendAnalysis 统计 Card | CardContent（默认 px-5）| 无 | 统一 |
| TrendAnalysis 趋势 Card | CardContent（默认 px-5）| ~~p-4~~（已修复）| 已修复 |
| SourceAnalysis Chart Card | CardContent（默认 px-5）| 无 | 统一 |
| SourceAnalysis 媒介表 Card | CardContent | `p-4` | 不一致 |
| SentimentAnalysis Card | CardContent（默认 px-5）| 无 | 统一 |

`SourceAnalysis.jsx:300` 的 `CardContent className="p-4"` 与其他页面不一致。

**违反规则**: `consistency`（全站风格统一）、`spacing-scale`（8dp 递增间距系统）

**建议**: 统一所有 CardContent 使用默认的 `px-5`（20px），移除 SourceAnalysis 中的 `p-4` 覆盖。

### 3.2 Header 控件在窄屏下溢出 [HIGH]

`DashboardLayout.jsx:113-152` 的 header 右侧控件组（实时数据 Badge + LiveClock + 数据更新日期 + 时间范围 ToggleGroup + 日期选择器）在 ≤960px 时虽然改为 `flex-wrap`，但 ToggleGroup 有 5 个按钮（昨天/7天/30天/自定义/全部），加上日期选择器后可能在 640px 以下溢出。

**违反规则**: `horizontal-scroll`（移动端无水平滚动）、`touch-density`（触摸间距舒适）

**建议**: 在 ≤640px 时将 ToggleGroup 改为 `<Select>` 下拉选择器，节省空间；或将日期选择器放入 Popover 弹出层。

### 3.3 首页缺少页面标题和面包屑 [HIGH]

`HomeView` 直接渲染三个卡片组件（BrandMentionRate、PlatformMentionRates、ReferencesTable），没有页面级标题（如"首页概览"）或面包屑导航。用户无法快速了解当前所在位置。

**违反规则**: `breadcrumb-web`（3+ 级深度使用面包屑）、`heading-hierarchy`（h1→h6 不跳级）

**建议**: 在 HomeView 顶部添加 `<h1>` 级别的页面标题和面包屑。

---

## 4. 交互与反馈 (Touch & Interaction) — MEDIUM

### 4.1 平台按钮缺少 focus 可见状态 [MEDIUM]

`PlatformMentionRates.jsx:125-165` 的平台按钮使用自定义样式，没有明确的 focus-visible 样式。键盘用户 Tab 到这些按钮时无法看到焦点指示器。

**违反规则**: `focus-states`（交互元素必须有可见焦点环，2-4px）

**建议**: 添加 `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` 到按钮 className。

### 4.2 DataTable 列调整手柄缺少键盘替代 [MEDIUM]

`DataTable.jsx:44-80` 的 `ResizableHandle` 仅支持鼠标拖拽（`onMouseDown`），不支持键盘操作。也没有 ARIA 标签说明其功能。

**违反规则**: `keyboard-nav`、`gesture-alternative`（不能仅依赖手势/拖拽）

**建议**: 为 ResizableHandle 添加 `aria-label="调整列宽"` 和键盘事件（左右箭头键调整宽度）；或考虑在列头添加宽度输入框替代。

### 4.3 错误重试使用 `window.location.reload()` [MEDIUM]

`BrandMentionRate.jsx:279,297` 的错误和空状态重试按钮使用 `window.location.reload()`，这会刷新整个页面，丢失用户当前的筛选状态、路由参数和侧边栏折叠状态。

**违反规则**: `state-preservation`（导航必须保留之前的滚动位置、筛选状态和输入）

**建议**: 改为重新触发数据获取函数（如重置 loading 状态重新调用 fetch），而非全页刷新。

### 4.4 LiveClock 每秒重渲染整个 Header [MEDIUM]

`DashboardLayout.jsx:18-34` 的 `LiveClock` 组件每秒 `setState` 触发重渲染。虽然 `LiveClock` 本身用 `React.memo` 包裹，但其父组件 `DashboardLayout` 会在 `LiveClock` 更新时因 DOM 差异产生不必要的重渲染检查。

**违反规则**: `main-thread-budget`（保持每帧工作 <16ms）、`debounce-throttle`

**建议**: 将 `LiveClock` 移到独立的不频繁更新区域，或改为每 30 秒更新一次（"实时数据"场景下秒级精度并非必要）。

### 4.5 "导出报告"按钮无实际功能 [MEDIUM]

`SourceAnalysis.jsx:294-297` 的"导出报告"按钮没有绑定任何导出逻辑，只是一个空的 `<Button>`。点击后没有任何反馈或提示。

**违反规则**: `error-feedback`（清晰错误消息）、`disabled-states`（禁用元素使用降低的透明度 + 光标变化 + 语义属性）

**建议**: 在功能未实现时将按钮设为 `disabled` 并添加 `tooltip` 提示"即将上线"，或直接移除该按钮。

---

## 5. 样式一致性 (Style Selection) — MEDIUM

### 5.1 MetricCircle 11px 字体过小 [MEDIUM]

`BrandMentionRate.jsx:55` 中 `MetricCircle` 的百分比数字使用 `text-[11px]`，低于最低推荐字体 12px。在小屏或高 DPI 设备上可读性差。

**违反规则**: `readable-font-size`（最小 16px 正文，最小 12px 标签）

**建议**: 将百分比数字改为 `text-xs`（12px）或 `text-sm`（14px），同时略微增大圆环尺寸以容纳更大的文字。

### 5.2 图表卡片标题风格不统一 [MEDIUM]

部分图表卡片标题带有图标（TrendAnalysis 的"品牌提及率分析"带 LineChart 图标、SourceAnalysis 的"信源分析"带 TrendingUp 图标、SentimentAnalysis 的"情感分析"带 Smile 图标），但 BrandMentionRate 的"品牌提及排名"没有图标，ReferencesTable 也没有。

**违反规则**: `consistency`、`icon-style-consistent`（全站使用一致的图标风格）

**建议**: 为所有 Card 标题统一添加对应的 Lucide 图标，保持视觉一致性。

---

## 6. 性能 (Performance) — LOW

### 6.1 首页三个组件串行请求 [LOW]

`HomeView` 渲染 `BrandMentionRate`、`PlatformMentionRates`、`ReferencesTable` 三个组件，各自独立发起 API 请求。虽然 `BrandMentionRate` 内部用了 `Promise.all` 并行请求两个接口，但三个组件之间是串行挂载后各自请求。

**违反规则**: `bundle-splitting`（按路由/功能拆分以减少初始负载和 TTI）

**建议**: 考虑在 HomeView 层面统一发起所有首页数据请求，减少请求延迟叠加。

### 6.2 DataTable 列宽拖拽缺少防抖 [LOW]

`DataTable.jsx:57-59` 的 `handleMouseMove` 在每次鼠标移动时直接调用 `onResize` 更新 state，高频触发 React 重渲染。

**违反规则**: `debounce-throttle`（高频事件使用防抖/节流）

**建议**: 对 `handleMouseMove` 中的 `onResize` 调用添加 `requestAnimationFrame` 节流。

### 6.3 情感分析页面使用硬编码 Mock 数据 [LOW]

`SentimentAnalysis.jsx:10-29` 的 `MOCK_SENTIMENT` 和 `WORD_CLOUD_DATA` 是硬编码的假数据。页面呈现的数据无法反映真实情况，可能误导用户。

**违反规则**: `empty-data-state`（无数据时显示有意义的空状态而非假数据）

**建议**: 在真实 API 就绪前，将图表替换为空状态提示"情感分析功能即将上线"，而非展示假数据。

---

## 修复优先级建议

| 优先级 | 问题编号 | 预估工时 |
|--------|---------|----------|
| P0（立即修复）| 1.1, 1.2, 1.3 | 4-6h |
| P1（本周修复）| 2.1, 2.2, 2.3, 3.1, 3.2 | 6-8h |
| P2（迭代修复）| 2.4, 2.5, 2.6, 3.3, 4.1-4.5, 5.1, 5.2 | 8-12h |
| P3（技术债务）| 6.1, 6.2, 6.3 | 2-4h |

---

## 参考资料

1. [WCAG 2.1 AA 对比度要求](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
2. [Apple Human Interface Guidelines - Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)
3. [Material Design - Data Visualization](https://m3.material.io/styles/color/overview)
4. [shadcn/ui Accessibility Patterns](https://ui.shadcn.com/docs/components/chart)
