# 平台只读工作台身份上下文 ExecPlan

## 目标

平台管理员从租户详情进入项目工作台后，顶部栏必须明确展示当前登录账号和当前客户视角，避免误以为登录态丢失。

## 范围

- 在 `DashboardLayout` 顶部展示当前登录账号邮箱。
- 当 `isPlatformReadonlyTenantAccess({ user, tenantKey })` 为 true 时，展示平台只读客户视角和当前路由 `tenantKey`。
- 同步测试、产品规格和 changelog。

## 非目标

- 不改变 AuthContext、token 存储或 `/auth/me` 刷新逻辑。
- 不把平台管理员写入客户租户 membership。
- 不恢复平台管理员在客户工作台中的租户选择器。

## 任务拆解

| Task | 状态 | 验收 |
|------|------|------|
| 根因复现 | complete | Playwright 证明 localStorage 登录态未丢失，页面缺少可见账号上下文 |
| 失败测试 | complete | DashboardLayout 源码契约测试先失败 |
| 前端实现 | complete | 定向测试通过 |
| 文档同步 | complete | 产品规格与 changelog 更新 |
| 验证归档 | complete | 门控通过，ExecPlan 移入 completed，临时任务清单删除 |

## 决策记录

| 决策 | 原因 |
|------|------|
| 展示邮箱而不是写入租户 membership | 平台管理员是平台身份，不应获得客户租户成员身份。 |
| 平台只读时展示路由 `tenantKey` | URL 租户是当前客户视角的真实上下文，但不应污染 AuthContext 的当前租户。 |

## 验证计划

| Gate | 命令 | 状态 |
|------|------|------|
| 前端定向测试 | `npm --prefix web test -- src/components/__tests__/DashboardLayout.test.js` | passed, 1/1 |
| 前端全量测试 | `npm --prefix web test` | passed, 110/110 |
| 前端构建 | `npm --prefix web run build` | passed |
| 浏览器烟测 | Playwright local smoke: 平台租户详情点击进入项目工作台后账号邮箱和客户视角可见 | passed |
| 文档结构 | `python scripts/validate_agents_docs.py --level ERROR` | passed |
| Diff 检查 | `git diff --check` | passed，仅 CRLF 提示 |

## 进度记录

- 2026-06-09：复现用户反馈；确认登录态未丢失，但项目工作台顶部缺少可见账号上下文。
- 2026-06-09：新增 DashboardLayout 红灯测试；确认当前源码未接入平台只读身份上下文展示。
- 2026-06-09：更新 DashboardLayout 顶部栏，显示当前账号邮箱和平台只读客户视角；定向测试 1/1 通过。
- 2026-06-09：同步产品规格和 changelog；文档结构校验 0 错误。
- 2026-06-09：完成全量前端测试、生产构建、Playwright 本地烟测、文档结构校验和 diff 检查；归档 ExecPlan 并删除临时任务清单。

## 错误记录

| 错误 | 处理 |
|------|------|
