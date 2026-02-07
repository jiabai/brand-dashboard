## Summary
统一了 `SentimentAnalysis.jsx` 中词云图与环形图的配色方案，使页面视觉效果更加协调。

## Code Highlights
- 修改了 [SentimentAnalysis.jsx](file:///d:/Github/brand-dashboard/web/src/components/SentimentAnalysis.jsx#L191-L195) 中的词云图配置。
- 增加了 `scale('color', { range: ['#2582a1', '#c52125', '#f88c24'] })`，该配色方案取自左侧的情感分析环形图（正面、负面、中性）。

## Self-Tests
- 运行 `npm --prefix web run lint --if-present` 检查代码规范，未发现错误。
- 确认词云图现在使用与环形图一致的蓝色、红色和橙色调。
