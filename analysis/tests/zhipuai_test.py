import asyncio
import os
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

if os.getenv("RUN_LLM_LIVE_TESTS") != "1":
    pytest.skip("Live LLM tests disabled", allow_module_level=True)

if not os.getenv("LLM_API_KEY"):
    pytest.skip("需要LLM_API_KEY环境变量", allow_module_level=True)

from zai import ZhipuAiClient  # noqa: E402


async def _run_zhipuai_async_test():
    """异步测试智谱AI客户端"""

    text = "在2024年的家电市场中，海尔表现出了惊人的统治力。根据最新数据，海尔冰箱市场份额高达46.4%，稳居行业第一，遥遥领先于第二名。"

    formatted_prompt = """
请作为专业的零售品牌分析专家，仔细分析以下文本，识别所有提及的零售品牌，并保持它们出现的原始顺序。

文本内容：
{text}

识别要求：
1. **全面识别**：找出所有品牌名称，包括：
   - 中文品牌名（如：海尔、美的、格力）
   - 英文品牌名（如：Samsung、LG、Whirlpool）
   - 中英文混合（如：海尔 (Haier)、美的 (Midea)）
   - 常见缩写（如：BSH代表博西家电）
   - 品牌昵称或别称（如：海信又称Hisense）

2. **顺序保持**：严格按照品牌在文本中出现的顺序排列，不要重新排序

返回格式（严格的JSON格式）：
```json
{{"brands": ["海尔", "美的", "格力"]}}
```
请确保：
1. 识别结果准确完整
2. 保持原始顺序
3. JSON格式严格正确，不要包含任何额外的文本或格式化字符
"""

    messages = [
        {
            "role": "system",
            "content": "你是一个专业的品牌分析专家，专门识别文本中的品牌提及。",
        },
        {"role": "user", "content": formatted_prompt.format(text=text)},
    ]

    # 获取配置信息
    model = os.environ.get("LLM_MODEL", "")
    base_url = os.environ.get("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")

    print(f"使用模型: {model}")
    print(f"Base URL: {base_url}")

    request_params = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,  # 降低温度以减少随机性
        "max_tokens": 5000,
        "top_p": 0.9,  # 稍微降低top_p以减少随机性
        "thinking": {"type": "disabled"},
    }
    request_params["response_format"] = {"type": "json_object"}

    # 初始化客户端
    client = ZhipuAiClient(
        api_key=os.environ.get("LLM_API_KEY", ""),
        base_url=base_url
    )

    # 使用异步方式调用API
    start_time = time.time()

    try:
        # 在事件循环中运行同步调用
        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: client.chat.completions.create(**request_params)
        )

        response_time = time.time() - start_time
        print(f"异步调用完成，耗时: {response_time:.2f}秒")
        # print("响应内容:")
        # print(response)

        # 解析响应内容
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content
            print(f"\n解析的内容: {content}")

            # 尝试解析JSON
            try:
                import json

                parsed_content = json.loads(content)
                print(f"解析的JSON: {parsed_content}")
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")

    except Exception as e:
        print(f"异步调用失败: {type(e).__name__}: {e}")
        raise


def test_zhipuai_async():
    asyncio.run(_run_zhipuai_async_test())


# 运行异步测试
if __name__ == "__main__":
    print("开始异步智谱AI测试...")

    # 创建事件循环并运行
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(_run_zhipuai_async_test())
        print("\n异步测试完成！")
    except Exception as e:
        print(f"\n异步测试失败: {type(e).__name__}: {e}")
    finally:
        loop.close()
