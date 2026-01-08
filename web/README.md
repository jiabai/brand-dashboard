# 品牌分析仪表板 (Brand Analysis Dashboard)

一个基于 React 的现代化品牌分析仪表板，用于展示品牌提及率、模型提及率和相关数据参考表格。

## 技术栈

### 前端框架
- **React 18.2.0** - 使用最新的 React 特性，包括 Hooks 和并发特性
- **Vite 5.0.8** - 现代化的前端构建工具，提供快速的开发体验和优化后的生产构建

### UI 组件库
- **Radix UI** - 无样式的可访问性组件库
  - `@radix-ui/react-progress` - 进度条组件
  - `@radix-ui/react-slot` - 灵活的组合组件
- **shadcn/ui** - 基于 Radix UI 和 Tailwind CSS 的组件系统
  - 风格：New York
  - 支持暗色模式
  - 使用 CSS 变量进行主题定制

### 样式解决方案
- **Tailwind CSS 4.1.17** - 原子化 CSS 框架
  - 响应式设计
  - 自定义主题配置
  - CSS 变量集成
- **PostCSS** - CSS 转换工具
- **Autoprefixer** - 自动添加 CSS 前缀

### 动画与交互
- **tailwindcss-animate** - 为 Tailwind CSS 提供动画支持
- **Lucide React** - 现代化的图标库
- **class-variance-authority (CVA)** - 组件变体管理
- **clsx & tailwind-merge** - 条件类名和 Tailwind 类名合并工具

## 项目结构

```
web/
├── public/                 # 静态资源
├── src/
│   ├── components/        # React 组件
│   │   ├── ui/           # shadcn/ui 基础组件
│   │   │   ├── button.jsx
│   │   │   ├── card.jsx
│   │   │   ├── progress.jsx
│   │   │   └── table.jsx
│   │   ├── BrandMentionRate.jsx    # 品牌提及率组件
│   │   ├── ModelMentionRates.jsx   # 模型提及率组件
│   │   ├── ReferencesTable.jsx     # 参考数据表格
│   │   ├── TaskName.jsx            # 任务名称组件
│   │   ├── Sidebar.jsx             # 侧边栏组件
│   │   ├── GooeyNav.jsx            # 粘性导航组件
│   │   ├── Squares.jsx             # 背景动画
│   │   ├── ErrorBoundary.jsx       # 错误边界
│   │   ├── LoadingSpinner.jsx      # 加载动画
│   │   ├── EmptyState.jsx          # 空状态
│   │   ├── SpotlightCard.jsx       # 聚光灯卡片
│   │   └── TimeFilter.jsx          # 时间筛选器
│   ├── lib/
│   │   └── cn.js           # 类名合并工具
│   ├── styles/             # 组件特定样式
│   │   ├── brand-mention-rate.css
│   │   ├── model-mention-rates.css
│   │   └── references-table.css
│   ├── utils/
│   │   └── index.js        # 工具函数
│   ├── App.jsx             # 主应用组件
│   ├── App.css             # 应用样式
│   ├── index.css           # 全局样式
│   └── main.jsx            # 应用入口
├── mock/                   # Mock 数据
│   └── index.js
├── .env.local              # 环境变量
├── vite.config.js          # Vite 配置
├── tailwind.config.js      # Tailwind CSS 配置
├── components.json         # shadcn/ui 配置
├── postcss.config.js       # PostCSS 配置
├── jsconfig.json           # JavaScript 项目配置
└── package.json            # 项目依赖
```

## 技术方案

### 1. 组件化架构
- 采用函数式组件和 Hooks 模式
- 使用 Error Boundary 实现错误隔离
- 组件间通过 props 和回调函数通信

### 2. 状态管理
- 使用 React 内置的 `useState` 和 `useEffect` 进行本地状态管理
- 实现了加载状态、时间筛选和数据刷新等状态逻辑

### 3. 样式方案
- **原子化 CSS**：使用 Tailwind CSS 实现快速样式开发
- **主题系统**：通过 CSS 变量实现动态主题切换
- **响应式设计**：支持移动端、平板和桌面端布局

### 4. 路径别名配置
```javascript
// vite.config.js
resolve: {
  alias: {
    '@': fileURLToPath(new URL('./src', import.meta.url)),
    '@/components': fileURLToPath(new URL('./src/components', import.meta.url)),
    '@/lib': fileURLToPath(new URL('./src/lib', import.meta.url))
  }
}
```

### 5. API 集成方案
- 支持真实 API 和 Mock 数据两种模式
- 通过环境变量控制：
  - `VITE_USE_MOCK=true` - 使用 Mock 数据
  - `VITE_API_TARGET` - 指定后端 API 地址
- 开发环境自动代理 `/api` 请求到后端服务

### 6. 构建与部署
- **开发服务器**：`npm run dev` - 启动热重载开发服务器（端口 3000）
- **生产构建**：`npm run build` - 生成优化的生产版本
- **预览构建**：`npm run preview` - 预览生产构建结果
- **Docker 支持**：包含 Dockerfile 和 nginx.conf 用于容器化部署

### 7. 代码质量工具
- **Husky** - Git hooks 管理
- **Commitlint** - 提交信息规范化
- **ESLint** - 代码质量检查（通过 Vite 集成）
- **Prettier** - 代码格式化（通过 Vite 集成）

## 核心功能特性

### 1. 实时数据更新
- 自动更新当前时间显示
- 实时数据状态指示器
- 带动画效果的数据刷新

### 2. 交互式导航
- 侧边栏导航与布局
- 时间筛选器（昨天、过去7天、过去30天）
- 平滑的页面过渡动画

### 3. 数据可视化
- **BrandMentionRate** - 品牌提及率可视化
- **ModelMentionRates** - 多模型提及率对比
- **ReferencesTable** - 详细数据表格展示

### 4. 视觉效果
- **LoadingSpinner** 加载状态动画
- 响应式布局适配各种屏幕尺寸

## 环境配置

创建 `.env.local` 文件：

```env
# 使用 Mock 数据（开发模式）
VITE_USE_MOCK=true

# 后端 API 地址
VITE_API_TARGET=http://localhost:8000
```

## 快速开始

1. **安装依赖**
```bash
npm install
```

2. **启动开发服务器**
```bash
npm run dev
```

3. **构建生产版本**
```bash
npm run build
```

4. **预览生产版本**
```bash
npm run preview
```

## 浏览器支持

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- 支持 ES2020+ 特性的现代浏览器

## 开发注意事项

1. 组件开发遵循单一职责原则
2. 使用 TypeScript 风格的 PropTypes 注释
3. 保持组件的可复用性和可测试性
4. 遵循 React Hooks 最佳实践
5. 使用语义化的 HTML 标签

## 许可证

私有项目（Private）