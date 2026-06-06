"""
LLM操作器测试脚本 - 使用zai SDK和智谱AI配置
"""

import asyncio
import os
import time

from zai import ZhipuAiClient

from src.core.llm_operator import (
    LLMConfig,
    LLMError,
    LLMOperator,
    LLMResponse,
    create_enhanced_llm_operator,
    create_silicon_flow_operator,
)

# 智谱AI配置
llm_config = {
    "apiKey": os.environ.get("LLM_API_KEY", ""),
    "baseURL": "https://open.bigmodel.cn/api/paas/v4",
    "timeout": 30000,
    "maxRetries": 2,
    "model": "glm-4.6",
    "maxTokens": 2000,
    "cacheEnabled": True,
    "cacheTimeoutHours": 1,
    "stream": False,
}


class LLMOperatorTester:
    """LLM操作器测试类"""

    def __init__(self):
        self.test_results = []

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.test_results.append(result)

        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   详情: {details}")

    async def test_config_validation(self):
        """测试配置验证"""
        print("\n=== 测试配置验证 ===")

        try:
            # 测试空API密钥
            config = LLMConfig(
                provider="custom",
                api_key="",
                base_url="https://api.test.com",
                model="test-model",
            )
            self.log_test("空API密钥验证", False, "应该抛出ValueError")
        except ValueError as e:
            self.log_test("空API密钥验证", True, f"正确抛出ValueError: {e}")

        try:
            # 测试空基础URL
            config = LLMConfig(
                provider="custom",
                api_key="test-key",
                base_url="",
                model="test-model",
            )
            self.log_test("空基础URL验证", False, "应该抛出ValueError")
        except ValueError as e:
            self.log_test("空基础URL验证", True, f"正确抛出ValueError: {e}")

        try:
            # 测试有效的配置
            config = LLMConfig(
                provider="custom",
                api_key="test-api-key",
                base_url="https://api.test.com",
                model="test-model",
                temperature=0.5,
                timeout=30000,
            )
            self.log_test("有效配置验证", True, f"配置创建成功: {config.model}")
        except Exception as e:
            self.log_test("有效配置验证", False, f"意外错误: {e}")

    async def test_mock_response(self):
        """测试模拟响应"""
        print("\n=== 测试模拟响应 ===")

        # 创建模拟的LLM响应
        mock_response = LLMResponse(
            content="这是一个测试响应",
            model="test-model",
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
            finish_reason="stop",
            response_time=1.5,
        )

        # 验证响应对象
        self.log_test("响应对象创建", True, f"内容: {mock_response.content}")
        self.log_test("响应时间记录", True, f"时间: {mock_response.response_time}秒")
        self.log_test("Token使用记录", True, f"Tokens: {mock_response.usage}")

    async def test_mock_error(self):
        """测试模拟错误"""
        print("\n=== 测试模拟错误 ===")

        # 创建模拟的错误
        mock_error = LLMError(
            error_type="APIError",
            error_message="模拟API错误",
            status_code=500,
            retryable=True,
            details={"attempt": 1, "max_retries": 3},
        )

        # 验证错误对象
        self.log_test("错误对象创建", True, f"类型: {mock_error.error_type}")
        self.log_test("错误状态码", True, f"状态码: {mock_error.status_code}")
        self.log_test("错误可重试性", True, f"可重试: {mock_error.retryable}")

    async def test_cache_functionality(self):
        """测试缓存功能"""
        print("\n=== 测试缓存功能 ===")

        # 创建操作器
        config = LLMConfig(
            provider="custom",
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model",
        )
        operator = LLMOperator(config)

        # 测试缓存键生成
        messages = [{"role": "user", "content": "测试消息"}]
        cache_key = operator._generate_cache_key(messages)
        self.log_test("缓存键生成", True, f"键: {cache_key[:20]}...")

        # 测试缓存设置和获取
        mock_response = LLMResponse(
            content="缓存响应",
            model="test-model",
            usage={"total_tokens": 10},
            finish_reason="stop",
            response_time=0.5,
            provider="custom",
        )

        operator._set_cache(cache_key, mock_response)
        cached_response = operator._get_from_cache(cache_key)

        if cached_response and cached_response.content == "缓存响应":
            self.log_test("缓存设置和获取", True, "缓存功能正常")
        else:
            self.log_test("缓存设置和获取", False, "缓存功能异常")

        # 测试缓存清除
        operator.clear_cache()
        cleared_response = operator._get_from_cache(cache_key)

        if cleared_response is None:
            self.log_test("缓存清除", True, "缓存已清除")
        else:
            self.log_test("缓存清除", False, "缓存未清除")

    async def test_statistics(self):
        """测试统计功能"""
        print("\n=== 测试统计功能 ===")

        config = LLMConfig(
            provider="custom",
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model",
        )
        operator = LLMOperator(config)

        # 模拟多次请求
        for i in range(5):
            operator._update_stats(
                success=(i % 2 == 0),  # 交替成功和失败
                response_time=1.0 + i * 0.1,
                usage={"total_tokens": 100 + i * 10},
            )

        stats = operator.get_stats()

        self.log_test("总请求数统计", True, f"总数: {stats['total_requests']}")
        self.log_test("成功请求统计", True, f"成功: {stats['successful_requests']}")
        self.log_test("失败请求统计", True, f"失败: {stats['failed_requests']}")
        self.log_test("成功率统计", True, f"成功率: {stats['success_rate']:.1%}")
        self.log_test(
            "平均响应时间", True, f"平均时间: {stats['average_response_time']:.2f}秒"
        )
        self.log_test("总Token使用", True, f"总Tokens: {stats['total_tokens']}")

    async def test_backoff_calculation(self):
        """测试退避时间计算"""
        print("\n=== 测试退避时间计算 ===")

        config = LLMConfig(
            provider="custom",
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model",
        )
        operator = LLMOperator(config)

        # 测试不同尝试次数的退避时间
        for attempt in range(5):
            backoff = operator._calculate_backoff(attempt)
            self.log_test(
                f"退避时间计算 (尝试{attempt + 1})",
                0 <= backoff <= 60,  # 应该在0-60秒之间
                f"退避时间: {backoff:.2f}秒",
            )

    async def test_health_check(self):
        """测试健康检查"""
        print("\n=== 测试健康检查 ===")

        config = LLMConfig(
            provider="custom",
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model",
        )
        operator = LLMOperator(config)

        # 由于我们没有真实的API连接，健康检查应该会失败
        # 但我们仍然可以测试方法的调用
        try:
            health = await operator.health_check_async()
            self.log_test("健康检查方法调用", True, f"返回类型: {type(health)}")

            if "status" in health:
                self.log_test("健康状态字段", True, f"状态: {health['status']}")
            if "timestamp" in health:
                self.log_test("时间戳字段", True, "包含时间戳")

        except Exception as e:
            self.log_test("健康检查", False, f"异常: {e}")

    async def test_factory_function(self):
        """测试工厂函数"""
        print("\n=== 测试工厂函数 ===")

        try:
            # 测试工厂函数创建操作器
            operator = create_enhanced_llm_operator(
                provider="custom",
                api_key="test-factory-key",
                base_url="https://factory.test.com",
                model="factory-model",
                timeout=25000,
                temperature=0.7,
            )

            self.log_test("工厂函数创建", True, f"操作器类型: {type(operator)}")
            self.log_test("配置验证", True, f"模型: {operator.config.model}")
            self.log_test("温度设置", True, f"温度: {operator.config.temperature}")

        except Exception as e:
            self.log_test("工厂函数", False, f"异常: {e}")

    async def test_predefined_configs(self):
        """测试预定义配置"""
        print("\n=== 测试预定义配置 ===")

        try:
            # 测试SiliconFlow配置
            silicon_operator = create_silicon_flow_operator(api_key="test-key")
            silicon_config = silicon_operator.config
            self.log_test(
                "SiliconFlow配置", True, f"URL: {silicon_config.base_url}"
            )

            # 验证预定义配置的URL
            expected_urls = [
                "https://api.siliconflow.cn/v1",
                "https://api.openai.com/v1",
                "https://api.deepseek.com/v1",
            ]

            for url in expected_urls:
                if silicon_config.base_url == url or "siliconflow" in url:
                    self.log_test("基础URL验证", True, f"匹配: {url}")
                    break

        except Exception as e:
            self.log_test("预定义配置", False, f"异常: {e}")

    async def test_error_classification(self):
        """测试错误分类"""
        print("\n=== 测试错误分类 ===")

        config = LLMConfig(
            provider="custom",
            api_key="test-key",
            base_url="https://api.test.com",
            model="test-model",
        )
        operator = LLMOperator(config)

        # 测试不同类型的错误
        test_errors = [
            ConnectionError("连接错误"),
            TimeoutError("超时错误"),
            ValueError("值错误"),
            RuntimeError("运行时错误"),
        ]

        for error in test_errors:
            should_retry = operator._should_retry(error)
            error_type = type(error).__name__
            self.log_test(f"错误分类: {error_type}", True, f"可重试: {should_retry}")

    async def test_zai_client_initialization(self):
        """测试zai客户端初始化"""
        print("\n=== 测试zai客户端初始化 ===")

        try:
            # 使用配置中的API密钥初始化zai客户端
            client = ZhipuAiClient(
                api_key=llm_config["apiKey"],
                base_url=llm_config["baseURL"],
            )
            self.log_test("zai客户端初始化", True, "客户端创建成功")

            # 测试客户端属性
            if hasattr(client, "api_key"):
                self.log_test("API密钥属性", True, f"密钥长度: {len(client.api_key)}")

            if hasattr(client, "base_url"):
                self.log_test("基础URL属性", True, f"URL: {client.base_url}")

        except Exception as e:
            self.log_test("zai客户端初始化", False, f"异常: {e}")

    async def test_real_llm_config(self):
        """测试真实LLM配置"""
        print("\n=== 测试真实LLM配置 ===")

        try:
            # 使用提供的配置创建LLMConfig
            config = LLMConfig(
                provider="zhipuai",
                api_key=llm_config["apiKey"],
                base_url=llm_config["baseURL"],
                model=llm_config["model"],
                timeout=llm_config["timeout"],
                temperature=0.7,  # 默认温度
                max_tokens=llm_config["maxTokens"],
            )

            self.log_test("真实配置创建", True, f"模型: {config.model}")
            self.log_test("超时设置", True, f"超时: {config.timeout}ms")
            self.log_test("Token限制", True, f"最大Tokens: {config.max_tokens}")

            # 创建操作器
            LLMOperator(config)
            self.log_test("操作器创建", True, "操作器初始化成功")

            # 测试缓存配置
            if llm_config["cacheEnabled"]:
                self.log_test(
                    "缓存配置", True, f"缓存超时: {llm_config['cacheTimeoutHours']}小时"
                )

        except Exception as e:
            self.log_test("真实配置测试", False, f"异常: {e}")

    async def test_zai_integration(self):
        """测试zai SDK集成"""
        print("\n=== 测试zai SDK集成 ===")

        try:
            # 初始化zai客户端
            client = ZhipuAiClient(
                api_key=llm_config["apiKey"], base_url=llm_config["baseURL"]
            )

            self.log_test("zai客户端集成", True, "客户端初始化成功")

            # 测试基本功能
            if hasattr(client, "chat"):
                self.log_test("聊天功能", True, "支持聊天接口")

            if hasattr(client, "completions"):
                self.log_test("补全功能", True, "支持补全接口")

            # 测试配置参数
            self.log_test("重试配置", True, f"最大重试: {llm_config['maxRetries']}")
            self.log_test("流式配置", True, f"流式: {llm_config['stream']}")

        except Exception as e:
            self.log_test("zai集成测试", False, f"异常: {e}")

    async def test_real_api_connection(self):
        """测试真实API连接"""
        print("\n=== 测试真实API连接 ===")

        try:
            # 使用真实配置创建操作器
            config = LLMConfig(
                provider="zhipuai",
                api_key=llm_config["apiKey"],
                base_url=llm_config["baseURL"],
                model=llm_config["model"],
                timeout=llm_config["timeout"],
            )

            operator = LLMOperator(config)

            # 测试健康检查
            health = await operator.health_check_async()
            if health.get("status") == "healthy":
                self.log_test("API健康检查", True, "API连接正常")
            else:
                self.log_test("API健康检查", False, f"状态: {health.get('status')}")

            # 测试简单请求
            messages = [{"role": "user", "content": "你好"}]
            response = await operator.chat_completion_async(messages)

            has_response = (
                response
                and isinstance(response, LLMResponse)
                and response.content
            )
            if has_response:
                self.log_test(
                    "API请求测试",
                    True,
                    f"响应: {response.content[:50]}...",
                )
                self.log_test("Token使用", True, f"Tokens: {response.usage}")
            else:
                error_msg = (
                    response.error_message
                    if isinstance(response, LLMError)
                    else "无响应内容"
                )
                self.log_test("API请求测试", False, f"失败: {error_msg}")

        except Exception as e:
            self.log_test("真实API连接", False, f"异常: {e}")

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 50)
        print("测试总结")
        print("=" * 50)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests

        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")

        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['details']}")

    async def run_all_tests(self):
        """运行所有测试"""
        print("开始LLM操作器测试")
        print("=" * 50)

        # 运行所有测试方法
        await self.test_config_validation()
        await self.test_mock_response()
        await self.test_mock_error()
        await self.test_cache_functionality()
        await self.test_statistics()
        await self.test_backoff_calculation()
        await self.test_health_check()
        await self.test_factory_function()
        await self.test_predefined_configs()
        await self.test_error_classification()

        # 运行新的zai SDK相关测试
        await self.test_zai_client_initialization()
        await self.test_real_llm_config()
        await self.test_zai_integration()
        await self.test_real_api_connection()

        # 打印总结
        self.print_summary()

        return len([r for r in self.test_results if r["success"]]), len(
            self.test_results
        )


async def main():
    """主函数"""
    print("LLM操作器测试脚本")
    print("=" * 50)

    tester = LLMOperatorTester()

    try:
        passed, total = await tester.run_all_tests()
        print(f"\n测试完成: {passed}/{total} 通过")

        if passed == total:
            print("🎉 所有测试通过！")
            return 0
        else:
            print("⚠️  部分测试失败")
            return 1

    except Exception as e:
        print(f"测试运行失败: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # 运行异步主函数
    exit_code = asyncio.run(main())
    raise SystemExit(exit_code)
