# 统一错误响应信封

> 状态：已实现，2026-06-10
>
> 关联：错误契约定义见 `docs/references/20260519-000000-tenant-account-api-reference.md` §1.1；前端错误解析见 `web/src/api/client.js`。

## 背景

后端此前并存三种错误响应形状：

| # | 形状 | 来源 | 消费状况 |
|---|------|------|----------|
| 1 | `{"status":"error","message":...,"code":...}` | 路由内手写 `JSONResponse`（`api/v1/routes/auth.py` 等业务 400/404） | 契约文档已定义；前端 `client.js` 解析 `message`；测试断言覆盖 |
| 2 | `{"detail":...}` | FastAPI 默认 `HTTPException` 序列化 | 仅出现在自建 app 的测试中（不挂全局 handler）；生产环境不可达（被 #3 重写） |
| 3 | `{"error":...,"status_code":...}` | `api/main.py` 全局 `HTTPException` handler | 无文档、无测试、无任何消费者解析该字段 |

生产环境中所有 `raise HTTPException`（认证 401、权限 403、资源 404、dashboard 400/500 等约 90 处）实际输出形状 #3。前端 `client.js` 只解析 `message` 与 `detail` 字段，不认 `error`，导致认证失败等场景在 UI 上显示原始 JSON 文本——这是本次修复的用户可见 bug。

`docs/references/20260519-000000-tenant-account-api-reference.md` §1.1 早已将形状 #1 定为对外错误契约（"HTTP 状态与业务 `code` 必须一致"），但全局 handler 的实现与契约不符。

## 决策

**统一到业务信封（形状 #1），在全局 handler 一处收口，路由侧不动。**

1. `api/main.py` 全局 handler 输出 `{"status":"error","message":exc.detail,"code":exc.status_code}`，HTTP 状态码不变（仍为 `exc.status_code`，满足"HTTP 状态与业务 code 一致"）。
2. handler 注册到 `starlette.exceptions.HTTPException`（`fastapi.HTTPException` 是其子类）。原实现注册在 fastapi 子类上,框架自身抛出的未路由 404 / 方法不匹配 405（starlette 基类实例）走不到自定义 handler，仍输出 `{"detail":...}`；注册到基类后两类异常统一收口。
3. 透传 `exc.headers`（原实现丢弃）。认证边界未来若需 `WWW-Authenticate` 等响应头不会被吞掉，与 FastAPI 默认 handler 行为对齐。
4. 保留 bodyless 状态码守卫（`is_body_allowed_for_status_code`，204/304 等不允许响应体的状态直接返回空响应），镜像 FastAPI 默认语义，避免 Content-Length 不一致。

路由内手写的 `JSONResponse` 信封（形状 #1 的既有出口）行为不变，本次不重构为 `raise HTTPException`——那是另一个可选的收敛方向，不属于本次边界。

## 前端评估

- `web/src/api/client.js` 解析顺序为 `message` 优先、`detail` 回退，对新信封零改动兼容；本次不改前端代码。
- **不**给 `client.js` 增加 `error` 字段回退：统一后无任何生产出口再发该形状，回退分支即死代码；前后端同仓原子部署，无长期版本错配窗口。
- 在 `web/src/api/__tests__/client.test.js` 新增认证 401 信封解析回归测试，钉住本次 bug 场景。

## 测试边界

- 新增 `api/tests/test_error_envelope.py` 走真实 `api.main:app`，覆盖：认证 401（依赖抛出的 `fastapi.HTTPException`）、平台权限 403（路由依赖抛出）、未路由 404（框架抛出的 starlette 基类异常）、headers 透传。全局 handler 此前完全无测试覆盖。
- 既有自建 `FastAPI()` app 的测试（`test_collection_attempts_api.py:295`、`test_query_jobs_project_link.py:268`）不挂全局 handler，断言的是 FastAPI 默认 `detail` 形状——属测试内部构造，不代表对外契约，维持不动。

## 范围外与残余风险

- **422 参数校验错误**（`RequestValidationError`）仍为 FastAPI 默认 `{"detail":[...]}` 形状，未纳入信封。前端 `detail` 回退分支对其兜底（数组拼接可读性差但不致显示原始 JSON）。已登记 `docs/exec-plans/tech-debt-tracker.md`。
- 本次按用户指定的轻量流程执行（设计文档 → 实现 → 全量门禁），未另建 ExecPlan：改动集中于单一 handler + 测试，无多阶段任务拆分需要。验证结果见 changelog `docs/changelog/20260610-070000-unified-error-envelope.md`。
