"""
LLM-based品牌识别器
使用OpenAI API进行品牌识别和顺序保持
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, List

# 导入LLM核心组件
from ..core.llm_operator import (
    PRESET_CONFIGS,
    LLMConfig,
    LLMOperator,
    LLMResponse,
)

logger = logging.getLogger(__name__)


@dataclass
class BrandMention:
    """品牌提及信息"""

    original_text: str
    standardized_name: str
    position: Dict[str, int]
    context: str
    confidence: float


@dataclass
class MultiBrandSection:
    """多品牌段落信息"""

    section_id: int
    content: str
    brands_in_order: List[str]
    section_type: str  # 'table', 'list', 'text'
    confidence: float


class LLMBrandRecognizer:
    """基于LLM的品牌识别器"""

    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        base_url: str = None,
        provider: str = "openai",
        timeout: int = 30000,
        max_retries: int = 2,
        max_tokens: int = 2000,
        stream: bool = False,
        llm_operator: LLMOperator = None,
    ):
        """
        初始化LLM品牌识别器

        Args:
            api_key: API密钥
            model: 模型名称（可选，使用提供商默认模型）
            base_url: 基础URL（可选，覆盖默认配置）
            provider: LLM提供商 (openai, zhipuai, silicon_flow, deepseek)
            timeout: 超时时间（毫秒）
            max_retries: 最大重试次数
            max_tokens: 最大token数
            stream: 是否使用流式响应
            llm_operator: 注入的LLM操作器实例（如果提供，将忽略其他配置参数）
        """
        if llm_operator:
            self.llm_operator = llm_operator
            # 从operator中提取配置以保持属性一致性
            self.api_key = llm_operator.config.api_key
            self.provider = llm_operator.config.provider
            self.timeout = llm_operator.config.timeout / 1000
            self.max_retries = llm_operator.config.max_retries
            self.max_tokens = llm_operator.config.max_tokens
            self.stream = llm_operator.config.stream
            self.model = llm_operator.config.model
            self.base_url = llm_operator.config.base_url
        else:
            # 原有的初始化逻辑
            self.api_key = api_key
            self.provider = provider
            self.timeout = timeout / 1000  # 转换为秒
            self.max_retries = max_retries
            self.max_tokens = max_tokens
            self.stream = stream

            # 根据提供商获取预设配置
            if provider in PRESET_CONFIGS:
                preset = PRESET_CONFIGS[provider]
                self.model = model or preset["model"]
                self.base_url = base_url or preset["base_url"]
            else:
                # 如果提供了base_url，则允许未知提供商（视为自定义）
                if base_url:
                    self.model = model or "gpt-3.5-turbo"
                    self.base_url = base_url
                else:
                    raise ValueError(
                        f"不支持的提供商: {provider}。"
                        f"支持的提供商: {list(PRESET_CONFIGS.keys())}"
                    )

            # 创建LLM操作器实例
            config = LLMConfig(
                provider=provider,
                api_key=api_key,
                base_url=self.base_url,
                model=self.model,
                timeout=timeout,
                max_retries=max_retries,
                max_tokens=max_tokens,
            )
            self.llm_operator = LLMOperator(config)

    def recognize_brands(self, text: str) -> Dict[str, Any]:
        """
        识别品牌（同步接口）

        Args:
            text: 要分析的文本

        Returns:
            品牌识别结果
        """
        return asyncio.run(self.recognize_brands_async(text))

    def chat(self, prompt: str) -> str:
        """
        通用对话接口（同步）

        Args:
            prompt: 用户提示词

        Returns:
            LLM响应内容
        """
        return asyncio.run(self.chat_async(prompt))

    async def chat_async(self, prompt: str) -> str:
        """
        通用对话接口（异步）
        """
        try:
            response = await self.llm_operator.chat_completion_async(
                messages=[{"role": "user", "content": prompt}], temperature=0.3
            )

            if isinstance(response, LLMResponse):
                return response.content
            elif hasattr(response, "error_message"):
                raise Exception(f"LLM调用失败: {response.error_message}")
            else:
                raise Exception(f"未知响应类型: {type(response)}")
        except Exception as e:
            logger.error("Error in chat_async: %s", e)
            raise e

    async def recognize_brands_async(self, text: str) -> Dict[str, Any]:
        """
        异步识别品牌

        Args:
            text: 要分析的文本

        Returns:
            品牌识别结果
        """
        # 构建prompt
        prompt = self._build_prompt(text)

        # 调用API
        response = await self._call_llm_api_async(prompt)
        logger.debug("=============== LLM响应: %s", response)

        # 解析结果
        result = self._parse_response(response)

        return result

    def _build_prompt(self, text: str) -> str:
        """构建prompt"""

        # 文本长度限制
        max_chars = 10000  # 限制输入长度
        if len(text) > max_chars:
            text = text[:max_chars] + "...（文本过长，已截断）"

        prompt_template = """
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

3. **重复保留**：当品牌在文本中多次出现时，**不要去重**，要**全部提取**出来放在列表中。例如：
   - 如果文本是"海尔的产品很好，海尔的服务也不错"，应该返回["海尔", "海尔"]
   - 如果文本是"美的空调很棒，美的冰箱也很好"，应该返回["美的", "美的"]

返回格式（严格的JSON格式）：
```json
{{"brands": ["海尔", "美的", "格力"]}}
```
请确保：
1. 识别结果准确完整
2. 保持原始顺序
3. **保留所有重复出现的品牌**，不要去重
4. JSON格式严格正确
"""

        return prompt_template.format(text=text)

    async def _call_llm_api_async(self, prompt: str) -> str:
        """
        异步调用LLM API - 使用LLM操作器

        Args:
            prompt: 输入提示

        Returns:
            API响应内容
        """

        try:
            # 使用LLM操作器进行异步调用
            response = await self.llm_operator.chat_completion_async(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一个专业的品牌分析专家，"
                            "专门识别文本中的品牌提及。"
                            "请严格按照要求返回JSON格式结果。"
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,  # 低温度确保一致性
                response_format={"type": "json_object"},  # 强制JSON格式
            )

            # 提取响应内容
            if isinstance(response, LLMResponse):
                return response.content
            elif hasattr(response, "error_message"):
                raise Exception(f"LLM调用失败: {response.error_message}")
            else:
                raise Exception(f"未知的响应类型: {type(response)}")

        except Exception as e:
            logger.error("LLM调用异常: %s", e)
            raise Exception(f"LLM调用失败: {e}")

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析API响应 - 仅处理简单brands格式

        Args:
            response_text: API响应文本

        Returns:
            解析后的结果，格式：{"brands": ["品牌1", "品牌2"]}
        """
        try:
            # 清理响应文本，移除Markdown代码块标记
            cleaned_text = response_text.strip()
            # 移除Markdown代码块标记 (```json 和 ```)
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]  # 移除 '```json'
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]  # 移除 '```'
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]  # 移除结尾的 '```'
            # 再次清理空白字符
            cleaned_text = cleaned_text.strip()
            # 尝试解析清理后的JSON
            result = json.loads(cleaned_text)

            # 确保结果是字典格式且包含brands字段
            if not isinstance(result, dict):
                return {"brands": []}

            if "brands" not in result:
                return {"brands": []}

            # 确保brands是列表格式
            if not isinstance(result["brands"], list):
                return {"brands": []}

            return result

        except json.JSONDecodeError as e:
            # 简化错误处理，只返回空brands结果
            return {"brands": [], "error": f"JSON解析失败: {e}"}

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        llm_stats = self.llm_operator.get_stats()
        return {
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "llm_operator_stats": llm_stats,
        }
