# Security

## 认证与授权

- 多租户架构：每个租户通过 `tenant_key` 隔离数据
- 用户角色：平台管理员（platform_admin）、租户管理员（tenant_admin）、普通员工（employee）
- 邀请码机制：新用户注册需验证邀请码，邀请码绑定租户和角色
- 认证路由：`/api/v1/auth/*`，包含租户创建、用户注册、登录认证、邀请码验证

## API 安全

- CORS：仅允许 `localhost:3000` 和 `localhost:5173`（开发环境）
- 请求追踪：asgi_correlation_id 中间件为每个请求分配唯一 ID
- 输入验证：所有 API 入参使用 Pydantic 模型校验，拒绝非法输入
- SQL 注入防护：使用 SQLAlchemy ORM，不拼接原始 SQL

## 数据安全

- 环境变量：敏感配置（数据库连接、API Key）通过 `.env` 文件管理，不提交到版本控制
- `.gitignore` 已排除 `.env*` 文件
- 多租户隔离：数据访问层强制 `tenant_key` 过滤，防止跨租户数据泄露

## 前端安全

- API 目标地址通过环境变量 `VITE_API_TARGET` 配置，不硬编码
- Mock 模式：`VITE_USE_MOCK=true` 时使用本地 mock 数据，避免开发阶段暴露真实 API

## LLM 服务安全

- LLM API Key 存储在 `api/config/llm_settings.json`，不提交到版本控制
- LLM 调用通过 `api/v1/services/llm_client.py` 统一封装，限制可用的 provider 和 model
- LLM 适配器模式：`api/v1/utils/llm_adapters.py` 隔离不同 LLM provider 的实现细节

## 部署安全

- Docker 部署：dev 和 prod 环境使用不同 Dockerfile 和 docker-compose 配置
- 生产环境 CORS 应限制为实际域名，不使用 localhost
- 数据库密码通过环境变量注入，不写入镜像
