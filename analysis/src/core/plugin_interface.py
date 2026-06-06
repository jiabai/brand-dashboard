from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Dict, Optional, Type


class PluginRegistry:
    """插件注册表 - 管理所有插件的注册信息"""

    _plugins: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register(
        cls,
        plugin_type: str = "traditional",
        requires_llm: bool = False,
        enabled_by_default: bool = True,
        **kwargs,
    ):
        """
        插件注册装饰器

        Args:
            plugin_type: 插件类型 (llm/traditional/diagnostic)
            requires_llm: 是否需要LLM配置
            enabled_by_default: 是否默认启用
            **kwargs: 其他插件配置
        """

        def decorator(plugin_class: Type["AnalysisPlugin"]):
            plugin_info = {
                "class": plugin_class,
                "type": plugin_type,
                "requires_llm": requires_llm,
                "enabled_by_default": enabled_by_default,
                "config": kwargs,
            }

            # 获取插件名称（使用类名或自定义名称）
            plugin_name = kwargs.get(
                "name", plugin_class.__name__.replace("Plugin", "").lower()
            )
            cls._plugins[plugin_name] = plugin_info

            # 添加插件元信息到类属性
            plugin_class._plugin_info = plugin_info

            @wraps(plugin_class)
            def wrapper(*args, **kwargs):
                return plugin_class(*args, **kwargs)

            return wrapper

        return decorator

    @classmethod
    def get_plugin_info(cls, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件信息"""
        return cls._plugins.get(plugin_name)

    @classmethod
    def list_plugins(cls) -> Dict[str, Dict[str, Any]]:
        """列出所有注册的插件"""
        return cls._plugins.copy()

    @classmethod
    def get_plugins_by_type(
        cls, plugin_type: str
    ) -> Dict[str, Dict[str, Any]]:
        """按类型获取插件"""
        return {
            name: info
            for name, info in cls._plugins.items()
            if info["type"] == plugin_type
        }

    @classmethod
    def get_llm_plugins(cls) -> Dict[str, Dict[str, Any]]:
        """获取需要LLM配置的插件"""
        return {
            name: info
            for name, info in cls._plugins.items()
            if info["requires_llm"]
        }


class AnalysisPlugin(ABC):
    """分析插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass

    @abstractmethod
    def analyze(self, text: str, brand_name: str) -> Dict[str, Any]:
        """
        分析文本并返回指标结果

        Args:
            text: 要分析的文本
            brand_name: 品牌名称

        Returns:
            包含指标结果的字典
        """
        pass

    def validate_input(self, text: str, brand_name: str) -> bool:
        """验证输入参数"""
        if not text or not isinstance(text, str):
            return False
        if not brand_name or not isinstance(brand_name, str):
            return False
        return True

    def aggregate_results(
        self, plugin_results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        聚合多个文件的分析结果
        默认实现：自动识别数值字段并计算总和与平均值

        Args:
            plugin_results: 多个文件的分析结果列表

        Returns:
            聚合后的结果字典
        """
        if not plugin_results:
            return {}

        aggregated = {}
        all_keys = self._collect_all_fields(plugin_results)

        for field in all_keys:
            numeric_values = self._collect_numeric_values(
                plugin_results, field
            )
            if numeric_values:
                self._add_aggregated_values(aggregated, field, numeric_values)

        return aggregated

    def _collect_all_fields(self, plugin_results: list[dict[str, Any]]) -> set:
        """收集所有结果中的字段名"""
        all_keys = set()
        for result in plugin_results:
            if isinstance(result, dict):
                all_keys.update(result.keys())
        return all_keys

    def _collect_numeric_values(
        self, plugin_results: list[dict[str, Any]], field: str
    ) -> list:
        """收集指定字段的所有数值"""
        values = []

        for result in plugin_results:
            if not isinstance(result, dict):
                continue

            val = result.get(field)
            if val is None:
                continue

            # 转换bool值为0/1，并检查是否为数值类型
            if isinstance(val, bool):
                values.append(1 if val else 0)
            elif isinstance(val, (int, float)):
                values.append(val)
            else:
                # 如果遇到非数值类型，跳过该字段
                return []

        return values

    def _add_aggregated_values(
        self, aggregated: dict[str, Any], field: str, values: list
    ) -> None:
        """添加聚合后的数值到结果字典"""
        total_val = sum(values)
        avg_val = total_val / len(values)

        aggregated[f"total_{field}"] = total_val
        aggregated[f"avg_{field}"] = avg_val
        # 默认将原字段名设为总和 (保持与原Analyzer逻辑一致)
        aggregated[field] = total_val

    @classmethod
    def get_plugin_info(cls) -> Optional[Dict[str, Any]]:
        """获取插件注册信息"""
        return getattr(cls, "_plugin_info", None)

    @property
    def requires_llm_config(self) -> bool:
        """插件是否需要LLM配置"""
        plugin_info = self.get_plugin_info()
        return plugin_info.get("requires_llm", False) if plugin_info else False

    @property
    def plugin_type(self) -> str:
        """插件类型"""
        plugin_info = self.get_plugin_info()
        return (
            plugin_info.get("type", "traditional")
            if plugin_info
            else "traditional"
        )

    def _validate_llm_config(self, llm_config: dict) -> bool:
        """验证LLM配置的基类方法"""
        if not llm_config:
            return False

        # 检查必要的配置字段
        api_key = llm_config.get("apiKey") or llm_config.get("api_key")
        base_url = llm_config.get("baseURL") or llm_config.get("base_url")
        model = llm_config.get("model")

        # 检查是否有有效的API密钥
        if not api_key or api_key == "your-api-key-here":
            return False

        return bool(base_url and model)
