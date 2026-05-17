# Brand Analysis API

为品牌分析dashboard提供RESTful API服务的独立模块。

## 📋 文档索引

- [Dashboard API详细文档](./docs/DASHBOARD_API_README.md) - 包含所有Dashboard API的详细说明
- [指标计算算法说明](./docs/METRICS_ALGORITHMS.md) - Dashboard指标计算口径说明

## 功能特性

- **品牌分析API**: 提供品牌识别、情感分析、竞争分析等功能
- **配置管理**: 管理LLM提供商、分析类型等配置
- **Dashboard API**: 提供品牌提及率、平台对比、引用URL统计等仪表板数据
- **品牌策略API**: 提供品牌策略建议和分析
- **异步处理**: 支持异步分析任务
- **CORS支持**: 支持跨域请求，便于前端集成
- **自动文档**: 自动生成API文档 (Swagger/ReDoc)

## 快速开始

### 安装依赖

```bash
uv sync
```

开发依赖（含测试）：

```bash
uv sync --extra dev
```

> 说明：路由中依赖的 `brand_analysis` 模块需提前可用（私有包或本地模块），否则分析相关接口无法正常运行。

### 启动服务

开发模式：
```bash
python -m api.main
```

或使用uvicorn：
```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### API文档

启动服务后，访问：
- Swagger文档: http://localhost:8000/api/v1/docs
- ReDoc文档: http://localhost:8000/api/v1/redoc

### 代码检查

开发时推荐使用 Ruff 进行静态检查：

```bash
ruff check api
```

## 项目结构

```
api/
├── pyproject.toml         # 项目配置与依赖声明（uv 管理）
├── main.py                # 应用入口
├── v1/
│   ├── routes/            # 路由层
│   ├── models/            # Pydantic 数据模型
│   ├── repositories/      # 数据访问层
│   ├── services/          # 业务逻辑层
│   └── utils/             # 工具层
├── database/              # SQL Schema 定义
├── config/                # LLM 配置
└── tests/                 # 测试
```

## 测试

```bash
uv run pytest
```
