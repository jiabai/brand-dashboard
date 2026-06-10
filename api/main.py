"""FastAPI应用主文件."""

import os
from contextlib import asynccontextmanager
from typing import Dict

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.utils import is_body_allowed_for_status_code
from starlette.exceptions import HTTPException as StarletteHTTPException

# from fastapi_structlog import LogSettings, setup_logger
# from fastapi_structlog.middleware import AccessLogMiddleware, StructlogMiddleware
from api.v1.models.schemas import HealthResponse
from api.v1.repositories.init_db import init_db
from api.v1.routes import (
    analysis,
    analysis_runs,
    auth,
    brand_strategy,
    collection_attempts,
    collection_tasks,
    config,
    conversation,
    dashboard,
    executors,
    projects,
    query_jobs,
)
from api.v1.services.job_reset_scheduler import start_scheduler


@asynccontextmanager
async def _lifespan(app):
    init_db()
    start_scheduler()
    yield

# log_settings = LogSettings(
#     logger="brand-analysis-api",
#     json_logs=False,
#     debug=False,
#     types=["console"],
# )
# setup_logger(log_settings)

app = FastAPI(
    title="Brand Analysis API",
    description="品牌分析API服务，为dashboard提供数据接口",
    version="0.1.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json",
    lifespan=_lifespan,
)

# app.add_middleware(AccessLogMiddleware)
# app.add_middleware(StructlogMiddleware)
app.add_middleware(CorrelationIdMiddleware)

_cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
_cors_origins = [origin.strip() for origin in _cors_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(
    analysis_runs.router,
    prefix="/api/v1/analysis-runs",
    tags=["analysis-runs"],
)
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(config.router, prefix="/api/v1/config", tags=["config"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(brand_strategy.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(
    collection_attempts.router,
    prefix="/api/v1/collection-attempts",
    tags=["collection-attempts"],
)
app.include_router(
    collection_tasks.router,
    prefix="/api/v1/collection-tasks",
    tags=["collection-tasks"],
)
app.include_router(query_jobs.router, prefix="/api/v1/query-jobs", tags=["query-jobs"])
app.include_router(executors.router, prefix="/api/v1/executors", tags=["executors"])
app.include_router(conversation.router, prefix="/api/v1/conversation", tags=["conversation"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])

@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径，返回API信息."""
    return {
        "message": "Brand Analysis API",
        "version": "0.1.0",
        "docs": "/api/v1/docs"
    }

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口."""
    return HealthResponse(
        status="healthy",
        service="brand-analysis-api",
        version="0.1.0"
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """全局异常处理：统一输出业务错误信封，HTTP 状态与业务 code 保持一致."""
    headers = getattr(exc, "headers", None)
    if not is_body_allowed_for_status_code(exc.status_code):
        return Response(status_code=exc.status_code, headers=headers)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "code": exc.status_code,
        },
        headers=headers,
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
