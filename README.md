# 品牌分析仪表板

一个现代化的 React 仪表板应用，用于展示品牌分析数据和统计信息。

## 功能特性

- 📊 **实时数据展示** - 显示品牌提及率、AI 模型使用率等关键指标
- ⏱️ **时间筛选** - 支持昨天、过去7天、过去30天的时间范围选择
- 📈 **可视化图表** - 环形进度图、进度条等多种数据可视化方式
- 🎨 **现代化设计** - 采用渐变色彩和毛玻璃效果的现代 UI 设计
- 📱 **响应式布局** - 完美适配桌面和移动设备
- 🛡️ **错误处理** - 完善的错误边界和加载状态管理

## 技术栈

- **React 18.2.0** - 现代 React 函数组件和 Hooks
- **Vite 5.0.8** - 快速的构建工具
- **CSS3** - 使用 CSS 变量和现代 CSS 特性
- **PropTypes** - 类型检查和组件文档

## 项目结构

```
src/
├── components/          # 组件目录
│   ├── BrandMentionRate.jsx      # 品牌提及率组件
│   ├── ModelMentionRates.jsx     # AI模型提及率组件
│   ├── ReferencesTable.jsx       # 参考数据表格
│   ├── TimeFilter.jsx            # 时间筛选器
│   ├── ErrorBoundary.jsx         # 错误边界组件
│   ├── LoadingSpinner.jsx        # 加载动画组件
│   └── EmptyState.jsx            # 空状态组件
├── utils/               # 工具函数
│   └── index.js         # 数据验证和格式化函数
├── types/               # 类型定义
│   └── index.js         # PropTypes 类型定义
├── App.jsx              # 主应用组件
├── App.css              # 应用样式
├── index.css            # 全局样式和 CSS 变量
└── main.jsx             # 应用入口
```

## 快速开始

### 环境要求

- Node.js >= 16.0.0
- npm 或 yarn

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## 组件说明

### BrandMentionRate
显示品牌总提及率，包含：
- 环形进度图表
- 关键词排名列表
- 实时数据更新

### ModelMentionRates
展示各种 AI 模型的提及率：
- 水平进度条显示
- 百分比数值
- 模型名称标识

### ReferencesTable
参考数据表格：
- 文章标题
- 网站来源
- 提及率统计
- 响应式表格设计

### TimeFilter
时间范围筛选器：
- 预设时间选项
- 活跃状态指示
- 平滑切换动画

## 样式特性

- **CSS 变量系统** - 统一的颜色、间距、字体等设计规范
- **响应式设计** - 支持多种屏幕尺寸的适配
- **现代视觉效果** - 毛玻璃效果、渐变背景、平滑动画
- **无障碍支持** - 完善的焦点管理和键盘导航

## 开发指南

### 添加新组件

1. 在 `src/components/` 目录下创建组件文件
2. 使用 PropTypes 进行类型定义
3. 添加适当的 JSDoc 注释
4. 遵循现有的代码风格

### 样式开发

- 使用 `index.css` 中定义的 CSS 变量
- 遵循 BEM 命名规范
- 确保响应式兼容性
- 添加适当的过渡动画

### 数据管理

当前版本使用模拟数据，如需集成真实 API：
1. 在 `utils/index.js` 中添加数据获取函数
2. 更新组件状态管理
3. 添加加载和错误处理

## 浏览器支持

- Chrome/Edge >= 88
- Firefox >= 85
- Safari >= 14
- 支持现代 CSS 特性

## 许可证

MIT License

## 更新日志

### v0.1.0
- 初始版本发布
- 基础仪表板功能
- 响应式设计实现
- 代码美化和优化