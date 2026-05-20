# 多租户管理与登录文档落实计划

## Goal
审阅并修正现有多租户架构、租户账号 API 参考、注册流程产品规格，随后按项目规范补齐可执行的 active plan 与 TASKS；在用户确认方案后，继续按 ExecPlan 落地多租户管理与登录功能。

## Phases
| Phase | Status | Purpose |
|---|---|---|
| 1. 初始化工作记忆 | complete | 建立本次任务的计划、发现、进度文件 |
| 2. 读取项目规范 | complete | 读取 AGENTS、ARCHITECTURE、SECURITY、WORKFLOW、执行门禁与现有任务 |
| 3. 审阅多租户文档 | complete | 检查多租户模型、认证授权、注册流程、API 契约是否满足 B2B SaaS |
| 4. 修改与补齐文档 | complete | 修正不一致、补齐安全边界、生成 active exec plan 与 TASKS |
| 5. 验证 | complete | 运行项目文档校验并记录结果 |
| 6. 后端认证与租户隔离 | complete | 标准 JWT、当前用户/租户依赖、平台管理员保护、租户路由保护、执行器 job scope |
| 7. 前端登录态 | complete | 登录页、AuthContext、本地 token、Authorization 与 X-Tenant-Key 注入、受保护路由 |
| 8. 全量验证与收尾 | complete | 后端/前端/文档门禁，更新 ExecPlan Outcomes |

## Decisions
- 第一阶段只做文档、计划、任务清单落地；用户确认“方案没问题”后进入代码实现。
- 用户已授权发现问题后直接修改文档，因此本轮不再停顿等待设计确认。
- 登录与租户隔离按 B2B SaaS 高风险面处理，优先要求服务端强制 tenant_key 与角色权限校验。
- 当前文档需要区分“现状可用注册 API”和“目标安全态”，避免把无鉴权路由误标为生产可用。
- 已选择用户身份与执行器身份分区：用户请求走 JWT + 租户上下文，执行器请求继续走 executor API Key + 任务绑定校验。

## Errors Encountered
| Error | Attempt | Resolution |
|---|---|---|
| 无 | 本轮未遇到阻塞性错误 | 文档结构验证通过 |

## Verification
- `$env:PYTHONPATH='.'; uv run --project api --extra dev pytest api/tests/ -q`：47 passed
- `uv run --project api ruff check api`：All checks passed
- `npm --prefix web test -- --test-reporter=spec`：35 passed
- `npm --prefix web run build`：通过
- `npm --prefix web run lint`：0 errors, 9 warnings（既有 warnings）
