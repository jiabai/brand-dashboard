# Product Specs Index

## Purpose

Product specs describe user-visible intent and boundaries before or alongside implementation work.

## Current Specs

| File | Scope |
|------|-------|
| [20260611-010000-project-dashboard-entry-collection-jobs.md](20260611-010000-project-dashboard-entry-collection-jobs.md) | 项目看板入口改用 collection_jobs 作为采集任务来源（一次采集一行，经 source_job_id 进 legacy 看板）；修订前一份的数据源 |
| [20260611-project-dashboard-entry.md](20260611-project-dashboard-entry.md) | 项目详情页「进入看板」入口：用户选 job 进 legacy 首页看板，复用 query-jobs/status 加 project_id 过滤 |
| [20260610-password-reset-and-change.md](20260610-password-reset-and-change.md) | 自助密码重置（防枚举邮件流程 + 指纹一次性令牌）与已登录修改密码 |
| [20260610-platform-resend-admin-activation.md](20260610-platform-resend-admin-activation.md) | 平台租户详情页重发管理员激活邮件：对待激活管理员重签 7 天令牌，复用 SMTP 发送与人工兜底 |
| [20260610-platform-tenant-admin-emergency-entry.md](20260610-platform-tenant-admin-emergency-entry.md) | 平台租户详情页补齐受审计的租户管理员应急设置入口 |
| [20260610-tenant-member-governance.md](20260610-tenant-member-governance.md) | 租户成员管理 API、平台应急角色修改审计与最后 active admin 保护 |
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
| [20260520-040000-platform-admin-tenant-read-access.md](20260520-040000-platform-admin-tenant-read-access.md) | 平台管理员全租户项目与看板只读：平台运营可查看 active 租户项目 GET 和 dashboard，但不获得写权限 |
| [20260521-185332-platform-admin-job-aware-dashboard-entry.md](20260521-185332-platform-admin-job-aware-dashboard-entry.md) | 平台管理员 Job 感知排障入口：平台租户详情使用真实 tenant/job/brand 进入 legacy dashboard |
| [20260603-000000-admin-activation-email.md](20260603-000000-admin-activation-email.md) | 管理员激活邮件发送：创建租户后通过 SMTP 自动发送激活链接，并保留人工兜底 |
| [20260606-brand-monitoring-system-refactor.md](20260606-brand-monitoring-system-refactor.md) | 品牌监测业务系统重构：以监测项目为主线，补齐采集、分析、指标、告警和报告闭环 |
| [20260609-tenant-join-entry-boundary.md](20260609-tenant-join-entry-boundary.md) | 租户加入团队入口：平台管理员只读客户视角隐藏入口，租户成员保留邀请码核验与员工注册 |
