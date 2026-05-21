# 明察 InsightFlow — 产品需求文档 (PRD)

> 基于代码库现状审查生成 | 2026-05-10

---

## Problem Statement

品牌方在当今的 AI 时代面临一个全新的挑战：消费者越来越多地通过大语言模型平台（如 DeepSeek、豆包、通义千问、Kimi、元宝等）获取购买建议和产品信息，而非传统的搜索引擎。品牌在这些 AI 平台上的"被提及情况"——是否被推荐、以什么顺序被提及、引用了哪些信源——直接决定了消费者的购买决策，但品牌方缺乏系统性的手段来监控和量化这些 AI 平台上的品牌曝光。

具体痛点包括：
- **不可见性**：品牌不知道自己在 AI 回答中被提及的频率和排名
- **无竞品对标**：无法量化自身与竞品在 AI 平台上的声量差距
- **信源黑盒**：不知道 AI 平台引用了哪些网站/媒体来生成关于品牌的回答
- **趋势盲区**：无法追踪品牌在 AI 平台上的提及率随时间的变化趋势
- **多平台碎片化**：不同 AI 平台的数据分散，缺乏统一视图

## Solution

明察 InsightFlow 是一个 **AI 平台品牌监测与分析仪表板**，通过以下方式解决上述问题：

1. **自动化数据采集**：通过分布式执行器（Executors）定时向各大 AI 平台发送预设的消费者问题，采集 AI 回答内容及引用信源
2. **多维度指标计算**：基于采集数据自动计算品牌提及率、首位提及率、Top3 提及率、声量份额等关键指标
3. **可视化仪表板**：提供直观的图表界面，展示品牌排名、平台分布、趋势变化、信源分析
4. **多租户 SaaS 架构**：支持多个品牌客户独立使用，数据完全隔离
5. **LLM 辅助策略**：利用大模型生成品牌定位关键词和消费者问题，辅助品牌策略制定

---

## User Stories

### 租户与账户管理

1. As a 平台运营人员，I want 创建新租户并配置其行业、订阅计划、用户上限，so that 新客户可以快速入驻平台
2. As a 平台运营人员，I want 系统自动生成租户管理员激活链接，so that 租户管理员可以自助完成账号激活
3. As a 租户管理员，I want 生成邀请码并设置使用次数和有效期，so that 我可以安全地邀请团队成员加入
4. As a 新员工，I want 通过邀请码注册账号，so that 我可以加入所属租户并开始使用仪表板
5. As a 注册用户，I want 使用邮箱和密码登录系统，so that 我可以访问仪表板数据
6. As a 平台管理员，I want 查看和管理所有执行器（Executors）的状态，so that 我可以确保数据采集系统正常运行
7. As a 平台管理员，I want 禁用异常的執行器，so that 防止未授权的数据采集行为

### 任务管理与数据采集

8. As a 品牌运营人员，I want 创建查询任务（Query Job），指定目标品牌、竞品列表、关键词和消费者问题，so that 执行器可以按计划采集 AI 平台数据
9. As a 品牌运营人员，I want 设置任务的生效时间范围和总执行次数，so that 我可以控制数据采集的周期和频率
10. As a 品牌运营人员，I want 查看任务的执行状态（未生效/生效中/已完成/已失效），so that 我了解数据采集的进度
11. As a 执行器程序，I want 通过 API 拉取待执行的任务（Round-Robin 策略），so that 多个执行器可以协同工作避免重复
12. As a 执行器程序，I want 上报每次任务执行的结果，so that 系统可以追踪执行次数和进度
13. As a 执行器程序，I want 将采集到的 AI 对话内容和引用链接批量写入数据库，so that 仪表板可以基于最新数据进行分析

### 品牌总览仪表板

14. As a 品牌经理，I want 在首页看到目标品牌的总体提及率（环形进度图），so that 我可以快速了解品牌在 AI 平台上的整体表现
15. As a 品牌经理，I want 看到所有品牌的排名表（含提及率、首位提及率、Top3提及率、问题数、关键词覆盖数），so that 我可以对标竞品表现
16. As a 品牌经理，I want 看到各 AI 平台对目标品牌的提及率分布，so that 我了解品牌在不同平台上的表现差异
17. As a 品牌经理，I want 点击某个平台卡片后进入该平台的详细品牌排名，so that 我可以深入分析特定平台上的竞争格局
18. As a 品牌经理，I want 看到品牌声量份额表（Brand Share of Voice），含各品牌在不同平台上的提及率矩阵，so that 我可以全面对比多品牌多平台的声量分布
19. As a 品牌经理，I want 看到引用域名分布表（含域名、中文名称、引用次数、引用率、关键词覆盖、平台覆盖），so that 我了解 AI 回答引用了哪些信源

### 趋势分析

20. As a 品牌经理，I want 查看品牌在指定平台和关键词下的每日提及率趋势图（柱状图+折线图），so that 我可以发现品牌声量的变化规律
21. As a 品牌经理，I want 通过选择不同关键词来切换趋势图的展示维度，so that 我可以分析不同话题对品牌提及率的影响
22. As a 品牌经理，I want 查看趋势图中的关键统计指标（平均提及率、最高/最低值及对应日期），so that 我可以快速获取趋势摘要

### 信源分析

23. As a 品牌经理，I want 查看引用信源的内容类型分布（新闻、科技评测、政府报告等）的堆叠条形图，so that 我了解 AI 回答引用了什么类型的信源
24. As a 品牌经理，I want 查看各引用域名的详细列表（含域名、引用次数、引用率、信源类型），so that 我可以评估信源的质量和权威性
25. As a 品牌经理，I want 通过关键词筛选信源分析结果，so that 我可以聚焦特定话题的信源分布
26. As a 品牌经理，I want 导出信源分析数据，so that 我可以用于进一步的报告和分析

### 情感分析

27. As a 品牌经理，I want 查看 AI 回答中关于品牌的情感倾向分布（正面/负面/中性环形图），so that 我了解品牌在 AI 平台上的舆论风向
28. As a 品牌经理，I want 查看具体的情感分析样本（含内容、情感标签、平台、日期），so that 我可以深入了解具体的情感表达

### 品牌策略辅助

29. As a 品牌策略师，I want 输入行业和品牌名称，让 LLM 自动生成 5 个标准化定位关键词，so that 我可以获得数据驱动的品牌定位建议
30. As a 品牌策略师，I want 基于定位关键词让 LLM 生成消费者可能提出的购买前问题，so that 我可以预判消费者关注点并优化品牌传播策略

### 通用交互

31. As a 仪表板用户，I want 通过时间筛选器切换"昨天/过去7天/过去30天/指定日期"的数据范围，so that 我可以灵活查看不同时间段的品牌表现
32. As a 仪表板用户，I want 通过侧边栏导航在不同分析页面之间切换，so that 我可以快速访问所需的分析视图
33. As a 仪表板用户，I want 在数据加载时看到加载动画，so that 我知道系统正在处理请求
34. As a 仪表板用户，I want 在数据为空或加载失败时看到友好的提示信息，so that 我不会因为空白页面而感到困惑
35. As a 仪表板用户，I want URL 参数自动同步当前的筛选状态（时间范围、租户、任务、品牌等），so that 我可以分享带有特定筛选条件的页面链接

---

## Implementation Decisions

### 架构决策

- **前后端分离**：前端 React SPA 通过 REST API 与后端 FastAPI 通信，不跨层直接访问数据库
- **API 版本化**：所有路由挂载在 `/api/v1/` 前缀下，为未来 API 演进预留空间
- **多租户数据隔离**：所有业务表包含 `tenant_key` 字段，数据访问层强制租户过滤，防止跨租户数据泄露
- **Dashboard 展示粒度**：Dashboard 以 `tenant_key + job_id` 为最小查询和展示单元；`job_id` 标识一次完整的 LLM 数据采集任务批次，同一租户可有多个 Job（不同品类/品牌/时间段），业务数据表按 `(tenant_key, job_id)` 联合过滤，前端路由 `/dashboard/:tenantKey/:jobId` 必须同时携带两者
- **分层依赖方向**：Routes → Services → Repositories → Models，禁止反向依赖
- **组件懒加载**：前端功能组件使用 `React.lazy()` 按需加载，优化首屏性能

### 模块设计

| 模块 | 职责 | 接口 |
|------|------|------|
| Dashboard Service | 仪表板核心业务逻辑，封装数据查询、转换和指标计算 | `get_brand_mention_rate()`, `get_platform_mention_rates()`, `get_brand_mention_trend()`, `get_citation_url_stats()`, `get_citation_type_stats()`, `get_domain_citation_rate()`, `get_brand_metrics()`, `get_platform_metrics_by_brand()`, `get_filter_metadata()`, `get_available_dates()` |
| LLM Client | 统一封装 LLM 服务调用，支持多 provider 适配 | `generate_positioning_keywords()`, `generate_consumer_questions()` |
| Auth Repository | 多租户认证与用户管理 | `create_tenant_with_admin()`, `activate_admin_account()`, `verify_invite_code()`, `register_employee()`, `authenticate_user()` |
| Query Jobs Router | 任务生命周期管理（创建、拉取、上报、状态同步） | `load_query_jobs()`, `fetch_query_job()`, `report_query_job()`, `get_job_status()` |
| Conversation Router | 对话数据批量入库 | `load_conversations()` |
| Executor Router | 执行器注册、管理与身份验证 | `create_executor()`, `register_executor()`, `list_executors()`, `deactivate_executor()` |
| URL Domain Resolver | URL 域名提取与内容类型推断 | `extract_domain_from_url()`, `infer_content_type()` |
| Date Range Utility | 时间范围计算 | `get_date_range()` |

### 数据模型

核心业务表：
- `tenants` — 租户信息（含行业、订阅计划、合同周期）
- `users` — 用户账号（邮箱、密码哈希、状态）
- `user_tenants` — 用户-租户多对多关系（含角色）
- `invitation_codes` — 邀请码（含使用次数、过期时间）
- `llm_query_jobs` — 查询任务（含品牌、竞品、关键词、消费者问题、执行计划）；每个 Job 通过 `job_id` 标识一次完整的采集批次，同一租户可有多个 Job，Dashboard 按 `(tenant_key, job_id)` 展示数据
- `executors` — 执行器（含 IP 地址、API Key、状态）
- `llm_conversations` — AI 对话内容（含平台、品牌、关键词、问答内容）
- `llm_conversation_references` — 对话引用链接（含 URL、域名、站点名称、内容类型）
- `qa_brand_state` — 品牌提及状态明细（含 is_mentioned, is_first_mentioned, is_top3_mentioned）

### API 契约

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/v1/dashboard/brand-mention-rate` | GET | 品牌总提及率 |
| `/api/v1/dashboard/platform-mention-rates` | GET | 品牌分平台提及率 |
| `/api/v1/dashboard/brand-mention-trend` | GET | 品牌提及率日趋势 |
| `/api/v1/dashboard/brand-metrics` | GET | 品牌总指标（多品牌排名） |
| `/api/v1/dashboard/platform-metrics-by-brand` | GET | 品牌分平台指标 |
| `/api/v1/dashboard/citation-url-stats` | GET | 引用 URL 统计 |
| `/api/v1/dashboard/citation-type-stats` | GET | 引用内容类型统计 |
| `/api/v1/dashboard/citation-domain-stats` | GET | 域名引用率分布 |
| `/api/v1/dashboard/citation-domain-summary` | GET | 域名引用汇总 |
| `/api/v1/dashboard/filter-metadata` | GET | 筛选器元数据 |
| `/api/v1/dashboard/available-dates` | GET | 可用日期列表 |
| `/api/v1/platform/tenants` | GET | 平台租户列表（含 job 摘要：jobCount、activeJobCount、latestJob） |
| `/api/v1/platform/tenants` | POST | 创建租户 |
| `/api/v1/public/auth/activate` | POST | 激活管理员账号 |
| `/api/v1/public/auth/login` | POST | 用户登录 |
| `/api/v1/public/users/verify-invite-code` | POST | 验证邀请码 |
| `/api/v1/public/users/register` | POST | 员工注册 |
| `/api/v1/query-jobs/load` | POST | 加载查询任务 |
| `/api/v1/query-jobs/fetch` | GET | 执行器拉取任务 |
| `/api/v1/query-jobs/report` | POST | 执行器上报结果 |
| `/api/v1/query-jobs/status` | GET | 查询任务状态 |
| `/api/v1/executors/` | GET/POST/DELETE | 执行器管理 |
| `/api/v1/executors/register` | POST | 执行器注册 |
| `/api/v1/conversation/load` | POST | 对话数据入库 |
| `/api/v1/analysis/positioning-keywords` | POST | LLM 生成定位关键词 |
| `/api/v1/analysis/consumer-questions` | POST | LLM 生成消费者问题 |

### 前端状态管理

- 全局状态由 `App.jsx` 管理：当前视图、时间筛选、平台选择、租户/任务/品牌参数
- URL 查询参数作为状态持久化机制，支持链接分享
- 各功能组件自管理局部状态（加载、错误、数据）
- 无全局状态库，直接使用 fetch API 获取数据

### 安全设计

- 执行器身份验证：通过 `X-Executor-Key` Header + `executor_id` 双重校验
- 执行器注册：基于 IP 地址白名单机制
- API Key 使用 `hmac.compare_digest` 防时序攻击
- CORS 白名单限制允许的来源域名
- 邀请码机制控制用户注册
- 密码使用哈希存储

---

## Testing Decisions

### 测试原则

- 只测试外部行为，不测试实现细节
- 优先测试数据访问层（Repository）的 SQL 查询正确性
- 优先测试 API 路由的请求/响应契约
- 前端工具函数（utils）应进行单元测试

### 已有测试覆盖

| 测试文件 | 覆盖范围 |
|----------|----------|
| `api/tests/test_auth.py` | 认证流程（租户创建、用户注册、登录） |
| `api/tests/test_dashboard_locf.py` | 仪表板指标计算 |
| `api/tests/test_keyword_platform_brand_rates.py` | 关键词-平台-品牌提及率 |
| `web/src/utils/__tests__/domainCitationQuery.test.js` | 域名引用查询参数构建 |
| `web/src/utils/__tests__/sourceAnalysis.test.js` | 信源分析数据标准化 |
| `web/src/utils/__tests__/trendChartConfig.test.js` | 趋势图配置 |

### 建议补充测试

- Dashboard Service 各方法的单元测试（mock engine）
- 前端组件的关键交互测试
- 执行器认证流程的集成测试
- 多租户数据隔离的安全测试

---

## Out of Scope

以下功能在当前代码库中尚未实现或仅为占位：

- **问答快照页面**：侧边栏中标记为 `disabled`，尚未开发
- **品牌设置页面**：侧边栏中标记为 `disabled`，尚未开发
- **订阅管理**：侧边栏中标记为 `disabled`，尚未开发
- **情感分析真实数据**：当前使用 Mock 数据，未接入真实数据源
- **分析结果持久化**：`/api/v1/analysis/results/{result_id}` 和 `/api/v1/analysis/history` 返回 501 Not Implemented
- **用户权限分级展示**：前端未根据用户角色（admin/member/viewer）差异化展示功能
- **数据导出**：信源分析页面有导出按钮但功能未完整实现
- **告警/通知**：品牌提及率异常变化时无自动告警机制
- **移动端适配**：当前仪表板主要面向桌面端设计

---

## Further Notes

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端框架 | React 18 + Vite |
| UI 组件库 | Ant Design 5.x + Radix UI |
| 图表 | @antv/g2 |
| 样式 | Tailwind CSS |
| 后端框架 | FastAPI (Python) |
| ORM | SQLAlchemy 2.x |
| 数据库 | MySQL 8.x (InnoDB, utf8mb4) |
| LLM 集成 | 智谱 AI (GLM-4.6)，支持适配器扩展 |
| 部署 | Docker + docker-compose |

### 支持的 AI 平台

当前系统监控以下中国主流 AI 大模型平台：
- DeepSeek
- 豆包 (Doubao)
- 通义千问 (Qwen)
- Kimi
- 元宝 (Yuanbao)
- 夸克 (Quark)
- 文心一言

### 关键指标计算口径

- **提及率 (mention_rate)**：`SUM(is_mentioned) / COUNT(DISTINCT conversation_id)` — 品牌在对话中被提及的比例
- **首位提及率 (first_mention_rate)**：`SUM(is_first_mentioned) / COUNT(DISTINCT conversation_id)` — 品牌作为首个被提及品牌的比例
- **Top3 提及率 (top3_mention_rate)**：`SUM(is_top3_mentioned) / COUNT(DISTINCT conversation_id)` — 品牌在前3个被提及品牌中的比例
- **域名引用率 (domain_citation_rate)**：某域名被引用次数 / 总引用次数 × 100%
- **关键词覆盖数 (keyword_coverage)**：品牌被提及时覆盖的去重关键词数量

### 项目命名

- 中文名：**明察**
- 英文名：**InsightFlow**
- 标语：监控 · 分析 · 报告
