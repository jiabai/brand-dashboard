import json
import logging
import os
from typing import List, Dict, Optional, Any

# ruff: noqa: E501

# 导入 LLM Operator 相关组件
try:
    from api.utils.llm_operator import LLMResponse, create_enhanced_llm_operator
except ImportError:
    # 允许在某些环境下导入失败（如缺少依赖），后续通过 try-except 处理
    create_enhanced_llm_operator = None
    LLMResponse = None

logger = logging.getLogger(__name__)

def _load_llm_settings() -> dict:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg_path = os.path.join(base_dir, "config", "llm_settings.json")
    if not os.path.exists(cfg_path):
        return {
            "provider": "zhipuai",
            "api_key": "mock_zhipuai_key",
            "model": "glm-4.6",
            "endpoint": "https://open.bigmodel.cn/api/paas/v4",
            "timeout_seconds": 30,
        }
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)

def _create_llm_operator(settings: dict) -> Optional[Any]:
    """创建 LLM Operator 实例"""
    if not create_enhanced_llm_operator:
        return None

    provider = settings.get("provider", "zhipuai")
    api_key = settings.get("api_key", "")
    model = settings.get("model", "glm-4.6")
    endpoint = settings.get("endpoint", "")

    # 处理 base_url：移除 /chat/completions 后缀
    base_url = endpoint.replace("/chat/completions", "").rstrip("/") if endpoint else None

    return create_enhanced_llm_operator(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url,
        timeout=settings.get("timeout_seconds", 30) * 1000,  # 转换为毫秒
        max_retries=1,
        temperature=0.3
    )

def _clean_json_content(content: str) -> str:
    """清理 LLM 响应内容，移除 Markdown 标记"""
    content = content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "", 1)
    if content.startswith("```"):
        content = content.replace("```", "", 1)
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()

POSITIONING_KEYWORDS_PROMPT_TEMPLATE = (
    """
    你是一个品牌策略顾问。请基于品牌或产品的公开信息，直接输出一个包含5个标准化定位关键词的 JSON 数组。

    要求检索品牌或产品的典型产品特征、用户评价和市场定位（可以通过搜索互联网信息进行检索），从检索结果中提取5个最核心的产品关键词
    确保这些关键词：
    - 精准反映产品核心优势
    - 与竞品形成差异化
    - 直接关联用户真实需求
    - 适用于品牌营销和定位
    - 仅输出 JSON 数组，不要任何解释、标注、注释或额外文本；
    - 使用双引号，符合标准 JSON 格式。

    现在为以下品牌或产品输出定位关键词：
    {brand}
    """
).strip()

CONSUMER_QUESTIONS_PROMPT_TEMPLATE = (
    """
    请根据{industry}行业{brand}的以下5个关键词，为每个关键词生成3个消费者在购买前可能提出的问题。

    要求：
    1. 每个关键词对应3个问题；
    2. 每个问题应从不同角度切入（例如价格、质量、售后服务、使用体验、环保性、兼容性、安全性、品牌信誉等）；
    3. 同一关键词下的3个问题之间应尽量避免内容重叠或逻辑关联；
    4. 问题需贴近真实消费者的语言习惯，具有实际参考价值。

    输出格式：
    严格使用 JSON 格式，键为关键词，值为包含3个问题的数组；
    不包含任何额外说明、注释或解释性文字。

    关键词列表：
    {keywords}
    """
).strip()

async def generate_positioning_keywords(industry: str, brand: str) -> List[str]:
    """
    生成品牌定位关键词
    
    Args:
        industry: 行业名称
        brand: 品牌名称
        
    Returns:
        List[str]: 包含5个定位关键词的列表
    """
    settings = _load_llm_settings()
    operator = _create_llm_operator(settings)

    # 尝试使用 LLMOperator 生成
    if operator:
        try:
            prompt = POSITIONING_KEYWORDS_PROMPT_TEMPLATE.format(brand=brand)
            messages = [{"role": "user", "content": prompt}]

            # 调用 LLM
            response = await operator.chat_completion_async(messages=messages)

            # 处理响应
            if isinstance(response, LLMResponse) and response.content:
                content = _clean_json_content(response.content)
                parsed = json.loads(content)

                if isinstance(parsed, list):
                    # 确保所有元素都是字符串
                    result = [str(x) for x in parsed][:5]
                    # 如果结果不足5个，用空字符串补齐（虽然prompt要求5个）
                    while len(result) < 5:
                        result.append("")
                    return result

        except Exception as e:
            logger.warning(f"Failed to generate keywords using LLM: {str(e)}")
            # 继续执行回退逻辑

    # 回退方案：基于输入返回通用占位关键词，保持顺序与规格
    safe_brand = brand.strip() or "品牌"
    safe_industry = industry.strip() or "行业"
    return [
        f"{safe_industry}核心功能",
        "服务体验",
        f"{safe_industry}赛道",
        "核心价值",
        f"{safe_brand}受众",
    ]

async def generate_consumer_questions(
    industry: str, brand: str, keywords: List[str]
) -> Dict[str, List[str]]:
    """
    生成消费者问题

    Args:
        industry: 行业名称
        brand: 品牌名称
        keywords: 关键词列表

    Returns:
        Dict[str, List[str]]: 关键词到问题列表的映射
    """
    settings = _load_llm_settings()
    operator = _create_llm_operator(settings)

    # 尝试使用 LLMOperator 生成
    if operator:
        try:
            prompt = CONSUMER_QUESTIONS_PROMPT_TEMPLATE.format(
                industry=industry,
                brand=brand,
                keywords=json.dumps(keywords, ensure_ascii=False)
            )
            messages = [{"role": "user", "content": prompt}]

            # 调用 LLM
            response = await operator.chat_completion_async(messages=messages)

            # 处理响应
            if isinstance(response, LLMResponse) and response.content:
                content = _clean_json_content(response.content)
                parsed = json.loads(content)

                if isinstance(parsed, dict):
                    # 确保所有值都是字符串列表
                    result = {}
                    for keyword, questions in parsed.items():
                        if isinstance(questions, list):
                            result[keyword] = [str(x) for x in questions]
                        else:
                            result[keyword] = []
                    return result

        except Exception as e:
            logger.warning("Failed to generate consumer questions using LLM: %s", e)
            # 继续执行回退逻辑

    # 回退方案
    result = {}
    for keyword in keywords:
        result[keyword] = [
            f"关于{brand}的{keyword}，性价比如何？",
            f"{keyword}方面有什么特别之处吗？",
            f"与其他品牌相比，{keyword}表现怎样？"
        ]
    return result
