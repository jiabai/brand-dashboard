"""
插件管理器
基于注册表的插件管理系统
"""

import importlib
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Type

from .plugin_interface import AnalysisPlugin, PluginRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    """基于注册表的插件管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化插件管理器

        Args:
            config: 配置信息，包含LLM配置等
        """
        self.config = config or {}
        self.plugins: Dict[str, AnalysisPlugin] = {}
        self.plugin_instances: Dict[str, AnalysisPlugin] = {}

        # 只显示插件激活状态
        plugins_config = (
            self.config.get("brand_analysis", {}).get("plugins", {})
        )
        if plugins_config:
            plugin_status = {}
            for plugin_name, plugin_config in plugins_config.items():
                enabled = plugin_config.get("enabled", False)
                plugin_status[plugin_name] = (
                    "enabled" if enabled else "disabled"
                )
            logger.info(
                "PluginManager initialized - Plugin status: %s",
                plugin_status,
            )
        else:
            logger.info(
                "PluginManager initialized - No plugins configuration found"
            )
        self._load_plugins()
        logger.info(
            "PluginManager initialization complete, plugins: %s",
            list(self.plugins.keys()),
        )

    def _load_plugins(self):
        """加载所有插件"""

        # 动态发现并注册所有插件
        self._discover_and_register_plugins()

        # 基于注册表加载插件
        self._load_plugins_from_registry()

        logger.info("Total plugins loaded: %d", len(self.plugins))

    def _discover_and_register_plugins(self):
        """动态发现并注册所有插件 - 使用标准导入"""

        # 确定当前包的基础路径
        # 如果当前包是 src.brand_analysis.core，我们需要 src.brand_analysis
        # 如果当前包是 brand_analysis.core，我们需要 brand_analysis
        base_package = None
        if __package__:
            parts = __package__.split(".")
            if "core" in parts:
                # 移除core及其后的部分，保留前面的部分
                core_index = parts.index("core")
                base_package = ".".join(parts[:core_index])
            else:
                # 如果不在core包中（不太可能），回退到上一级
                base_package = ".".join(parts[:-1])

        if not base_package:
            base_package = "brand_analysis"

        # 定义插件模块映射
        plugin_modules = {
            "metrics": [
                "mention_status",
                "reference_status",
            ],
            "utils": [
                "llm_ping",
                "extract_source",
                "import_mention_data",
            ],
        }

        for category, plugins in plugin_modules.items():
            for plugin_name in plugins:
                module_name = (
                    f"{base_package}.plugins.{category}.{plugin_name}"
                )
                try:
                    # 尝试从子包导入
                    importlib.import_module(module_name)
                    logger.debug(
                        "Successfully imported %s from %s",
                        plugin_name,
                        module_name,
                    )
                except Exception as e:  # pylint: disable=broad-exception-caught
                    logger.warning(
                        "Failed to import %s from %s: %s",
                        plugin_name,
                        module_name,
                        e,
                    )
                    # 尝试回退到扁平结构（为了兼容性）
                    try:
                        fallback_module = f"{base_package}.plugins.{plugin_name}"
                        if fallback_module not in sys.modules:
                            importlib.import_module(fallback_module)
                            logger.debug(
                                "Successfully imported %s from %s (fallback)",
                                plugin_name,
                                fallback_module,
                            )
                    except Exception as e2:  # pylint: disable=broad-exception-caught
                        logger.error(
                            "Failed to import %s (fallback): %s",
                            plugin_name,
                            e2,
                        )

    def _load_plugins_from_registry(self):
        """基于注册表加载插件"""
        plugins_config = (
            self.config.get("brand_analysis", {}).get("plugins", {})
        )
        llm_config = self.config.get("brand_analysis", {}).get("llm", {})

        # 尝试从环境变量补充LLM配置
        self._enrich_llm_config_from_env(llm_config)

        # 获取所有注册的插件
        registered_plugins = PluginRegistry.list_plugins()

        for plugin_name, plugin_info in registered_plugins.items():
            plugin_class = plugin_info["class"]
            plugin_type = plugin_info["type"]
            requires_llm = plugin_info["requires_llm"]

            # 检查插件是否在配置中启用
            plugin_config = plugins_config.get(plugin_name, {})
            enabled = plugin_config.get(
                "enabled", plugin_info["enabled_by_default"]
            )

            if not enabled:
                logger.info("插件 %s 已禁用，跳过加载", plugin_name)
                continue

            try:
                # 根据插件类型决定实例化方式
                if requires_llm:
                    plugin_instance = self._load_llm_plugin(
                        plugin_class, plugin_name, llm_config
                    )
                else:
                    plugin_instance = self._load_traditional_plugin(
                        plugin_class, plugin_name
                    )

                if plugin_instance:
                    if hasattr(plugin_instance, "set_app_config"):
                        try:
                            plugin_instance.set_app_config(
                                self.config, plugin_config
                            )
                        except Exception:
                            logger.warning(
                                "插件 %s set_app_config 失败",
                                plugin_name,
                                exc_info=True,
                            )
                    else:
                        try:
                            setattr(plugin_instance, "app_config", self.config)
                            setattr(
                                plugin_instance,
                                "plugin_config",
                                plugin_config,
                            )
                        except Exception:
                            logger.warning(
                                "插件 %s 注入配置失败",
                                plugin_name,
                                exc_info=True,
                            )
                    self.plugins[plugin_name] = plugin_instance
                    logger.info(
                        "✅ Loaded %s plugin: %s", plugin_type, plugin_name
                    )

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "❌ Failed to load plugin %s: %s", plugin_name, e
                )

    def _enrich_llm_config_from_env(self, llm_config: dict):
        """从环境变量补充LLM配置"""

        # 映射环境变量到配置键
        env_mapping = {
            "LLM_API_KEY": "apiKey",
            "LLM_BASE_URL": "baseURL",
            "LLM_MODEL": "model",
            "LLM_PROVIDER": "provider",
        }

        for env_key, config_key in env_mapping.items():
            env_val = os.environ.get(env_key)
            # 如果配置中缺失或为默认值，且环境变量存在，则使用环境变量
            if env_val:
                current_val = llm_config.get(config_key)
                if not current_val or current_val == "your-api-key-here":
                    llm_config[config_key] = env_val

    def _load_llm_plugin(
        self,
        plugin_class: Type[AnalysisPlugin],
        plugin_name: str,
        llm_config: dict,
    ) -> Optional[AnalysisPlugin]:
        """加载需要LLM配置的插件"""
        # 验证LLM配置
        if not self._validate_llm_config(llm_config):
            logger.warning(
                "⚠️ LLM配置无效，跳过LLM插件 %s", plugin_name
            )
            return None

        # 准备插件配置
        plugin_config = {
            "provider": llm_config.get("provider", "openai"),
            "api_key": llm_config.get("apiKey", ""),
            "base_url": llm_config.get(
                "baseURL", "https://api.openai.com/v1"
            ),
            "model": llm_config.get("model", "gpt-3.5-turbo"),
            "timeout": llm_config.get("timeout", 30000),
            "max_retries": llm_config.get("maxRetries", 2),
            "max_tokens": llm_config.get("maxTokens", 2000),
        }

        try:
            return plugin_class(llm_config=plugin_config)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to instantiate LLM plugin %s: %s", plugin_name, e
            )
            return None

    def _load_traditional_plugin(
        self, plugin_class: Type[AnalysisPlugin], plugin_name: str
    ) -> Optional[AnalysisPlugin]:
        """加载传统插件"""
        try:
            return plugin_class()
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                "Failed to instantiate traditional plugin %s: %s",
                plugin_name,
                e,
            )
            return None

    def _validate_llm_config(self, llm_config: dict) -> bool:
        """验证LLM配置"""
        required_keys = ["apiKey", "baseURL", "model"]

        # 检查必需字段
        for key in required_keys:
            if not llm_config.get(key):
                logger.error(
                    "❌ LLM config validation failed: missing %s", key
                )
                return False

        # 检查API密钥是否为默认值
        if llm_config.get("apiKey") == "your-api-key-here":
            logger.warning(
                "⚠️  Warning: Using default API key. "
                "Please update with your actual API key."
            )
            return False

        return True

    def get_plugin(self, name: str) -> Optional[AnalysisPlugin]:
        """获取插件实例"""
        if name not in self.plugin_instances:
            if name in self.plugins:
                self.plugin_instances[name] = self.plugins[name]
            else:
                return None

        return self.plugin_instances[name]

    def list_plugins(self) -> List[str]:
        """列出所有可用插件"""
        return list(self.plugins.keys())

    def get_plugin_info(self, name: str) -> Dict[str, Any]:
        """获取插件信息"""
        if name not in self.plugins:
            return {}

        plugin = self.plugins[name]

        # 获取注册表信息
        registry_info = PluginRegistry.list_plugins().get(name, {})

        info = {
            "name": name,
            "type": type(plugin).__name__,
            "description": getattr(
                plugin, "description", "No description available"
            ),
            "requires_llm": registry_info.get("requires_llm", False),
        }

        # 检查LLM配置状态
        if hasattr(plugin, "llm_recognizer"):
            info["llm_configured"] = plugin.llm_recognizer is not None
            if info["requires_llm"]:
                info["mode"] = "LLM"

        return info

    def run_all_plugins(
        self, text: str, brand_name: str
    ) -> Dict[str, dict]:
        """运行所有插件"""
        results = {}

        for plugin_name in self.plugins:
            plugin = self.get_plugin(plugin_name)
            try:
                print(f"Running plugin: {plugin_name}")
                result = plugin.analyze(text, brand_name)
                results[plugin_name] = result
                print(f"✅ Plugin {plugin_name} completed successfully")
            except Exception as e:  # pylint: disable=broad-exception-caught
                print(f"❌ Plugin {plugin_name} failed: {e}")
                results[plugin_name] = {"error": str(e)}

        return results

    def get_plugin_stats(self) -> Dict[str, Any]:
        """获取插件统计信息"""
        stats = {
            "total_plugins": len(self.plugins),
            "llm_plugins": 0,
            "normal_plugins": 0,
            "llm_enabled_plugins": 0,
            "plugin_details": [],
        }

        for name, plugin in self.plugins.items():
            plugin_info = PluginRegistry.list_plugins().get(name, {})
            if plugin_info.get("requires_llm", False):
                stats["llm_plugins"] += 1
                if hasattr(plugin, "llm_recognizer") and plugin.llm_recognizer:
                    stats["llm_enabled_plugins"] += 1
            else:
                stats["normal_plugins"] += 1

            stats["plugin_details"].append(self.get_plugin_info(name))

        return stats
