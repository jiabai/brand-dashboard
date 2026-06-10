# 统一全局 HTTPException 错误信封

## 变更

- `api/main.py` 全局异常 handler 输出业务信封 `{"status":"error","message":...,"code":...}`，替换原 `{"error":...,"status_code":...}` 形状（后者无文档、无测试、无任何消费者解析，导致认证 401 等错误在前端显示原始 JSON）。HTTP 状态码不变，满足契约"HTTP 状态与业务 `code` 一致"。
- handler 注册类从 `fastapi.HTTPException` 改为其基类 `starlette.exceptions.HTTPException`：框架自身抛出的未路由 404 / 方法不匹配 405 同样收口为信封，消除 FastAPI 默认 `{"detail":...}` 的最后一个生产出口。
- 透传 `exc.headers` 并增加 bodyless 状态码守卫（`is_body_allowed_for_status_code`），对齐 FastAPI 默认 handler 语义（原实现丢弃 headers）。
- 新增 `api/tests/test_error_envelope.py`：认证 401、平台权限 403、未路由 404、headers 透传共 4 条契约回归（此前全局 handler 零测试覆盖）。
- `web/src/api/__tests__/client.test.js` 新增认证 401 信封解析回归测试；`client.js` 解析顺序 message 优先、detail 回退，对新信封零改动兼容，本次不改前端代码。

## 边界

- 路由内手写 `JSONResponse` 信封出口（`api/v1/routes/auth.py` 等业务 400/404）行为不变，不重构为 `raise HTTPException`。
- 自建 `FastAPI()` app 的既有测试（`test_collection_attempts_api.py`、`test_query_jobs_project_link.py`）不挂全局 handler，继续断言 FastAPI 默认 `detail` 形状，属测试内部构造，维持不动。
- 422 `RequestValidationError` 仍为 FastAPI 默认 `{"detail":[...]}` 形状，已登记 `docs/exec-plans/tech-debt-tracker.md`；前端 `detail` 回退分支兜底。
- 不给前端增加 `error` 字段回退：统一后无生产出口再发该形状，避免死代码。
- 设计决策与现状盘点见 `docs/design-docs/20260610-unified-error-envelope.md`。

## 验证

- `uv run --project api ruff check api`（All checks passed）
- `PYTHONPATH=. uv run --project api --extra dev pytest api/tests/ -q`（198 passed；基线 194，新增 4 条全过）
- `npm --prefix web test`（122 pass / 0 fail；基线 121）
- `npm --prefix web run build`（构建成功）
- `python scripts/validate_agents_docs.py --level ERROR`（0 错误）
