import os
import json
import logging
from typing import List, Optional

# 导入 LLM Operator 相关组件
try:
    from .llm_operator import create_enhanced_llm_operator, LLMResponse
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
            "endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            "timeout_seconds": 30,
        }
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


PROMPT_TEMPLATE = (
    """
你是一个品牌策略顾问。请基于任意品牌或产品的公开信息，直接输出一个包含5个标准化定位关键词的 JSON 数组。

这5个关键词必须依次对应以下维度：
1. **产品特性/功能特点** - 描述产品本身的技术特征和核心功能，如"智能驾驶"（蔚来）、"无痕"（Ubras）等，直接体现产品差异化优势。
2. **服务模式/创新体验** - 展现品牌提供的独特服务或创新体验方式，如"换电服务"（蔚来），体现品牌在服务层面的创新价值。
3. **品类赛道定位** - 明确品牌在细分市场中的定位和产品类型，如"电动汽车"（蔚来）、"运动内衣"（Ubras），界定品牌在行业中的具体赛道。
4. **核心价值定位** - 传达品牌最想传递给用户的核心价值和情感连接，如"用户体验"（蔚来）、"舒适文胸"（Ubras），是用户选择品牌的关键理由。
5. **目标受众定位** - 精准定义品牌的核心服务人群，如"高端新能源"（蔚来隐含高端用户群体）、"女性内衣"（Ubras），明确品牌服务的特定人群。

要求：

- 每个关键词简短、可跨行业复用；
- 不使用主观评价词汇（如“高端”“最好”）；
- 仅输出 JSON 数组，不要任何解释、标注、注释或额外文本；
- 使用双引号，符合标准 JSON 格式。

现在为以下品牌输出定位关键词：
{brand}
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

    # 尝试使用 LLMOperator 生成
    if create_enhanced_llm_operator:
        try:
            # 准备配置参数
            provider = settings.get("provider", "zhipuai")
            api_key = settings.get("api_key", "")
            model = settings.get("model", "glm-4.6")
            endpoint = settings.get("endpoint", "")
            
            # 处理 base_url：移除 /chat/completions 后缀
            base_url = endpoint.replace("/chat/completions", "").rstrip("/") if endpoint else None
            
            # 创建 Operator
            operator = create_enhanced_llm_operator(
                provider=provider,
                api_key=api_key,
                model=model,
                base_url=base_url,
                timeout=settings.get("timeout_seconds", 30) * 1000,  # 转换为毫秒
                max_retries=1,
                temperature=0.3
            )
            
            prompt = PROMPT_TEMPLATE.format(brand=brand)
            messages = [{"role": "user", "content": prompt}]
            
            # 调用 LLM
            response = await operator.chat_completion_async(messages=messages)
            
            # 处理响应
            if isinstance(response, LLMResponse) and response.content:
                content = response.content.strip()
                # 尝试解析 JSON
                # 有些模型可能返回 markdown 代码块，尝试去除
                if content.startswith("```json"):
                    content = content.replace("```json", "", 1)
                if content.startswith("```"):
                    content = content.replace("```", "", 1)
                if content.endswith("```"):
                    content = content[:-3]
                
                content = content.strip()
                
                import json as _json
                parsed = _json.loads(content)
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
    base = brand.strip() or "品牌"
    ind = industry.strip() or "行业"
    return [
        f"{ind}核心功能",
        "服务体验",
        f"{ind}赛道",
        "核心价值",
        f"{base}受众",
    ]
