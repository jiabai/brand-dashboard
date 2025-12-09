"""FastAPI应用主文件."""

import os
import sys
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# 添加父目录到Python路径，以便导入brand_analysis模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brand_analysis_api.models.schemas import HealthResponse
from brand_analysis_api.routes import analysis, config, dashboard

# 创建FastAPI应用
app = FastAPI(
    title="Brand Analysis API",
    description="品牌分析API服务，为dashboard提供数据接口",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # dashboard开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])


@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径，返回API信息."""
    return {
        "message": "Brand Analysis API",
        "version": "0.1.0",
        "docs": "/api/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口."""
    return HealthResponse(
        status="healthy",
        service="brand-analysis-api",
        version="0.1.0"
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """全局异常处理."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.brand_analysis_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
