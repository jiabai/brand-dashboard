# 移除无引用的 utils/http fetch 封装

## 变更

- 删除 `web/src/utils/http.js`：与 `web/src/api/client.js` 平行的裸 fetch 封装，经全仓 grep 核实无任何生产模块引用（所有 API 模块统一走 `client.js`，后者含鉴权与租户头注入）。
- 同步移除 `web/src/utils/index.js` barrel 中的 `export * from './http.js'` 转出口（无模块经 barrel 消费 `fetchJson`/`postJson`）。
- 一并删除孤儿测试 `web/src/utils/__tests__/http.test.js`（仅覆盖被删封装）。
- 错误解析「业务 message 优先、detail 回退」的语义保留在 `client.js`（提交 bbe7dc0），http.js 上未提交的同步改动随文件删除一并废弃。

## 边界

- 归档文档 `docs/exec-plans/completed/20260517-174000-web-frontend-architecture-deepening.md` 中对 http.js 的历史记载保持原样，不改写归档。
- 不调整 `client.js` 行为；本次仅消除平行封装，错误解析的单一事实来源收敛到 `api/client.js`。

## 验证

- `npm --prefix web test`（121 pass / 0 fail；基线 122 含被删孤儿测试 1 条）
- `npm --prefix web run build`（构建成功）
- `python scripts/validate_agents_docs.py --level ERROR`（0 错误）
- 提交树 `git grep` 核实：无 `utils/http`、`./http.js` 残留引用，`fetchJson`/`postJson` 消费方均指向 `api/client.js`
