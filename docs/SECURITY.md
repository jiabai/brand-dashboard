# Security

## 认证与授权

- 多租户架构：每个租户通过 `tenant_key` 隔离数据。
- 用户角色：平台管理员（platform_admin）、租户管理员（tenant_admin）、租户成员（tenant_member）、租户只读成员（tenant_viewer，预留）。
- 邀请码机制：新用户注册需验证邀请码，邀请码绑定租户和角色。
- 认证与账户路由：公开登录/激活/注册使用 `/api/v1/public/auth/*` 和 `/api/v1/public/users/*`；当前用户使用 `/api/v1/auth/me`；租户创建使用平台域 `/api/v1/platform/tenants`。
- 用户态受保护接口：必须校验 `Authorization: Bearer <access_token>`，并通过服务端依赖解析当前用户。
- 租户上下文：前端传入的 `tenant_key` 或 `X-Tenant-Key` 只表示目标租户，后端必须校验 `user_tenants` 成员关系和角色。
- 项目权限：项目、报告、告警、数据质量等项目 API 必须先校验当前租户，再按 `tenant_key + project_id` 查询。
- Legacy dashboard 读接口：兼容期可接受 `tenant_key + job_id`，但仍必须经过用户认证、租户授权和 Repository 租户过滤；平台管理员只读旁路只允许读接口。
- 平台管理接口：`/api/v1/platform/*` 与执行器管理接口必须限制为 `platform_admin`。
- 平台运营后台：`/platform/*` 不属于任何客户租户，不应发送 `X-Tenant-Key`；后端必须以 `require_platform_admin` 作为授权入口。
- 平台管理员 bootstrap：首个平台管理员只能通过本地/部署 CLI 初始化，不提供公开 HTTP API；CLI 不得输出或落盘明文密码。
- 租户访问授权：非平台用户或需要真实租户 membership 的场景必须显式写入 `user_tenants`，本阶段只允许通过本地/部署 CLI 操作。
- 执行器接口：机器身份使用 `executor_id` + `X-Executor-Key`，不得复用用户 JWT；执行器只能领取或上报与自身和租户匹配的采集任务。

## API 安全

- CORS：开发环境默认允许 `localhost:3000` 和 `localhost:5173`；生产环境必须使用实际域名配置。
- 请求追踪：asgi_correlation_id 中间件为每个请求分配唯一 ID。
- 输入验证：所有 API 入参使用 Pydantic 模型校验，拒绝非法输入。
- SQL 注入防护：使用 SQLAlchemy ORM 或 `text()` 参数化查询；动态 SQL 只允许白名单结构片段，不得拼接用户输入。
- Access Token：标准 JWT payload 只承载用户身份与有效期，不承载可授权的 `tenant_key`。
- 登录失败：邮箱不存在、密码错误等场景应返回统一错误，避免账号枚举。
- 重算与 retry：analysis retry 必须校验原 analysis run 属于当前租户和项目血缘，不能让客户端指定跨租户运行。
- 报告生成：报告 API 只能读取当前租户、当前项目下的分析事实聚合指标和告警事件，不能接受客户端传入任意指标 JSON 作为可信数据。
- 数据质量：数据质量 API 必须使用 `tenant_key + project_id` 查询失败采集、过期分析和分析事实覆盖率，不能按裸 `project_id` 聚合。
- 速率限制：登录、邀请码验证、员工注册、激活、忘记密码、重置密码、报告生成和重算类接口上线前必须纳入限流计划；忘记密码接口已内置按邮箱 60 秒进程级冷却。
- 已知局限：忘记密码接口同步发送 SMTP 邮件，命中 active 账号的首次请求存在可测量的时延差（计时侧信道）；响应体已全路径一致，发送异步化列为未来增强。

## 数据安全

- 环境变量：敏感配置（数据库连接、API Key）通过 `.env` 文件或部署环境变量管理，不提交到版本控制。
- `PLATFORM_ADMIN_EMAILS` 只保存平台管理员邮箱白名单；bootstrap 密码只能通过命令参数或进程环境变量传入，并以哈希入库。
- `.gitignore` 已排除 `.env*` 文件。
- 多租户隔离：数据访问层强制 `tenant_key` 过滤，防止跨租户数据泄露。
- 项目数据隔离：项目相关查询必须同时过滤 `tenant_key` 和 `project_id`；旧兼容 job 查询必须过滤 `tenant_key` 和 `job_id`。
- 分析血缘：事实表、告警和报告必须保留 `analysis_run_id`、`collection_job_id` 或项目血缘，便于审计和重算。
- 导入租户补授权：非平台用户优先授予 `viewer`，仅在明确需要租户内代操作时授予 `admin`。
- 平台只读访问：只允许 dashboard 查询，不允许复用到任务加载、成员管理、执行器写入、项目配置写入或其他租户写接口。
- 审计：创建租户、登录失败、激活失败、权限拒绝、执行器认证失败、报告生成和分析 retry 应记录 request id、操作者、租户、项目和结果，不记录密码、token 或 API Key。

## 前端安全

- API 目标地址通过环境变量 `VITE_API_TARGET` 配置，不硬编码。
- Mock 模式：`VITE_USE_MOCK=true` 时仅使用本地 mock 数据，避免开发阶段暴露真实 API。
- 登录态：前端只能把 access token 用于 API Authorization；不能通过解码 JWT 自行判断租户授权结果。
- 租户切换：前端从路由或当前租户选择注入 `X-Tenant-Key`，后端仍以 `user_tenants` 校验结果为准。
- 项目路由：`/projects/:tenantKey/:projectId` 中的 `tenantKey/projectId` 只用于导航和请求参数，不能作为授权依据。
- Legacy 路由：旧 dashboard/task 路由仍可直接访问，但不在主导航中暴露；访问时仍必须带登录态和租户上下文。
- 平台 API：前端调用平台 API 时必须显式跳过租户 header，避免平台权限和租户权限混淆。

## LLM 与分析安全

- LLM API Key 存储在本地或部署配置中，不提交到版本控制。
- LLM 调用通过 `api/v1/services/llm_client.py` 或分析插件适配层统一封装，限制可用 provider 和 model。
- 分析插件写库必须通过系统分析运行服务绑定 `tenant_key`、`project_id`、`collection_job_id` 和 `analysis_run_id`。
- 分析失败和 stale run 可重试，但不得覆盖原失败运行的审计信息。

## 部署安全

- Docker 部署：dev 和 prod 环境使用不同 Dockerfile 和 docker-compose 配置。
- 生产环境 CORS 应限制为实际域名，不使用 localhost。
- 数据库密码和 LLM Key 通过环境变量或密钥管理系统注入，不写入镜像。
- 生产环境应开启 HTTPS、访问日志、错误审计和基础限流。
