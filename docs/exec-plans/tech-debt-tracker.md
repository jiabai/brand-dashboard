# Tech Debt Tracker

| Topic | Why it matters | Source | Removal Condition |
|------|----------------|--------|-------------------|
| 业务路由未消费登录 accessToken | 当前登录会签发 token，但 dashboard/config/executors/query-jobs/conversation 等业务路由仍主要依赖显式 tenant_key 或 executor key，缺少用户身份与租户成员关系校验 | 2026-05-17 API review | 引入 `get_current_user`/租户授权依赖，并覆盖所有敏感业务路由 |
| `api/config/llm_settings.json` 被 Git 跟踪 | LLM 配置文件容易承载 API Key，跟踪真实配置会增加密钥泄露风险 | 2026-05-17 API review | 改为提交 `.example` 模板，真实配置通过环境变量或未跟踪本地文件注入 |
| 数据库 engine 在 import 时创建 | 测试导入路由时会触发默认数据库连接，导致测试出现 ResourceWarning，也让依赖注入边界不够清晰 | 2026-05-17 API review | 将 engine 创建延迟到应用 lifespan 或显式 app factory，并让测试覆盖 dependency override |
