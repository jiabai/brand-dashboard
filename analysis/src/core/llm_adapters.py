"""
LLM适配器 - 统一多种LLM SDK的接口适配器
支持OpenAI、智谱AI等多种LLM提供商
"""

from typing import List

from .llm_adapter_base import BaseLLMAdapter, UnifiedError, UnifiedResponse
from .openai_adapter import OpenAIAdapter
from .silicon_flow_adapter import SiliconFlowAdapter
from .zhipuai_adapter import ZhipuAIAdapter

__all__ = [
    "BaseLLMAdapter",
    "UnifiedResponse",
    "UnifiedError",
    "OpenAIAdapter",
    "ZhipuAIAdapter",
    "SiliconFlowAdapter",
    "LLMFactory",
    "create_llm_adapter",
    "PRESET_CONFIGS",
]


class LLMFactory:
    """LLM工厂类 - 创建和管理LLM适配器"""

    _adapters = {
        "openai": OpenAIAdapter,
        "zhipuai": ZhipuAIAdapter,
        "silicon_flow": SiliconFlowAdapter,
    }

    @classmethod
    def register_adapter(cls, name: str, adapter_class: type):
        """注册新的适配器"""
        cls._adapters[name] = adapter_class

    @classmethod
    def create_adapter(
        cls, provider: str, api_key: str, base_url: str, model: str, **kwargs
    ) -> BaseLLMAdapter:
        """创建适配器实例"""
        if provider not in cls._adapters:
            raise ValueError(
                f"不支持的提供商: {provider}。支持的提供商: {list(cls._adapters.keys())}"
            )

        adapter_class = cls._adapters[provider]
        return adapter_class(api_key, base_url, model, **kwargs)

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """获取支持的提供商列表"""
        return list(cls._adapters.keys())


# 预定义配置
PRESET_CONFIGS = {
    "openai": {
        "provider": "openai",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-3.5-turbo",
    },
    "zhipuai": {
        "provider": "zhipuai",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4.6",
    },
    "silicon_flow": {
        "provider": "silicon_flow",  # 使用专用的SiliconFlow适配器
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3.2-Exp",
    },
    "silicon_flow_deepseek_v3": {
        "provider": "silicon_flow",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3",
    },
    "silicon_flow_qwen_32b": {
        "provider": "silicon_flow",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "Qwen/Qwen2.5-32B-Instruct",
    },
    "deepseek": {
        "provider": "openai",  # DeepSeek使用OpenAI兼容接口
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
}


def create_llm_adapter(
    provider: str,
    api_key: str,
    model: str = None,
    base_url: str = None,
    **kwargs,
) -> BaseLLMAdapter:
    """
    创建LLM适配器的便捷函数

    Args:
        provider: 提供商名称 (openai, zhipuai, silicon_flow, deepseek)
        api_key: API密钥
        model: 模型名称（可选，使用预设配置）
        base_url: 基础URL（可选，使用预设配置）
        **kwargs: 其他参数

    Returns:
        BaseLLMAdapter实例

    Note:
        silicon_flow: 使用专用的SiliconFlow适配器，支持SiliconFlow特有的功能和优化
    """
    # 获取预设配置
    if provider in PRESET_CONFIGS:
        preset = PRESET_CONFIGS[provider].copy()
        preset["api_key"] = api_key
        if model:
            preset["model"] = model
        if base_url:
            preset["base_url"] = base_url
        preset.update(kwargs)

        return LLMFactory.create_adapter(**preset)
    else:
        # 自定义配置或动态注册的适配器
        # 如果开发者调用了 LLMFactory.register_adapter("new_provider", NewClass)
        # 但没有将其加入 PRESET_CONFIGS，那么 create_llm_adapter("new_provider", ...)
        # 就会走到这个 else 分支。

        # 首先检查provider是否被支持
        supported_providers = LLMFactory.get_supported_providers()
        if provider not in supported_providers:
            raise ValueError(
                f"不支持的提供商: '{provider}'。\n"
                f"支持的提供商: {supported_providers}。\n"
                "或者使用PRESET_CONFIGS中的预设配置: "
                f"{list(PRESET_CONFIGS.keys())}"
            )

        # 如果是支持的提供商（但不在预设配置中），则必须提供配置参数
        if not model or not base_url:
            raise ValueError(
                f"使用非预设提供商 '{provider}' 时，需要明确提供 model 和 base_url 参数"
            )

        return LLMFactory.create_adapter(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            **kwargs,
        )
