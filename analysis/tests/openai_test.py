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

if not os.getenv("LLM_API_KEY"):
    pytest.skip("需要 LLM_API_KEY 环境变量", allow_module_level=True)


async def _run_openai_api_test():
    """测试 OpenAI 通用接口"""

    # 获取配置
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")
    provider = os.getenv("LLM_PROVIDER")

    print(f"正在连接到: {base_url}")
    print(f"使用模型: {model}")
    print(f"使用提供商: {provider}")

    # 初始化客户端
    client = OpenAI(api_key=api_key, base_url=base_url)

    messages = [
        {"role": "system", "content": "你是一个有用的助手"},
        {"role": "user", "content": "你好，请介绍一下你自己"},
    ]

    # 记录开始时间
    start_time = time.time()

    try:
        # 在执行器中运行同步调用以避免阻塞事件循环
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=model,
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
        else:
            print("未收到有效响应内容")

    except Exception as e:
        print(f"API 调用失败: {type(e).__name__}: {e}")
        raise


def test_openai_api():
    """Pytest 入口"""
    asyncio.run(_run_openai_api_test())


if __name__ == "__main__":
    print("开始 OpenAI 通用接口测试...")

    # 创建并运行事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(_run_openai_api_test())
        print("测试完成！")
    except Exception as e:
        print(f"\n测试过程中出现错误: {type(e).__name__}: {e}")
    finally:
        loop.close()
