"""
LLM品牌识别功能测试脚本
用于验证LLM品牌识别器和增强版首位提及率插件
"""

import asyncio
import json
import os

import pytest

# Import modules at top level to fix Pylint C0413
from src.business_services.llm_brand_recognizer import LLMBrandRecognizer

# Import plugin for tests
# pylint: disable=import-error, no-name-in-module
from src.plugins.mention_status import MentionStatusPlugin

if os.getenv("RUN_LLM_LIVE_TESTS") != "1":
    pytest.skip("Live LLM tests disabled", allow_module_level=True)


async def _run_llm_brand_recognition() -> bool:
    """测试LLM品牌识别功能"""

    print("=== LLM品牌识别功能测试 ===\n")

    # 测试文本
    test_text = """
根据全球权威机构欧睿国际在2025年8月发布的数据，我为你整理了当前全球冰箱市场的品牌排名。

排名|品牌|全球市场份额|所属国家/地区
---|---|---|---
1|海尔 (Haier)|22.8%|中国
2|惠而浦 (Whirlpool)|信息缺失|美国
3|三星 (Samsung)|信息缺失|韩国
4|LG|信息缺失|韩国
5|松下 (Panasonic)|信息缺失|日本
6|西门子 (Siemens)|信息缺失|德国

双开门冰箱品牌榜：海尔、西门子、美的、容声、卡萨帝。
商用冰箱品牌榜中，前列的品牌有：海尔、星星、松洋冷链。
高端冰箱市场主要被以下品牌占据：三星、LG、松下、西门子。

在消费者心中，海尔这个品牌有着很高的认知度，美的和格力也是知名的家电品牌。
""".strip()

    # 1. 测试LLM品牌识别器
    print("1. 测试LLM品牌识别器")
    print("-" * 50)

    # 创建LLM识别器（使用用户配置）
    llm_config = {
        "api_key": os.environ.get("LLM_API_KEY", ""),
        "provider": "zhipuai",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4.6",
        "timeout": 30000,
        "max_retries": 2,
        "max_tokens": 2000,
    }

    recognizer = LLMBrandRecognizer(**llm_config)

    try:
        # 使用真实API进行测试
        print("🧪 使用真实API进行测试...")

        result = await recognizer.recognize_brands_async(test_text)

        print("✅ LLM品牌识别完成 (真实模式)")
        print("📊 识别统计:")
        brands = result.get("brands", [])
        print(f"   - 品牌数量: {len(brands)}")

        print("\n🔍 识别的品牌列表:")
        print(f"   {brands}")

    except Exception as e:
        print(f"❌ LLM品牌识别失败: {e}")
        pytest.skip(f"LLM品牌识别调用失败: {e}")

    # 2. 测试提及状态插件
    print("\n2. 测试提及状态插件")
    print("-" * 50)

    # 创建提及状态插件
    plugin = MentionStatusPlugin(llm_config=llm_config)

    # 使用真实识别器
    if plugin.llm_recognizer:
        print("🧪 使用真实内部LLM识别器")

    try:
        # 测试海尔品牌
        target_brand = "海尔"
        result = await plugin.analyze_async(test_text, target_brand)

        print("✅ 提及状态分析完成")
        print(f"📊 分析结果 - {target_brand}:")
        print(f"   - 是否提及: {result.get('is_mentioned', False)}")
        print(f"   - 是否首位提及: {result.get('is_first_mentioned', False)}")
        print(f"   - 是否前三提及: {result.get('is_top3_mentioned', False)}")
        print(f"   - 情感状态: {result.get('sentiment_status', 'unknown')}")

        print("\n📋 识别的品牌列表:")
        print(f"   {result.get('brands_found', [])}")

    except Exception as e:
        print(f"❌ 提及状态插件测试失败: {e}")
        pytest.skip(f"提及状态插件调用失败: {e}")

    print("\n✅ 所有测试完成！")
    return True


def test_llm_brand_recognition():
    assert asyncio.run(_run_llm_brand_recognition())


def save_test_results(results: dict, filename: str = "llm_test_results.json"):
    """保存测试结果"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"测试结果已保存到: {filename}")


async def main():
    """主函数"""

    print("🚀 开始LLM品牌识别功能测试")
    print("=" * 60)

    # 检查是否提供了API密钥
    api_key = os.environ.get("LLM_API_KEY", "your-api-key-here")

    if api_key == "your-api-key-here":
        print("⚠️  警告: 请设置环境变量 LLM_API_KEY 或使用有效的API密钥")
        print("   当前使用的是默认测试密钥，可能无法正常工作")
        print("   示例: export LLM_API_KEY='your-actual-api-key'")
        print()

    # 运行测试
    success = await test_llm_brand_recognition()

    if success:
        print("\n🎉 测试成功完成！")
    else:
        print("\n❌ 测试失败，请检查配置和网络连接")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
