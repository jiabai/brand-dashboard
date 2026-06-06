"""
LLM服务连通性检测插件
通过发送简单的测试请求验证LLM服务的可用性和响应时间
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# 导入插件接口
# 使用相对导入，确保插件目录结构正确
from ...core.plugin_interface import AnalysisPlugin, PluginRegistry

logger = logging.getLogger(__name__)


@PluginRegistry.register(
    name="llm_ping",
    description=(
        "LLM服务连通性检测工具 - "
        "通过发送简单的测试请求验证LLM服务的可用性和响应时间"
    ),
    plugin_type="enhanced",
    requires_llm=True,
    enabled_by_default=True,
)
class LLMPingPlugin(AnalysisPlugin):
    """LLM服务连通性检测插件"""

    def __init__(self, llm_config=None):
        """初始化插件"""
        self._name = "llm_ping"
        self._description = (
            "LLM服务连通性检测工具 - "
            "通过发送简单的测试请求验证LLM服务的可用性和响应时间，"
            "用于诊断AI服务连接状态。"
        )
        self.llm_config = llm_config

    @property
    def name(self) -> str:
        """插件名称"""
        return self._name

    @property
    def description(self) -> str:
        """插件描述"""
        return self._description

    def analyze(self, text: str, brand_name: str) -> Dict[str, Any]:
        """使用文本中的配置验证LLM连通性"""
        logger.info("LLM服务检测开始 - 品牌: %s", brand_name)

        # 从文本中获取LLM配置
        llm_config = self._extract_llm_config(text)

        # 验证连通性
        result = self._ping_llm_service(llm_config)

        logger.info("LLM服务检测完成 - 状态: %s", result["status"])
        return result

    def _extract_llm_config(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取LLM配置"""
        try:
            # 尝试解析JSON格式的配置
            if text.strip().startswith("{"):
                config = json.loads(text)
                if self._validate_config(config):
                    return config
            # 尝试从配置文件读取
            config_path = Path("config/analysis_config.json")
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    full_config = json.load(f)
                    if (
                        "brand_analysis" in full_config
                        and "llm" in full_config["brand_analysis"]
                    ):
                        llm_config = full_config["brand_analysis"]["llm"]
                        if self._validate_config(llm_config):
                            return llm_config
            # 返回默认配置
            return self._get_default_config()
        except Exception as e:
            logger.error("配置提取失败: %s", e)
            return self._get_default_config()

    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """验证LLM配置的有效性"""
        required_fields = ["apiKey", "baseURL", "model"]

        for field in required_fields:
            if field not in config or not config[field]:
                return False
        return True

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认LLM配置"""
        return {
            "apiKey": "sk-xxx-key",
            "baseURL": "https://api.siliconflow.cn/v1",
            "model": "deepseek-ai/DeepSeek-V3.2-Exp",
            "timeout": 30000,
            "maxRetries": 2,
            "maxTokens": 100,
        }

    def _ping_llm_service(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行LLM服务连通性检测

        Args:
            config: LLM配置

        Returns:
            检测结果
        """
        start_time = time.time()

        try:
            # 构建测试请求
            headers = {
                "Authorization": f"Bearer {config['apiKey']}",
                "Content-Type": "application/json",
            }

            # 简单的测试消息
            test_message = (
                "Hello, this is a connectivity test. "
                "Please respond with '测试通过，没有问题'."
            )

            payload = {
                "model": config["model"],
                "messages": [{"role": "user", "content": test_message}],
                "max_tokens": config.get("maxTokens", 100),
                "temperature": 0.1,
            }

            # 发送请求
            timeout = config.get("timeout", 30000) / 1000  # 转换为秒

            response = requests.post(
                f"{config['baseURL']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
            )

            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # 毫秒

            # 分析响应
            if response.status_code == 200:
                response_data = response.json()

                # 检查响应内容
                if "choices" in response_data and len(
                    response_data["choices"]
                ) > 0:
                    response_message = response_data["choices"][0].get(
                        "message", {}
                    )
                    response_content = response_message.get("content", "")
                    return {
                        "status": "success",
                        "message": "LLM服务连通性良好",
                        "available": True,
                        "response_time": response_time,
                        "status_code": response.status_code,
                        "model_used": config["model"],
                        "response_content": response_content,
                        "config_used": {
                            "baseURL": config["baseURL"],
                            "model": config["model"],
                            "timeout": config.get("timeout", 30000),
                        },
                    }
                else:
                    return {
                        "status": "warning",
                        "message": "LLM服务响应格式异常",
                        "available": True,
                        "response_time": response_time,
                        "status_code": response.status_code,
                        "model_used": config["model"],
                        "config_used": {
                            "baseURL": config["baseURL"],
                            "model": config["model"],
                        },
                    }
            else:
                return {
                    "status": "error",
                    "message": f"LLM服务返回错误状态码: {response.status_code}",
                    "available": False,
                    "response_time": response_time,
                    "status_code": response.status_code,
                    "error_details": (
                        response.text
                        if hasattr(response, "text")
                        else str(response)
                    ),
                    "config_used": {
                        "baseURL": config["baseURL"],
                        "model": config["model"],
                    },
                }

        except requests.exceptions.Timeout:
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            return {
                "status": "error",
                "message": "LLM服务请求超时",
                "available": False,
                "response_time": response_time,
                "timeout": config.get("timeout", 30000),
                "config_used": {
                    "baseURL": config["baseURL"],
                    "model": config["model"],
                },
            }

        except requests.exceptions.ConnectionError as e:
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            return {
                "status": "error",
                "message": "LLM服务连接失败",
                "available": False,
                "response_time": response_time,
                "error_type": "connection_error",
                "error_details": str(e),
                "config_used": {
                    "baseURL": config["baseURL"],
                    "model": config["model"],
                },
            }

        except Exception as e:
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            return {
                "status": "error",
                "message": f"LLM服务检测异常: {str(e)}",
                "available": False,
                "response_time": response_time,
                "error_type": type(e).__name__,
                "error_details": str(e),
                "config_used": {
                    "baseURL": config["baseURL"],
                    "model": config["model"],
                },
            }
