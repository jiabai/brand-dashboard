"""
测试流程中使用LLM Mock的示例脚本
"""

from src.core.llm_operator import LLMError, LLMResponse
from tests.llm_mock import create_mock_error_operator, create_mock_llm_operator


def test_mock_in_test_flow():
    """在测试流程中使用LLM Mock的示例"""
    print("=== 测试流程中使用LLM Mock的示例 ===")

    # 1. 创建模拟成功响应的LLM操作器
    print("\n1. 创建模拟成功响应的LLM操作器：")
    mock_operator = create_mock_llm_operator(
        mock_content=(
            "这是一个品牌提及的模拟响应，品牌：[苹果公司]，"
            "情绪：[正面]，是否首位提及：[是]"
        ),
        mock_usage={
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        },
        mock_response_time=0.2,
    )

    # 2. 使用模拟操作器进行测试
    print("\n2. 使用模拟操作器处理品牌提及检测请求：")
    messages = [
        {
            "role": "system",
            "content": (
                "你是一个品牌分析师，负责检测文本中是否提及指定品牌，"
                "情绪如何，是否首位提及。"
            ),
        },
        {"role": "user", "content": "苹果公司的新产品非常棒，我很喜欢！"},
    ]

    response = mock_operator.chat_completion(messages)

    if isinstance(response, LLMResponse):
        print("   ✅ 模拟响应成功：")
        print(f"      响应内容: {response.content}")
        print(f"      模型: {response.model}")
        print(f"      Token使用: {response.usage}")
        print(f"      响应时间: {response.response_time:.2f}秒")
    else:
        print(f"   ❌ 模拟响应失败: {response}")

    # 3. 测试错误响应场景
    print("\n3. 测试错误响应场景：")
    error_operator = create_mock_error_operator(
        error_type="RateLimitError",
        error_message="请求频率过高，请稍后重试",
        status_code=429,
        retryable=True,
    )

    error_response = error_operator.chat_completion(messages)

    if isinstance(error_response, LLMError):
        print("   ✅ 错误响应模拟成功：")
        print(f"      错误类型: {error_response.error_type}")
        print(f"      错误消息: {error_response.error_message}")
        print(f"      状态码: {error_response.status_code}")
        print(f"      可重试: {error_response.retryable}")
    else:
        print(f"   ❌ 错误响应模拟失败: {error_response}")

    # 4. 展示如何在插件测试中使用
    print("\n4. 在插件测试中使用示例：")
    print("   # 伪代码示例：")
    print("   def test_mention_status_plugin():")
    print("       # 创建模拟LLM操作器")
    print("       mock_operator = create_mock_llm_operator(")
    print(
        "           mock_content='品牌：[苹果公司]，情绪：[正面]，"
        "是否首位提及：[是]'"
    )
    print("       )")
    print("       ")
    print("       # 将模拟操作器注入到插件中（根据插件实现方式调整）")
    print("       plugin = MentionStatusPlugin()")
    print("       plugin.llm_operator = mock_operator")
    print("       ")
    print("       # 执行插件测试")
    print("       result = plugin.analyze('苹果公司的产品很棒')")
    print("       assert result['is_mentioned'] == True")
    print("       assert result['sentiment'] == 'positive'")

    print("\n✅ 所有示例测试完成！")


if __name__ == "__main__":
    test_mock_in_test_flow()
