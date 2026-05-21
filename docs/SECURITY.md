# Security

## 认证与授权

- 多租户架构：每个租户通过 `tenant_key` 隔离数据
- 用户角色：平台管理员（platform_admin）、租户管理员（tenant_admin）、租户成员（tenant_member）、租户只读成员（tenant_viewer，预留）
- 邀请码机制：新用户注册需验证邀请码，邀请码绑定租户和角色
- 认证路由：`/api/v1/auth/*`，包含租户创建、用户注册、登录认证、邀请码验证
- 用户态受保护接口：必须校验 `Authorization: Bearer <access_token>`，并通过服务端依赖解析当前用户
- 租户上下文：前端传入的 `tenant_key` 或 `X-Tenant-Key` 只表示目标租户，后端必须校验 `user_tenants` 成员关系和角色；dashboard 读接口可额外接受平台管理员只读旁路
- 平台管理接口：`/api/v1/platform/*` 与执行器管理接口必须限制为 `platform_admin`
- 平台运营后台：`/platform/*` 不属于任何客户租户，不应发送 `X-Tenant-Key`；后端必须以 `require_platform_admin` 作为唯一授权入口
- 平台管理员 bootstrap：首个平台管理员只能通过本地/部署 CLI 初始化，不提供公开 HTTP API；CLI 不得输出或落盘明文密码
- 平台管理员 dashboard 只读：平台管理员可查看所有 active 租户 dashboard 数据，但不写入 `user_tenants`，也不获得租户内写权限
- 租户访问授权：非平台用户或需要真实租户 membership 的场景必须显式写入 `user_tenants`，本阶段只允许通过本地/部署 CLI 操作
- 执行器接口：机器身份使用 `executor_id` + `X-Executor-Key`，不得复用用户 JWT；写入结果时必须校验执行器、租户和 job 绑定

## API 安全

- CORS：仅允许 `localhost:3000` 和 `localhost:5173`（开发环境）
- 请求追踪：asgi_correlation_id 中间件为每个请求分配唯一 ID
- 输入验证：所有 API 入参使用 Pydantic 模型校验，拒绝非法输入
- SQL 注入防护：使用 SQLAlchemy ORM，不拼接原始 SQL
- Access Token：当前格式为标准 JWT，payload 只承载用户身份与有效期，不承载可授权的 `tenant_key`
- 登录失败：邮箱不存在、密码错误等场景应返回统一错误，避免账号枚举
- 速率限制：登录、邀请码验证、员工注册和激活接口上线前必须纳入限流计划

## 数据安全

- 环境变量：敏感配置（数据库连接、API Key）通过 `.env` 文件管理，不提交到版本控制
- `PLATFORM_ADMIN_EMAILS` 只保存平台管理员邮箱白名单；bootstrap 密码只能通过命令参数或进程环境变量传入，并以哈希入库
- `.gitignore` 已排除 `.env*` 文件
- 多租户隔离：数据访问层强制 `tenant_key` 过滤，防止跨租户数据泄露
- 导入租户补授权：非平台用户优先授予 `viewer`，仅在明确需要租户内代操作时授予 `admin`
- 平台只读访问：只允许 dashboard 查询，不允许复用到任务加载、成员管理、执行器写入或其他写接口
- 审计：创建租户、登录失败、激活失败、权限拒绝、执行器认证失败必须记录 request id、操作者、租户和结果，不记录密码、token 或 API Key

## 前端安全

- API 目标地址通过环境变量 `VITE_API_TARGET` 配置，不硬编码
- Mock 模式：`VITE_USE_MOCK=true` 时使用本地 mock 数据，避免开发阶段暴露真实 API
- 登录态：前端只能把 access token 用于 API Authorization；不能通过解码 JWT 自行判断租户授权结果
- 租户切换：前端从路由或当前租户选择注入 `X-Tenant-Key`，后端仍以 `user_tenants` 校验结果为准
- 平台 API：前端调用平台 API 时必须显式跳过租户 header，避免平台权限和租户权限混淆

## LLM 服务安全

- LLM API Key 存储在 `api/config/llm_settings.json`，不提交到版本控制
- LLM 调用通过 `api/v1/services/llm_client.py` 统一封装，限制可用的 provider 和 model
- LLM 适配器模式：`api/v1/utils/llm_adapters.py` 隔离不同 LLM provider 的实现细节

## 部署安全

- Docker 部署：dev 和 prod 环境使用不同 Dockerfile 和 docker-compose 配置
- 生产环境 CORS 应限制为实际域名，不使用 localhost
- 数据库密码通过环境变量注入，不写入镜像
