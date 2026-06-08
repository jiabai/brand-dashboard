# Legacy 兼容边界固化

## 变更内容

- 明确架构口径为“兼容历史资产，不兼容历史产品形态”。
- 在 `web/src/config/routes.js` 新增 `getProductShapeRoutes()` 和 `getLegacyCompatibilityRoutes()`，把当前产品形态路由与 legacy 兼容路由显式分离。
- 补充前端路由测试，确保项目优先路由不要求 `jobId`，legacy dashboard/task 路由只作为兼容入口保留。
- 新增 `docs/design-docs/20260608-legacy-compatibility-boundary.md`，记录兼容范围、取舍、ADR 和删除条件。
- 更新 `docs/ARCHITECTURE.md`、`docs/DESIGN.md` 和设计文档索引。

## 边界说明

本次不删除任何旧 dashboard、旧任务路由或旧 API；历史链接、历史数据和排障读取面仍然可用。后续新功能应进入项目主流程，不再围绕旧 `tenant_key + job_id` 产品形态扩展。

## 验证

- 新增路由策略测试先在缺少 helper 时失败，再补实现通过。
- `npm --prefix web test` 通过（89 passed）。
- `npm --prefix web run lint` 通过，0 error，保留既有 8 个 warning。
- `npm --prefix web run build` 通过，保留 Browserslist 数据过期提示。
- `python scripts/validate_agents_docs.py --level ERROR` 和 `--level WARN` 均为 0 错误、0 警告。
- `git diff --check` 通过，仅输出既有 LF/CRLF 换行提示。
