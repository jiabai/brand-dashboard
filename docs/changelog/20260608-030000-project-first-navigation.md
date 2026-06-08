# Phase 8.1 项目优先导航

## 变更内容

- 将租户用户默认入口从旧任务状态页调整为 `/projects/:tenantKey`。
- 将旧 dashboard 分析页和旧任务页从侧边栏主导航移除，并标记为 `legacy` 兼容路由。
- 侧边栏主分组改为“工作台”，当前只展示“监测项目”和“账户管理”。
- 保留 `/dashboard/:tenantKey/:jobId`、`/trend/:tenantKey/:jobId`、`/snapshots/:tenantKey/:jobId`、`/tasks/:tenantKey/new`、`/tasks/:tenantKey/status` 等旧路径继续参与路由生成。

## 边界说明

本阶段只清理主导航暴露，不删除旧 dashboard、旧任务页面或相关 API。历史链接、排障路径和兼容期读取面仍可直接访问。

## 验证

- 前端路由定向测试覆盖默认入口、主侧边栏菜单、legacy 路由保留和登录默认跳转（11 passed）。
- 全量前端测试通过（88 passed）。
- 前端 lint 通过，无错误，保留既有 8 个 warning。
- 前端 build 通过。
- 系统 Chrome + Playwright smoke：默认 `/` 进入 `/projects/tn_acme`，项目页侧边栏不再显示旧任务/首页/趋势入口，旧 `/tasks/tn_acme/status` 仍可直接打开。
