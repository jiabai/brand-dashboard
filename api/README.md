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
- Swagger文档: http://localhost:8000/api/v1/docs
- ReDoc文档: http://localhost:8000/api/v1/redoc

### 代码检查

开发时推荐使用 Ruff 进行静态检查：

```bash
pip install ruff  # 如果尚未安装
ruff check api
```

## API端点

### 健康检查
- `GET /api/v1/health` - 服务健康检查

### 分析相关
- `POST /api/v1/analysis/analyze` - 执行品牌分析
- `POST /api/v1/analysis/recognize-brand` - 品牌识别
- `GET /api/v1/analysis/results/{result_id}` - 获取分析结果
- `GET /api/v1/analysis/history` - 获取分析历史

### 配置相关
- `GET /api/v1/config/providers` - 获取LLM提供商列表
- `GET /api/v1/config/analysis-types` - 获取分析类型
- `GET /api/v1/config/settings` - 获取当前配置
- `POST /api/v1/config/settings` - 更新配置

### Dashboard相关
- `GET /api/v1/dashboard/brand-mention-rate` - 获取品牌总提及率数据
- `GET /api/v1/dashboard/platform-mention-rates` - 获取品牌在各平台的提及率数据
- `GET /api/v1/dashboard/reference-url-stats` - 获取全局引用URL统计数据
- `GET /api/v1/dashboard/brand-metrics` - 获取品牌核心指标列表
- `GET /api/v1/dashboard/platform-metrics-by-brand` - 获取指定品牌在各平台的详细指标
- `GET /api/v1/dashboard/domain-citation-rate` - 获取域名引用率分布
- `GET /api/v1/dashboard/post-citation-rate` - 获取发文引用率数据

### 查询记录相关
- `POST /api/v1/query-records/load` - 批量加载LLM查询记录到数据库

### 品牌策略相关 (分析子项)
- `POST /api/v1/analysis/positioning-keywords` - 生成品牌定位关键词
- `POST /api/v1/analysis/consumer-questions` - 生成消费者常见问题

## 项目结构

```
api/
├── config/                  # 配置文件
│   ├── README.md
│   └── llm_settings.json
├── database/                # 数据库相关文件
│   ├── README.md           # 数据库文档
│   ├── database_schema.sql  # 核心数据库模式
│   └── schema_tenants_and_users.sql # 租户与用户模式
├── docs/                    # 文档与示例
│   ├── DASHBOARD_API_README.md
│   ├── METRICS_ALGORITHMS.md
│   ├── openapi.json
│   └── ...
├── v1/                      # API v1 版本 (核心逻辑)
│   ├── models/              # 数据模型 (Pydantic)
│   │   └── schemas.py
│   ├── repositories/        # 数据访问层 (SQLAlchemy)
│   │   └── database.py
│   ├── routes/              # API 路由处理
│   │   ├── analysis.py
│   │   ├── brand_strategy.py
│   │   ├── config.py
│   │   ├── dashboard.py
│   │   └── query_records.py
│   ├── services/            # 业务逻辑服务
│   │   └── llm_client.py
│   ├── utils/               # 工具类
│   │   ├── llm_adapters.py
│   │   ├── llm_operator.py
│   │   └── url_domain_resolver.py
│   └── __init__.py
├── Dockerfile.dev           # 本地开发镜像
├── Dockerfile.prod          # 生产环境镜像
├── __init__.py              # 模块初始化
├── generate_openapi.py      # 生成OpenAPI文档
├── main.py                  # FastAPI应用主文件
├── requirements.txt         # 运行时依赖
└── pyproject.toml           # 项目配置
```

## 与前端集成

前端dashboard可以通过以下方式调用API：

```javascript
// 执行品牌分析
const response = await fetch('http://localhost:8000/api/v1/analysis/analyze', {
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
const mentionRateResponse = await fetch('http://localhost:8000/api/v1/dashboard/brand-mention-rate?brand=Apple&timeframe=7days', {
  method: 'GET',
  headers: {
    'Accept': 'application/json',
  }
});

const mentionRateData = await mentionRateResponse.json();

// 获取品牌在各平台的提及率数据（单个品牌）
const platformResponse = await fetch('http://localhost:8000/api/v1/dashboard/platform-mention-rates?brand=Apple&timeframe=7days', {
  method: 'GET',
  headers: {
    'Accept': 'application/json',
  }
});

const platformData = await platformResponse.json();

// 获取引用URL统计数据
const referenceResponse = await fetch('http://localhost:8000/api/v1/dashboard/reference-url-stats?timeframe=7days', {
  method: 'GET',
  headers: {
    'Accept': 'application/json',
  }
});

const referenceData = await referenceResponse.json();

// 批量加载LLM查询记录
const loadResponse = await fetch('http://localhost:8000/api/v1/query-records/load', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    tenant_key: 'default',
    job_id: 'job_123456',
    data: { /* 原始查询记录数据 */ }
  })
});

const loadResult = await loadResponse.json();

// 获取品牌定位关键词
const positioningResponse = await fetch('http://localhost:8000/api/v1/analysis/positioning-keywords', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    industry: '教育',
    brand: '学而思'
  })
});

const keywords = await positioningResponse.json();
```

## 开发指南

### 添加新的API端点

1. 在`v1/routes`中添加路由函数
2. 在`v1/models/schemas.py`中定义请求/响应模型
3. 在`v1/repositories/database.py`中添加数据库查询函数
4. 在`v1/routes/__init__.py`中导出新的路由模块
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

