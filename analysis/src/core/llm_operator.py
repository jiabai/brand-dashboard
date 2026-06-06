"""
LLM操作器 - 支持多种LLM SDK的统一接口
兼容OpenAI、智谱AI等多种LLM提供商
"""

import asyncio
import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

# 导入适配器
from .llm_adapters import (
    PRESET_CONFIGS,
    BaseLLMAdapter,
    OpenAIAdapter,
    UnifiedError,
    UnifiedResponse,
    create_llm_adapter,
)


class LLMProvider(Enum):
    """LLM提供商枚举"""

    OPENAI = "openai"
    ZHIPUAI = "zhipuai"
    SILICON_FLOW = "silicon_flow"
    DEEPSEEK = "deepseek"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """LLM配置数据类"""

    provider: str
    api_key: str
    base_url: str
    model: str
    timeout: int = 30000  # 毫秒
    max_retries: int = 3
    max_tokens: int = 2000
    temperature: float = 0.1
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stream: bool = False
    response_format: Optional[Dict[str, Any]] = None
    use_cache: bool = True

    def __post_init__(self):
        """验证配置"""
        self._validate_required_fields()
        self._normalize_url()
        self._validate_numeric_ranges()

    def _validate_required_fields(self):
        """验证必填字段"""
        if not self.api_key or not self.api_key.strip():
            raise ValueError("API密钥不能为空")
        if not self.base_url or not self.base_url.strip():
            raise ValueError("基础URL不能为空")
        if not self.model or not self.model.strip():
            raise ValueError("模型名称不能为空")
        if not self.provider or not self.provider.strip():
            raise ValueError("提供商不能为空")

    def _normalize_url(self):
        """标准化URL"""
        self.base_url = self.base_url.rstrip("/")

    def _validate_numeric_ranges(self):
        """验证数值范围"""
        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("temperature必须在0-2之间")
        if self.top_p < 0 or self.top_p > 1:
            raise ValueError("top_p必须在0-1之间")
        if self.frequency_penalty < -2 or self.frequency_penalty > 2:
            raise ValueError("frequency_penalty必须在-2-2之间")
        if self.presence_penalty < -2 or self.presence_penalty > 2:
            raise ValueError("presence_penalty必须在-2-2之间")
        if self.timeout <= 0:
            raise ValueError("timeout必须大于0")
        if self.max_retries < 0:
            raise ValueError("max_retries不能为负数")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens必须大于0")


@dataclass
class LLMResponse:
    """LLM响应数据类"""

    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    response_time: float  # 响应时间（秒）
    status_code: int = 200
    headers: Optional[Dict[str, str]] = None
    provider: str = "unknown"  # 提供商信息


@dataclass
class LLMError:
    """LLM错误数据类"""

    error_type: str
    error_message: str
    status_code: Optional[int] = None
    retryable: bool = True
    details: Optional[Dict[str, Any]] = None
    provider: str = "unknown"  # 提供商信息


class LLMOperator:
    """
    LLM操作器 - 支持多种LLM SDK的统一接口

    本类提供对 OpenAI、智谱AI、Silicon Flow、DeepSeek 等主流大模型服务的统一封装，
    内置：
    - 自动重试与指数退避
    - 请求缓存（1 小时 TTL）
    - 流式与非流式对话
    - 实时统计（请求量、Token 消耗、平均耗时、成功率）
    - 健康检查
    - 多线程安全的缓存清理

    使用示例：
        config = LLMConfig(
            provider="openai",
            api_key="sk-xxx",
            base_url="https://api.openai.com",
            model="gpt-4o"
        )
        operator = LLMOperator(config)
        response = await operator.chat_completion_async(
            [{"role":"user","content":"Hello"}]
        )
    """

    def __init__(self, config: LLMConfig):
        """
        初始化LLM操作器

        Args:
            config: LLM配置
        """
        self.config = config
        self.logger = self._setup_logger()

        # 创建适配器
        self.adapter = self._create_adapter()

        # 缓存机制
        self._cache: Dict[str, tuple] = {}
        self._cache_timeout = timedelta(hours=1)
        self._cache_lock = threading.RLock()

        # 统计信息
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "average_response_time": 0.0,
            "provider": config.provider,
            "model": config.model,
        }

        # 添加provider属性供测试访问
        self.provider = config.provider

        self.logger.debug(
            "LLMOperator initialized - Provider: %s, Model: %s",
            config.provider,
            config.model,
        )

    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器 - 使用控制台输出处理器"""
        logger = logging.getLogger(f"LLMOperator_{id(self)}")
        logger.propagate = False
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.DEBUG)
        return logger

    def _create_adapter(self) -> BaseLLMAdapter:
        """创建LLM适配器"""
        try:
            return create_llm_adapter(
                provider=self.config.provider,
                api_key=self.config.api_key,
                base_url=self.config.base_url,
                model=self.config.model,
                timeout=self.config.timeout / 1000,  # 转换为秒
                max_retries=self.config.max_retries,
            )
        except Exception as e:
            # 对于自定义提供商，使用OpenAI适配器作为默认适配器
            if self.config.provider == "custom":
                self.logger.info(
                    "Using OpenAIAdapter as default for custom provider"
                )
                return OpenAIAdapter(
                    api_key=self.config.api_key,
                    base_url=self.config.base_url,
                    model=self.config.model,
                    timeout=self.config.timeout / 1000,
                    max_retries=self.config.max_retries,
                )
            self.logger.error("Failed to create adapter: %s", str(e))
            raise

    def _generate_cache_key(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """生成缓存键"""
        content = json.dumps(
            {
                "messages": messages,
                "model": self.config.model,
                "provider": self.config.provider,
                "temperature": kwargs.get(
                    "temperature", self.config.temperature
                ),
                "max_tokens": kwargs.get(
                    "max_tokens", self.config.max_tokens
                ),
                **kwargs,
            },
            sort_keys=True,
        )
        return hashlib.sha256(content.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[LLMResponse]:
        """从缓存获取"""
        with self._cache_lock:
            if cache_key in self._cache:
                cache_time, response = self._cache[cache_key]
                if datetime.now() - cache_time < self._cache_timeout:
                    self.logger.debug("Cache hit for key: %s", cache_key)
                    return response
                else:
                    del self._cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, response: LLMResponse):
        """设置缓存"""
        with self._cache_lock:
            self._cache[cache_key] = (datetime.now(), response)
            self.logger.debug("Cache set for key: %s", cache_key)

            # 清理过期缓存
            self._cleanup_expired_cache()

    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        with self._cache_lock:
            current_time = datetime.now()
            expired_keys = []

            # 使用list避免在迭代时修改字典
            for key, (cache_time, _) in list(self._cache.items()):
                if current_time - cache_time > self._cache_timeout:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                self.logger.debug(
                    "Cleaned up %d expired cache entries", len(expired_keys)
                )

    def _update_stats(
        self,
        success: bool,
        response_time: float,
        usage: Optional[Dict[str, int]] = None,
    ):
        """更新统计信息"""
        self._stats["total_requests"] += 1
        if success:
            self._stats["successful_requests"] += 1
        else:
            self._stats["failed_requests"] += 1

        # 更新平均响应时间（使用移动平均算法）
        if self._stats["total_requests"] == 1:
            self._stats["average_response_time"] = response_time
        else:
            # 指数移动平均，给最近的响应时间更高权重
            alpha = 0.2  # 平滑因子
            self._stats["average_response_time"] = (
                alpha * response_time
                + (1 - alpha) * self._stats["average_response_time"]
            )

        # 更新token使用
        if usage:
            total_tokens = usage.get("total_tokens", 0)
            self._stats["total_tokens"] += total_tokens

            # 估算成本（基于OpenAI定价，每1K tokens $0.002）
            estimated_cost = (total_tokens / 1000) * 0.002
            self._stats["total_cost"] += estimated_cost

    def _should_retry(self, error: Union[Exception, UnifiedError]) -> bool:
        """判断是否应该重试"""
        if isinstance(error, UnifiedError):
            return error.retryable

        # 对于非UnifiedError的异常，进行具体类型判断
        retryable_errors = (
            TimeoutError,
            ConnectionError,
            asyncio.TimeoutError,
        )
        return isinstance(error, retryable_errors)

    def _calculate_backoff(self, attempt: int) -> float:
        """计算退避时间"""
        return min(2**attempt + (time.time() % 1), 60)

    def _prepare_request_params(
        self, kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """准备请求参数"""
        params = {
            "temperature": kwargs.get(
                "temperature", self.config.temperature
            ),
            "max_tokens": kwargs.get(
                "max_tokens", self.config.max_tokens
            ),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "frequency_penalty": kwargs.get(
                "frequency_penalty", self.config.frequency_penalty
            ),
            "presence_penalty": kwargs.get(
                "presence_penalty", self.config.presence_penalty
            ),
        }

        if self.config.response_format:
            params["response_format"] = self.config.response_format
        elif kwargs.get("response_format"):
            params["response_format"] = kwargs["response_format"]

        return params

    async def _maybe_wait_for_retry(
        self, attempt: int, error: Union[Exception, UnifiedError]
    ) -> bool:
        if attempt < self.config.max_retries and self._should_retry(error):
            backoff_time = self._calculate_backoff(attempt)
            self.logger.info("Retrying in %.2f seconds...", backoff_time)
            await asyncio.sleep(backoff_time)
            return True
        return False

    def _create_llm_error_from_unified_error(
        self, error: UnifiedError
    ) -> LLMError:
        return LLMError(
            error_type=error.error_type,
            error_message=error.error_message,
            status_code=error.status_code,
            retryable=error.retryable,
            details=error.details,
            provider=self.config.provider,
        )

    def _create_llm_error_from_exception(self, error: Exception) -> LLMError:
        return LLMError(
            error_type=type(error).__name__,
            error_message=str(error),
            retryable=self._should_retry(error),
            provider=self.config.provider,
        )

    async def _chat_completion_attempt(
        self,
        messages: List[Dict[str, str]],
        request_params: Dict[str, Any],
        attempt: int,
        start_time: float,
        use_cache: bool,
        cache_key: Optional[str],
    ) -> Optional[Union[LLMResponse, LLMError]]:
        self.logger.info(
            "Attempting API call (attempt %d) - Provider: %s",
            attempt + 1,
            self.config.provider,
        )

        try:
            response = await self.adapter.create_chat_completion(
                messages=messages, **request_params
            )
        except Exception as e:
            return await self._handle_exception(e, attempt, start_time)

        response_time = time.time() - start_time

        if isinstance(response, UnifiedResponse):
            return self._handle_success_response(
                response, response_time, use_cache, cache_key
            )
        if isinstance(response, UnifiedError):
            return await self._handle_unified_error(
                response, attempt, response_time
            )
        return None

    async def _chat_completion_with_retries(
        self,
        messages: List[Dict[str, str]],
        request_params: Dict[str, Any],
        start_time: float,
        use_cache: bool,
        cache_key: Optional[str],
    ) -> Union[LLMResponse, LLMError]:
        for attempt in range(self.config.max_retries + 1):
            result = await self._chat_completion_attempt(
                messages=messages,
                request_params=request_params,
                attempt=attempt,
                start_time=start_time,
                use_cache=use_cache,
                cache_key=cache_key,
            )
            if result is not None:
                return result

        return LLMError(
            error_type="MaxRetriesExceeded",
            error_message="Maximum retry attempts exceeded",
            retryable=False,
            provider=self.config.provider,
        )

    async def chat_completion_async(
        self,
        messages: List[Dict[str, str]],
        use_cache: Optional[bool] = None,
        **kwargs,
    ) -> Union[LLMResponse, LLMError]:
        """
        异步聊天完成（核心方法）

        Args:
            messages: 消息列表
            use_cache: 是否使用缓存（默认使用配置中的设置）
            **kwargs: 额外参数

        Returns:
            LLM响应或错误
        """
        start_time = time.time()
        use_cache = (
            use_cache if use_cache is not None else self.config.use_cache
        )

        # Check cache
        cache_key = None
        if use_cache:
            cache_key = self._generate_cache_key(messages, **kwargs)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                return cached_response

        request_params = self._prepare_request_params(kwargs)
        return await self._chat_completion_with_retries(
            messages=messages,
            request_params=request_params,
            start_time=start_time,
            use_cache=use_cache,
            cache_key=cache_key,
        )

    def _handle_success_response(
        self,
        response: UnifiedResponse,
        response_time: float,
        use_cache: bool,
        cache_key: Optional[str],
    ) -> LLMResponse:
        """处理成功响应"""
        llm_response = LLMResponse(
            content=response.content,
            model=response.model,
            usage=response.usage,
            finish_reason=response.finish_reason,
            response_time=response_time,
            status_code=response.status_code,
            headers=response.headers,
            provider=self.config.provider,
        )

        self._update_stats(True, response_time, response.usage)

        if use_cache and cache_key:
            self._set_cache(cache_key, llm_response)

        self.logger.info(
            "API call successful - Provider: %s, Model: %s, "
            "Response time: %.2fs",
            self.config.provider,
            response.model,
            response_time,
        )
        return llm_response

    async def _handle_unified_error(
        self, error: UnifiedError, attempt: int, response_time: float
    ) -> Optional[LLMError]:
        """处理UnifiedError"""
        if await self._maybe_wait_for_retry(attempt, error):
            return None

        # Final failure
        self._update_stats(False, response_time)
        self.logger.error(
            "API call failed after %d attempts - Provider: %s",
            attempt + 1,
            self.config.provider,
        )
        return self._create_llm_error_from_unified_error(error)

    async def _handle_exception(
        self, error: Exception, attempt: int, start_time: float
    ) -> Optional[LLMError]:
        """处理异常"""
        self.logger.error(
            "API call failed (attempt %d) - Provider: %s: %s",
            attempt + 1,
            self.config.provider,
            str(error),
        )

        if await self._maybe_wait_for_retry(attempt, error):
            return None

        # Final failure
        response_time = time.time() - start_time
        self._update_stats(False, response_time)

        error_obj = self._create_llm_error_from_exception(error)

        self.logger.error(
            "API call failed after %d attempts - Provider: %s",
            attempt + 1,
            self.config.provider,
        )
        return error_obj

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        use_cache: Optional[bool] = None,
        **kwargs,
    ) -> Union[LLMResponse, LLMError]:
        """
        同步聊天完成

        Args:
            messages: 消息列表
            use_cache: 是否使用缓存
            **kwargs: 额外参数

        Returns:
            LLM响应或错误
        """
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                return LLMError(
                    error_type="AsyncContextError",
                    error_message=(
                        "Cannot call synchronous chat_completion from an "
                        "asynchronous context. "
                        "Use chat_completion_async instead."
                    ),
                    provider=self.config.provider,
                    retryable=False,
                )
        except RuntimeError:
            pass

        return asyncio.run(
            self.chat_completion_async(messages, use_cache, **kwargs)
        )

    async def chat_completion_stream_async(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        异步流式聊天完成

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            流式响应块
        """
        try:
            self.logger.info(
                "Starting streaming API call - Provider: %s",
                self.config.provider,
            )

            async for chunk in self.adapter.create_chat_completion_stream(
                messages=messages,
                temperature=kwargs.get(
                    "temperature", self.config.temperature
                ),
                max_tokens=kwargs.get(
                    "max_tokens", self.config.max_tokens
                ),
                top_p=kwargs.get("top_p", self.config.top_p),
            ):
                # 添加提供商信息
                if "provider" not in chunk:
                    chunk["provider"] = self.config.provider
                yield chunk

        except Exception as e:
            self.logger.error(
                "Streaming API call failed - Provider: %s: %s",
                self.config.provider,
                str(e),
            )
            yield {
                "error": str(e),
                "error_type": type(e).__name__,
                "provider": self.config.provider,
            }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = 0.0
        if self._stats["total_requests"] > 0:
            success_rate = (
                self._stats["successful_requests"]
                / self._stats["total_requests"]
            )
        # 计算平均token使用量
        avg_tokens_per_request = 0.0
        if self._stats["total_requests"] > 0:
            avg_tokens_per_request = (
                self._stats["total_tokens"] / self._stats["total_requests"]
            )

        return {
            "total_requests": self._stats["total_requests"],
            "successful_requests": self._stats["successful_requests"],
            "failed_requests": self._stats["failed_requests"],
            "success_rate": success_rate,
            "total_tokens": self._stats["total_tokens"],
            "avg_tokens_per_request": avg_tokens_per_request,
            "total_cost": self._stats["total_cost"],
            "average_response_time": self._stats["average_response_time"],
            "cache_size": len(self._cache),
            "provider": self._stats["provider"],
            "model": self._stats["model"],
            "base_url": self.config.base_url,
            "timestamp": datetime.now().isoformat(),
        }

    def clear_cache(self):
        """清除缓存"""
        with self._cache_lock:
            cache_size = len(self._cache)
            self._cache.clear()
            self.logger.info("Cache cleared - %s entries removed", cache_size)

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._cache_lock:
            total_entries = len(self._cache)
            expired_entries = 0
            current_time = datetime.now()

            for _, (cache_time, _) in self._cache.items():
                if current_time - cache_time > self._cache_timeout:
                    expired_entries += 1

            return {
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "valid_entries": total_entries - expired_entries,
                "cache_timeout_hours": (
                    self._cache_timeout.total_seconds() / 3600
                ),
                "memory_usage_estimate": total_entries * 1024,
            }

    def reset_stats(self):
        """重置统计信息"""
        self._stats.update(
            {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "average_response_time": 0.0,
            }
        )
        self.logger.info("Statistics reset")

    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "base_url": self.config.base_url,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "max_tokens": self.config.max_tokens,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
            "enable_cache": self.config.enable_cache,
            "cache_timeout_hours": (
                self._cache_timeout.total_seconds() / 3600
            ),
            "enable_streaming": self.config.enable_streaming,
        }

    async def health_check_async(self) -> Dict[str, Any]:
        """异步健康检查"""
        try:
            # 简单的健康检查请求
            messages = [{"role": "user", "content": "Hello"}]
            response = await self.chat_completion_async(
                messages, use_cache=False, max_tokens=10
            )

            if isinstance(response, LLMResponse):
                return {
                    "status": "healthy",
                    "provider": response.provider,
                    "model": response.model,
                    "response_time": response.response_time,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                return {
                    "status": "unhealthy",
                    "provider": self.config.provider,
                    "error": response.error_message,
                    "timestamp": datetime.now().isoformat(),
                }
        except Exception as e:
            return {
                "status": "error",
                "provider": self.config.provider,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                return {
                    "status": "error",
                    "provider": self.config.provider,
                    "error": (
                        "Cannot call synchronous health_check from an "
                        "asynchronous context. Use health_check_async instead."
                    ),
                    "timestamp": datetime.now().isoformat(),
                }
        except RuntimeError:
            pass

        return asyncio.run(self.health_check_async())

    def __del__(self):
        """析构函数"""
        if hasattr(self, "logger"):
            self.logger.info(
                "LLMOperator destroyed - Provider: %s", self.config.provider
            )


# 工厂函数
def create_enhanced_llm_operator(
    provider: str,
    api_key: str,
    model: str = None,
    base_url: str = None,
    timeout: int = 30000,
    max_retries: int = 3,
    max_tokens: int = 2000,
    temperature: float = 0.1,
    use_cache: bool = True,
    **kwargs,
) -> LLMOperator:
    """
    创建增强版LLM操作器的工厂函数

    Args:
        provider: 提供商名称 (openai, zhipuai, silicon_flow, deepseek)
        api_key: API密钥
        model: 模型名称（可选，使用预设配置）
        base_url: 基础URL（可选，使用预设配置）
        timeout: 超时时间（毫秒）
        max_retries: 最大重试次数
        max_tokens: 最大token数
        temperature: 温度参数
        use_cache: 是否使用缓存
        **kwargs: 其他参数

    Returns:
        LLMOperator实例
    """
    # 获取预设配置
    if provider in PRESET_CONFIGS:
        preset = PRESET_CONFIGS[provider].copy()
        preset["api_key"] = api_key
        preset["timeout"] = timeout
        preset["max_retries"] = max_retries
        preset["max_tokens"] = max_tokens
        preset["temperature"] = temperature
        preset["use_cache"] = use_cache

        if model:
            preset["model"] = model
        if base_url:
            preset["base_url"] = base_url
        preset.update(kwargs)

        config = LLMConfig(**preset)
    else:
        # 自定义配置
        if not model or not base_url:
            raise ValueError("自定义提供商需要提供model和base_url参数")

        config = LLMConfig(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            timeout=timeout,
            max_retries=max_retries,
            max_tokens=max_tokens,
            temperature=temperature,
            use_cache=use_cache,
            **kwargs,
        )

    return LLMOperator(config)


# 便捷函数
def create_openai_operator(
    api_key: str, model: str = "gpt-3.5-turbo", **kwargs
) -> LLMOperator:
    """创建OpenAI操作器"""
    return create_enhanced_llm_operator(
        provider="openai", api_key=api_key, model=model, **kwargs
    )


def create_zhipuai_operator(
    api_key: str, model: str = "glm-4.6", **kwargs
) -> LLMOperator:
    """创建智谱AI操作器"""
    return create_enhanced_llm_operator(
        provider="zhipuai", api_key=api_key, model=model, **kwargs
    )


def create_silicon_flow_operator(
    api_key: str, model: str = "deepseek-ai/DeepSeek-V3.2-Exp", **kwargs
) -> LLMOperator:
    """创建SiliconFlow操作器"""
    return create_enhanced_llm_operator(
        provider="silicon_flow", api_key=api_key, model=model, **kwargs
    )


def create_deepseek_operator(
    api_key: str, model: str = "deepseek-chat", **kwargs
) -> LLMOperator:
    """创建DeepSeek操作器"""
    return create_enhanced_llm_operator(
        provider="deepseek", api_key=api_key, model=model, **kwargs
    )
