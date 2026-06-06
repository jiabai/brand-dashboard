from typing import Any, AsyncGenerator, Dict, List, Union

from openai import AsyncOpenAI, OpenAI
from .llm_adapter_base import BaseLLMAdapter, UnifiedError, UnifiedResponse


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI SDK适配器"""

    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(api_key, base_url, model, **kwargs)

        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=kwargs.get("timeout", 30),
        )

        self.sync_client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=kwargs.get("timeout", 30),
        )

    async def create_chat_completion(
        self, messages: List[Dict[str, str]], **kwargs
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

            if "response_format" in kwargs:
                request_params["response_format"] = kwargs["response_format"]

            response = await self.async_client.chat.completions.create(
                **request_params
            )

            response_time = time.time() - start_time

            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": (
                    response.usage.prompt_tokens if response.usage else 0
                ),
                "completion_tokens": (
                    response.usage.completion_tokens if response.usage else 0
                ),
                "total_tokens": (
                    response.usage.total_tokens if response.usage else 0
                ),
            }

            return UnifiedResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                response_time=response_time,
            )

        except Exception as e:
            response_time = time.time() - start_time

            return UnifiedError(
                error_type=type(e).__name__,
                error_message=str(e),
                status_code=getattr(e, "status_code", None),
                retryable=self._is_retryable_error(e),
            )

    async def create_chat_completion_stream(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """创建OpenAI流式聊天完成"""
        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "top_p": kwargs.get("top_p", 1.0),
            "stream": True,
        }

        try:
            stream = await self.async_client.chat.completions.create(
                **request_params
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield {
                        "content": chunk.choices[0].delta.content,
                        "model": chunk.model,
                        "finish_reason": chunk.choices[0].finish_reason,
                    }

        except Exception as e:
            yield {"error": str(e), "error_type": type(e).__name__}

    def _is_retryable_error(self, error: Exception) -> bool:
        """判断是否为可重试错误"""
        retryable_errors = (
            "RateLimitError",
            "APIError",
            "Timeout",
            "APIConnectionError",
            "ConnectionError",
            "TimeoutError",
        )
        return type(error).__name__ in retryable_errors
