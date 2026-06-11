# 租户加入团队入口收敛 ExecPlan

## 目标

将项目工作台中的“账户管理”入口收敛为租户侧“加入团队”，并在平台管理员只读客户视角下隐藏该入口。

## 范围

- 更新 `accounts` 路由的侧边栏文案。
- 侧边栏根据 `isPlatformReadonlyTenantAccess` 过滤租户加入入口。
- 收敛 `AccountManagement` 页面：移除登录辅助和租户开通 tab，保留邀请码核验和员工注册。
- 同步产品规格、核心文档、changelog 和测试。

## 非目标

- 不实现成员管理 CRUD。
- 不新增后端接口。
- 不改变公开登录、注册或激活 API。
- 不调整平台后台租户管理页面。

## 任务拆解

| Task | 状态 | 验收 |
|------|------|------|
| 建立任务和门控 | complete | `TASKS.md` 和本 ExecPlan 可见 |
| 文档规格 | complete | 产品规格明确“加入团队”边界 |
| 失败测试 | complete | Sidebar、AccountManagement、routes 测试先失败 |
| 前端实现 | complete | 定向测试通过 |
| 文档同步 | complete | 核心文档和 changelog 更新 |
| 验证归档 | complete | 门控通过，ExecPlan 移入 completed，临时任务清单删除 |

## 决策记录

| 决策 | 原因 |
|------|------|
| 保留 `/accounts/:tenantKey` 路径 | 避免破坏历史链接和路由配置，只调整产品语义。 |
| 侧边栏文案改为“加入团队” | 当前页面没有成员管理能力，“账户管理”会过度承诺。 |
| 平台只读客户视角隐藏入口 | 平台管理员不是租户成员代理，不应进入客户租户注册/账户流程。 |
| 移除登录辅助表单 | 登录后的工作台不应再次调用公开登录 API；登录应在 `/login` 完成。 |

## 验证计划

| Gate | 命令 | 状态 |
|------|------|------|
| 前端定向测试 | `npm --prefix web test -- src/components/__tests__/Sidebar.test.js src/components/__tests__/AccountManagement.test.js src/config/__tests__/routes.test.js` | passed, 9/9 |
| 前端全量测试 | `npm --prefix web test` | passed, 109/109 |
| 前端构建 | `npm --prefix web run build` | passed |
| 浏览器烟测 | Playwright local smoke: 租户成员显示加入团队，平台只读隐藏加入团队 | passed |
| 文档结构 | `python scripts/validate_agents_docs.py --level ERROR` | passed |
| Diff 检查 | `git diff --check` | passed，仅 CRLF 提示 |

## 进度记录

- 2026-06-09：用户确认按推荐执行；创建任务清单、产品规格和 active ExecPlan。
- 2026-06-09：新增 Sidebar、AccountManagement 和 routes 红灯测试；定向测试确认 5 个断言因现有实现不符而失败。
- 2026-06-09：更新路由文案、侧栏平台只读过滤和加入团队页面；定向测试 9/9 通过。
- 2026-06-09：同步核心文档、参考文档和产品规格索引；文档结构校验 0 错误。
- 2026-06-09：完成全量前端测试、生产构建、Playwright 本地烟测、文档结构校验和 diff 检查；归档 ExecPlan 并删除临时任务清单。

## 错误记录

| 错误 | 处理 |
|------|------|
| Playwright smoke 初次使用 `**/api/**` 误拦截前端 `/src/api/*` 模块，导致页面脚本被 JSON 响应替换 | 将兜底拦截收窄为 `**/api/v1/**` |
| Playwright 通配 `/api/v1/**` 注册顺序覆盖了 `/api/v1/auth/me`，导致登录态刷新为空并跳回登录页 | 先注册通配兜底，再注册 projects 和 auth/me 特例 |
