# Tasks: 前端 URL 路由改造

## 进行中

（暂无）

## 待办

（暂无）

## 已完成

### Phase 1: 基础设施

- [x] 新增路由映射工具测试并确认先失败 ✅ `npm --prefix web test -- src/utils/__tests__/routing.test.js` 首次失败原因是目标实现缺失
- [x] 安装 react-router-dom 依赖 ✅ `npm --prefix web install react-router-dom@^6` 无报错，`package.json` 新增 `react-router-dom`
- [x] main.jsx 包裹 BrowserRouter ✅ `npm --prefix web run build` 构建通过

### Phase 2: 布局提取

- [x] 创建 useDashboardParams hook ✅ `npm --prefix web run build` 构建通过
- [x] 创建 DashboardLayout 组件（从 App.jsx 提取 Header + Sidebar + 时间筛选） ✅ `npm --prefix web run build` 构建通过
- [x] 创建 HomeView 薄包装组件 ✅ `npm --prefix web run build` 构建通过

### Phase 3: 路由替换

- [x] 重写 App.jsx 为 Routes 定义 ✅ `npm --prefix web run build` 构建通过
- [x] 修改 Sidebar.jsx 使用 useNavigate ✅ `npm --prefix web run build` 构建通过

### Phase 4: 组件清理

- [x] 修改 TrendAnalysis.jsx 去掉 getQueryParam 直接调用 ✅ `npm --prefix web run build` 构建通过
- [x] 修改 QueryJobStatus.jsx 改用 useSearchParams ✅ `npm --prefix web run build` 构建通过
- [x] 修改 CreateQueryJob.jsx 改用 useSearchParams ✅ `npm --prefix web run build` 构建通过

### Phase 5: 兼容与验证

- [x] 创建 LegacyRedirect 组件 ✅ `npm --prefix web run build` 构建通过
- [x] 路由映射单元测试 ✅ `npm --prefix web test -- src/utils/__tests__/routing.test.js` 通过
- [x] 构建验证 ✅ `npm --prefix web run build` 无 error
- [x] 浏览器手动验证：旧 URL 自动重定向 ✅ 访问 `/?view=home&tenant_key=...&job_id=...` 跳转到 `/dashboard/.../...`
- [x] 浏览器手动验证：侧边栏导航 ✅ 点击趋势分析和任务状态 URL 正确变化
- [x] 浏览器手动验证：时间筛选 ✅ 切换指定日期后 URL 查询参数同步，且无旧 `date`
- [x] 浏览器手动验证：平台下钻 ✅ 访问 `?platform=GPT-4` 后返回清除 `platform`
- [x] 浏览器手动验证：前进/后退 ✅ 浏览器导航按钮行为正确
