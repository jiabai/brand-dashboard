"""配置相关API路由."""

import json
import os
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/providers")
async def get_llm_providers():
    """获取可用的LLM提供商列表."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), "../../config/llm_providers.json")

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                providers = json.load(f)
        else:
            # 默认提供商配置
            providers = {
                "providers": [
                    {
                        "name": "zhipuai",
                        "display_name": "智谱AI",
                        "models": ["glm-4.6", "glm-4"]
                    },
                    {
                        "name": "siliconflow",
                        "display_name": "SiliconFlow",
                        "models": ["Qwen/Qwen2.5-7B-Instruct", "THUDM/glm-4-9b-chat"]
                    }
                ]
            }
        return {
            "success": True,
            "data": providers,
            "message": "获取提供商列表成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提供商列表失败: {str(e)}") from e

@router.get("/analysis-types")
async def get_analysis_types():
    """获取可用的分析类型."""
    try:
        analysis_types = [
            {
                "type": "brand_recognition",
                "name": "品牌识别",
                "description": "识别文本中的品牌提及"
            },
            {
                "type": "sentiment_analysis",
                "name": "情感分析",
                "description": "分析品牌相关文本的情感倾向"
            },
            {
                "type": "competitive_analysis",
                "name": "竞争分析",
                "description": "分析品牌在市场中的竞争地位"
            },
            {
                "type": "mention_analysis",
                "name": "提及分析",
                "description": "分析品牌的提及频率和趋势"
            }
        ]
        return {
            "success": True,
            "data": {"analysis_types": analysis_types},
            "message": "获取分析类型成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析类型失败: {str(e)}") from e

@router.get("/settings")
async def get_settings():
    """获取当前配置设置."""
    try:
        # 这里可以读取实际的配置文件
        settings = {
            "default_provider": "openai",
            "default_model": "gpt-3.5-turbo",
            "max_analysis_threads": 5,
            "result_cache_timeout": 3600,
            "auto_save_results": True
        }
        return {
            "success": True,
            "data": settings,
            "message": "获取配置成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}") from e


@router.post("/settings")
async def update_settings(settings: Dict[str, Any]):
    """更新配置设置."""
    try:
        # 这里可以实现配置更新逻辑
        # 验证配置项
        valid_keys = ["default_provider", "default_model", "max_analysis_threads", 
                       "result_cache_timeout", "auto_save_results"]

        for key in settings.keys():
            if key not in valid_keys:
                raise ValueError(f"无效的配置项: {key}")

        return {
            "success": True,
            "data": settings,
            "message": "配置更新成功"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}") from e
