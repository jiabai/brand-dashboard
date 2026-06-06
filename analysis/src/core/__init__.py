"""
LLM核心模块 - 统一LLM SDK接口的核心组件
包含适配器和操作器等基础模块
"""

from .llm_adapters import (
    PRESET_CONFIGS,
    BaseLLMAdapter,
    LLMFactory,
    OpenAIAdapter,
    SiliconFlowAdapter,
    UnifiedError,
    UnifiedResponse,
    ZhipuAIAdapter,
    create_llm_adapter,
)
from .llm_operator import (
    LLMConfig,
    LLMError,
    LLMOperator,
    LLMProvider,
    LLMResponse,
)

__all__ = [
    # 适配器相关
    "BaseLLMAdapter",
    "OpenAIAdapter",
    "ZhipuAIAdapter",
    "SiliconFlowAdapter",
    "LLMFactory",
    "create_llm_adapter",
    "PRESET_CONFIGS",
    "UnifiedResponse",
    "UnifiedError",
    # 操作器相关
    "LLMOperator",
    "LLMConfig",
    "LLMResponse",
    "LLMError",
    "LLMProvider",
]
