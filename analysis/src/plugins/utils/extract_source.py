import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from ...business_services.llm_brand_recognizer import LLMBrandRecognizer
from ...core.llm_operator import LLMConfig, LLMOperator
from ...core.plugin_interface import AnalysisPlugin, PluginRegistry

logger = logging.getLogger(__name__)


@PluginRegistry.register(
    plugin_type="llm",
    requires_llm=True,
    enabled_by_default=False,
    name="extract_source",
)
class ExtractSourcePlugin(AnalysisPlugin):
    """
    URL来源提取插件
    使用LLM从URL中识别来源媒体/平台名称
    """

    name = "extract_source"
    description = (
        "从单文件中提取URL的来源信息（主要从URL域名来识别），"
        "形成URL-来源的映射关系"
    )

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """
        初始化插件

        Args:
            llm_config: LLM配置信息
        """
        self.llm_config = llm_config or {}
        self.llm_recognizer = None

        # 尝试初始化LLM组件
        if self._validate_llm_config():
            try:
                provider = self.llm_config.get("provider", "openai")
                api_key = (
                    self.llm_config.get("apiKey")
                    or self.llm_config.get("api_key", "")
                )
                base_url = (
                    self.llm_config.get("baseURL")
                    or self.llm_config.get("base_url", "")
                )
                model = self.llm_config.get("model", "gpt-3.5-turbo")
                timeout = self.llm_config.get("timeout", 30000)
                max_retries = (
                    self.llm_config.get("maxRetries")
                    or self.llm_config.get("max_retries", 2)
                )
                max_tokens = (
                    self.llm_config.get("maxTokens")
                    or self.llm_config.get("max_tokens", 2000)
                )

                operator_config = LLMConfig(
                    provider=provider,
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    timeout=timeout,
                    max_retries=max_retries,
                    max_tokens=max_tokens,
                )
                llm_operator = LLMOperator(operator_config)
                self.llm_recognizer = LLMBrandRecognizer(
                    llm_operator=llm_operator
                )
                logger.info(
                    "[ExtractSourcePlugin] LLM initialized successfully"
                )
            except Exception as e:
                logger.error(
                    "[ExtractSourcePlugin] Failed to initialize LLM: %s", e
                )
        else:
            logger.warning(
                "[ExtractSourcePlugin] Warning: Invalid LLM config, "
                "plugin will run in fallback mode"
            )

    def _validate_llm_config(self) -> bool:
        """验证LLM配置"""
        has_api_key = (
            "apiKey" in self.llm_config or "api_key" in self.llm_config
        )
        has_base_url = (
            "baseURL" in self.llm_config or "base_url" in self.llm_config
        )
        has_model = "model" in self.llm_config
        return has_api_key and has_base_url and has_model

    def set_llm_recognizer(self, recognizer):
        """注入LLM识别器 (保留用于兼容性)"""
        self.llm_recognizer = recognizer

    def analyze(self, text: str, brand_name: str) -> Dict[str, Any]:
        """
        分析文本中的URL并识别来源 (同步接口)
        """
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # 如果已经在事件循环中，应该使用 analyze_async
                # 但由于接口限制，这里只能尝试抛错或hack
                raise RuntimeError(
                    "Cannot call sync analyze from async context"
                )
            else:
                return asyncio.run(self.analyze_async(text, brand_name))
        except Exception as e:
            logger.error("[ExtractSourcePlugin] analyze error: %s", e)
            # 出错时返回空结果
            return {
                "url_source_map": {},
                "source_counts": {},
                "total_urls": 0,
                "error": str(e),
            }

    async def analyze_async(
        self, text: str, brand_name: str
    ) -> Dict[str, Any]:
        """
        异步分析实现
        """
        # 1. 提取所有URL
        unique_urls = self._extract_unique_urls(text)

        if not unique_urls:
            return {
                "url_source_map": {},
                "source_counts": {},
                "total_urls": 0,
            }

        # 2. 调用LLM进行识别
        url_source_map = await self._identify_url_sources(unique_urls)

        # 3. 统计来源
        source_counts = self._count_sources(url_source_map)

        return {
            "url_source_map": url_source_map,
            "source_counts": source_counts,
            "total_urls": len(unique_urls),
        }

    def _extract_unique_urls(self, text: str) -> List[str]:
        """从文本中提取唯一的URL列表"""
        urls = re.findall(r"(https?://[^\s]+)", text)
        cleaned_urls = [u.strip() for u in urls if len(u) > 10]
        return sorted(set(cleaned_urls))

    async def _identify_url_sources(
        self, unique_urls: List[str]
    ) -> Dict[str, str]:
        """识别URL的来源信息"""
        url_source_map = {}

        if self.llm_recognizer:
            try:
                url_source_map = await self._identify_sources_with_llm_batch(
                    unique_urls
                )
            except Exception as e:
                logger.error(
                    "[ExtractSourcePlugin] LLM identification failed: %s", e
                )
                # 降级处理
                self._fallback_to_domain_extraction(
                    unique_urls, url_source_map
                )
        else:
            # 无LLM时的回退逻辑
            for url in unique_urls:
                url_source_map[url] = self._extract_domain(url)

        return url_source_map

    async def _identify_sources_with_llm_batch(
        self, unique_urls: List[str]
    ) -> Dict[str, str]:
        """使用LLM批量识别URL来源"""
        url_source_map = {}
        batch_size = 20

        for i in range(0, len(unique_urls), batch_size):
            batch_urls = unique_urls[slice(i, i + batch_size)]
            # 异步调用LLM
            batch_map = await self._identify_sources_with_llm_async(batch_urls)
            url_source_map.update(batch_map)

        return url_source_map

    def _fallback_to_domain_extraction(
        self, unique_urls: List[str], url_source_map: Dict[str, str]
    ) -> None:
        """降级到域名提取逻辑"""
        for url in unique_urls:
            if url not in url_source_map:
                url_source_map[url] = self._extract_domain(url)

    def _count_sources(self, url_source_map: Dict[str, str]) -> Dict[str, int]:
        """统计来源的出现次数"""
        source_counts = {}
        for source in url_source_map.values():
            source_counts[source] = source_counts.get(source, 0) + 1
        return source_counts

    async def _identify_sources_with_llm_async(
        self, urls: List[str]
    ) -> Dict[str, str]:
        """使用LLM异步识别URL来源"""
        if not self.llm_recognizer:
            return {}

        url_list = json.dumps(urls, indent=2, ensure_ascii=False)
        prompt = (
            "请分析以下URL列表，识别每个URL所属的媒体平台或网站名称（例如："
            "新华网、知乎、微信公众号、中关村在线等）。\n"
            "请直接返回一个JSON对象，Key是URL，Value是来源名称。\n"
            "不要包含Markdown代码块标记，只返回纯JSON字符串。\n\n"
            "URL列表：\n" + url_list
        )

        try:
            # 使用 chat_async 接口
            response = await self.llm_recognizer.chat_async(prompt)

            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("\n", 1)[1]
                if clean_response.endswith("```"):
                    clean_response = clean_response.rsplit("\n", 1)[0]

            result = json.loads(clean_response)
            return result
        except Exception as e:
            logger.error("[ExtractSourcePlugin] Batch LLM error: %s", e)
            return {}

    def _extract_domain(self, url: str) -> str:
        """简单的域名提取作为回退"""
        try:
            domain = urlparse(url).netloc
            return domain
        except Exception as e:
            logger.error(
                "[ExtractSourcePlugin] Domain extraction error: %s", e
            )
            return "unknown"

    def aggregate_results(
        self, plugin_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        聚合多个文件的分析结果
        """
        aggregated_map = {}
        aggregated_counts = {}
        total_urls = 0

        for res in plugin_results:
            if not isinstance(res, dict):
                continue

            # 合并 Map
            if "url_source_map" in res:
                aggregated_map.update(res["url_source_map"])

            # 合并 Counts
            if "source_counts" in res:
                for source, count in res["source_counts"].items():
                    aggregated_counts[source] = (
                        aggregated_counts.get(source, 0) + count
                    )

            # 合并 Total
            total_urls += res.get("total_urls", 0)

        return {
            "url_source_map": aggregated_map,
            "source_counts": aggregated_counts,
            "total_urls": total_urls,
        }
