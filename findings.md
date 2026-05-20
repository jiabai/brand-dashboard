# 多租户管理与登录文档发现记录

## Initial Repository Context
- 工作区已有 `AGENTS.md`、`WORKFLOW.md`、`TASKS.md` 与 docs 分层目录。
- 当前 git 状态包含用户已有改动：删除 `api/docs/TENANT_ACCOUNT_API_README.md`、删除一个中文注册流程说明文件，新增/修改 docs 下多租户相关文档。后续不回滚这些改动。
- 本次目标文件包括 `docs/ARCHITECTURE_MULTITENANT.md`、`docs/references/20260519-000000-tenant-account-api-reference.md`、`docs/product-specs/20260519-000000-multi-tenant-registration-flow.md`。

## Review Questions
- 多租户模型是否明确租户身份、账号身份、成员关系与角色边界？
- 登录态是否避免前端自报租户导致越权？
- 注册流程是否适合 to B 企业：企业创建、所有者账号、邀请码/成员加入、审核与幂等？
- API 参考是否覆盖认证、租户切换、错误码、审计、限流、测试用例？
- 执行计划是否能让后续实现者按最小闭环推进？

## Project Rules Read
- `AGENTS.md` 要求非平凡任务按 Spec -> ExecPlan -> Tasks -> 实现 -> 验证推进，且多租户业务查询必须带 `tenant_key`，数据层强制租户过滤。
- `WORKFLOW.md` 要求认证、权限、数据、安全边界变化必须进入 `docs/product-specs/` 与 `docs/exec-plans/active/`。
- `docs/EXECUTION_GATES.md` 要求 touched active ExecPlan 的 Progress、Decision Log、验证记录必须更新，并运行文档结构验证。
- `docs/SECURITY.md` 当前只写了基本认证/授权原则，需要与多租户登录目标态保持一致。

## Code Reality Check
- `api/v1/routes/auth.py` 已提供 `/api/v1/platform/tenants`、`/api/v1/public/auth/activate`、`/api/v1/public/users/verify-invite-code`、`/api/v1/public/users/register`、`/api/v1/public/auth/login`。
- `api/v1/repositories/auth.py` 已实现创建租户、激活管理员、员工注册、登录；访问令牌和激活令牌都使用 `api/v1/utils/security.py` 的自定义 `body.signature` HMAC 格式。
- `api/pyproject.toml` 当前没有 `PyJWT` 或 `python-jose` 依赖。
- `api/v1/routes/dashboard.py`、`query_jobs.py`、`conversation.py` 仍大量使用客户端传入的 `tenant_key`；`tenant_exists` 只校验租户存在，不校验当前用户是否属于该租户。
- `api/tests/test_auth.py` 覆盖了现有注册/登录 API 的基础响应，但尚未覆盖认证依赖、跨租户访问拒绝、平台操作员鉴权、JWT 标准格式。
- `api/v1/routes/query_jobs.py` 的执行器 `/fetch` 和 `/report` 有 `X-Executor-Key` 校验；但 `/load`、`/status` 仍只校验租户存在，不校验用户或平台权限。
- `api/v1/routes/executors.py` 的执行器创建、列表、禁用、注册接口当前无平台管理员鉴权；注册依赖 IP 白名单，仍需纳入平台管理安全边界。
- `web/src/components/AccountManagement.jsx` 当前把租户开通、管理员激活、员工注册、登录集中在账户管理页，适合作为管理工具雏形；后续正式登录态仍需独立受保护路由、auth context 和 API header 注入。

## Document Issues To Fix
- API 参考把激活令牌描述为 JWT，与现有自定义签名 token 不一致；应写为现状自定义 HMAC、目标态 access token 迁移标准 JWT。
- 角色命名需要统一：业务权限使用 `platform_admin`、`tenant_admin`、`tenant_member`，数据库关系表保持 `admin`、`member`、`viewer`，文档必须说明映射。
- 多租户上下文不能完全“从 token 推导 tenant_key”，因为一个用户可属于多个租户；目标应为“token 识别用户，目标租户由 path/header 显式选择，服务端校验 membership”。
- 平台路由必须明确生产禁用未鉴权创建租户，短期可以用白名单平台管理员，长期用 `platform_admins` 或平台成员关系。
- 执行器/数据加载属于机器到机器边界，不应简单套用用户 JWT；需要单独保留执行器 API Key 机制，并限制执行器可访问的租户/任务范围。
- 员工注册复用已有邮箱时需要防止撞库和越权，应要求统一错误信息、密码校验策略和审计记录。
