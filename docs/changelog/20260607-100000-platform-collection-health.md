# Phase 4.4 平台采集健康度

## 背景

Phase 4.1 到 Phase 4.3 已经落地采集批次、任务、attempt、领取租约和 attempt 状态推进，但平台运营后台还无法从统一入口看到采集链路是否健康。平台管理员需要跨租户查看执行器状态、队列长度和失败任务，同时平台 API 不能依赖租户工作台的 `X-Tenant-Key`。

## 变更

- 新增 `GET /api/v1/platform/collection-health`，由平台管理员权限控制，不读取 `X-Tenant-Key`。
- 新增 `api/v1/repositories/platform_health.py`，汇总执行器、队列和失败任务。
- 新增平台前端 `/platform/executors` 页面，展示执行器健康、队列长度和失败任务。
- 新增前端 API `fetchPlatformCollectionHealth`，沿用 `skipTenantHeader: true`，避免平台请求误带租户头。
- 新增后端与前端测试，覆盖平台管理员访问、普通用户拒绝、前端请求不发送 `X-Tenant-Key` 和健康数据归一化。

## 边界

- 当前没有执行器 heartbeat 表，健康状态由 `executors.status`、活跃 lease、running attempt 和失败 attempt 推断。
- 本阶段不提供平台侧重试、取消、重新分配任务等写操作。
- 旧 `/api/v1/query-jobs/fetch` 继续保留兼容期行为，不在本阶段映射到新 collection task。

## 验证

- `uv run --project api ruff check api`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/test_platform_collection_health.py -q`
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`
- `npm --prefix web test -- src/api/__tests__/platform.test.js src/components/platform/__tests__/executorHealthPresentation.test.js`
- `npm --prefix web test`
- `npm --prefix web run lint`
- `npm --prefix web run build`
- 系统 Chrome mock 数据 smoke：`http://127.0.0.1:3001/platform/executors`
- `python scripts/validate_agents_docs.py --level ERROR`
- `python scripts/validate_agents_docs.py --level WARN`
