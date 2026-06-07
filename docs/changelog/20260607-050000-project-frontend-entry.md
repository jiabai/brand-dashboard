# feat: 新增监测项目前端入口

## 背景

Phase 3.2 已经提供项目列表和项目详情 API，但租户用户仍只能从旧任务或 dashboard 入口进入系统。Phase 3.3 将“监测项目”挂入租户工作台主导航，为后续项目关联采集任务、项目概览和项目设置打基础。

## 变更

- 新增前端项目 API adapter：`fetchProjects`、`fetchProjectDetail`。
- 新增 `/projects/:tenantKey` 项目列表页，展示项目数量、状态和基础配置摘要。
- 新增 `/projects/:tenantKey/:projectId` 项目详情壳层，展示项目基本信息、品牌配置和问题集配置。
- 更新前端路由配置、路径构造工具和侧边栏图标，让“监测项目”成为租户工作台主入口之一。
- 补充项目展示纯函数、API adapter、路由配置和路径识别测试。
- 更新 ExecPlan、TASKS 和领域参考文档，记录 Phase 3.3 的落地边界。

## 验证

- `npm --prefix web test`
- `npm --prefix web run lint`
- `npm --prefix web run build`
- 系统 Chrome + Playwright 桌面/移动 smoke test：项目列表可打开项目详情，详情显示品牌配置和问题集
- `python scripts/validate_agents_docs.py --level ERROR`
- `python scripts/validate_agents_docs.py --level WARN`
