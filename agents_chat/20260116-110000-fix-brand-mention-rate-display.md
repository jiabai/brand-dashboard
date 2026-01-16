## Summary
修复了 `BrandMentionRate` 组件中数值为 1.0 时显示错误的问题。

问题原因：
组件内部的 `toPercent` 函数逻辑为 `num < 1 ? num * 100 : num`。当 API 返回 `mention_rate` 为 1.0 时，由于 1.0 不小于 1，函数直接返回 1.0，导致页面显示为 "1.00%" 而不是预期的 "100.00%"。

修复方案：
修改 `web/src/components/BrandMentionRate.jsx` 中的 `toPercent` 函数，将判断条件改为 `num <= 1`，确保 1.0 也能正确乘以 100 转换为百分比。

## Code Highlights
- `web/src/components/BrandMentionRate.jsx`: 更新了 `toPercent` 函数的判断逻辑。

## Self-Tests
- 手动验证逻辑：
  - 输入 `1.0` -> `toPercent(1.0)` -> `1.0 <= 1` 为真 -> 返回 `100` -> 显示 `100.00%` (修复后符合预期)
  - 输入 `0.5` -> `toPercent(0.5)` -> `0.5 <= 1` 为真 -> 返回 `50` -> 显示 `50.00%` (保持原有逻辑)
  - 输入 `85.5` -> `toPercent(85.5)` -> `85.5 <= 1` 为假 -> 返回 `85.5` -> 显示 `85.50%` (保持原有逻辑)
