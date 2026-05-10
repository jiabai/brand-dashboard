from typing import Any, Dict, List, Optional

from sqlalchemy import text

from api.v1.utils import get_logger
from api.v1.utils.url_domain_resolver import get_chinese_name

logger = get_logger(__name__)


def query_post_citation_rate(
    engine,
    tenant_key: str,
    job_id: str,
    brand: str,
    start_date,
    end_date,
) -> Dict[str, Any]:
    """
    查询品牌发文引用率数据

    Args:
        engine: SQLAlchemy engine
        brand: 品牌名称
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        包含发文引用率数据的字典
    """

    query = """
    SELECT
        COUNT(DISTINCT qr.domain) AS citation_source_count,
        COALESCE(
            (
                SELECT AVG(has_published_link)
                FROM (
                    SELECT
                        conversation_id,
                        MAX(is_published_link) AS has_published_link
                    FROM qa_reference
                    WHERE tenant_key = :tenant_key
                    AND job_id = :job_id
                    AND brand = :brand
                    AND date BETWEEN :start_date AND :end_date
                    GROUP BY conversation_id
                ) AS conv_stats
            ),
            0
        ) AS citation_rate_by_post
    FROM qa_reference qr
    WHERE qr.tenant_key = :tenant_key
    AND qr.job_id = :job_id
    AND qr.brand = :brand
    AND qr.date BETWEEN :start_date AND :end_date
    """

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(query),
                {
                    "tenant_key": tenant_key,
                    "job_id": job_id,
                    "brand": brand,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )

            row = result.fetchone()

            if not row:
                return {
                    "brand": brand,
                    "citation_source_count": 0,
                    "citation_rate_by_post": 0.0
                }

            return {
                "brand": brand,
                "citation_source_count": int(row[0]) if row[0] else 0,
                "citation_rate_by_post": float(row[1]) if row[1] else 0.0
            }

    except Exception as e:
        logger.error("查询发文引用率数据失败", error=str(e))
        raise


def query_domain_citation_rate(
    engine,
    tenant_key: str,
    job_id: str,
    brand: str,
    start_date,
    end_date,
    keyword: Optional[str] = None,
    platform: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    查询域名引用率数据

    按 domain 聚合统计引用率。
    计算口径：
    - 分子：特定 platform 和 keyword 下的域名引用数
    - 分母：特定 platform 下该品牌的总引用数（不受 keyword 筛选影响，保证贡献度可加性）
    """
    base_where = """
    WHERE tenant_key = :tenant_key
    AND job_id = :job_id
    AND brand = :brand
    AND domain IS NOT NULL
    AND date BETWEEN :start_date AND :end_date
    """

    denominator_where = base_where
    if platform:
        denominator_where += "\n    AND platform = :platform"

    numerator_where = base_where
    if keyword:
        numerator_where += "\n    AND keyword = :keyword"
    if platform:
        numerator_where += "\n    AND platform = :platform"

    total_query = f"""
    SELECT COUNT(*)
    FROM qa_reference
    {denominator_where}
    """

    domain_query = f"""
    SELECT
        domain,
        GROUP_CONCAT(DISTINCT keyword) AS keywords,
        GROUP_CONCAT(DISTINCT content_type) AS content_types,
        GROUP_CONCAT(DISTINCT platform) AS platforms,
        COUNT(*) AS domain_count
    FROM qa_reference
    {numerator_where}
    GROUP BY domain
    """

    params: Dict[str, Any] = {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "brand": brand,
        "start_date": start_date,
        "end_date": end_date,
    }
    if keyword:
        params["keyword"] = keyword
    if platform:
        params["platform"] = platform

    try:
        with engine.connect() as conn:
            total_count = conn.execute(text(total_query), params).scalar() or 0
            total_count_int = int(total_count)
            if total_count_int <= 0:
                return []

            rows = conn.execute(text(domain_query), params).fetchall()
            result: List[Dict[str, Any]] = []
            for row in rows:
                domain = row[0]
                row_keywords = row[1] if row[1] is not None else ""
                content_types = row[2] if row[2] is not None else ""
                platforms = row[3] if row[3] is not None else ""
                domain_count = row[4]

                domain_count_int = int(domain_count) if domain_count else 0
                percentage = round(domain_count_int * 100.0 / total_count_int, 2)
                chinese_name = get_chinese_name(domain)
                result.append({
                    "domain": domain,
                    "chinese_name": chinese_name,
                    "keywords": row_keywords,
                    "content_types": content_types,
                    "platforms": platforms,
                    "domain_citation_rate": percentage
                })

            result.sort(key=lambda item: item["domain_citation_rate"], reverse=True)
            return result
    except Exception as e:
        logger.error("查询域名引用率数据失败: %s", str(e))
        raise


def query_citation_url_stats(
    engine,
    tenant_key: str,
    job_id: str,
    keyword: str,
    domain: str,
    start_date,
    end_date,
) -> List[Dict[str, Any]]:
    """
    查询引用URL的统计数据

    Args:
        engine: SQLAlchemy engine
        tenant_key: 租户键
        job_id: 任务ID
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        包含引用URL统计数据的列表，按引用次数降序排列
    """

    url_query = """
    SELECT 
        url, 
        COUNT(*) AS citation_count 
    FROM qa_reference 
    WHERE tenant_key = :tenant_key
    AND job_id = :job_id
    AND keyword = :keyword
    AND domain = :domain
    AND url IS NOT NULL 
    AND date BETWEEN :start_date AND :end_date 
    GROUP BY url 
    ORDER BY citation_count DESC
    """

    total_questions_query = """
    SELECT COUNT(DISTINCT conversation_id) AS total_questions 
    FROM qa_reference 
    WHERE tenant_key = :tenant_key
    AND job_id = :job_id
    AND date BETWEEN :start_date AND :end_date
    """

    try:
        with engine.connect() as conn:
            url_result = conn.execute(
                text(url_query),
                {
                    "tenant_key": tenant_key,
                    "job_id": job_id,
                    "keyword": keyword,
                    "domain": domain,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            url_rows = url_result.fetchall()

            total_result = conn.execute(
                text(total_questions_query),
                {
                    "tenant_key": tenant_key,
                    "job_id": job_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            total_questions_scalar = total_result.scalar()
            total_questions = (
                int(total_questions_scalar)
                if total_questions_scalar is not None
                else 0
            )

            if not url_rows:
                return []

            citation_data = []
            for row in url_rows:
                citation_url = row[0]
                citation_count = int(row[1]) if row[1] else 0

                citation_data.append({
                    "url": citation_url,
                    "citation_count": citation_count,
                    "total_questions": total_questions
                })

            return citation_data
    except Exception as e:
        logger.error("查询引用URL统计数据失败", error=str(e))
        raise Exception(f"查询引用URL统计数据失败: {str(e)}") from e


def query_citation_type_stats(
    engine,
    tenant_key: str,
    job_id: str,
    start_date,
    end_date,
) -> tuple:
    """
    查询引用类型占比统计数据

    Args:
        engine: SQLAlchemy engine
        tenant_key: 租户键
        job_id: 任务ID
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        包含总条数、去重对话数及各引用类型占比的元组
    """
    summary_query = """
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT conversation_id) AS conversations
    FROM qa_reference
    WHERE tenant_key = :tenant_key
    AND job_id = :job_id
    AND date BETWEEN :start_date AND :end_date
    """

    type_query = """
    SELECT
        content_type,
        COUNT(*) AS type_count
    FROM qa_reference
    WHERE tenant_key = :tenant_key
    AND job_id = :job_id
    AND date BETWEEN :start_date AND :end_date
    GROUP BY content_type
    ORDER BY type_count DESC
    """

    params = {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "start_date": start_date,
        "end_date": end_date,
    }

    try:
        with engine.connect() as conn:
            summary_row = conn.execute(text(summary_query), params).fetchone()
            total_rows = (
                int(summary_row[0])
                if summary_row and summary_row[0] is not None
                else 0
            )
            conversations = (
                int(summary_row[1])
                if summary_row and summary_row[1] is not None
                else 0
            )
            if total_rows <= 0:
                return {"total_rows": total_rows, "conversations": conversations}, []

            rows = conn.execute(text(type_query), params).fetchall()
            stats: List[Dict[str, Any]] = []
            for content_type, type_count in rows:
                count_int = int(type_count) if type_count else 0
                type_pct = (
                    round(count_int * 100.0 / total_rows, 2)
                    if total_rows > 0
                    else 0.0
                )
                content_type_value = (
                    content_type
                    if content_type is not None
                    else "unknown"
                )
                stats.append(
                    {
                        "content_type": content_type_value,
                        "type_pct": type_pct,
                    }
                )

            return {"total_rows": total_rows, "conversations": conversations}, stats
    except Exception as e:
        logger.error("查询引用类型占比统计失败", error=str(e))
        raise Exception(f"查询引用类型占比统计失败: {str(e)}") from e


def query_domain_citation_summary(
    engine,
    tenant_key: str,
    job_id: str,
    brand: str,
    start_date,
    end_date,
) -> List[Dict[str, Any]]:
    """
    查询域名维度的引用率汇总数据（按域名聚合）

    Args:
        engine: SQLAlchemy engine
        tenant_key: 租户键
        job_id: 任务ID
        brand: 品牌名称
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        包含域名引用率汇总数据的列表
    """
    where_sql = """
    WHERE tenant_key = :tenant_key
    AND job_id = :job_id
    AND brand = :brand
    AND domain IS NOT NULL
    AND date BETWEEN :start_date AND :end_date
    """

    total_query = f"""
    SELECT COUNT(*)
    FROM qa_reference
    {where_sql}
    """

    domain_query = f"""
    SELECT
        domain,
        COUNT(*) AS citation_count,
        COUNT(DISTINCT keyword) AS keyword_coverage,
        COUNT(DISTINCT platform) AS platform_coverage
    FROM qa_reference
    {where_sql}
    GROUP BY domain
    ORDER BY citation_count DESC
    """

    params: Dict[str, Any] = {
        "tenant_key": tenant_key,
        "job_id": job_id,
        "brand": brand,
        "start_date": start_date,
        "end_date": end_date,
    }

    try:
        with engine.connect() as conn:
            total_count = conn.execute(text(total_query), params).scalar() or 0
            total_count_int = int(total_count)
            if total_count_int <= 0:
                return []

            rows = conn.execute(text(domain_query), params).fetchall()
            result: List[Dict[str, Any]] = []
            for row in rows:
                domain = row[0]
                citation_count = int(row[1]) if row[1] else 0
                keyword_coverage = int(row[2]) if row[2] else 0
                platform_coverage = int(row[3]) if row[3] else 0

                percentage = round(citation_count * 100.0 / total_count_int, 2)
                chinese_name = get_chinese_name(domain)
                result.append({
                    "domain": domain,
                    "chinese_name": chinese_name,
                    "citation_count": citation_count,
                    "keyword_coverage": keyword_coverage,
                    "platform_coverage": platform_coverage,
                    "domain_citation_rate": percentage,
                })

            return result
    except Exception as e:
        logger.error("查询域名引用率汇总数据失败: %s", str(e))
        raise