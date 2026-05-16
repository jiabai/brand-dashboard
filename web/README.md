# 品牌分析仪表板 Web

React + Vite 前端，用于品牌声量、趋势、分平台、信源、情感、任务加载和账户流程管理。前端只通过 `/api` REST 接口获取数据，不直接访问数据库。

## 技术栈

- React 18
- Vite 5
- Ant Design 5
- Tailwind CSS 4
- AntV G2，按图表视图懒加载
- Lucide React 与 Ant Design Icons

## 目录结构

```text
web/
├── src/
│   ├── components/           # 页面和业务组件
│   ├── lib/cn.js             # 共享 className 合并工具
│   ├── styles/               # 当前仍被组件显式 import 的 scoped 样式
│   ├── utils/                # 查询、日期、数值、图表加载等共享工具
│   ├── App.jsx               # 应用壳层、路由视图和全局筛选
│   ├── index.css             # 全局 CSS 变量、Tailwind 和基础样式
│   └── main.jsx              # 应用入口
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── package.json
```

## 主要视图

- `home`：品牌提及排名、平台提及率、引用媒介详情
- `trend`：趋势分析
- `platforms`：分平台分析
- `sources`：信源分析
- `sentiment`：情感分析
- `task-load`：LLM 查询任务加载
- `task-status`：任务状态监控
- `accounts`：账户与注册管理

## URL 参数

- `view`：当前视图，默认 `home`
- `timeframe`：`yesterday` / `7days` / `30days` / `specific_day`
- `start_date`、`end_date`、`date`：指定日期模式使用，格式为 `YYYYMMDD`
- `tenant_key`：租户 Key
- `job_id`：任务 ID
- `brand`：品牌名称
- `platform`：平台详情页的平台名称
- `executor_id`：创建任务页执行器 ID
- `include_deleted`：任务状态页是否包含已删除数据

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

- 组件优先使用 Ant Design，避免混入第二套基础 UI 体系。
- 共享逻辑放在 `src/utils/`，共享 className 工具放在 `src/lib/cn.js`。
- 图表库通过 `src/utils/loadG2Chart.js` 懒加载，避免普通页面同步绑定大体积图表依赖。
- 样式文件必须由组件或入口显式 import；未引用样式应删除。
- 数据查询必须携带后端需要的租户和任务上下文参数。
