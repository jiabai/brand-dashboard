# 平台管理员 Membership 只读边界 ExecPlan

## 目标

平台管理员进入任意租户项目工作台时，都应按平台客户视角处理；即使该账号历史上拥有目标租户 membership，也不显示“加入团队”等租户侧入口。

## 范围

- 修正 `isPlatformReadonlyTenantAccess` 的判定语义。
- 覆盖平台管理员有目标租户 membership 的测试场景。
- 同步产品规格和 changelog。

## 非目标

- 不修改数据库 membership。
- 不调整后端权限依赖。
- 不新增平台管理员代租户操作能力。

## 任务拆解

| Task | 状态 | 验收 |
|------|------|------|
| 根因复现 | complete | 查明 `lantianye@163.com` 拥有目标租户 viewer membership |
| 失败测试 | complete | 平台管理员有 membership 时仍应只读的测试先失败 |
| 前端实现 | complete | 定向测试通过 |
| 文档同步 | complete | 产品规格与 changelog 更新 |
| 验证归档 | complete | 门控通过，ExecPlan 移入 completed，临时任务清单删除 |

## 决策记录

| 决策 | 原因 |
|------|------|
| 平台管理员租户工作台始终按客户视角 | 平台管理员职责是查看、排障和体验客户视角，不应因为历史 membership 暴露租户加入入口。 |
| 不删除 membership 数据 | 本次修复产品边界，不做数据修复或权限迁移。 |

## 验证计划

| Gate | 命令 | 状态 |
|------|------|------|
| 前端定向测试 | `npm --prefix web test -- src/auth/__tests__/platformAccess.test.js src/components/__tests__/Sidebar.test.js` | passed, 5/5 |
| 前端全量测试 | `npm --prefix web test` | passed, 110/110 |
| 前端构建 | `npm --prefix web run build` | passed |
| 浏览器烟测 | Playwright local smoke: 平台管理员有 membership 时项目工作台隐藏“加入团队” | passed |
| 文档结构 | `python scripts/validate_agents_docs.py --level ERROR` | passed |
| Diff 检查 | `git diff --check` | passed，仅 CRLF 提示 |

## 进度记录

- 2026-06-09：用户指出真实账号 `lantianye@163.com` 在项目工作台侧栏仍显示“加入团队”；查明旧逻辑因该账号有目标租户 viewer membership 没有命中平台只读过滤。
- 2026-06-09：新增平台管理员有目标租户 membership 时仍应只读的红灯测试；定向测试按预期失败。
- 2026-06-09：修正 `isPlatformReadonlyTenantAccess`，平台管理员在租户工作台始终按客户只读视角；定向测试 5/5 通过。
- 2026-06-09：同步产品规格和 changelog；文档结构校验 0 错误。
- 2026-06-09：完成全量前端测试、生产构建、Playwright 本地烟测、文档结构校验和 diff 检查；归档 ExecPlan 并删除临时任务清单。

## 错误记录

| 错误 | 处理 |
|------|------|
