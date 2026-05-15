import glob
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from sqlalchemy import text

from api.v1.repositories.connection import engine, get_dialect
from api.v1.utils import get_logger

logger = get_logger(__name__)


def get_query_directories(output_path: str) -> List[Dict[str, any]]:
    """
    获取output目录下所有DB_QUERY_ID=*目录及其包含的文件信息
    """
    result = []

    # 匹配所有DB_QUERY_ID=*目录
    dir_pattern = os.path.join(output_path, "DB_QUERY_ID=*")
    dir_paths = glob.glob(dir_pattern)

    for dir_path in dir_paths:
        dir_name = os.path.basename(dir_path)
        query_id = dir_name.split("=", 1)[1]

        # 匹配对话文件
        request_pattern = os.path.join(dir_path, "DEEPSEEK_REQUEST_*.txt")
        request_files = glob.glob(request_pattern)
        request_file = request_files[0] if request_files else None

        # 匹配非对话数据文件
        citation_pattern = os.path.join(dir_path, "DEEPSEEK_CITATION_*.txt")
        citation_files = glob.glob(citation_pattern)
        citation_file = citation_files[0] if citation_files else None

        result.append({
            "query_id": query_id,
            "directory": {
                "name": dir_name,
                "path": dir_path
            },
            "files": {
                "request": request_file,
                "citation": citation_file
            }
        })

    return result

def parse_metadata(lines: List[str]) -> Tuple[datetime, Optional[str], Optional[int]]:
    generated_at: Optional[datetime] = None
    model_name: Optional[str] = None
    token_usage: Optional[int] = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("Generated at:"):
            value = stripped.split("Generated at:", 1)[1].strip()
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            generated_at = datetime.fromisoformat(value)
        elif stripped.startswith("Model:"):
            model_name = stripped.split("Model:", 1)[1].strip()
        elif stripped.startswith("Token Usage:"):
            raw = stripped.split("Token Usage:", 1)[1].strip()
            token_usage = int(raw)

    if generated_at is None:
        raise ValueError("Generated at timestamp not found in file")

    return generated_at, model_name, token_usage


def extract_query_and_answer(lines: List[str]) -> Tuple[str, str]:
    user_idx: Optional[int] = None
    ai_idx: Optional[int] = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Remove invisible characters (like BOM) from the start of the file
        if i == 0:
            stripped = stripped.lstrip('\ufeff')

        # Check for user line
        if user_idx is None:
            if (
                stripped.startswith("用户:")
                or stripped.startswith("User:")
                or stripped.startswith("用户：")
            ):
                user_idx = i
                continue

        # Check for AI line
        if user_idx is not None:
            if (
                stripped.startswith("AI:")
                or stripped.startswith("Assistant:")
                or stripped.startswith("AI：")
            ):
                ai_idx = i
                break

    if user_idx is None:
        raise ValueError("User line not found in file body")
    if ai_idx is None:
        raise ValueError("AI answer line not found in file body")

    user_line = lines[user_idx].strip()
    user_text = re.sub(r"^(用户|User)\s*[:：]\s*", "", user_line).strip()
    user_extra = [line.rstrip("\n") for line in lines[user_idx + 1 : ai_idx]]
    if user_extra:
        query_content = "\n".join([user_text] + user_extra).strip()
    else:
        query_content = user_text

    ai_first_line = lines[ai_idx].strip()
    ai_first_text = re.sub(r"^(AI|Assistant)\s*[:：]\s*", "", ai_first_line).strip()
    ai_rest = [line.rstrip("\n") for line in lines[ai_idx + 1 :]]
    answer_parts = [ai_first_text] + ai_rest
    answer_content = "\n".join(answer_parts).strip()

    return query_content, answer_content

def load_output_metadata(conn, query_id: str) -> Dict[str, Any]:
    """
    从数据库llm_query_jobs表获取metadata信息
    """
    sql = text("""
    SELECT tenant_key, job_id, category, brand, keyword, query_content, created_at
    FROM llm_query_jobs
    WHERE id = :query_id
    """)

    result = conn.execute(sql, {"query_id": query_id}).fetchone()

    if not result:
        raise ValueError(f"query_id {query_id} not found in llm_query_jobs table")

    return {
        "tenant_key": result[0],
        "job_id": result[1],
        "category": result[2],
        "brand": result[3],
        "keyword": result[4],
        "query_content": result[5],
        "created_at": result[6],
    }

def parse_dialogue_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    lines = [line.rstrip("\n") for line in raw_lines]
    query_content, answer_content = extract_query_and_answer(lines)

    return {
        "query_content": query_content,
        "answer_content": answer_content,
        "model_name": None,
        "token_usage": None,
        "extracted_at": None,
    }

def parse_citation_file(path: Optional[str]) -> List[Dict[str, Any]]:
    if not path:
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {path}: {e}")
        return []
    except Exception as e:
        print(f"Error reading citation file {path}: {e}")
        return []

def extract_domain(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc or ""
    if not host:
        return ""
    host = host.split("@")[-1]
    host = host.split(":", 1)[0]
    host = host.lower()

    # 循环去除前缀，直到不再变化，解决 m.www.example.com 的问题
    prefixes = ("www.", "m.", "amp.")
    while True:
        changed = False
        for prefix in prefixes:
            if host.startswith(prefix):
                host = host[len(prefix) :]
                changed = True
        if not changed:
            break

    return host

def infer_content_type(domain: str, url: str) -> Optional[str]:
    d = domain.lower()
    if not d:
        return None

    # 1. 社交媒体 (Social Media)
    if any(
        x in d
        for x in [
            "weibo.com",
            "zhihu.com",
            "douban.com",
            "xhslink.com",
            "xiaohongshu.com",
            "tieba.baidu.com",
            "bilibili.com",
            "kuaishou.com",
            "soulapp.cn",
            "twitter.com",
            "x.com",
            "t.co",
            "facebook.com",
            "instagram.com",
            "youtube.com",
            "twitch.tv",
            "tiktok.com",
            "douyin.com",
            "threads.net",
            "reddit.com",
            "discord.com",
            "discord.gg",
            "telegram.org",
            "t.me",
            "linkedin.com",
            "pinterest.com",
            "snapchat.com",
            "tumblr.com",
            "vk.com",
            "mp.weixin.qq.com",
            "qq.com",
            "qzone.qq.com",
            "wechat.com",
            "line.me",
            "kakao.com",
            "weverse.io",
        ]
    ):
        return "social_media"

    # 2. 电商 (E-commerce)
    if any(
        x in d
        for x in [
            "jd.com",
            "taobao.com",
            "tmall.com",
            "vip.com",
            "suning.com",
            "amazon",
            "pinduoduo.com",
            "1688.com",
            "ebay.com",
            "aliexpress.com",
            "temu.com",
            "shein.com",
            "shopee.com",
            "lazada.com",
            "rakuten.co.jp",
            "mercari.com",
            "flipkart.com",
            "walmart.com",
            "bestbuy.com",
            "target.com",
            "costco.com",
            "etsy.com",
            "shopify.com",
            "weidian.com",
            "youzan.com",
            "dangdang.com",
            "yhd.com",
            "kaola.com",
            "mogujie.com",
            "jd.hk",
            "amazon.cn",
            "amazon.jp",
            "amazon.de",
            "amazon.fr",
            "amazon.co.uk",
            "aldi.com",
            "lidl.com",
            "carrefour.com",
            "ikea.com",
            "hm.com",
            "zara.com",
            "uniqlo.com",
        ]
    ):
        return "ecommerce"

    # 3. 问答百科 (Q&A / Wiki)
    if any(
        x in d
        for x in [
            "baike.baidu.com",
            "wikipedia.org",
            "wikidata.org",
            "wiktionary.org",
            "wikihow.com",
            "zhidao.baidu.com",
            "wenwen.sogou.com",
            "wukong.com",
            "baike.sogou.com",
            "mbd.baidu.com",
            "quora.com",
            "stackexchange.com",
            "stackoverflow.com",
            "baike.360.cn",
            "baike.so.com",
            "zh.wikipedia.org",
            "en.wikipedia.org",
            "stackoverflow.cn",
            "segmentfault.com",
            "oschina.net",
            "csdn.net",
        ]
    ):
        return "qa_wiki"

    # 4. 官网 (Official Website - 启发式规则)
    if any(
        x in d
        for x in [
            "apple.com",
            "huawei.com",
            "mi.com",
            "oppo.com",
            "vivo.com",
            "samsung.com",
            "tesla.com",
            "microsoft.com",
            "google.com",
            "openai.com",
            "amazon.com",
            "bytedance.com",
            "tencent.com",
            "alibaba.com",
            "baidu.com",
            "lenovo.com.cn",
            "huawei.com/cn",
            "samsung.com/cn",
            "sony.com",
            "canon.com",
            "nikon.com",
            "adidas.com",
            "nike.com",
            "coca-cola.com",
            "pepsico.com",
            "mcdonalds.com",
            "kfc.com",
        ]
    ):
        return "official_site"

    # 5. 政府/机构报告 (Gov Report)
    if any(
        x in d
        for x in [
            ".gov.",
            ".gov.cn",
            "miit.gov.cn",
            "gov.uk",
            "europa.eu",
            "whitehouse.gov",
            "stats.gov.cn",
            "mof.gov.cn",
            "pbc.gov.cn",
            ".gov.au",
            ".gov.nz",
            ".gov.sg",
            ".gov.hk",
            ".gov.mo",
            "un.org",
            "who.int",
            "wto.org",
            "imf.org",
            "worldbank.org",
            "ilo.org",
        ]
    ):
        return "gov_report"

    # 6. 科技评测 (Tech Review)
    if any(
        x in d
        for x in [
            "zol.com",
            "it168.com",
            "pconline.com.cn",
            "zealer.com",
            "36kr.com",
            "ifanr.com",
            "dgtle.com",
            "mydrivers.com",
            "cnbeta.com",
            "ithome.com",
            "techweb.com.cn",
            "tmtpost.com",
            "geekpark.net",
            "huxiu.com",
            "sspai.com",
            "pingwest.com",
            "techcrunch.com",
            "theverge.com",
            "engadget.com",
            "wired.com",
            "arstechnica.com",
            "macrumors.com",
            "9to5mac.com",
            "9to5google.com",
            "androidcentral.com",
            "phonearena.com",
            "gsmarena.com",
        ]
    ):
        return "tech_review"

    # 7. 新闻 (News)
    if any(
        x in d
        for x in [
            "news.cn",
            "xinhuanet",
            "huanqiu.com",
            "people.com.cn",
            "cctv.com",
            "sina.com.cn",
            "163.com",
            "qq.com",
            "sohu.com",
            "ifeng.com",
            "thepaper.cn",
            "jiemian.com",
            "caixin.com",
            "chinanews.com",
            "cnr.cn",
            "yicai.com",
            "guancha.cn",
            "infzm.com",
            "bbc.com",
            "cnn.com",
            "reuters.com",
            "bloomberg.com",
            "nytimes.com",
            "ft.com",
            "wsj.com",
            "washpost.com",
            "latimes.com",
            "guardian.com",
            "independent.co.uk",
            "telegraph.co.uk",
            "japantimes.co.jp",
            "koreaherald.com",
            "straitstimes.com",
            "toutiao.com",
        ]
    ):
        return "news"

    return "other"

def _build_upsert_conversation_sql() -> str:
    """根据方言生成 upsert SQL"""
    dialect = get_dialect()
    if dialect == "mysql":
        return """
        INSERT INTO llm_conversations
          (tenant_key, job_id, conversation_id, platform, keyword, brand, category,
           query_content, answer_content, model_name, token_usage, extracted_at)
        VALUES
          (:tenant_key, :job_id, :conversation_id, :platform, :keyword, :brand, :category,
           :query_content, :answer_content, :model_name, :token_usage, :extracted_at)
        ON DUPLICATE KEY UPDATE
          platform = VALUES(platform),
          keyword = VALUES(keyword),
          brand = VALUES(brand),
          category = VALUES(category),
          query_content = VALUES(query_content),
          answer_content = VALUES(answer_content),
          model_name = VALUES(model_name),
          token_usage = VALUES(token_usage)
        """
    else:
        return """
        INSERT OR REPLACE INTO llm_conversations
          (tenant_key, job_id, conversation_id, platform, keyword, brand, category,
           query_content, answer_content, model_name, token_usage, extracted_at)
        VALUES
          (:tenant_key, :job_id, :conversation_id, :platform, :keyword, :brand, :category,
           :query_content, :answer_content, :model_name, :token_usage, :extracted_at)
        """

def _build_upsert_reference_sql() -> str:
    """根据方言生成 upsert SQL"""
    dialect = get_dialect()
    if dialect == "mysql":
        return """
        INSERT INTO llm_conversation_references
          (tenant_key, job_id, conversation_id, platform, brand, category, keyword,
           query_content, url, domain, cite_index, site_name, content_type)
        VALUES
          (:tenant_key, :job_id, :conversation_id, :platform, :brand, :category, :keyword,
           :query_content, :url, :domain, :cite_index, :site_name, :content_type)
        ON DUPLICATE KEY UPDATE
          platform = VALUES(platform),
          brand = VALUES(brand),
          category = VALUES(category),
          keyword = VALUES(keyword),
          query_content = VALUES(query_content),
          url = VALUES(url),
          domain = VALUES(domain),
          cite_index = VALUES(cite_index),
          site_name = VALUES(site_name),
          content_type = VALUES(content_type)
        """
    else:
        return """
        INSERT OR REPLACE INTO llm_conversation_references
          (tenant_key, job_id, conversation_id, platform, brand, category, keyword,
           query_content, url, domain, cite_index, site_name, content_type)
        VALUES
          (:tenant_key, :job_id, :conversation_id, :platform, :brand, :category, :keyword,
           :query_content, :url, :domain, :cite_index, :site_name, :content_type)
        """


def insert_llm_conversation(
    conn,
    tenant_key: str,
    job_id: str,
    record: Dict[str, Any],
) -> None:
    sql = text(_build_upsert_conversation_sql())
    conn.execute(sql, {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "conversation_id": record["conversation_id"],
        "platform": record["platform"],
        "keyword": record["keyword"],
        "brand": record.get("brand"),
        "category": record.get("category"),
        "query_content": record["query_content"],
        "answer_content": record["answer_content"],
        "model_name": record.get("model_name"),
        "token_usage": record.get("token_usage"),
        "extracted_at": record["extracted_at"],
    })


def insert_llm_conversation_references(
    conn,
    tenant_key: str,
    job_id: str,
    record: Dict[str, Any],
    citation: List[Dict[str, Any]],
) -> None:
    sql = text(_build_upsert_reference_sql())
    for ref in citation:
        if not ref.get("url"):
            continue
        domain = extract_domain(ref["url"])
        content_type = infer_content_type(domain, ref["url"])
        conn.execute(sql, {
            "tenant_key": tenant_key,
            "job_id": job_id,
            "conversation_id": record["conversation_id"],
            "platform": record["platform"],
            "brand": record.get("brand"),
            "category": record.get("category"),
            "keyword": record["keyword"],
            "query_content": record["query_content"],
            "url": ref["url"],
            "domain": domain,
            "cite_index": ref.get("cite_index"),
            "site_name": ref.get("site_name"),
            "content_type": content_type,
        })

def main() -> None:
    # 从output目录读取所有DB_QUERY_ID目录
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, "output")

    dir_pattern = os.path.join(output_path, "tenant_key/platform/job_id/")
    dir_paths = glob.glob(dir_pattern)

    if not dir_paths:
        print("No tenant_key/platform/job_id directories found in output folder")
        sys.exit(0)

    query_dirs = get_query_directories(output_path)
    with engine.begin() as conn:
        for query_dir in query_dirs:
            if not query_dir["files"]["request"]:
                print(f"Skipping {query_dir['query_id']}: Request file not found")
                continue

            meta = load_output_metadata(conn, query_dir["query_id"])
            print(query_dir["files"]["request"])
            record = parse_dialogue_file(query_dir["files"]["request"])
            citation = parse_citation_file(query_dir["files"]["citation"])
            # 使用UUID生成唯一的conversation_id
            import uuid
            conversation_id = f"conversation_{uuid.uuid4().hex}"
            record["conversation_id"] = conversation_id
            record["platform"] = "deepseek"
            record["keyword"] = meta["keyword"]
            record["brand"] = meta["brand"]
            record["category"] = meta["category"]

            insert_llm_conversation(conn, meta["tenant_key"], meta["job_id"], record)
            insert_llm_conversation_references(
                conn,
                meta["tenant_key"],
                meta["job_id"],
                record,
                citation,
            )

if __name__ == "__main__":
    main()
