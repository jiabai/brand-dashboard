## Summary
修复了 `api/repositories/database.py` 中 `query_domain_citation_rate` 函数的实现与 `DASHBOARD_API_README.md` 中描述的 SQL 逻辑不一致的问题。

主要修正内容：
1.  将查询条件中的 `created_at` 字段修改为 `date` 字段，以匹配 `qa_reference` 表的实际使用情况（参考 `query_reference_url_stats` 的实现）和 README 中的 SQL 定义。
2.  调整了日期范围的参数传递方式，直接使用 `date` 对象而不是转换为 `datetime` 对象，确保 `BETWEEN` 查询在日期字段上的正确性。

## Code Highlights
- `api/repositories/database.py`: 修改了 `query_domain_citation_rate` 函数中的 `total_query` 和 `domain_query` SQL 语句及参数。

## Self-Tests
- 静态代码分析：运行 `ruff check api` 通过。
- 逻辑验证：对比了 `query_reference_url_stats` 函数的实现，确认了 `date` 字段的使用模式。
