"""
统一LLM操作器测试
测试OpenAI和智谱AI SDK的兼容性
"""

import os
from unittest.mock import patch

import pytest

from src.core.llm_adapters import UnifiedError, UnifiedResponse
from src.core.llm_operator import (
    LLMError,
    create_enhanced_llm_operator,
    create_openai_operator,
    create_zhipuai_operator,
)


class TestUnifiedLLMOperator:
    """测试统一LLM操作器"""

    def setup_method(self):
        """测试前的设置"""
        self.test_messages = [
            {"role": "system", "content": "你是一个有用的AI助手。"},
            {"role": "user", "content": "你好，请介绍一下自己。"},
        ]

    @pytest.mark.asyncio
    async def test_openai_operator_creation(self):
        """测试OpenAI操作器创建"""
        operator = create_openai_operator(
            api_key="test-api-key", model="gpt-3.5-turbo"
        )

        assert operator is not None
        assert operator.provider == "openai"
        assert operator.config.model == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_zhipuai_operator_creation(self):
        """测试智谱AI操作器创建"""
        operator = create_zhipuai_operator(
            api_key="test-api-key", model="glm-4.6"
        )

        assert operator is not None
        assert operator.provider == "zhipuai"
        assert operator.config.model == "glm-4.6"

    @pytest.mark.asyncio
    async def test_custom_operator_creation(self):
        """测试自定义操作器创建"""
        operator = create_enhanced_llm_operator(
            provider="custom",
            api_key="test-api-key",
            base_url="https://custom-api.com/v1",
            model="custom-model",
        )

        assert operator is not None
        assert operator.provider == "custom"
        assert operator.config.model == "custom-model"

    @patch("src.core.llm_adapters.OpenAIAdapter.create_chat_completion")
    @pytest.mark.asyncio
    async def test_openai_chat_completion(self, mock_create):
        """测试OpenAI聊天完成"""
        # 模拟响应
        mock_response = UnifiedResponse(
            content="你好！我是一个AI助手，很高兴为你提供帮助。",
            model="gpt-3.5-turbo",
            usage={
                "total_tokens": 50,
                "prompt_tokens": 20,
                "completion_tokens": 30,
            },
            finish_reason="stop",
            response_time=1.2,
        )
        mock_create.return_value = mock_response

        operator = create_openai_operator(
            api_key="test-api-key", model="gpt-3.5-turbo"
        )

        response = await operator.chat_completion_async(self.test_messages)

        assert hasattr(response, "content")
        assert hasattr(response, "model")
        assert response.model == "gpt-3.5-turbo"
        assert "AI助手" in response.content

    @patch("src.core.llm_adapters.ZhipuAIAdapter.create_chat_completion")
    @pytest.mark.asyncio
    async def test_zhipuai_chat_completion(self, mock_create):
        """测试智谱AI聊天完成"""
        # 模拟响应
        mock_response = UnifiedResponse(
            content="你好！我是智谱AI助手，很高兴为你提供帮助。",
            model="glm-4.6",
            usage={
                "total_tokens": 45,
                "prompt_tokens": 18,
                "completion_tokens": 27,
            },
            finish_reason="stop",
            response_time=0.8,
        )
        mock_create.return_value = mock_response

        operator = create_zhipuai_operator(
            api_key="test-api-key", model="glm-4.6"
        )

        response = await operator.chat_completion_async(self.test_messages)

        assert hasattr(response, "content")
        assert hasattr(response, "model")
        assert response.model == "glm-4.6"
        assert "智谱AI助手" in response.content

    @patch("src.core.llm_adapters.OpenAIAdapter.create_chat_completion")
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_create):
        """测试错误处理"""
        # 模拟错误响应
        mock_error = UnifiedError(
            error_message="API密钥无效",
            error_type="authentication_error",
            status_code=401,
            retryable=False,
        )
        mock_create.return_value = mock_error

        operator = create_openai_operator(
            api_key="invalid-api-key", model="gpt-3.5-turbo"
        )

        response = await operator.chat_completion_async(self.test_messages)

        assert hasattr(response, "error_message")
        assert hasattr(response, "error_type")
        assert hasattr(response, "status_code")
        assert response.error_type == "authentication_error"
        assert response.status_code == 401

    @patch("src.core.llm_adapters.OpenAIAdapter.create_chat_completion_stream")
    @pytest.mark.asyncio
    async def test_streaming_response(self, mock_create_stream):
        """测试流式响应"""

        # 模拟流式响应
        async def mock_stream():
            yield {"content": "你好"}
            yield {"content": "！我是"}
            yield {"content": "AI助手"}
            yield {"content": "。"}

        mock_create_stream.return_value = mock_stream()

        operator = create_openai_operator(
            api_key="test-api-key", model="gpt-3.5-turbo"
        )

        chunks = []
        async for chunk in operator.chat_completion_stream_async(
            self.test_messages
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_content = "".join(
            [chunk.get("content", "") for chunk in chunks]
        )
        assert "你好" in full_content
        assert "AI助手" in full_content

    def test_sync_chat_completion(self):
        """测试同步聊天完成"""
        operator = create_openai_operator(
            api_key="test-api-key", model="gpt-3.5-turbo"
        )

        # 由于同步方法内部调用异步方法，我们测试其存在性
        assert hasattr(operator, "chat_completion")
        assert callable(operator.chat_completion)

    def test_stats_and_cache(self):
        """测试统计和缓存功能"""
        operator = create_openai_operator(
            api_key="test-api-key",
            model="gpt-3.5-turbo",
            use_cache=True,
        )

        # 测试统计功能
        stats = operator.get_stats()
        assert isinstance(stats, dict)
        assert "total_requests" in stats
        assert "success_rate" in stats
        assert "average_response_time" in stats

        # 测试缓存功能
        assert hasattr(operator, "clear_cache")
        assert callable(operator.clear_cache)

        # 测试健康检查
        health = operator.health_check()
        assert isinstance(health, dict)
        assert "status" in health

    def test_provider_configurations(self):
        """测试不同提供商的配置"""
        # 测试OpenAI配置
        openai_operator = create_openai_operator(
            api_key="test-api-key",
            model="gpt-4",
            temperature=0.8,
            max_tokens=1000,
        )

        assert openai_operator.config.temperature == 0.8
        assert openai_operator.config.max_tokens == 1000

        # 测试智谱AI配置
        zhipuai_operator = create_zhipuai_operator(
            api_key="test-api-key",
            model="glm-4.6",
            temperature=0.6,
            max_tokens=800,
        )

        assert zhipuai_operator.config.temperature == 0.6
        assert zhipuai_operator.config.max_tokens == 800


class TestIntegration:
    """集成测试（需要真实的API密钥）"""

    @pytest.mark.skipif(
        os.getenv("RUN_LLM_LIVE_TESTS") != "1"
        or not os.getenv("OPENAI_API_KEY"),
        reason="需要 RUN_LLM_LIVE_TESTS=1 且设置 OPENAI_API_KEY",
    )
    @pytest.mark.asyncio
    async def test_openai_real_api(self):
        """测试真实的OpenAI API"""
        operator = create_openai_operator(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-3.5-turbo",
        )

        messages = [
            {"role": "user", "content": "你好，请用一句话介绍自己。"}
        ]

        response = await operator.chat_completion_async(messages)

        if isinstance(response, LLMError) and response.status_code == 401:
            pytest.skip("OPENAI_API_KEY 无效或无权限")

        assert hasattr(response, "content")
        assert len(response.content) > 0
        assert response.provider == "openai"
        print(f"OpenAI响应: {response.content}")

    @pytest.mark.skipif(
        os.getenv("RUN_LLM_LIVE_TESTS") != "1" or not os.getenv("LLM_API_KEY"),
        reason="需要 RUN_LLM_LIVE_TESTS=1 且设置 LLM_API_KEY",
    )
    @pytest.mark.asyncio
    async def test_zhipuai_real_api(self):
        """测试真实的智谱AI API"""
        operator = create_zhipuai_operator(
            api_key=os.getenv("LLM_API_KEY"),
            model="glm-4.6",
        )

        messages = [
            {"role": "user", "content": "你好，请用一句话介绍自己。"}
        ]

        response = await operator.chat_completion_async(messages)

        if isinstance(response, LLMError) and response.status_code in {
            401,
            403,
        }:
            pytest.skip("LLM_API_KEY 无效或无权限")

        assert hasattr(response, "content")
        assert len(response.content) > 0
        assert response.provider == "zhipuai"
        print(f"智谱AI响应: {response.content}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
