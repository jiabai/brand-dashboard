"""配置相关API路由."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from api.v1.services.config_service import (
    get_analysis_types,
    get_providers,
    get_settings,
    update_settings,
)

router = APIRouter()


@router.get("/providers")
async def get_llm_providers():
    """获取可用的LLM提供商列表."""
    try:
        providers = get_providers()
        return {
            "success": True,
            "data": providers,
            "message": "获取提供商列表成功",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提供商列表失败: {str(e)}") from e


@router.get("/analysis-types")
async def get_analysis_types_route():
    """获取可用的分析类型."""
    try:
        analysis_types = get_analysis_types()
        return {
            "success": True,
            "data": {"analysis_types": analysis_types},
            "message": "获取分析类型成功",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析类型失败: {str(e)}") from e


@router.get("/settings")
async def get_settings_route():
    """获取当前配置设置."""
    try:
        settings = get_settings()
        return {
            "success": True,
            "data": settings,
            "message": "获取配置成功",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}") from e


@router.post("/settings")
async def update_settings_route(settings: Dict[str, Any]):
    """更新配置设置."""
    try:
        updated = update_settings(settings)
        return {
            "success": True,
            "data": updated,
            "message": "配置更新成功",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}") from e