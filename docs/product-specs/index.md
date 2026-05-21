# Product Specs Index

## Purpose

Product specs describe user-visible intent and boundaries before or alongside implementation work.

## Current Specs

| File | Scope |
|------|-------|
| [20260201-140000-add-platform-filter-to-brand-metrics.md](20260201-140000-add-platform-filter-to-brand-metrics.md) | 品牌指标接口新增 platform 可选参数，支持按平台筛选 |
| [20260204-150415-add-top3-mention-rate.md](20260204-150415-add-top3-mention-rate.md) | 声量份额表格新增 Top 3 Mention Rate 列 |
| [20260206-120000-add-source-analysis-page.md](20260206-120000-add-source-analysis-page.md) | 新增信源分析页面，展示品牌渠道分布与引用数据 |
| [20260207-100000-optimize-source-analysis-visuals.md](20260207-100000-optimize-source-analysis-visuals.md) | 信源分析页面视觉优化：图表尺寸、配色、可读性增强 |
| [20260517-000000-refactor-frontend-routing.md](20260517-000000-refactor-frontend-routing.md) | 前端 URL 路由改造：引入 react-router-dom，路径参数替代 query param 驱动 |
| [20260518-003119-migrate-web-ui-to-shadcn.md](20260518-003119-migrate-web-ui-to-shadcn.md) | Web UI 组件系统从 Ant Design/G2 迁移到 shadcn/ui/Recharts 的产品边界与验收标准 |
| [20260518-145556-optimize-dashboard-ui-visual-design.md](20260518-145556-optimize-dashboard-ui-visual-design.md) | 仪表板 UI 视觉优化：暖色浅底主题、信息密度、App shell 与空状态体验 |
| [20260519-000000-multi-tenant-registration-flow.md](20260519-000000-multi-tenant-registration-flow.md) | B2B SaaS 多租户注册、登录、租户管理、角色权限与安全验收标准 |
| [20260520-010000-platform-operations-console.md](20260520-010000-platform-operations-console.md) | 平台运营后台：独立 `/platform` 权限域、租户列表、创建租户和运营入口 |
| [20260520-020000-platform-admin-bootstrap.md](20260520-020000-platform-admin-bootstrap.md) | 首个平台管理员账号 bootstrap：本地 CLI 初始化用户和平台管理员白名单 |
| [20260520-030000-tenant-access-grant.md](20260520-030000-tenant-access-grant.md) | 租户访问授权：为已有用户显式授予已有租户的 viewer/member/admin 成员关系 |
| [20260520-040000-platform-admin-tenant-read-access.md](20260520-040000-platform-admin-tenant-read-access.md) | 平台管理员全租户只读看板：平台运营可查看所有 active 租户 dashboard，但不获得写权限 |
| [20260521-185332-platform-admin-job-aware-dashboard-entry.md](20260521-185332-platform-admin-job-aware-dashboard-entry.md) | 平台管理员 Job 感知看板入口：平台租户列表展示 job 摘要并使用真实 tenant/job/brand 进入 dashboard |
