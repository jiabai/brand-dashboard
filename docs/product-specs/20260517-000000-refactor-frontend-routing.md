# 前端 URL 路由改造

## 背景

当前前端没有使用任何路由库，所有页面状态通过根路径 `/?view=home&tenant_key=...&job_id=...` 的查询参数驱动。`App.jsx` 同时承担路由分发、全局状态管理、URL 同步、日期逻辑、数据预加载等职责，已膨胀至 461 行。

核心问题：

1. **语义混乱**：路径（"是什么"）和查询参数（"怎么过滤"）职责不清，`view` 参数充当伪路由
2. **参数冗余**：`start_date` 和 `date` 同时存在，代码中 `start_date || date` 做 fallback
3. **跨层读 URL**：`TrendAnalysis`、`QueryJobStatus`、`CreateQueryJob` 既接收 props，又自己调用 `getQueryParam`，数据来源不一致
4. **可分享性差**：所有导航在同一路径上，用户无法直观感知当前页面位置
5. **无路由库**：`package.json` 中没有 `react-router-dom`，纯手工 query param 驱动

## 目标

1. 引入 `react-router-dom` v6，用路径路由替代 `view` 查询参数
2. 将 `tenantKey` 从查询参数提升为路径参数；分析类页面同时将 `jobId` 提升为路径参数（资源定位符）
3. 统一日期参数，去掉 `date` 冗余，只保留 `start_date` + `end_date`
4. 从 `App.jsx` 中提取 `DashboardLayout`，分离路由定义与布局逻辑
5. 创建 `useDashboardParams` hook，统一顶层参数读取方式，消除组件跨层读取旧 URL 参数
6. 旧 URL 自动重定向到新 URL，保证书签和分享链接不失效

## 非目标

- 不改变任何 API 调用逻辑或数据流
- 不改变任何组件的 UI 渲染
- 不引入状态管理库（Redux、Zustand 等）
- 不改变后端路由或 API 设计
- 不改变日期格式（保持 YYYYMMDD，与 API 一致）

## 使用场景

1. **用户通过书签访问**：旧 URL `/?view=home&tenant_key=tn_xxx&job_id=job_xxx` 自动跳转到 `/dashboard/tn_xxx/job_xxx`
2. **用户点击侧边栏导航**：点击"趋势分析"后 URL 变为 `/trend/tn_xxx/job_xxx`，页面正确渲染
3. **用户切换时间筛选**：选择"昨天"后 URL 查询参数更新为 `?timeframe=yesterday`，数据正确刷新
4. **用户分享链接**：复制 `/dashboard/tn_xxx/job_xxx?brand=QuickCEP&timeframe=specific_day&start_date=20260212&end_date=20260212` 给同事，对方打开后看到相同页面

## 路由矩阵

| 页面 | 新路径 | 说明 |
|------|--------|------|
| 首页 | `/dashboard/:tenantKey/:jobId` | 分析数据页，`jobId` 是资源定位符 |
| 趋势分析 | `/trend/:tenantKey/:jobId` | 分析数据页，`jobId` 是资源定位符 |
| 分平台分析 | `/platforms/:tenantKey/:jobId` | 分析数据页，`jobId` 是资源定位符 |
| 信源分析 | `/sources/:tenantKey/:jobId` | 分析数据页，`jobId` 是资源定位符 |
| 情感分析 | `/sentiment/:tenantKey/:jobId` | 分析数据页，`jobId` 是资源定位符 |
| 账户管理 | `/accounts/:tenantKey` | 租户级页面，不强制携带 `jobId` |
| 新建任务 | `/tasks/:tenantKey/new` | 租户级页面，`executor_id` 保留为查询参数 |
| 任务状态 | `/tasks/:tenantKey/status` | 租户级页面，`job_id` 保留为可选查询筛选 |

## 约束

- 必须兼容旧 URL（通过重定向），不破坏现有书签
- 必须保持 Ant Design 5.x + Tailwind CSS 技术栈不变
- 必须保持 `web/src/config.js` 的配置读取方式不变
- 必须保持 Vite 代理配置不变（`/api` → `localhost:8000`）
- 新增依赖仅限 `react-router-dom` v6，不引入额外子包
- 遵循项目命名约定：组件 PascalCase，变量 camelCase

## 验收标准

1. `npm --prefix web run build` 构建通过，无报错
2. 浏览器访问旧 URL `/?view=home&tenant_key=...&job_id=...` 自动跳转到新 URL
3. 点击侧边栏各菜单项，URL 正确变化，页面正确渲染
4. 切换时间筛选（yesterday / 7days / 30days / specific_day），URL 查询参数同步
5. 平台下钻（点击平台卡片），URL 出现 `?platform=xxx`，返回后清除
6. 浏览器前进/后退按钮行为正确
7. `date` 参数不再出现在任何新 URL 中
8. 任务状态页的 `job_id` 作为可选筛选查询参数保留，不作为租户级页面的路径段
