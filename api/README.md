# Brand Analysis API

为品牌分析dashboard提供RESTful API服务的独立模块。

## 📋 文档索引

- [Dashboard API详细文档](./DASHBOARD_API_README.md) - 包含所有Dashboard API的详细说明

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
pip install -r requirements.txt
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
- Swagger文档: http://localhost:8000/api/docs
- ReDoc文档: http://localhost:8000/api/redoc

### 代码检查

开发时推荐安装开发依赖并运行 Ruff 进行静态检查：

```bash
pip install -r requirements-dev.txt
ruff check api
```

## API端点

### 健康检查
- `GET /health` - 服务健康检查

### 分析相关
- `POST /api/analysis/analyze` - 执行品牌分析
- `POST /api/analysis/recognize-brand` - 品牌识别
- `GET /api/analysis/results/{result_id}` - 获取分析结果
- `GET /api/analysis/history` - 获取分析历史

### 配置相关
- `GET /api/config/providers` - 获取LLM提供商列表
- `GET /api/config/analysis-types` - 获取分析类型
- `GET /api/config/settings` - 获取当前配置
- `POST /api/config/settings` - 更新配置

### Dashboard相关
- `GET /api/dashboard/brand-mention-rate` - 获取品牌总提及率数据
- `GET /api/dashboard/platform-mention-rates` - 获取品牌在各平台的提及率数据
- `GET /api/dashboard/reference-url-stats` - 获取全局引用URL统计数据

### 品牌策略相关
- `GET /api/analysis/brand-strategy/advice` - 获取品牌策略建议
- `GET /api/analysis/brand-strategy/compare` - 品牌对比分析

## 项目结构

```
api/
├── __init__.py              # 模块初始化
├── main.py                  # FastAPI应用主文件
├── database/                # 数据库相关文件
│   ├── README.md           # 数据库文档
│   └── schema.sql          # 数据库模式
├── repositories/            # 数据访问层
│   ├── __init__.py
│   └── database.py         # 数据库查询函数
├── routes/                  # API路由
│   ├── __init__.py
│   ├── analysis.py          # 分析相关API
│   ├── brand_strategy.py    # 品牌策略API
│   ├── config.py            # 配置相关API
│   └── dashboard.py         # Dashboard相关API
├── models/                  # 数据模型
│   ├── __init__.py
│   └── schemas.py           # Pydantic模型
├── services/                # 服务层
│   ├── __init__.py
│   └── llm_client.py        # LLM客户端服务
├── utils/                   # 工具函数
│   ├── __init__.py
│   ├── llm_adapters.py      # LLM适配器
│   ├── llm_client.py        # LLM客户端工具
│   ├── llm_operator.py      # LLM操作器
│   └── url_domain_resolver.py  # URL域名解析工具
├── requirements.txt         # 运行时依赖
└── requirements-dev.txt     # 开发/检查依赖
```

## 与前端集成

前端dashboard可以通过以下方式调用API：

```javascript
// 执行品牌分析
const response = await fetch('http://localhost:8000/api/analysis/analyze', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    brand_name: 'Apple',
    analysis_type: 'brand_recognition',
    params: {}
  })
});

const result = await response.json();

// 获取品牌提及率数据
const mentionRateResponse = await fetch('http://localhost:8000/api/dashboard/brand-mention-rate?brand=Apple&timeframe=7days', {
  method: 'GET',
  headers: {
    'Accept': 'application/json',
  }
});

const mentionRateData = await mentionRateResponse.json();

// 获取品牌在各平台的提及率数据（单个品牌）
const platformResponse = await fetch('http://localhost:8000/api/dashboard/platform-mention-rates?brand=Apple&timeframe=7days', {
  method: 'GET',
  headers: {
    'Accept': 'application/json',
  }
});

const platformData = await platformResponse.json();

// 获取引用URL统计数据
const referenceResponse = await fetch('http://localhost:8000/api/dashboard/reference-url-stats?timeframe=7days', {
  method: 'GET',
  headers: {
    'Accept': 'application/json',
  }
});

const referenceData = await referenceResponse.json();

// 获取品牌策略建议
const strategyResponse = await fetch('http://localhost:8000/api/brand-strategy/advice?brand=Apple', {
  method: 'GET',
  headers: {
    'Accept': 'application/json',
  }
});

const strategyData = await strategyResponse.json();
```

## 开发指南

### 添加新的API端点

1. 在相应的路由文件中添加路由函数
2. 在`models/schemas.py`中定义请求/响应模型
3. 在`repositories/database.py`中添加数据库查询函数
4. 在`routes/__init__.py`中导出新的路由模块
5. 在`main.py`中注册新的路由
6. 更新API文档和README.md

### Dashboard API使用

品牌提及率API支持以下时间范围参数：
- `yesterday` - 昨日数据
- `7days` - 近7天数据
- `30days` - 近30天数据

必需参数：
- `brand` - 品牌名称 (如: Apple, Huawei)

可选参数：
- `date` - 指定日期 (格式: YYYYMMDD)

引用URL统计API为全局统计，不需要品牌参数。

### 配置CORS

在`main.py`中修改CORS配置以支持更多的前端域名。

