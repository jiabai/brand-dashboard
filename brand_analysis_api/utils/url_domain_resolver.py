"""
URL域名解析器
用于解析answer_reference_url的域名和对应的中文/英文名称
"""

from typing import Dict, Tuple
from urllib.parse import urlparse

# 域名缓存
domain_cache: Dict[str, Tuple[str, str]] = {}

# 预定义的域名映射表
domain_mappings = {
    # 国内平台
    "chat.deepseek.com": ("DeepSeek", "深度求索"),
    "deepseek.com": ("DeepSeek", "深度求索"),
    "kimi.moonshot.cn": ("Kimi", "月之暗面"),
    "moonshot.cn": ("Kimi", "月之暗面"),
    "yuanbao.tencent.com": ("腾讯元宝", "腾讯元宝"),
    "tongyi.aliyun.com": ("通义千问", "通义千问"),
    "aliyun.com": ("通义千问", "通义千问"),
    "wenxin.baidu.com": ("文心一言", "文心一言"),
    "baidu.com": ("百度", "百度"),
    "doubao.com": ("豆包", "豆包"),
    "bytedance.com": ("字节跳动", "字节跳动"),
    # 国际平台
    "chat.openai.com": ("ChatGPT", "ChatGPT"),
    "openai.com": ("OpenAI", "OpenAI"),
    "gemini.google.com": ("Gemini", "Gemini"),
    "google.com": ("Google", "谷歌"),
    "claude.ai": ("Claude", "Claude"),
    "anthropic.com": ("Anthropic", "Anthropic"),
    # 新闻网站
    "huanqiu.com": ("环球网", "环球网"),
    "miit.gov.cn": ("工信部", "工业和信息化部"),
    "zol.com.cn": ("中关村在线", "中关村在线"),
    "eeo.com.cn": ("经济观察网", "经济观察网"),
    "it168.com": ("IT168", "IT168"),
    "askci.com": ("前瞻网", "前瞻网"),
    "chinabgao.com": ("前瞻产业研究院", "前瞻产业研究院"),
    # 通用域名
    "com": ("商业网站", "商业网站"),
    "cn": ("中国网站", "中国网站"),
    "net": ("网络服务", "网络服务"),
    "org": ("组织网站", "组织网站"),
    "edu": ("教育网站", "教育网站"),
    "gov": ("政府网站", "政府网站"),
}

def extract_domain_from_url(url: str) -> str:
    """
    从URL中提取主域名
    
    Args:
        url: 完整的URL字符串
        
    Returns:
        主域名字符串
    """
    try:
        # 如果URL没有协议头，添加http://
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return ""

        # 移除www前缀
        if hostname.startswith('www.'):
            hostname = hostname[4:]

        return hostname.lower()
    except Exception:
        return ""

def get_domain_name(domain: str) -> Tuple[str, str]:
    """
    获取域名的中英文名称
    
    Args:
        domain: 域名字符串
        
    Returns:
        (英文名称, 中文名称) 元组
    """
    # 首先尝试完全匹配
    if domain in domain_mappings:
        return domain_mappings[domain]

    # 尝试子域名匹配（从具体到一般）
    parts = domain.split('.')
    for i in range(len(parts)):
        # 从右到左构建域名（优先匹配更具体的域名）
        test_domain = '.'.join(parts[i:])
        if test_domain in domain_mappings:
            return domain_mappings[test_domain]

    # 尝试顶级域名
    if len(parts) >= 2:
        tld = parts[-1]
        if tld in domain_mappings:
            return domain_mappings[tld]

    # 默认返回域名本身作为英文名称
    domain_display = domain.replace('.com', '').replace('.cn', '').replace('.net', '').replace('.org', '')
    domain_display = domain_display.replace('-', ' ').replace('_', ' ').title()

    return (domain_display, domain_display)

def analyze_url_domain(url: str) -> Tuple[str, str]:
    """
    分析URL的域名信息（实际分析方法）
    
    Args:
        url: 完整的URL字符串
        
    Returns:
        (英文名称, 中文名称) 元组
    """
    domain = extract_domain_from_url(url)
    
    if not domain:
        return ("未知域名", "未知域名")
    
    return get_domain_name(domain)

def resolve_url_domain(url: str) -> Dict[str, str]:
    """
    解析answer_reference_url的域名信息（带缓存的公开函数）
    
    Args:
        url: answer_reference_url字符串
        
    Returns:
        包含域名信息的字典，格式：
        {
            "domain": "主域名",
            "english_name": "英文名称",
            "chinese_name": "中文名称"
        }
    """
    if not url or not isinstance(url, str):
        return {
            "domain": "",
            "english_name": "未知域名",
            "chinese_name": "未知域名"
        }

    # 提取主域名
    domain = extract_domain_from_url(url)

    if not domain:
        return {
            "domain": "",
            "english_name": "未知域名",
            "chinese_name": "未知域名"
        }

    # 检查缓存
    if domain in domain_cache:
        english_name, chinese_name = domain_cache[domain]
    else:
        # 缓存未命中，执行实际分析
        english_name, chinese_name = get_domain_name(domain)
        # 存入缓存
        domain_cache[domain] = (english_name, chinese_name)

    return {
        "domain": domain,
        "english_name": english_name,
        "chinese_name": chinese_name or english_name  # 如果没有中文名，使用英文名
    }

# 提供一个异步版本（如果需要）
async def resolve_url_domain_async(url: str) -> Dict[str, str]:
    """
    异步版本的域名解析函数
    
    Args:
        url: answer_reference_url字符串
        
    Returns:
        包含域名信息的字典
    """
    return resolve_url_domain(url)

# 缓存管理函数
def clear_domain_cache() -> None:
    """清除域名缓存"""
    global domain_cache
    domain_cache.clear()

def get_cache_size() -> int:
    """获取缓存大小"""
    return len(domain_cache)

def get_cache_info() -> Dict[str, any]:
    """获取缓存信息"""
    return {
        "cache_size": len(domain_cache),
        "cached_domains": list(domain_cache.keys())
    }

# 测试函数
def test_domain_resolver():
    """测试域名解析器"""
    test_urls = [
        "https://chat.deepseek.com/a/chat/s/e2762808-0e0d-41e2-bf9d-78fe45feefb2",
        "https://kimi.moonshot.cn",
        "https://www.huanqiu.com/article/test",
        "https://miit.gov.cn/xwfb/gxdt/sjdt/art/2025/test.html",
        "invalid_url"
    ]

    print("测试域名解析器:")
    print("=" * 50)
    
    for url in test_urls:
        result = resolve_url_domain(url)
        print(f"URL: {url}")
        print(f"域名: {result['domain']}")
        print(f"英文名称: {result['english_name']}")
        print(f"中文名称: {result['chinese_name']}")
        print("-" * 30)
    
    print(f"缓存大小: {get_cache_size()}")
    print(f"缓存信息: {get_cache_info()}")

if __name__ == "__main__":
    test_domain_resolver()