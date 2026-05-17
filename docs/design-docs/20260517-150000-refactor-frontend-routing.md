# 前端路由路径化设计记录

> 日期：2026-05-17

## 背景

旧版仪表板通过查询参数同时承载页面身份和筛选状态，例如 `view`, `tenant_key`, `job_id`, `date`。当新路径 `/dashboard/:tenantKey/:jobId` 已经包含租户和任务后，旧同步逻辑仍会把这些身份参数回写到查询串，导致 URL 出现重复状态来源。

## 决策

- 引入 React Router，分析页使用路径承载页面身份：
  - `/dashboard/:tenantKey/:jobId`
  - `/trend/:tenantKey/:jobId`
  - `/platforms/:tenantKey/:jobId`
  - `/sources/:tenantKey/:jobId`
  - `/sentiment/:tenantKey/:jobId`
- 管理页和任务页使用租户路径：
  - `/accounts/:tenantKey`
  - `/tasks/:tenantKey/new`
  - `/tasks/:tenantKey/status`
- 查询串只保留筛选条件，例如 `timeframe`, `brand`, `start_date`, `end_date`, `platform`。
- 旧版 `/?view=...&tenant_key=...&job_id=...` 入口废弃。根路径和未知路径直接进入默认新入口，不解析旧入口查询参数。
- 分析页会清理不属于当前页面的查询参数，例如 `view`, `tenant_key`, `job_id`, `date`, `executor_id`, `include_deleted`，避免任务页筛选参数污染分析页 URL。

## 影响

- 分享链接更稳定：路径决定页面和数据身份，查询串决定筛选条件。
- 侧边栏导航通过 `web/src/utils/routing.js` 统一构建路径和查询串，避免各组件手写路由规则。
- `DashboardLayout.jsx` 负责统一清理不属于当前页面的查询参数，防止无效参数在新路由中反复回写。

## 验证

- 新增 `web/src/utils/__tests__/routing.test.js` 覆盖默认新入口、查询串清理和路径到视图映射。
- 浏览器验证：访问 `/dashboard/:tenantKey/:jobId` 时，旧参数不会被重新追加到查询串。
