# 添加平台筛选到品牌指标接口

## Summary
修改了 `/brand-metrics` 接口，新增可选参数 `platform`。当不指定 `brand` 但指定 `platform` 时，可以查询特定平台下的所有品牌指标数据。

## Code Highlights
- `api/v1/routes/dashboard.py`: `get_brand_metrics` 函数新增 `platform` 参数。
- `api/v1/repositories/database.py`: `query_brand_metrics` 函数支持 `platform` 参数，并在 SQL 查询中动态添加过滤条件。

## Self-Tests
- [x] `ruff check api` 检查通过。
- [x] 代码逻辑审查确认符合 SQL 需求。
