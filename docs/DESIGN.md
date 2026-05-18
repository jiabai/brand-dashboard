# Design

## UI 设计规范

- 组件库：shadcn/ui 源码组件为主，组件源码位于 `web/src/components/ui/`
- 图表：使用 React/SVG/CSS 原生组合实现轻量图表，不引入 G2 或第二套图表运行时
- 样式：Tailwind CSS v4 semantic tokens 优先，自定义 CSS 仅放 `web/src/styles/`
- 图标：Lucide React
- 布局：shadcn Sidebar + React 组件组合（Header + Sidebar + Content），响应式适配
- 主题：`web/src/index.css` 中的 CSS variables + Tailwind `@theme inline` 统一主题，支持暗色模式扩展
- 共享工具：条件 class 合并统一使用 `web/src/lib/cn.js`

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
- 时间字段：`created_at` 使用 `DEFAULT CURRENT_TIMESTAMP`，`updated_at` 使用 `ON UPDATE CURRENT_TIMESTAMP`
- 枚举字段：使用 MySQL ENUM 类型，在 Pydantic 中对应 Python Enum

## 前端状态管理

- 路由状态：`react-router-dom` 管理页面路径；`web/src/config/routes.js` 是路由、侧栏菜单和任务入口的单一配置源
- URL 参数：`useDashboardParams` 统一读取路径参数和查询参数，分析页路径携带 `tenantKey + jobId`，租户级页面路径携带 `tenantKey`
- 时间筛选：`useTimeframeManager` 管理 timeframe、可用日期、日期范围归一化和 URL 日期参数同步，`DashboardLayout.jsx` 只负责渲染布局控件
- 组件状态：各功能组件自管理局部状态
- 数据获取：业务组件通过 `web/src/api/` Adapter 调用后端端点，不在组件中手写 API URL；无全局状态库
- 配置：`web/src/config.js` 从环境变量读取，提供默认值

## 命名约定

- 前端组件：PascalCase 文件名和组件名
- 前端变量/函数：camelCase
- 后端路由：snake_case URL 路径
- 后端模型：PascalCase 类名，snake_case 字段名
- CSS 类名：Tailwind 工具类为主，自定义类用 kebab-case
