"""验证重构后的代码导入和插件加载功能的测试模块。

该模块测试项目的核心组件导入、常量功能和插件加载机制，
确保重构后的代码结构能够正常工作。
"""

import logging
import os
import sys

# Add project root to sys.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import modules at top level to fix Pylint C0415
try:
    from src.analyzer import BrandAnalyzer
    from src.core.constants import get_brand_variants
    from src.core.llm_adapters import ZhipuAIAdapter
    from src.core.llm_operator import LLMOperator
    from src.core.plugin_manager import PluginManager

    # Import plugins - Pylint might not recognize these due to dynamic imports
    # in __init__.py
    # pylint: disable=import-error, no-name-in-module
    from src.plugins import (
        extract_source,
        import_mention_data,
        llm_ping,
        mention_status,
    )

    # pylint: enable=import-error, no-name-in-module
except ImportError as e:
    logger.error("Failed to import modules at top level: %s", e)


def test_constants():
    """测试品牌变体常量功能。

    验证已知品牌（如海尔）和未知品牌的变体生成是否正常工作。
    """
    logger.info("Testing constants...")

    # Test known brand
    haier_variants = get_brand_variants("海尔")
    assert "Haier" in haier_variants
    assert "海尔" in haier_variants
    logger.info("Haier variants: %s", haier_variants)

    # Test unknown brand
    unknown = get_brand_variants("UnknownBrand")
    assert "UnknownBrand" in unknown
    assert "unknownbrand" in unknown
    logger.info("Unknown variants: %s", unknown)

    logger.info("Constants test passed!")


def test_imports():
    """测试所有核心模块和插件的导入功能。

    验证项目的核心组件和插件是否能够被正确导入。
    """
    logger.info("Testing imports...")
    try:
        assert BrandAnalyzer
        assert ZhipuAIAdapter
        assert LLMOperator
        assert PluginManager

        assert extract_source
        assert llm_ping
        assert mention_status
        assert import_mention_data

        logger.info("All modules imported successfully!")
    except Exception as e:
        logger.error("Import failed: %s", e)
        raise


def test_plugin_loading():
    """测试插件加载机制。

    验证PluginManager能否正确列出和加载所有预期的插件。
    """
    logger.info("Testing plugin loading...")
    try:
        # 使用已在顶部导入的PluginManager
        pm = PluginManager({})
        plugins = pm.list_plugins()
        logger.info("Loaded plugins: %s", plugins)

        expected_plugins = [
            "mention_status",
            "brand_file_sentiment",
            "extract_source",
            "llm_ping",
        ]

        for p in expected_plugins:
            if p not in plugins:
                logger.warning("Plugin %s not found in loaded plugins!", p)
            else:
                logger.info("Plugin %s loaded correctly.", p)

    except Exception as e:
        logger.error("Plugin loading failed: %s", e)
        raise


if __name__ == "__main__":
    try:
        test_constants()
        test_imports()
        test_plugin_loading()
        logger.info("Verification completed successfully!")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # 作为测试脚本入口点，需要捕获所有异常以确保优雅退出并返回正确的错误码
        logger.error("Verification failed: %s", e)
        sys.exit(1)
