# Brand Dashboard AI Collaboration Rules

## 快速入口

- 架构：见 `docs/ARCHITECTURE.md`
- 完成门禁：见 `docs/EXECUTION_GATES.md`
- 执行清单：见 `TASKS.md`（如存在，全部完成后删除）
- 工作流：见 `WORKFLOW.md`
- 设计规范：见 `docs/DESIGN.md`
- 安全规范：见 `docs/SECURITY.md`
- 执行计划：见 `docs/exec-plans/active/`

## 核心信念

- 前后端分离：`web/` 只管 UI，`api/` 只管数据；不跨层直接访问数据库或 DOM
- 多租户隔离：所有业务查询必须带 `tenant_key`，数据层强制租户过滤
- 共享工具优于手写 helper：`web/src/lib/cn.js`、`web/src/utils/`、`api/v1/utils/` 是唯一共享入口
- 边界验证优于 YOLO 猜测：API 入参用 Pydantic 校验，前端用 Ant Design Form 校验
- "无聊"技术优先：React 18 + Ant Design + Tailwind + FastAPI + SQLAlchemy，不引入未经评估的新库

## 开发流程

1. 读取 `AGENTS.md` + `docs/ARCHITECTURE.md` 了解上下文
2. 非平凡任务：写 Spec → 写 ExecPlan → 拆任务 → 实现 → 验证
3. 轻量任务：inspect → 最小改动 → 验证
4. 每次提交更新 `agents_chat/` 记录（中文），使用 Conventional Commits

## 约束机制

- 模式：`linter+agents`
- 配置：`api/pyproject.toml`

## 常用命令

- `npm --prefix web run dev` — 启动前端开发服务器（localhost:3000）
- `npm --prefix web run build` — 构建前端生产包
- `uvicorn api.main:app --reload --host 0.0.0.0 --port 8000` — 启动后端 API
- `ruff check api` — 后端代码检查
- `python scripts/validate_agents_docs.py --level ERROR` — 文档结构验证
- `python scripts/validate_agents_docs.py --level WARN` — 文档完整性验证
