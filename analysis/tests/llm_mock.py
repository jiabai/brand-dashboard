"""
LLM模拟工具 - 用于测试环境中模拟LLM配置和响应
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from src.core.llm_adapters import (
    BaseLLMAdapter,
    LLMFactory,
    UnifiedError,
    UnifiedResponse,
)
from src.core.llm_operator import LLMConfig, LLMError, LLMOperator, LLMResponse


@dataclass
class MockResponseConfig:
    """模拟响应配置"""

    content: str = "这是一个模拟的LLM响应"
    model: str = "mock-model"
    usage: Dict[str, int] = None
    finish_reason: str = "stop"
    status_code: int = 200
    response_time: float = 0.5
    error: Optional[Dict[str, Any]] = None


class MockLLMAdapter(BaseLLMAdapter):
    """模拟LLM适配器 - 用于测试环境"""

    def __init__(
        self,
        api_key: str = "mock-api-key",
        base_url: str = "http://mock.llm",
        model: str = "mock-model",
        **kwargs,
    ):
        super().__init__(api_key, base_url, model, **kwargs)
        self.mock_responses: Dict[str, MockResponseConfig] = {}
        self.default_response = MockResponseConfig(
            content=kwargs.get("mock_content", "这是一个模拟的LLM响应"),
            model=model,
            usage=kwargs.get(
                "mock_usage",
                {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            ),
            finish_reason=kwargs.get("mock_finish_reason", "stop"),
            response_time=kwargs.get("mock_response_time", 0.5),
        )
        self.logger = logging.getLogger("MockLLMAdapter")
        self.logger.info("MockLLMAdapter initialized")

    def set_mock_response(
        self, message_content: str, response_config: MockResponseConfig
    ):
        """设置特定消息的模拟响应"""
        self.mock_responses[message_content] = response_config

    def clear_mock_responses(self):
        """清除所有模拟响应"""
        self.mock_responses.clear()

    async def create_chat_completion(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> Union[UnifiedResponse, UnifiedError]:
        """创建模拟的聊天完成响应"""
        self.logger.debug(
            "Mock chat completion called with messages: %s", messages
        )
        time.sleep(self.default_response.response_time)

        # 检查是否有针对最后一条消息的特定响应
        if messages:
            last_message = messages[-1]["content"]
            if last_message in self.mock_responses:
                response_config = self.mock_responses[last_message]
            else:
                response_config = self.default_response
        else:
            response_config = self.default_response

        # 如果配置了错误，返回错误响应
        if response_config.error:
            return UnifiedError(
                error_type=response_config.error.get("type", "MockError"),
                error_message=response_config.error.get("message", "模拟错误"),
                status_code=response_config.error.get("status_code", 500),
                retryable=response_config.error.get("retryable", True),
            )

        # 返回成功响应
        return UnifiedResponse(
            content=response_config.content,
            model=response_config.model,
            usage=response_config.usage
            or {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
            finish_reason=response_config.finish_reason,
            response_time=response_config.response_time,
            status_code=response_config.status_code,
        )

    async def create_chat_completion_stream(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """创建模拟的流式聊天完成响应"""
        self.logger.debug(
            "Mock streaming chat completion called with messages: %s", messages
        )

        # 模拟流式响应
        response_content = self.default_response.content
        for i, char in enumerate(response_content):
            yield {
                "content": char,
                "model": self.default_response.model,
                "finish_reason": (
                    None
                    if i < len(response_content) - 1
                    else self.default_response.finish_reason
                ),
            }
            # 模拟流式传输延迟
            time.sleep(0.05)


# 注册Mock适配器
def register_mock_adapter():
    """注册模拟适配器到LLM工厂"""
    LLMFactory.register_adapter("mock", MockLLMAdapter)
    logging.info("MockLLMAdapter registered successfully")


# 创建Mock LLM操作器的便捷函数
def create_mock_llm_operator(
    mock_content: str = "这是一个模拟的LLM响应",
    mock_usage: Dict[str, int] = None,
    mock_response_time: float = 0.5,
    **kwargs,
) -> LLMOperator:
    """
    创建模拟的LLM操作器 - 用于测试环境

    Args:
        mock_content: 模拟响应的内容
        mock_usage: 模拟的token使用情况
        mock_response_time: 模拟的响应时间（秒）
        **kwargs: 其他配置参数

    Returns:
        LLMOperator: 配置了Mock适配器的LLM操作器
    """
    # 确保Mock适配器已注册
    if "mock" not in LLMFactory._adapters:
        register_mock_adapter()

    # 创建模拟配置
    config = LLMConfig(
        provider="mock",
        api_key="mock-api-key",
        base_url="http://mock.llm",
        model="mock-model",
        timeout=5000,
        max_retries=0,
        **kwargs,
    )

    # 创建操作器
    operator = LLMOperator(config)

    # 配置Mock适配器
    if isinstance(operator.adapter, MockLLMAdapter):
        operator.adapter.default_response = MockResponseConfig(
            content=mock_content,
            usage=mock_usage
            or {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
            response_time=mock_response_time,
        )

    return operator


# 创建返回错误的模拟LLM操作器
def create_mock_error_operator(
    error_type: str = "APIError",
    error_message: str = "模拟API错误",
    status_code: int = 500,
    retryable: bool = True,
    **kwargs,
) -> LLMOperator:
    """
    创建返回错误的模拟LLM操作器 - 用于测试错误处理

    Args:
        error_type: 错误类型
        error_message: 错误消息
        status_code: 状态码
        retryable: 是否可重试
        **kwargs: 其他配置参数

    Returns:
        LLMOperator: 配置了错误响应的Mock LLM操作器
    """
    operator = create_mock_llm_operator(**kwargs)

    if isinstance(operator.adapter, MockLLMAdapter):
        operator.adapter.default_response.error = {
            "type": error_type,
            "message": error_message,
            "status_code": status_code,
            "retryable": retryable,
        }

    return operator


# 上下文管理器：临时设置模拟响应
def mock_llm_response(config: MockResponseConfig):
    """
    上下文管理器：临时设置模拟响应

    Example:
        with mock_llm_response(MockResponseConfig(content="自定义响应")):
            response = operator.chat_completion(
                [{"role": "user", "content": "测试"}]
            )
    """

    class MockContext:
        def __enter__(self):
            register_mock_adapter()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            # 清理操作
            pass

    return MockContext()


# 测试辅助函数
def test_mock_llm():
    """测试模拟LLM功能"""
    print("测试模拟LLM功能...")

    # 创建模拟操作器
    operator = create_mock_llm_operator(
        mock_content="这是一个测试响应",
        mock_usage={
            "prompt_tokens": 5,
            "completion_tokens": 15,
            "total_tokens": 20,
        },
        mock_response_time=0.3,
    )

    # 测试同步聊天完成
    messages = [{"role": "user", "content": "你好，测试"}]
    response = operator.chat_completion(messages)

    if isinstance(response, LLMResponse):
        print("✅ 同步聊天完成测试通过")
        print(f"   响应内容: {response.content}")
        print(f"   模型: {response.model}")
        print(f"   Token使用: {response.usage}")
        print(f"   响应时间: {response.response_time:.2f}秒")
    else:
        print(f"❌ 同步聊天完成测试失败: {response}")

    # 测试错误响应
    error_operator = create_mock_error_operator(
        error_type="RateLimitError",
        error_message="请求频率过高",
        status_code=429,
        retryable=True,
    )

    error_response = error_operator.chat_completion(messages)
    if isinstance(error_response, LLMError):
        print("✅ 错误响应测试通过")
        print(f"   错误类型: {error_response.error_type}")
        print(f"   错误消息: {error_response.error_message}")
        print(f"   状态码: {error_response.status_code}")
        print(f"   可重试: {error_response.retryable}")
    else:
        print(f"❌ 错误响应测试失败: {error_response}")

    print("模拟LLM功能测试完成！")


if __name__ == "__main__":
    test_mock_llm()
