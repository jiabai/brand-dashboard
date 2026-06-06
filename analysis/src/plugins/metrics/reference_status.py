"""
引用状态插件
判断引用链接是否属于已发布链接集合，并识别链接内容类型
"""

import asyncio
import hashlib
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

from ...business_services.llm_brand_recognizer import LLMBrandRecognizer
from ...core.llm_operator import LLMConfig, LLMError, LLMOperator, LLMResponse
from ...core.plugin_interface import AnalysisPlugin, PluginRegistry

logger = logging.getLogger(__name__)


@PluginRegistry.register(
    name="reference_status",
    description="引用状态插件 - 输出每条记录的引用链接发布状态与内容类型",
    plugin_type="enhanced",
    requires_llm=True,
    enabled_by_default=False,
)
class ReferenceStatusPlugin(AnalysisPlugin):
    @property
    def name(self) -> str:
        return "reference_status"

    @property
    def description(self) -> str:
        return "判断引用链接是否已发布，并识别链接内容类型"

    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        self.llm_config = llm_config or {}
        self.llm_recognizer: Optional[LLMBrandRecognizer] = None
        self.app_config: Dict[str, Any] = {}
        self.plugin_config: Dict[str, Any] = {}
        self.datasource_fields: List[str] = []
        self._published_urls: Optional[Set[str]] = None
        self._db_engine = None

        if not self._validate_llm_config():
            logger.warning(
                "reference_status: LLM配置无效或缺失，"
                "将使用规则回退识别content_type。"
            )

    def set_app_config(
        self,
        app_config: Optional[Dict[str, Any]],
        plugin_config: Optional[Dict[str, Any]],
    ) -> None:
        self.app_config = app_config or {}
        self.plugin_config = plugin_config or {}
        self.datasource_fields = self._extract_datasource_fields(
            self.plugin_config
        )
        self._db_engine = None

    def _extract_datasource_fields(
        self, plugin_cfg: Dict[str, Any]
    ) -> List[str]:
        datasources = plugin_cfg.get("datasources")
        if not isinstance(datasources, list) or not datasources:
            return []
        first = datasources[0]
        if not isinstance(first, dict):
            return []
        fields = first.get("fields")
        if not isinstance(fields, list):
            return []
        return [
            f.strip() for f in fields if isinstance(f, str) and f.strip()
        ]

    def _extract_value(
        self, result: Dict[str, Any], logical_key: str
    ) -> Optional[Any]:
        if logical_key in result and result.get(logical_key) not in (
            None,
            "",
        ):
            return result.get(logical_key)

        source_row = result.get("source_row")
        if isinstance(source_row, dict):
            if logical_key in source_row and source_row.get(
                logical_key
            ) not in (
                None,
                "",
            ):
                return source_row.get(logical_key)

        candidates = []
        lk = logical_key.lower()
        for f in self.datasource_fields:
            fl = f.lower()
            if fl == lk:
                candidates.insert(0, f)
            elif lk in fl:
                candidates.append(f)

        if isinstance(source_row, dict):
            for k in candidates:
                if k in source_row and source_row.get(k) not in (None, ""):
                    return source_row.get(k)

        for k in candidates:
            if k in result and result.get(k) not in (None, ""):
                return result.get(k)

        return None

    def _extract_platform(self, result: Dict[str, Any]) -> Optional[str]:
        v = self._extract_value(result, "platform")
        if v is not None:
            return str(v)

        source_row = result.get("source_row")
        if isinstance(source_row, dict):
            platform_keys = [
                f
                for f in self.datasource_fields
                if re.search(r"\bplatform\b", f, re.IGNORECASE)
                or re.search(r"platform", f, re.IGNORECASE)
            ]
            for k in platform_keys:
                value = source_row.get(k)
                if value not in (None, ""):
                    return str(value)

        return None

    def _validate_llm_config(self) -> bool:
        return super()._validate_llm_config(self.llm_config)

    def set_llm_recognizer(self, recognizer):
        self.llm_recognizer = recognizer

    def _ensure_llm_initialized(self) -> None:
        if self.llm_recognizer is not None:
            return

        if not self._validate_llm_config():
            raise ValueError("LLM配置无效或缺失，无法初始化reference_status插件。")

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
            "reference_status: Lazily initialized internal LLM recognizer"
        )

    def _project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    def _published_urls_path(self) -> Path:
        return self._project_root() / "data" / "urls.txt"

    def _normalize_url_for_compare(self, url: str) -> str:
        raw = (url or "").strip()
        if not raw:
            return ""
        raw = raw.strip("<>").strip()
        if "#" in raw:
            raw = raw.split("#", 1)[0]
        if raw.endswith("/"):
            raw = raw[:-1]

        try:
            parsed = urlparse(raw)
            scheme = (parsed.scheme or "").lower()
            netloc = (parsed.netloc or "").lower()
            path = parsed.path or ""
            query = parsed.query or ""

            if netloc.endswith(":80") and scheme == "http":
                netloc = netloc[:-3]
            if netloc.endswith(":443") and scheme == "https":
                netloc = netloc[:-4]

            if scheme and netloc:
                base = f"{scheme}://{netloc}{path}"
                return f"{base}?{query}" if query else base
        except Exception:
            return raw

        return raw

    def _load_published_urls(self) -> Set[str]:
        if self._published_urls is not None:
            return self._published_urls

        path = self._published_urls_path()
        published: Set[str] = set()
        try:
            if not path.exists():
                self._published_urls = set()
                return self._published_urls

            for line in path.read_text(encoding="utf-8").splitlines():
                url = line.strip()
                if not url:
                    continue
                published.add(self._normalize_url_for_compare(url))
        except Exception:
            published = set()

        self._published_urls = published
        return self._published_urls

    def analyze(self, text: str, brand_name: str) -> Dict[str, Any]:
        return {}

    def _get_db_cfg(self, config: Dict[str, Any]) -> Dict[str, Any]:
        cfg = (config.get("brand_analysis") or {}).get("database") or {}
        return cfg if isinstance(cfg, dict) else {}

    def _get_db_engine(self):
        if self._db_engine is not None:
            return self._db_engine

        db_cfg = self._get_db_cfg(self.app_config)
        host = db_cfg.get("host")
        port = db_cfg.get("port", 3306)
        user = db_cfg.get("user")
        password = db_cfg.get("password")
        name = db_cfg.get("name")

        if not isinstance(host, str) or not host.strip():
            return None
        if not isinstance(user, str) or not user.strip():
            return None
        if not isinstance(password, str) or not password.strip():
            return None
        if not isinstance(name, str) or not name.strip():
            return None

        if isinstance(port, str):
            if not port.isdigit():
                return None
            port = int(port)
        if not isinstance(port, int) or not (1 <= port <= 65535):
            return None

        try:
            from sqlalchemy import create_engine

            url = (
                f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
                "?charset=utf8mb4"
            )
            self._db_engine = create_engine(url, pool_pre_ping=True)
            return self._db_engine
        except Exception:
            return None

    def _to_tinyint_bool(self, value: Any) -> int:
        if value is True:
            return 1
        if value is False:
            return 0
        if isinstance(value, (int, float)):
            return 1 if value else 0
        if isinstance(value, str):
            v = value.strip().lower()
            if v in {"1", "true", "yes", "y", "t"}:
                return 1
            if v in {"0", "false", "no", "n", "f"}:
                return 0
        return 0

    def _coerce_date(self, value: Any) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value).date()
            except Exception:
                return None
        if isinstance(value, str):
            s = value.strip()
            if not s:
                return None
            try:
                iso = s.replace("Z", "+00:00")
                return datetime.fromisoformat(iso).date()
            except Exception:
                logger.debug("ISO日期解析失败: %s", s, exc_info=True)
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt).date()
                except Exception:
                    logger.debug("日期格式解析失败: %s", s, exc_info=True)
        return None

    def _build_upsert_rows(
        self, answers: Dict[str, Dict[str, Any]], answer_date: date
    ) -> tuple[List[Dict[str, Any]], int]:
        rows: List[Dict[str, Any]] = []
        skipped = 0

        for a in answers.values():
            if not isinstance(a, dict):
                skipped += 1
                continue

            tenant_key = a.get("tenant_key")
            job_id = a.get("job_id")
            conversation_id = a.get("conversation_id")
            platform = a.get("platform")
            brand = a.get("brand")
            category = a.get("category")
            keyword = a.get("keyword")
            query_content = a.get("query_content")
            url = a.get("url")

            required_values = [
                tenant_key,
                job_id,
                conversation_id,
                platform,
                brand,
                category,
                keyword,
                query_content,
                url,
            ]
            if any(v is None or str(v).strip() == "" for v in required_values):
                skipped += 1
                continue

            row_date = self._coerce_date(a.get("date")) or answer_date
            brand_str = str(brand).strip()
            is_published_link = self._to_tinyint_bool(
                a.get("is_published_link")
            )
            domain_val = a.get("domain")
            domain = (
                str(domain_val)
                if domain_val not in (None, "")
                else None
            )
            content_type_val = a.get("content_type")
            content_type = (
                str(content_type_val)
                if content_type_val not in (None, "")
                else None
            )

            row = {
                "date": row_date,
                "tenant_key": str(tenant_key),
                "job_id": str(job_id),
                "conversation_id": str(conversation_id),
                "platform": str(platform),
                "brand": brand_str,
                "category": str(category),
                "keyword": str(keyword),
                "query_content": str(query_content),
                "url": str(url),
                "is_published_link": is_published_link,
                "domain": domain,
                "content_type": content_type,
            }
            rows.append(row)

        return rows, skipped

    def _upsert_qa_reference_rows(self, rows: List[Dict[str, Any]]) -> None:
        if not rows:
            return

        engine = self._get_db_engine()
        if engine is None:
            return

        try:
            from sqlalchemy import text

            stmt = text(
                """
                INSERT INTO qa_reference
                  (date, tenant_key, job_id, conversation_id, platform,
                   brand, category, keyword, query_content, url,
                   is_published_link, domain, content_type)
                VALUES
                  (:date, :tenant_key, :job_id, :conversation_id, :platform,
                   :brand, :category, :keyword, :query_content, :url,
                   :is_published_link, :domain, :content_type)
                ON DUPLICATE KEY UPDATE
                  date = VALUES(date),
                  tenant_key = VALUES(tenant_key),
                  job_id = VALUES(job_id),
                  platform = VALUES(platform),
                  brand = VALUES(brand),
                  category = VALUES(category),
                  keyword = VALUES(keyword),
                  query_content = VALUES(query_content),
                  is_published_link = VALUES(is_published_link),
                  domain = VALUES(domain),
                  content_type = VALUES(content_type)
                """
            )

            with engine.begin() as conn:
                conn.execute(stmt, rows)
        except Exception as e:
            logger.error("reference_status: qa_reference upsert失败: %s", e)

    def _rule_based_content_type(self, url: str, domain: str) -> str:
        u = (url or "").lower()
        d = (domain or "").lower()
        social_domains = [
            "coolapk.com",
            "douban.com",
            "facebook.com",
            "immomo.com",
            "instagram.com",
            "jike.com",
            "kakao.com",
            "line.me",
            "linkedin.com",
            "maimai.cn",
            "pinterest.com",
            "qq.com",
            "qzone.qq.com",
            "snapchat.com",
            "soulapp.cn",
            "t.co",
            "t.me",
            "telegram.org",
            "threads.net",
            "tumblr.com",
            "twitter.com",
            "vk.com",
            "weibo.com",
            "weibo.com.cn",
            "weibo.cn",
            "wechat.com",
            "weishi.qq.com",
            "weverse.io",
            "wx.qq.com",
            "x.com",
            "xhslink.com",
            "xiaohongshu.com",
        ]
        qa_domains = [
            "baike.baidu.com",
            "wikipedia.org",
            "wikidata.org",
            "wiktionary.org",
            "wikihow.com",
            "zhihu.com",
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
            "guokr.com",
        ]
        official_domains = [
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
        gov_report_domains = [
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
        tech_review_domains = [
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
        ecommerce_domains = [
            "tmall.com",
            "taobao.com",
            "jd.com",
            "pinduoduo.com",
            "vip.com",
            "suning.com",
            "1688.com",
            "amazon.",
            "amazon.cn",
            "amazon.jp",
            "amazon.de",
            "amazon.fr",
            "amazon.co.uk",
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
            "gome.com.cn",
            "gome.com",
            "jumei.com",
            "meituan.com",
            "ele.me",
            "hema.com",
            "dingdong.com",
            "aldi.com",
            "lidl.com",
            "carrefour.com",
            "ikea.com",
            "hm.com",
            "zara.com",
            "uniqlo.com",
        ]
        news_domains = [
            "news.",
            "people.com",
            "xinhuanet.com",
            "yiche.com",
            "zol.com.cn",
            "ifeng.com",
            "sina.com.cn",
            "sohu.com",
            "163.com",
            "thepaper.cn",
            "chinanews.com",
            "cnr.cn",
            "cctv.com",
            "eastday.com",
        ]
        forum_domains = [
            "bbs.",
            "tieba.baidu.com",
            "reddit.com",
            "discord.com",
            "discord.gg",
            "hupu.com",
            "v2ex.com",
            "nga.cn",
            "chiphell.com",
            "4chan.org",
            "discourse.org",
            "linux.do",
            "rutracker.org",
            "smzdm.com",
            "tianya.cn",
        ]
        blog_domains = [
            "blog.",
            "cnblogs.com",
            "medium.com",
            "jianshu.com",
            "blog.csdn.net",
            "juejin.cn",
            "blog.51cto.com",
            "51cto.com",
            "infoq.cn",
            "dev.to",
            "hashnode.com",
            "substack.com",
            "zhihu.com/zhuanlan",
            "weixin.qq.com",
            "mp.weixin.qq.com",
        ]
        video_domains = [
            "youku.com",
            "iqiyi.com",
            "bilibili.com",
            "b23.tv",
            "acfun.cn",
            "douyin.com",
            "kuaishou.com",
            "tiktok.com",
            "youtube.com",
            "twitch.tv",
            "douyu.com",
            "huya.com",
            "ximalaya.com",
            "video.qq.com",
        ]

        if any(x in d for x in social_domains):
            return "社交媒体"
        if any(x in d for x in qa_domains):
            return "问答百科"
        if any(x in d for x in official_domains):
            return "官网"
        if any(x in d for x in gov_report_domains):
            return "政务报告"
        if any(x in d for x in tech_review_domains):
            return "科技评测"
        if any(x in d for x in ecommerce_domains):
            return "电商"
        if any(x in d for x in news_domains) or "/news" in u:
            return "新闻"
        if any(x in d for x in forum_domains) or "forum" in u or "bbs" in u:
            return "论坛"
        if any(x in d for x in blog_domains) or "blog" in u:
            return "博客"
        if any(x in u for x in ["video", "v="]) or any(
            x in d for x in video_domains
        ):
            return "视频"
        if d:
            return "官网"
        return "其他"

    def _extract_domain(self, url: str) -> str:
        try:
            parsed = urlparse(url)
            if parsed.netloc:
                return parsed.netloc
        except Exception:
            return ""
        return ""

    def _build_content_type_prompt(self, urls: List[str]) -> str:
        categories = [
            "新闻",
            "社交媒体",
            "论坛",
            "问答百科",
            "官网",
            "电商",
            "博客",
            "视频",
            "政务报告",
            "科技评测",
            "其他",
        ]
        definitions = [
            "新闻：以发布时事、行业资讯为主的媒体网站。",
            "社交媒体：用户创建个人主页、关注他人、分享动态进行互动为主的平台。",
            "论坛：围绕特定话题展开公共讨论、发帖回帖的社区。",
            "问答百科：以提问、回答或编辑词条来构建知识库的网站。",
            "官网：公司、机构、产品或个人的官方信息发布网站。",
            "电商：直接进行商品或服务在线交易的平台。",
            "博客：以个人或团体发表文章、日志为主的网站。",
            "视频：以上传、分享、观看视频内容为核心功能的平台。",
            "政务报告：政府机构发布的公开文件、数据或通告。",
            "科技评测：专注于对科技产品进行测评、分析的网站或频道。",
            "其他：以上类别均无法涵盖的网站。",
        ]

        allowed_str = ", ".join(categories)
        definitions_str = "\n".join(
            [f"{i+1}. {d}" for i, d in enumerate(definitions)]
        )
        example_input = (
            '输入：["https://www.zhihu.com/question/123", '
            '"https://www.apple.com/iphone/"]'
        )
        example_output = (
            '输出：{"items":[{"url":"https://www.zhihu.com/question/123",'
            '"content_type":"问答百科"},{"url":"https://www.apple.com/iphone/",'
            '"content_type":"官网"}]}'
        )
        url_list = json.dumps(urls, ensure_ascii=False, indent=2)

        return (
            "任务：根据URL判断链接内容类型。\n\n"
            "要求：\n"
            "1. content_type 必须且只能从以下列表中选择精确的字符串："
            f"{allowed_str}\n"
            "2. 只输出合法JSON，不要包含Markdown代码块或任何解释文字。\n"
            '3. 返回JSON格式：{"items":[{"url":"...","content_type":"..."}]}\n\n'
            "【分类定义参考】\n"
            f"{definitions_str}\n\n"
            "【示例】\n"
            f"{example_input}\n"
            f"{example_output}\n\n"
            "URL列表：\n" + url_list
        )

    async def _classify_content_types_async(
        self, urls: List[str]
    ) -> Dict[str, str]:
        if not urls:
            return {}

        try:
            self._ensure_llm_initialized()
        except Exception:
            return {}

        if not self.llm_recognizer:
            return {}

        prompt = self._build_content_type_prompt(urls)
        llm_operator = self.llm_recognizer.llm_operator
        response = await llm_operator.chat_completion_async(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个严格的链接内容类型识别器，"
                        "请根据我提供的类别定义，"
                        "将后续网址归类到最匹配的单一类别中。"
                        "只返回合法JSON。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        if isinstance(response, LLMError):
            return {}
        if not isinstance(response, LLMResponse):
            return {}

        try:
            parsed = json.loads(response.content)
        except Exception:
            return {}

        items = parsed.get("items") if isinstance(parsed, dict) else None
        if not isinstance(items, list):
            return {}

        out: Dict[str, str] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            content_type = item.get("content_type")
            if not isinstance(url, str) or not url.strip():
                continue
            if not isinstance(content_type, str) or not content_type.strip():
                continue
            out[self._normalize_url_for_compare(url)] = content_type.strip()
        return out

    def _classify_content_types(
        self, norm_to_url: Dict[str, str]
    ) -> Dict[str, str]:
        if not norm_to_url:
            return {}

        if not self._validate_llm_config():
            return {}

        unique_urls = list(norm_to_url.values())
        batch_size = 20
        results: Dict[str, str] = {}

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None
            if loop and loop.is_running():
                raise RuntimeError(
                    "Cannot call sync classify from async context"
                )
        except Exception:
            return {}

        for i in range(0, len(unique_urls), batch_size):
            batch = unique_urls[slice(i, i + batch_size)]
            batch_map: Optional[Dict[str, str]]
            try:
                batch_map = asyncio.run(
                    self._classify_content_types_async(batch)
                )
            except Exception:
                batch_map = None

            if batch_map:
                results.update(batch_map)

        return results

    def aggregate_results(
        self, plugin_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        if not plugin_results:
            return {}

        published_urls = self._load_published_urls()
        default_date = date.today()

        norm_to_url: Dict[str, str] = {}
        for result in plugin_results:
            url_val = self._extract_value(result, "url")
            if url_val is None:
                continue
            url = str(url_val).strip()
            if not url:
                continue
            norm = self._normalize_url_for_compare(url)
            if not norm:
                continue
            if norm not in norm_to_url:
                norm_to_url[norm] = url

        content_type_map = self._classify_content_types(norm_to_url)

        answers: Dict[str, Dict[str, Any]] = {}
        content_type_counts: Dict[str, int] = {}
        published_count = 0

        for result in plugin_results:
            tenant_key = self._extract_value(result, "tenant_key")
            tenant_key_str = (
                str(tenant_key).strip() if tenant_key is not None else ""
            )
            if not tenant_key_str:
                continue
            job_id = self._extract_value(result, "job_id")
            record_id = self._extract_value(result, "record_id")
            if record_id is None:
                record_id = self._extract_value(result, "conversation_id")
            record_id = (
                str(record_id) if record_id is not None else "unknown_record"
            )

            conversation_id = (
                self._extract_value(result, "conversation_id") or record_id
            )
            platform = self._extract_platform(result)
            brand = self._extract_value(result, "brand")
            brand_str = str(brand).strip() if brand is not None else ""
            if not brand_str:
                continue
            category = self._extract_value(result, "category")
            keyword = self._extract_value(result, "keyword")
            query_content = self._extract_value(result, "query_content")

            url_val = self._extract_value(result, "url")
            url = str(url_val).strip() if url_val is not None else ""
            norm_url = self._normalize_url_for_compare(url) if url else ""

            domain_val = self._extract_value(result, "domain")
            domain = (
                str(domain_val).strip() if domain_val is not None else ""
            )
            if not domain and url:
                domain = self._extract_domain(url)

            reference_row_id = self._extract_value(result, "id")
            if reference_row_id is not None and str(reference_row_id).strip():
                ref_id = str(reference_row_id).strip()
                key_raw = f"{tenant_key_str}::{brand_str}::id:{ref_id}"
            elif norm_url:
                conv = str(conversation_id).strip()
                key_raw = f"{tenant_key_str}::{brand_str}::{conv}::{norm_url}"
            else:
                key_raw = f"{tenant_key_str}::{brand_str}::{record_id}"

            item_id = hashlib.sha256(
                key_raw.encode("utf-8")
            ).hexdigest()

            is_published_link = bool(norm_url and norm_url in published_urls)
            if is_published_link:
                published_count += 1

            content_type = None
            if norm_url:
                content_type = content_type_map.get(norm_url)
                if not content_type:
                    content_type = self._rule_based_content_type(url, domain)

            if isinstance(content_type, str) and content_type:
                content_type_counts[content_type] = (
                    content_type_counts.get(content_type, 0) + 1
                )

            generated_date = self._extract_value(result, "generated_date")
            record_date = self._coerce_date(generated_date) or default_date

            conversation_id_str = (
                str(conversation_id) if conversation_id is not None else None
            )
            answers[item_id] = {
                "date": record_date,
                "tenant_key": tenant_key_str,
                "job_id": str(job_id) if job_id is not None else None,
                "conversation_id": conversation_id_str,
                "platform": str(platform) if platform is not None else None,
                "brand": brand_str,
                "category": str(category) if category is not None else None,
                "keyword": str(keyword) if keyword is not None else None,
                "query_content": (
                    str(query_content) if query_content is not None else None
                ),
                "url": url or None,
                "domain": domain or None,
                "is_published_link": is_published_link,
                "content_type": content_type,
            }

        total_records = len(plugin_results)
        published_rate = (
            (published_count / total_records) if total_records else 0.0
        )
        rows, _skipped = self._build_upsert_rows(answers, default_date)
        self._upsert_qa_reference_rows(rows)

        return {
            "answers": answers,
            "summary": {
                "total_records": total_records,
                "published_records": published_count,
                "published_rate": published_rate,
                "content_type_counts": content_type_counts,
            },
        }
