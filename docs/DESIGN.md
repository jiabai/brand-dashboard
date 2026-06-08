# Design

## UI 设计规范

- 组件库：使用 shadcn/ui 源码组件，组件源码位于 `web/src/components/ui/`。
- 图标：使用 Lucide React，按钮中的工具类动作优先使用图标加简短文本。
- 样式：Tailwind CSS v4 semantic tokens 优先，自定义 CSS 仅放 `web/src/styles/`。
- 图表：使用 React/SVG/CSS 原生组合实现轻量图表，不引入第二套大型图表运行时。
- 布局：租户工作台使用 shadcn Sidebar + Header + Content；平台后台使用独立 Platform Layout。
- 共享工具：条件 class 合并统一使用 `web/src/lib/cn.js`。

## UI 视觉方向

- 风格：暖色浅底、运营工具型界面，强调扫描效率和稳定信息层级。
- 页面主流程：租户默认进入“监测项目”，再进入项目详情、数据质量、报告等项目上下文页面。
- 侧边栏：主导航只展示当前主流程入口，不展示 legacy dashboard/task 排障路由。
- 页面底色：默认使用 warm canvas，不使用深紫或紫蓝作为全局背景。
- 主强调：coral 仅用于主操作、active 标记和少量关键状态。
- 卡片：默认 8px 圆角、1px warm hairline border、低阴影或无阴影；避免卡片套卡片。
- 信息密度：仪表板和项目页首屏优先展示关键业务状态；空状态保持轻量，不占据整屏视觉中心。
- Typography：业务 UI 使用清晰 sans-serif 层级；密集表格、表单和状态面板不使用展示型字体。
- 图表颜色：使用 warm ink、coral、teal、amber、success、warning、error 等 semantic/chart tokens，避免单一紫色体系。

## API 设计规范

- RESTful 风格，所有路由挂载 `/api/v1/` 前缀。
- 请求/响应模型使用 Pydantic BaseModel，定义在 `api/v1/models/schemas.py`。
- 业务 API 按领域聚合：`projects`、`collection-tasks`、`collection-attempts`、`analysis-runs`、`dashboard`、`query-jobs`、`platform`。
- 项目 API 不从请求体接收 `tenant_key`；租户上下文由认证依赖解析后传入 Service/Repository。
- 错误响应使用 HTTPException 或统一 JSONResponse。
- 分页参数使用 `page`、`page_size` 或 `limit`、`offset`，具体以 API 契约为准。
- 时间参数使用 `timeframe`（`yesterday`、`7days`、`30days`、`specific_day`）+ `start_date` / `end_date`（YYYYMMDD）；旧 `date` 参数仅用于兼容。
- Legacy dashboard API 仍以 `tenant_key + job_id` 查询，但新项目读面优先以 `tenant_key + project_id` 查询。

## 数据模型规范

- 数据库：MySQL 8.x，InnoDB 引擎，utf8mb4 字符集；测试兼容 SQLite。
- ORM：SQLAlchemy 2.x，Repository 可使用 ORM 或参数化 `text()` 查询。
- 多租户：所有业务表包含 `tenant_key` 字段，所有业务查询强制过滤。
- 项目主线：`monitoring_projects.project_id` 是租户内长期监测业务主键，项目下挂品牌、问题集、采集批次、分析运行、指标、告警、报告和数据质量读面。
- 采集生命周期：`collection_jobs` 表示采集批次，`collection_tasks` 表示可领取任务，`collection_attempts` 表示执行尝试和失败重试。
- 兼容 job：旧 `llm_query_jobs.job_id` 仍作为 legacy dashboard/task 查询键；通过 `collection_jobs.source_job_id` 与新采集批次桥接。
- 原始数据：兼容期继续使用 `llm_conversations` 和 `llm_conversation_references` 保存回答与引用。
- 分析血缘：`analysis_runs` 记录状态、错误、插件版本和项目/采集批次；事实表中的 `analysis_run_id` 可追溯重算来源。
- 指标快照：`metric_snapshots` 是 dashboard、报告、告警和质量页优先读取的稳定 read model，必须记录指标口径版本、覆盖率和生成时间。
- 洞察交付：`alert_rules` / `alert_events` 记录可去重的异常事件，`generated_reports` 保存报告 JSON 快照。
- 时间字段：`created_at` 使用 `DEFAULT CURRENT_TIMESTAMP`，`updated_at` 使用 `ON UPDATE CURRENT_TIMESTAMP` 或应用侧等效更新。

## 前端状态管理

- 路由状态：`react-router-dom` 管理页面路径；`web/src/config/routes.js` 是路由、菜单和 legacy 入口的单一配置源。
- 默认路由：租户用户默认进入 `projects`，未知租户路径回退到项目列表；平台管理员默认进入 `/platform/tenants`。
- URL 参数：`useDashboardParams` 统一读取路径参数和查询参数；项目页使用 `tenantKey/projectId`，legacy 分析页使用 `tenantKey/jobId`。
- 时间筛选：`useTimeframeManager` 管理 dashboard 兼容页的 timeframe、可用日期和 URL 日期参数同步。
- 数据获取：业务组件通过 `web/src/api/` Adapter 调用后端端点，不在组件中手写 API URL。
- 组件状态：页面组件自管理局部 loading、feedback、filter 和 retry 状态，不引入全局状态库。
- 平台管理员入口：`/platform/tenants` 与 `/platform/executors` 独立于租户工作台；平台 API 调用必须跳过租户 header。

## 命名约定

- 前端组件：PascalCase 文件名和组件名。
- 前端变量/函数：camelCase。
- 后端路由：snake_case URL 路径，业务资源使用复数或清晰领域名。
- 后端模型：PascalCase 类名，snake_case 字段名。
- CSS 类名：Tailwind 工具类为主，自定义类使用 kebab-case。
