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
    # AI 平台 - 国内
    "chat.deepseek.com": ("DeepSeek", "深度求索"),
    "deepseek.com": ("DeepSeek", "深度求索"),
    "kimi.moonshot.cn": ("Kimi", "月之暗面"),
    "moonshot.cn": ("Kimi", "月之暗面"),
    "yuanbao.tencent.com": ("腾讯元宝", "腾讯元宝"),
    "qianwen.com": ("通义千问", "通义千问"),
    "wenxin.baidu.com": ("文心一言", "文心一言"),
    "doubao.com": ("豆包", "豆包"),
    "yiyan.baidu.com": ("文心一言", "文心一言"),
    "hunyuan.tencent.com": ("腾讯混元", "腾讯混元"),
    
    # 互联网巨头 - 腾讯
    "tencent.com": ("Tencent", "腾讯"),
    "qq.com": ("Tencent", "腾讯"),
    "weixin.qq.com": ("WeChat", "微信"),
    "work.weixin.qq.com": ("WeCom", "企业微信"),
    
    # 互联网巨头 - 阿里巴巴
    "aliyun.com": ("Aliyun", "阿里云"),
    "alibaba.com": ("Alibaba", "阿里巴巴"),
    "taobao.com": ("Taobao", "淘宝"),
    "tmall.com": ("Tmall", "天猫"),
    "alipay.com": ("Alipay", "支付宝"),
    "dingtalk.com": ("DingTalk", "钉钉"),
    
    # 互联网巨头 - 百度
    "baidu.com": ("Baidu", "百度"),
    "pan.baidu.com": ("Baidu Netdisk", "百度网盘"),
    "tieba.baidu.com": ("Baidu Tieba", "百度贴吧"),
    
    # 互联网巨头 - 字节跳动
    "bytedance.com": ("ByteDance", "字节跳动"),
    "douyin.com": ("Douyin", "抖音"),
    "toutiao.com": ("Toutiao", "今日头条"),
    "feishu.cn": ("Feishu", "飞书"),
    
    # 其他互联网平台
    "jd.com": ("JD.com", "京东"),
    "meituan.com": ("Meituan", "美团"),
    "xiaomi.com": ("Xiaomi", "小米"),
    "zhihu.com": ("Zhihu", "知乎"),
    "bilibili.com": ("Bilibili", "哔哩哔哩"),
    "sina.com.cn": ("Sina", "新浪"),
    "sohu.com": ("Sohu", "搜狐"),
    "163.com": ("NetEase", "网易"),
    "csdn.net": ("CSDN", "CSDN"),
    "xiaohongshu.com": ("Xiaohongshu", "小红书"),
    "redbook.com": ("Xiaohongshu", "小红书"),
    
    # AI 平台 - 国际
    "chatgpt.com": ("ChatGPT", "ChatGPT"),
    "chat.openai.com": ("ChatGPT", "ChatGPT"),
    "openai.com": ("OpenAI", "OpenAI"),
    "gemini.google.com": ("Gemini", "Gemini"),
    "google.com": ("Google", "谷歌"),
    "claude.ai": ("Claude", "Claude"),
    "anthropic.com": ("Anthropic", "Anthropic"),
    "perplexity.ai": ("Perplexity", "Perplexity"),
    "microsoft.com": ("Microsoft", "微软"),
    "bing.com": ("Bing", "必应"),
    
    # 新闻与政务
    "huanqiu.com": ("Huanqiu", "环球网"),
    "xinhuanet.com": ("Xinhua", "新华网"),
    "people.com.cn": ("People's Daily", "人民网"),
    "miit.gov.cn": ("MIIT", "工信部"),
    "zol.com.cn": ("ZOL", "中关村在线"),
    "eeo.com.cn": ("EEO", "经济观察网"),
    "it168.com": ("IT168", "IT168"),
    "askci.com": ("AskCI", "前瞻网"),
    "chinabgao.com": ("ChinaBGAO", "前瞻产业研究院"),
    
    # 通用域名后缀
    "com": ("Commercial", "商业网站"),
    "cn": ("China", "中国网站"),
    "net": ("Network", "网络服务"),
    "org": ("Organization", "组织网站"),
    "edu": ("Education", "教育网站"),
    "gov": ("Government", "政府网站"),
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
    if not domain:
        return ("未知域名", "未知域名")

    parts = domain.split('.')
    
    # 1. 尝试从最具体到最一般进行匹配（a.b.com -> b.com -> com）
    for i in range(len(parts)):
        test_domain = '.'.join(parts[i:])
        if test_domain in domain_mappings:
            return domain_mappings[test_domain]

    # 2. 如果没有任何匹配，执行兜底逻辑：提取域名主体并美化
    # 过滤掉常见的顶级域名后缀，以找到“主体”名称
    common_tlds = {
        'com', 'cn', 'net', 'org', 'edu', 'gov', 'io', 'me', 'ai', 'cc', 'tv', 
        'info', 'biz', 'us', 'uk', 'jp', 'hk', 'mo', 'tw', 'xyz', 'site', 'online'
    }
    
    # 提取非顶级域名的部分
    meaningful_parts = [p for p in parts if p.lower() not in common_tlds and p]
    
    if meaningful_parts:
        # 取最后一个有意义的部分（通常是二级域名）
        # 例如: blog.example.com -> example
        # 例如: tech.tencent.com -> tencent (虽然 tencent 应该在 mapping 里，但作为兜底逻辑这样更稳健)
        display_name = meaningful_parts[-1]
    else:
        # 如果全是顶级域名或异常情况，取第一部分
        display_name = parts[0] if parts else domain

    # 美化名称：将连字符和下划线替换为空格，并转为标题格式
    display_name = display_name.replace('-', ' ').replace('_', ' ').title()

    # 对于未知的域名，返回美化后的名称作为英文名，中文名留空
    # 这样上层调用者 resolve_url_domain 可以通过 'chinese_name or english_name' 逻辑进行处理
    return (display_name, "")

def get_chinese_name(domain: str) -> str:
    """
    根据域名获取中文名称
    
    Args:
        domain: 域名字符串
        
    Returns:
        中文名称，如果没有则返回英文名称
    """
    english_name, chinese_name = get_domain_name(domain)
    return chinese_name or english_name

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

if __name__ == "__main__":
    test_urls = [
        "https://chat.deepseek.com",
        "https://kimi.moonshot.cn",
        "https://www.baidu.com",
        "https://github.com/features/copilot",
        "https://www.people.com.cn/n1/2024/0101/c1001-40150567.html"
    ]
    
    for url in test_urls:
        result = resolve_url_domain(url)
        domain = result['domain']
        direct_chinese = get_chinese_name(domain) if domain else "N/A"
        print(f"URL: {url}")
        print(f"域名: {domain}")
        print(f"英文名称: {result['english_name']}")
        print(f"中文名称: {result['chinese_name']}")
        print(f"直接获取中文名: {direct_chinese}")
        print("-" * 30)
