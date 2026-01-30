## Summary
修正了 `llm_conversations` 表中 `extracted_at` 字段的语义冲突。

主要修改：
1. 从 `extracted_at` 字段定义中移除了 `ON UPDATE CURRENT_TIMESTAMP`。
2. 该字段代表“原始文件创建时间”，应当在入库后保持不变，而不应随记录更新而变动。
3. 数据库记录的更新时间由已有的 `updated_at` 字段负责承载。

## Code Highlights
- [database_schema.sql](file:///d:/Github/brand-dashboard/api/database/database_schema.sql): 移除了 `extracted_at` 的自动更新触发器。

## Self-Tests
- [x] 静态代码分析：通过 `database_schema.sql` 文件确认字段定义。
- [x] 逻辑验证：确认 `updated_at` 字段仍保留 `ON UPDATE CURRENT_TIMESTAMP` 以支持审计。
