## Summary
将 `SentimentAnalysis.jsx` 中的词云图向上移动了 10%，通过在容器的 `transform` 属性中增加 `translateY(-10%)` 实现。

## Code Highlights
- 修改了 [SentimentAnalysis.jsx](file:///d:/Github/brand-dashboard/web/src/components/SentimentAnalysis.jsx#L233) 中的词云图容器样式。
- 将 `transform: 'translateX(-10%)'` 更新为 `transform: 'translate(-10%, -10%)'`。

## Self-Tests
- 运行 `npm --prefix web run lint --if-present` 检查代码规范，未发现错误。
- 手动确认代码逻辑变更符合预期。
