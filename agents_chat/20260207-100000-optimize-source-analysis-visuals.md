## Summary
针对信源分析页面的视觉清晰度进行了专项优化，重点解决了图表过小、对比度不足的问题。

## Code Highlights
- **SourceAnalysisChart 视觉增强**：
  - 将分布统计图高度从 `60px` 提升至 `100px`。
  - 引入了 `label` 配置，在柱状图内部直接显示百分比（>5% 时显示），并添加了文字阴影以增强在深色背景上的可读性。
  - 优化了配色方案，使用了更具 SaaS 感的高对比度调色板。
  - 为柱状图添加了白色描边（lineWidth: 2），使各分段界限更加分明。
  - 增强了图表容器的背景视觉，使用了线性渐变和内阴影，提升层次感。
- **MediaListTable 细节打磨**：
  - 将列表中的“引用率”进度条高度从 `4px` 增加到 `6px`，宽度从 `40px` 增加到 `60px`，使其更加易读。

## Self-Tests
- 检查 [SourceAnalysis.jsx](file:///d:/Github/brand-dashboard/web/src/components/SourceAnalysis.jsx) 代码逻辑，确保图表配置正确无误。
- 验证 Ant Design Charts 的 `label` 和 `barStyle` 属性符合 API 规范。
