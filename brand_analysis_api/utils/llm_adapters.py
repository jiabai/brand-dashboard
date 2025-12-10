"""
LLM适配器 - 统一多种LLM SDK的接口适配器
支持OpenAI、智谱AI等多种LLM提供商
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
import logging
from dataclasses import dataclass
import asyncio
import time

# OpenAI SDK
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion
# 智谱AI SDK
try:
    from zai import ZhipuAiClient
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False

@dataclass
class UnifiedResponse:
    """统一的响应格式"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float
    status_code: int = 200
    headers: Optional[Dict[str, str]] = None

@dataclass
class UnifiedError:
    """统一的错误格式"""
    error_type: str
    error_message: str
    status_code: Optional[int] = None
    retryable: bool = True
    details: Optional[Dict[str, Any]] = None

class BaseLLMAdapter(ABC):
    """LLM适配器基类"""

    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.config = kwargs
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(f"{self.__class__.__name__}_{id(self)}")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    @abstractmethod
    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Union[UnifiedResponse, UnifiedError]:
        """创建聊天完成"""
        pass

    @abstractmethod
    async def create_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """创建流式聊天完成"""
        pass

class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI SDK适配器"""

    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(api_key, base_url, model, **kwargs)

        # 创建OpenAI客户端
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=kwargs.get('timeout', 30)
        )

        self.sync_client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=kwargs.get('timeout', 30)
        )

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Union[UnifiedResponse, UnifiedError]:
        """创建OpenAI聊天完成"""
        import time

        start_time = time.time()

        try:
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 2000),
                "top_p": kwargs.get("top_p", 1.0),
                "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
                "presence_penalty": kwargs.get("presence_penalty", 0.0),
            }

            # 添加响应格式
            if "response_format" in kwargs:
                request_params["response_format"] = kwargs["response_format"]

            response: ChatCompletion = await self.async_client.chat.completions.create(
                **request_params
            )

            response_time = time.time() - start_time

            # 提取响应内容
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }

            return UnifiedResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                response_time=response_time
            )

        except Exception as e:
            response_time = time.time() - start_time

            return UnifiedError(
                error_type=type(e).__name__,
                error_message=str(e),
                status_code=getattr(e, 'status_code', None),
                retryable=self._is_retryable_error(e)
            )

    async def create_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """创建OpenAI流式聊天完成"""
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "top_p": kwargs.get("top_p", 1.0),
            "stream": True
        }

        try:
            stream = await self.async_client.chat.completions.create(**request_params)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "model": chunk.model,
                        "finish_reason": chunk.choices[0].finish_reason
                    }

        except Exception as e:
            yield {
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _is_retryable_error(self, error: Exception) -> bool:
        """判断是否为可重试错误"""
        retryable_errors = (
            'RateLimitError',
            'APIError',
            'Timeout',
            'APIConnectionError',
            'ConnectionError',
            'TimeoutError'
        )
        return type(error).__name__ in retryable_errors

class SiliconFlowAdapter(BaseLLMAdapter):
    """SiliconFlow SDK适配器 - 基于OpenAI兼容接口"""

    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(api_key, base_url, model, **kwargs)

        # SiliconFlow使用OpenAI兼容接口
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.siliconflow.cn/v1",
            timeout=kwargs.get('timeout', 30)
        )

        self.sync_client = OpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.siliconflow.cn/v1",
            timeout=kwargs.get('timeout', 30)
        )

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Union[UnifiedResponse, UnifiedError]:
        """创建SiliconFlow聊天完成"""
        import time

        start_time = time.time()

        try:
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 2000),
                "top_p": kwargs.get("top_p", 1.0),
                "frequency_penalty": kwargs.get("frequency_penalty", 0.0),
                "presence_penalty": kwargs.get("presence_penalty", 0.0),
            }

            # 添加响应格式
            if "response_format" in kwargs:
                request_params["response_format"] = kwargs["response_format"]

            response: ChatCompletion = await self.async_client.chat.completions.create(
                **request_params
            )

            response_time = time.time() - start_time

            # 提取响应内容
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }

            return UnifiedResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                response_time=response_time
            )

        except Exception as e:
            response_time = time.time() - start_time

            return UnifiedError(
                error_type=type(e).__name__,
                error_message=str(e),
                status_code=getattr(e, 'status_code', None),
                retryable=self._is_retryable_error(e)
            )

    async def create_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """创建SiliconFlow流式聊天完成"""
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "top_p": kwargs.get("top_p", 1.0),
            "stream": True
        }

        try:
            stream = await self.async_client.chat.completions.create(**request_params)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "model": chunk.model,
                        "finish_reason": chunk.choices[0].finish_reason
                    }

        except Exception as e:
            yield {
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _is_retryable_error(self, error: Exception) -> bool:
        """判断是否为可重试错误"""
        # SiliconFlow常见的可重试错误
        retryable_errors = (
            'RateLimitError',
            'APIError',
            'Timeout',
            'APIConnectionError',
            'ConnectionError',
            'TimeoutError',
            'ServiceUnavailableError'
        )
        return type(error).__name__ in retryable_errors

class ZhipuAIAdapter(BaseLLMAdapter):
    """智谱AI SDK适配器"""

    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(api_key, base_url, model, **kwargs)

        if not ZHIPUAI_AVAILABLE:
            raise ImportError("智谱AI SDK未安装，请安装: pip install zai-sdk")

        # 创建智谱AI客户端
        self.client = ZhipuAiClient(
            api_key=api_key,
            base_url=base_url if base_url != "https://open.bigmodel.cn/api/paas/v4" else None
        )
        # self.client = ZhipuAI(
        #     api_key=api_key,
        #     base_url=base_url if base_url != "https://open.bigmodel.cn/api/paas/v4" else None
        # )

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Union[UnifiedResponse, UnifiedError]:
        """创建智谱AI聊天完成"""
        start_time = time.time()

        try:
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 2000),
                "top_p": kwargs.get("top_p", 0.9),
                "thinking":{
                    "type":"disabled"
                }
            }

            # 添加响应格式参数（如果提供）
            if kwargs.get("response_format"):
                request_params["response_format"] = kwargs["response_format"]

            # 使用异步方式调用智谱AI API
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(**request_params)
            )

            response_time = time.time() - start_time

            # 提取响应内容
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0
            }

            return UnifiedResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                response_time=response_time
            )

        except Exception as e:
            response_time = time.time() - start_time

            return UnifiedError(
                error_type=type(e).__name__,
                error_message=str(e),
                status_code=getattr(e, 'status_code', None),
                retryable=self._is_retryable_error(e)
            )

    async def create_chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """创建智谱AI流式聊天完成"""
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "top_p": kwargs.get("top_p", 1.0),
            "thinking":{
                "type":"disabled"
            },
            "stream": True
        }

        # 添加响应格式参数（如果提供）
        if kwargs.get("response_format"):
            request_params["response_format"] = kwargs["response_format"]

        try:
            # 使用异步方式获取流式响应
            stream = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.client.chat.completions.create(**request_params)
            )

            # 异步迭代流式响应
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "model": chunk.model,
                        "finish_reason": chunk.choices[0].finish_reason
                    }

        except Exception as e:
            yield {
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _is_retryable_error(self, error: Exception) -> bool:
        """判断是否为可重试错误"""
        # 智谱AI常见的可重试错误
        retryable_errors = (
            'RateLimitError',
            'APIError',
            'Timeout',
            'ConnectionError',
            'TimeoutError'
        )
        return type(error).__name__ in retryable_errors

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
        cls,
        provider: str,
        api_key: str,
        base_url: str,
        model: str,
        **kwargs
    ) -> BaseLLMAdapter:
        """创建适配器实例"""
        if provider not in cls._adapters:
            raise ValueError(f"不支持的提供商: {provider}。支持的提供商: {list(cls._adapters.keys())}")

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
        "model": "gpt-3.5-turbo"
    },
    "zhipuai": {
        "provider": "zhipuai", 
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4.6"
    },
    "silicon_flow": {
        "provider": "silicon_flow",  # 使用专用的SiliconFlow适配器
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3.2-Exp"
    },
    "silicon_flow_deepseek_v3": {
        "provider": "silicon_flow",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3"
    },
    "silicon_flow_qwen_32b": {
        "provider": "silicon_flow",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "Qwen/Qwen2.5-32B-Instruct"
    },
    "deepseek": {
        "provider": "openai",  # DeepSeek使用OpenAI兼容接口
        "base_url": "https://api.deepseek.com/v1", 
        "model": "deepseek-chat"
    }
}

def create_llm_adapter(
    provider: str,
    api_key: str,
    model: str = None,
    base_url: str = None,
    **kwargs
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
                f"或者使用PRESET_CONFIGS中的预设配置: {list(PRESET_CONFIGS.keys())}"
            )

        # 如果是支持的提供商（但不在预设配置中），则必须提供配置参数
        if not model or not base_url:
            raise ValueError(f"使用非预设提供商 '{provider}' 时，需要明确提供 model 和 base_url 参数")

        return LLMFactory.create_adapter(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            **kwargs
        )
