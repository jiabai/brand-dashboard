from typing import Any, AsyncGenerator, Dict, List, Union

from .llm_adapter_base import BaseLLMAdapter, UnifiedError, UnifiedResponse

try:
    from zai import ZhipuAiClient

    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False


class ZhipuAIAdapter(BaseLLMAdapter):
    """智谱AI SDK适配器"""

    def __init__(self, api_key: str, base_url: str, model: str, **kwargs):
        super().__init__(api_key, base_url, model, **kwargs)

        if not ZHIPUAI_AVAILABLE:
            raise ImportError(
                "智谱AI SDK未安装，请安装: pip install zai-sdk"
            )

        base_url_override = (
            base_url
            if base_url != "https://open.bigmodel.cn/api/paas/v4"
            else None
        )
        if base_url_override:
            self.client = ZhipuAiClient(
                api_key=api_key, base_url=base_url_override
            )
        else:
            self.client = ZhipuAiClient(api_key=api_key)

    async def create_chat_completion(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Union[UnifiedResponse, UnifiedError]:
        """创建智谱AI聊天完成"""
        import asyncio
        import time

        start_time = time.time()

        try:
            request_params = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.1),
                "max_tokens": kwargs.get("max_tokens", 2000),
                "top_p": kwargs.get("top_p", 0.9),
                "thinking": {"type": "disabled"},
            }

            if kwargs.get("response_format"):
                request_params["response_format"] = kwargs["response_format"]

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(**request_params),
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
        """创建智谱AI流式聊天完成"""
        import asyncio

        request_params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.1),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "top_p": kwargs.get("top_p", 1.0),
            "thinking": {"type": "disabled"},
            "stream": True,
        }

        if kwargs.get("response_format"):
            request_params["response_format"] = kwargs["response_format"]

        try:
            stream = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(**request_params),
            )

            for chunk in stream:
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
            "ConnectionError",
            "TimeoutError",
        )
        return type(error).__name__ in retryable_errors
