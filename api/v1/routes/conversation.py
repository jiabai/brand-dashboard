from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.v1.models.schemas import ConversationLoadRequest, ConversationLoadResponse
from api.v1.repositories.database import get_db
from api.v1.routes.query_jobs import verify_executor

router = APIRouter()


def extract_domain(url: str) -> str:
    parsed = urlparse(url.strip())
    host = parsed.netloc or ""
    if not host:
        return ""
    host = host.split("@")[-1]
    host = host.split(":", 1)[0]
    host = host.lower()
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

@router.post("/load", response_model=ConversationLoadResponse)
async def load_conversations(
    request: ConversationLoadRequest,
    executor_id: str = Depends(verify_executor),
    db: Session = Depends(get_db),
):
    tenant_check = db.execute(
        text("SELECT 1 FROM tenants WHERE tenant_key = :tenant_key"),
        {"tenant_key": request.tenant_key},
    ).first()
    if not tenant_check:
        raise HTTPException(status_code=400, detail=f"租户不存在: {request.tenant_key}")

    inserted_conversations = 0
    inserted_references = 0
    now = datetime.now(timezone.utc)

    try:
        for item in request.items:
            extracted_at = item.extracted_at or now
            existing = db.execute(
                text(
                    """
                    SELECT 1
                    FROM llm_conversations
                    WHERE tenant_key = :tenant_key
                      AND conversation_id = :conversation_id
                    """
                ),
                {
                    "tenant_key": request.tenant_key,
                    "conversation_id": item.conversation_id,
                },
            ).first()

            if not existing:
                db.execute(
                    text(
                        """
                        INSERT INTO llm_conversations
                          (tenant_key, job_id, conversation_id, platform, keyword, brand, category,
                           query_content, answer_content, generated_date, extracted_at)
                        VALUES
                          (
                            :tenant_key,
                            :job_id,
                            :conversation_id,
                            :platform,
                            :keyword,
                            :brand,
                            :category,
                            :query_content,
                            :answer_content,
                            :generated_date,
                            :extracted_at
                          )
                        """
                    ),
                    {
                        "tenant_key": request.tenant_key,
                        "job_id": request.job_id,
                        "conversation_id": item.conversation_id,
                        "platform": request.platform,
                        "keyword": item.keyword,
                        "brand": item.brand,
                        "category": item.category,
                        "query_content": item.query_content,
                        "answer_content": item.answer_content,
                        "generated_date": extracted_at.date(),
                        "extracted_at": extracted_at,
                    },
                )
                inserted_conversations += 1

            if item.references:
                for ref in item.references:
                    if not ref.url:
                        continue
                    ref_exists = db.execute(
                        text(
                            """
                            SELECT 1
                            FROM llm_conversation_references
                            WHERE tenant_key = :tenant_key
                              AND conversation_id = :conversation_id
                              AND url = :url
                            """
                        ),
                        {
                            "tenant_key": request.tenant_key,
                            "conversation_id": item.conversation_id,
                            "url": ref.url,
                        },
                    ).first()

                    domain = extract_domain(ref.url)
                    content_type = infer_content_type(domain, ref.url)

                    if not ref_exists:
                        db.execute(
                            text(
                                """
                                INSERT INTO llm_conversation_references
                                  (
                                    tenant_key,
                                    job_id,
                                    conversation_id,
                                    platform,
                                    brand,
                                    category,
                                    keyword,
                                    query_content,
                                    url,
                                    domain,
                                    cite_index,
                                    site_name,
                                    content_type,
                                    generated_date
                                  )
                                VALUES
                                  (
                                    :tenant_key,
                                    :job_id,
                                    :conversation_id,
                                    :platform,
                                    :brand,
                                    :category,
                                    :keyword,
                                    :query_content,
                                    :url,
                                    :domain,
                                    :cite_index,
                                    :site_name,
                                    :content_type,
                                    :generated_date
                                  )
                                """
                            ),
                            {
                                "tenant_key": request.tenant_key,
                                "job_id": request.job_id,
                                "conversation_id": item.conversation_id,
                                "platform": request.platform,
                                "brand": item.brand,
                                "category": item.category,
                                "keyword": item.keyword,
                                "query_content": item.query_content,
                                "url": ref.url,
                                "domain": domain,
                                "cite_index": ref.cite_index,
                                "site_name": ref.site_name,
                                "content_type": content_type,
                                "generated_date": extracted_at.date(),
                            },
                        )
                        inserted_references += 1

        db.commit()
        return ConversationLoadResponse(
            success=True,
            inserted_conversations=inserted_conversations,
            inserted_references=inserted_references,
            message="对话入库成功",
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"对话入库失败: {str(exc)}") from exc
