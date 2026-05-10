import json
import os
from typing import Any, Dict, List

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "../../config")

DEFAULT_PROVIDERS: Dict[str, Any] = {
    "providers": [
        {
            "name": "zhipuai",
            "display_name": "智谱AI",
            "models": ["glm-4.6", "glm-4"],
        },
        {
            "name": "siliconflow",
            "display_name": "SiliconFlow",
            "models": ["Qwen/Qwen2.5-7B-Instruct", "THUDM/glm-4-9b-chat"],
        },
    ],
}

DEFAULT_ANALYSIS_TYPES: List[Dict[str, str]] = [
    {"type": "brand_recognition", "name": "品牌识别", "description": "识别文本中的品牌提及"},
    {"type": "sentiment_analysis", "name": "情感分析", "description": "分析品牌相关文本的情感倾向"},
    {
        "type": "competitive_analysis",
        "name": "竞争分析",
        "description": "分析品牌在市场中的竞争地位",
    },
    {"type": "mention_analysis", "name": "提及分析", "description": "分析品牌的提及频率和趋势"},
]

DEFAULT_SETTINGS: Dict[str, Any] = {
    "default_provider": "zhipuai",
    "default_model": "glm-4.6",
    "max_analysis_threads": 5,
    "result_cache_timeout": 3600,
    "auto_save_results": True,
}

VALID_SETTING_KEYS = {
    "default_provider", "default_model", "max_analysis_threads",
    "result_cache_timeout", "auto_save_results",
}


def _read_json(file_name: str) -> Dict[str, Any]:
    path = os.path.join(CONFIG_DIR, file_name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _write_json(file_name: str, data: Dict[str, Any]) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    path = os.path.join(CONFIG_DIR, file_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_providers() -> Dict[str, Any]:
    data = _read_json("llm_providers.json")
    if data:
        return data
    return DEFAULT_PROVIDERS


def get_analysis_types() -> List[Dict[str, str]]:
    data = _read_json("analysis_types.json")
    if data and "analysis_types" in data:
        return data["analysis_types"]
    return DEFAULT_ANALYSIS_TYPES


def get_settings() -> Dict[str, Any]:
    data = _read_json("llm_settings.json")
    if data:
        return {k: data.get(k, DEFAULT_SETTINGS[k]) for k in DEFAULT_SETTINGS}
    return dict(DEFAULT_SETTINGS)


def update_settings(updates: Dict[str, Any]) -> Dict[str, Any]:
    for key in updates:
        if key not in VALID_SETTING_KEYS:
            raise ValueError(f"无效的配置项: {key}")

    current = _read_json("llm_settings.json") or {}
    current.update(updates)
    _write_json("llm_settings.json", current)
    return {k: current.get(k, DEFAULT_SETTINGS[k]) for k in DEFAULT_SETTINGS}