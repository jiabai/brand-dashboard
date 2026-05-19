# 品牌分析仪表板 Web

React + Vite 前端，用于品牌声量、趋势、分平台、信源、情感、任务加载和账户流程管理。前端只通过 `/api` REST 接口获取数据，不直接访问数据库。

## 技术栈

- React 18
- Vite 5
- shadcn/ui（基于 Radix UI 原语）
- Tailwind CSS 4（CSS variables + `@theme inline` 语义主题）
- Lucide React 图标
- 原生 SVG/CSS 轻量图表（无 G2 或 Recharts 运行时）
- react-router-dom v6
- dayjs 日期工具

## 目录结构

```text
web/
├── src/
│   ├── api/                # API Adapter（dashboard, queryJobs, auth）
│   ├── components/         # 页面和业务组件
│   │   └── ui/             # shadcn/ui 可复用 UI 原语（自动生成）
│   ├── config/             # 路由与菜单配置（routes.js）
│   ├── hooks/              # 自定义 hooks（useDashboardParams, useTimeframeManager, useTheme）
│   ├── lib/cn.js           # 共享 className 合并工具
│   ├── styles/             # 组件级 CSS
│   ├── utils/              # 查询、日期、数值、图表等共享工具
│   ├── App.jsx             # 应用壳层、路由定义和 TooltipProvider
│   ├── index.css           # 全局 CSS 变量、Tailwind 和 shadcn 基础样式
│   └── main.jsx            # 应用入口
├── mock/                   # 本地 Mock 数据
├── components.json         # shadcn/ui 配置文件
├── vite.config.js
├── tailwind.config.js
└── package.json
```

## 主要视图

- `home`：品牌提及排名、平台提及率、引用媒介详情
- `trend`：趋势分析
- `platforms`：分平台分析（声量份额表格）
- `sources`：信源分析
- `sentiment`：情感分析
- `task-load`：LLM 查询任务加载
- `task-status`：任务状态监控
- `accounts`：账户与注册管理

## URL 参数

| 参数 | 说明 |
|------|------|
| `timeframe` | `yesterday` / `7days` / `30days` / `specific_day` |
| `start_date` / `end_date` | 指定日期范围，格式 `YYYYMMDD`（`specific_day` 时使用） |
| `brand` | 品牌名称筛选 |
| `platform` | 平台详情页的平台名称 |
| `executor_id` | 创建任务页执行器 ID |
| `include_deleted` | 任务状态页是否包含已删除数据 |

页面路径由 `tenantKey + jobId`（分析页）或 `tenantKey`（租户级页面）驱动，通过 `useDashboardParams` hook 统一读取。

## 本地开发

```bash
npm install
npm run dev
npm test
npm run build
```

开发服务器默认运行在 `http://localhost:3000/`。未启用 Mock 时，Vite 会把 `/api` 代理到 `VITE_API_TARGET`，默认 `http://localhost:8000`。

## 环境变量

```env
VITE_USE_MOCK=false
VITE_API_TARGET=http://localhost:8000
VITE_DEFAULT_TENANT_KEY=tn_xxx
VITE_DEFAULT_JOB_ID=job_xxx
VITE_DEFAULT_BRAND=QuickCEP
VITE_DEFAULT_EXECUTOR_ID=exec_xxx
VITE_DEFAULT_INCLUDE_DELETED=false
```

## 架构约定

- 组件优先使用 shadcn/ui 原语，避免引入第二套基础 UI 体系。
- 共享逻辑放在 `src/utils/`，共享 className 工具放在 `src/lib/cn.js`。
- 图表使用原生 SVG/CSS 组合，不引入独立图表运行时库。
- 样式文件必须由组件或入口显式 import；未引用样式应删除。
- 数据查询通过 `src/api/` Adapter 调用后端端点，不在组件中手写 API URL。
- URL 参数通过 `useDashboardParams` 统一读取，不直接操作 `useSearchParams`。
- 时间筛选通过 `useTimeframeManager` 管理，`DashboardLayout` 只负责渲染布局控件。
- 路由、侧栏菜单和任务入口的配置源统一为 `src/config/routes.js`。