"""Brand Analysis - 品牌AI认知分析工具包.

这是一个用于品牌AI认知分析的工具包，提供插件架构支持多种分析功能。

主要功能:
- LLM品牌识别
- 插件化分析架构
- 统一LLM操作接口
- 多提供商支持
"""

__version__ = "0.1.0"
__author__ = "Brand Analysis Team"

from .analyzer import BrandAnalyzer
from .business_services.llm_brand_recognizer import LLMBrandRecognizer
from .core.llm_adapters import UnifiedError, UnifiedResponse, create_llm_adapter

# 主要导出符号
from .core.llm_operator import LLMConfig, LLMError, LLMOperator, LLMResponse
from .core.plugin_interface import AnalysisPlugin, PluginRegistry
from .core.plugin_manager import PluginManager

__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    # LLM核心功能
    "LLMOperator",
    "LLMConfig",
    "LLMResponse",
    "LLMError",
    "create_llm_adapter",
    "UnifiedResponse",
    "UnifiedError",
    # 品牌识别
    "LLMBrandRecognizer",
    # 分析功能
    "BrandAnalyzer",
    # 插件系统
    "PluginManager",
    "AnalysisPlugin",
    "PluginRegistry",
]
