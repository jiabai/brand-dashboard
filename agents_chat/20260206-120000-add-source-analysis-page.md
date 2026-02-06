## Summary
新增了“信源分析”页面 (SourceAnalysis)，用于展示品牌在不同渠道的分布和详细引用数据。目前数据为 Mock 状态。

## Code Highlights
- **Frontend**:
  - 新建 `web/src/components/SourceAnalysis.jsx`：
    - 包含“品牌关键词”、“信源分布统计”（堆叠条形图）、“引用媒介列表”三个核心模块。
    - 使用 Tailwind CSS 进行高对比度、专业风格的布局。
    - 使用 `@ant-design/charts` 实现水平堆叠条形图。
  - 修改 `web/src/App.jsx`：
    - 添加 `SourceAnalysis` 的懒加载。
    - 在 `renderContent` 中增加 `currentView === 'sources'` 的路由分支。

## Self-Tests
- 检查了 `App.jsx` 的路由逻辑，确保 `view=sources` 时能正确渲染组件。
- 确认 `SourceAnalysis.jsx` 导入了必要的 Ant Design 组件和图表库。
- 页面布局符合“简洁、专业、高对比度”的要求。
