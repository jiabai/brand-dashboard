# Design Docs Index

## Purpose

Design docs capture architectural decisions, refactoring rationale, and cross-cutting design choices.

## Current Docs

| File | Focus |
|------|-------|
| [20260517-184500-web-frontend-architecture-deepening.md](20260517-184500-web-frontend-architecture-deepening.md) | Web 前端架构深化：时间 hook、API Adapter 消费、统一路由配置 |
| [20260517-200000-migration-to-shadcn.md](20260517-200000-migration-to-shadcn.md) | Ant Design → shadcn/ui 迁移设计评审与修订：分阶段策略、依赖边界、验收门禁 |
| [20260518-145556-dashboard-ui-visual-optimization.md](20260518-145556-dashboard-ui-visual-optimization.md) | 仪表板 UI 视觉优化：warm canvas、coral accent、信息密度与空状态策略 |
| [20260520-040000-platform-admin-tenant-read-access.md](20260520-040000-platform-admin-tenant-read-access.md) | 平台管理员全租户只读访问设计：项目与 dashboard 只读旁路、权限边界与测试策略 |
| [20260606-brand-monitoring-business-architecture-refactor.md](20260606-brand-monitoring-business-architecture-refactor.md) | 品牌监测业务系统架构评估与重构建议：产品流程、领域模型、数据生命周期与分阶段路线 |
| [20260606-brand-monitoring-target-architecture.md](20260606-brand-monitoring-target-architecture.md) | 品牌监测业务系统初版目标架构；指标读取已同步为事实聚合路线 |
| [20260608-legacy-compatibility-boundary.md](20260608-legacy-compatibility-boundary.md) | Legacy 兼容边界：兼容历史资产，不兼容历史产品形态 |
| [20260609-remove-metric-snapshots.md](20260609-remove-metric-snapshots.md) | 移除指标快照：以分析事实表聚合替代快照 read model |
| [20260609-platform-tenant-operations-workflow.md](20260609-platform-tenant-operations-workflow.md) | 平台租户项目工作台中转页：租户详情承接项目主入口和排障路径 |
| [20260610-unified-error-envelope.md](20260610-unified-error-envelope.md) | 统一错误响应信封：全局 HTTPException handler 收口为业务信封，前端解析与测试边界评估 |
