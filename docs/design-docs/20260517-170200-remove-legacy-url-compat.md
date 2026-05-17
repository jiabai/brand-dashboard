## Summary
移除前端旧式 URL 兼容代码。旧式 URL 使用查询参数传递路由信息（`?view=home&tenant_key=xxx&job_id=xxx&date=xxx`），由 `LegacyRedirect` 组件处理后重定向到新式路径 URL。新式路径 URL 已全面启用，旧式兼容代码不再需要。

## Code Highlights
- [App.jsx](file:///d:/Github/brand-dashboard/web/src/App.jsx): 移除 `LegacyRedirect` 引用；`/` 和 `*` 路由改为直接 `<Navigate>` 到默认 dashboard
- [routing.js](file:///d:/Github/brand-dashboard/web/src/utils/routing.js): 移除 `LEGACY_KEYS` 常量、`buildLegacyRedirectUrl()` 函数、`buildRouteSearch()` 中对旧参数名的清理
- [useDashboardParams.js](file:///d:/Github/brand-dashboard/web/src/hooks/useDashboardParams.js): `tenantKey`/`jobId` 不再从 `?tenant_key=` / `?job_id=` 回退；`updateParams` 不再清理 `view`/`tenant_key`/`date`
- [DashboardLayout.jsx](file:///d:/Github/brand-dashboard/web/src/components/DashboardLayout.jsx): 移除所有 `date: null` 清理（5 处）
- [routing.test.js](file:///d:/Github/brand-dashboard/web/src/utils/__tests__/routing.test.js): 移除 `buildLegacyRedirectUrl` 相关测试用例
- LegacyRedirect.jsx: 整个文件删除

## Self-Tests
- `npm --prefix web run build` 构建通过
- `npm --prefix web test` 8 个测试全部通过
- `python scripts/validate_agents_docs.py --level ERROR` 文档结构验证通过
