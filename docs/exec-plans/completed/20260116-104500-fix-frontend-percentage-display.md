## Summary
修复了前端 `ReferencesTable` 组件中域名引用率（domain-citation-rate）显示数值错误的问题。

问题原因：
组件内部定义了一个 `toPercent` 函数，该函数包含一个启发式逻辑：如果数值在 0 到 1 之间（0 < num <= 1），则认为它是小数形式的比例（ratio），并将其乘以 100 转换为百分比。
然而，API 返回的数据实际上已经是百分比数值（例如 `0.28` 代表 0.28%）。该启发式逻辑错误地将 `0.28` 转换为了 `28`，导致前端显示为 `28%` 而非正确的 `0.28%`。

修复方案：
移除了 `toPercent` 函数及其调用，直接使用 API 返回的数值进行展示，保持与 API 数据定义一致。

## Code Highlights
- `web/src/components/ReferencesTable.jsx`: 删除了 `toPercent` 函数定义，并在数据处理逻辑中移除了对 `toPercent` 的调用。

## Self-Tests
- 手动验证逻辑：
  - 输入 `49.15` -> `clampPercent(49.15)` -> `49.15` -> 显示 `49.15%` (符合预期)
  - 输入 `0.28` -> `clampPercent(0.28)` -> `0.28` -> 显示 `0.28%` (修复后符合预期，原为 28%)
- 检查了 `web/src/utils/index.js` 中的 `formatPercentage` 函数，确认其逻辑是直接格式化数值，不会进行错误的乘法运算。
