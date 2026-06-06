import asyncio
import os
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# 只有在设置了运行实时测试的环境变量时才运行
if os.getenv("RUN_LLM_LIVE_TESTS") != "1":
    pytest.skip("Live LLM tests disabled", allow_module_level=True)

# 硅基流动通常使用 SILICON_FLOW_API_KEY 或通用的 LLM_API_KEY
API_KEY = os.getenv("SILICON_FLOW_API_KEY") or os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("SILICON_FLOW_BASE_URL") or "https://api.siliconflow.cn/v1"
MODEL = os.getenv("SILICON_FLOW_MODEL") or "deepseek-ai/DeepSeek-V3"

if not API_KEY:
    pytest.skip("需要 SILICON_FLOW_API_KEY 或 LLM_API_KEY 环境变量", allow_module_level=True)


async def _run_silicon_flow_test():
    """测试硅基流动 API 接口 (基于 OpenAI 兼容模式)"""

    print(f"\n--- 硅基流动测试配置 ---")
    print(f"使用模型: {MODEL}")
    print(f"Base URL: {BASE_URL}")
    print(f"-----------------------\n")

    # 初始化客户端 (硅基流动完全兼容 OpenAI SDK)
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    messages = [
        {"role": "system", "content": "你是一个专业的品牌分析助手"},
        {"role": "user", "content": "请简要介绍一下硅基流动 (SiliconFlow) 的主要优势。"},
    ]

    # 记录开始时间
    start_time = time.time()

    try:
        # 在执行器中运行同步调用以避免阻塞事件循环
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            ),
        )

        response_time = time.time() - start_time
        print(f"请求完成，耗时: {response_time:.2f}秒")

        # 解析响应内容
        if response.choices:
            content = response.choices[0].message.content
            print("\n--- 响应内容 ---")
            print(content)
            print("----------------\n")
            
            # 打印 token 消耗情况（如果返回中包含）
            if hasattr(response, 'usage'):
                print(f"Token 消耗: {response.usage.total_tokens} (输入: {response.usage.prompt_tokens}, 输出: {response.usage.completion_tokens})")
        else:
            print("未收到有效响应内容")

    except Exception as e:
        print(f"API 调用失败: {type(e).__name__}: {e}")
        raise


def test_silicon_flow_api():
    """Pytest 入口"""
    asyncio.run(_run_silicon_flow_test())


if __name__ == "__main__":
    print("开始硅基流动 (SiliconFlow) 接口测试...")

    # 创建并运行事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(_run_silicon_flow_test())
        print("测试完成！")
    except Exception as e:
        print(f"\n测试过程中出现错误: {type(e).__name__}: {e}")
    finally:
        loop.close()
