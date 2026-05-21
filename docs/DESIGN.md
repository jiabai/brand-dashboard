# Design

## UI 设计规范

- 组件库：shadcn/ui 源码组件为主，组件源码位于 `web/src/components/ui/`
- 图表：使用 React/SVG/CSS 原生组合实现轻量图表，不引入 G2 或第二套图表运行时
- 样式：Tailwind CSS v4 semantic tokens 优先，自定义 CSS 仅放 `web/src/styles/`
- 图标：Lucide React
- 布局：shadcn Sidebar + React 组件组合（Header + Sidebar + Content），响应式适配
- 主题：`web/src/index.css` 中的 CSS variables + Tailwind `@theme inline` 统一主题，支持暗色模式扩展
- 共享工具：条件 class 合并统一使用 `web/src/lib/cn.js`

## UI 视觉方向

- 风格：暖色浅底运营仪表板，参考 `DESIGN-TOKENS.md` 的 cream canvas、warm ink、coral primary 和 dark product surface，但不照搬营销页 hero、pricing 或 CTA band 结构
- 页面底色：默认使用 warm canvas，不使用深紫或紫蓝作为全局背景
- 主强调：coral 仅用于主操作、active 标记和少量关键状态，不大面积铺满业务卡片
- 深色 surface：仅用于侧栏、局部高对比模块或复杂数据承载区，不作为内容区默认背景
- 卡片：默认 8px 圆角、1px warm hairline border、低阴影或无阴影；禁止卡片套卡片
- 信息密度：仪表板首屏优先展示核心数据；空状态必须轻量，不能占据整屏视觉中心
- Typography：业务 UI 以清晰 sans-serif 层级为主，display serif 仅可作为少量品牌化标题试点，不用于表格、表单和密集数据
- 图表颜色：使用 warm ink、coral、teal、amber、success、warning、error 等 semantic/chart tokens，不回到单一紫色体系

## API 设计规范

- RESTful 风格，所有路由挂载 `/api/v1/` 前缀
- 请求/响应模型使用 Pydantic BaseModel，定义在 `api/v1/models/schemas.py`
- 错误响应统一使用 HTTPException + JSONResponse
- 分页参数：`page`, `page_size`
- 时间参数：`timeframe`（枚举：yesterday, 7days, 30days, specific_day）+ `start_date` / `end_date`（YYYYMMDD）；旧前端 `date` 参数仅用于兼容重定向，不再生成新 URL

## 数据模型规范

- 数据库：MySQL 8.x，InnoDB 引擎，utf8mb4 字符集
- ORM：SQLAlchemy 2.x，声明式映射
- 多租户：所有业务表包含 `tenant_key` 字段，查询时强制过滤
- Dashboard 展示粒度：Dashboard 查询和展示以 `tenant_key + job_id` 为最小单元；`job_id` 标识一次完整的 LLM 数据采集任务批次，同一租户的不同 Job 对应不同品类/品牌/时间段的采集数据，业务数据表（`qa_brand_state`、`qa_reference`、`llm_conversations`）按 `(tenant_key, job_id)` 联合过滤，前端路由 `/dashboard/:tenantKey/:jobId` 必须同时携带两者才能正确加载数据
- 时间字段：`created_at` 使用 `DEFAULT CURRENT_TIMESTAMP`，`updated_at` 使用 `ON UPDATE CURRENT_TIMESTAMP`
- 枚举字段：使用 MySQL ENUM 类型，在 Pydantic 中对应 Python Enum

## 前端状态管理

- 路由状态：`react-router-dom` 管理页面路径；`web/src/config/routes.js` 是路由、侧栏菜单和任务入口的单一配置源
- URL 参数：`useDashboardParams` 统一读取路径参数和查询参数，分析页路径携带 `tenantKey + jobId`，租户级页面路径携带 `tenantKey`
- 时间筛选：`useTimeframeManager` 管理 timeframe、可用日期、日期范围归一化和 URL 日期参数同步，`DashboardLayout.jsx` 只负责渲染布局控件
- 组件状态：各功能组件自管理局部状态
- 数据获取：业务组件通过 `web/src/api/` Adapter 调用后端端点，不在组件中手写 API URL；无全局状态库
- 配置：`web/src/config.js` 从环境变量读取，提供默认值
- 平台管理员入口：`/platform/tenants` 表格必须同时展示租户信息和 job 摘要；看板操作只在 active 租户且存在真实 `latestJob.jobId` 时启用，跳转时必须携带 `latestJob.brand` 作为 `brand` 查询参数，任务状态入口保留为完整 job 列表入口

## 命名约定

- 前端组件：PascalCase 文件名和组件名
- 前端变量/函数：camelCase
- 后端路由：snake_case URL 路径
- 后端模型：PascalCase 类名，snake_case 字段名
- CSS 类名：Tailwind 工具类为主，自定义类用 kebab-case
