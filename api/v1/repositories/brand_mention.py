from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from api.v1.repositories.dialect import get_columns
from api.v1.utils import get_logger
from api.v1.utils.date_range import get_date_range

logger = get_logger(__name__)


def query_brand_platform_mention_data(
    engine,
    tenant_key: str,
    job_id: str,
    brand: str,
    category: str,
    keyword: str,
    timeframe: str,
    specific_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    查询品牌在各平台的提及率数据

    Args:
        engine: SQLAlchemy engine
        tenant_key: 租户键
        job_id: 任务ID
        brand: 品牌名称
        category: 商品大类
        keyword: 品牌关键词（或"全部"）
        timeframe: 时间范围
        specific_date: 指定日期

    Returns:
        包含各平台提及率数据的列表

    Note:
        如果品牌不存在，返回空列表
    """
    start_date, end_date = get_date_range(timeframe, specific_date)

    try:
        with engine.connect() as conn:
            columns = get_columns(conn, "qa_brand_state")

            id_column = (
                "conversation_id"
                if "conversation_id" in columns
                else "question_id"
                if "question_id" in columns
                else "id"
            )

            if "is_mentioned" not in columns:
                raise Exception("qa_brand_state 表缺少 is_mentioned 字段")

            if "is_first_mentioned" not in columns:
                raise Exception("qa_brand_state 表缺少 is_first_mentioned 字段")
            first_mention_column = "is_first_mentioned"

            category_column = (
                "category"
                if "category" in columns
                else "product"
                if "product" in columns
                else None
            )
            if category_column is None:
                raise Exception("qa_brand_state 表缺少 category 字段")

            keyword_column = "keyword" if "keyword" in columns else None
            if keyword != "全部" and keyword_column is None:
                raise ValueError("qa_brand_state 表缺少 keyword 字段，无法按 keyword 筛选")

            where_clauses = [
                "tenant_key = :tenant_key",
                "job_id = :job_id",
                "brand = :brand",
                "date BETWEEN :start_date AND :end_date",
                f"{category_column} = :category",
            ]
            params: Dict[str, Any] = {
                "tenant_key": tenant_key,
                "job_id": job_id,
                "brand": brand,
                "category": category,
                "start_date": start_date,
                "end_date": end_date,
            }

            if keyword != "全部":
                where_clauses.append(f"{keyword_column} = :keyword")
                params["keyword"] = keyword

            where_sql = " AND ".join(where_clauses)

            platform_query = f"""
            SELECT
                platform,
                COUNT(DISTINCT {id_column}) AS query_count,
                COUNT(
                    DISTINCT CASE WHEN is_mentioned = 1 THEN {id_column} END
                ) AS mention_count,
                COUNT(
                    DISTINCT CASE WHEN {first_mention_column} = 1 THEN {id_column} END
                ) AS first_mention_count
            FROM qa_brand_state
            WHERE {where_sql}
            GROUP BY platform
            """

            result = conn.execute(text(platform_query), params)
            rows = result.fetchall()

            if not rows:
                return []

            platform_data: List[Dict[str, Any]] = []
            for row in rows:
                platform = row[0]
                query_count = int(row[1]) if row[1] else 0
                mention_count = int(row[2]) if row[2] else 0
                first_mention_count = int(row[3]) if row[3] else 0

                mention_rate = (
                    round(mention_count / query_count * 100, 2) if query_count > 0 else 0.0
                )
                first_mention_rate = (
                    round(first_mention_count / query_count * 100, 2) if query_count > 0 else 0.0
                )

                platform_data.append(
                    {
                        "platform": platform,
                        "query_count": query_count,
                        "mention_count": mention_count,
                        "first_mention_count": first_mention_count,
                        "mention_rate": mention_rate,
                        "first_mention_rate": first_mention_rate,
                    }
                )

            platform_data.sort(key=lambda x: x["mention_rate"], reverse=True)
            return platform_data
    except Exception as e:
        logger.error("数据库查询失败", error=str(e))
        raise Exception(f"数据库查询失败: {str(e)}") from e


def query_brand_platform_keyword_daily_mention_rates(
    engine,
    tenant_key: str,
    job_id: str,
    brand: str,
    platform: str,
    keyword: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> List[Dict[str, Any]]:
    try:
        with engine.connect() as conn:
            columns = get_columns(conn, "qa_brand_state")

            required_columns = {"brand", "platform", "keyword", "is_mentioned", "date"}
            missing_columns = required_columns - columns
            if missing_columns:
                raise Exception(f"qa_brand_state 表缺少字段: {', '.join(sorted(missing_columns))}")

            query = """
            SELECT
                date,
                brand,
                platform,
                keyword,
                ROUND(
                    SUM(is_mentioned) * 1.0 / NULLIF(COUNT(DISTINCT conversation_id), 0),
                    4
                ) AS mention_rate
            FROM qa_brand_state
            WHERE tenant_key = :tenant_key
              AND job_id = :job_id
              AND brand = :brand
              AND platform = :platform
              AND keyword = :keyword
              AND date BETWEEN :start_date AND :end_date
            GROUP BY date, platform, brand, keyword
            ORDER BY date ASC
            """

            params = {
                "tenant_key": tenant_key,
                "job_id": job_id,
                "brand": brand,
                "platform": platform,
                "keyword": keyword,
                "start_date": start_date,
                "end_date": end_date,
            }

            rows = conn.execute(text(query), params).fetchall()
            if not rows:
                return []

            result: List[Dict[str, Any]] = []
            for row in rows:
                result.append(
                    {
                        "date": row[0],
                        "brand": row[1],
                        "platform": row[2],
                        "keyword": row[3],
                        "mention_rate": float(row[4]) if row[4] is not None else 0.0,
                    }
                )

            return result
    except Exception as e:
        logger.error("数据库查询失败", error=str(e))
        raise Exception(f"数据库查询失败: {str(e)}") from e


def query_brand_metrics(
    engine,
    tenant_key: str,
    job_id: str,
    start_date: datetime.date,
    end_date: datetime.date,
    brand: Optional[str] = None,
    platform: Optional[str] = None,
) -> List[Dict[str, Any]]:
    try:
        with engine.connect() as conn:
            columns = get_columns(conn, "qa_brand_state")

            if "is_mentioned" not in columns:
                raise Exception("qa_brand_state 表缺少 is_mentioned 字段")

            if "is_first_mentioned" not in columns:
                raise Exception("qa_brand_state 表缺少 is_first_mentioned 字段")
            first_mention_column = "is_first_mentioned"

            if "is_top3_mentioned" not in columns:
                raise Exception("qa_brand_state 表缺少 is_top3_mentioned 字段")
            top3_mention_column = "is_top3_mentioned"

            if platform and "platform" not in columns:
                raise Exception("qa_brand_state 表缺少 platform 字段")

            keyword_column = "keyword" if "keyword" in columns else None

            where_clauses = [
                "tenant_key = :tenant_key",
                "job_id = :job_id",
                "date BETWEEN :start_date AND :end_date",
            ]
            params: Dict[str, Any] = {
                "tenant_key": tenant_key,
                "job_id": job_id,
                "start_date": start_date,
                "end_date": end_date,
            }

            if brand:
                where_clauses.append("brand = :brand")
                params["brand"] = brand

            if platform:
                where_clauses.append("platform = :platform")
                params["platform"] = platform

            where_sql = " AND ".join(where_clauses)

            keyword_coverage_expr = (
                "COUNT(DISTINCT CASE WHEN is_mentioned = 1 THEN keyword END)"
                if keyword_column
                else "0"
            )

            query = f"""
            SELECT
                brand,
                COUNT(DISTINCT conversation_id) AS prompt_count,
                SUM(is_mentioned) AS mention_count,
                SUM({first_mention_column}) AS first_mention_count,
                SUM({top3_mention_column}) AS top3_mention_count,
                {keyword_coverage_expr} AS keyword_coverage
            FROM qa_brand_state
            WHERE {where_sql}
            GROUP BY brand
            ORDER BY
                CASE
                    WHEN COUNT(DISTINCT conversation_id) = 0 THEN 0
                    ELSE SUM(is_mentioned) / COUNT(DISTINCT conversation_id)
                END DESC,
                brand ASC
            """

            result = conn.execute(text(query), params)
            rows = result.fetchall()

            if not rows:
                return []

            metrics: List[Dict[str, Any]] = []
            for row in rows:
                prompt_count = int(row[1]) if row[1] else 0
                mention_count = int(row[2]) if row[2] else 0
                first_mention_count = int(row[3]) if row[3] else 0
                top3_mention_count = int(row[4]) if row[4] else 0
                keyword_coverage = int(row[5]) if row[5] else 0

                mention_rate = (
                    round(mention_count / prompt_count, 4) if prompt_count > 0 else 0.0
                )
                first_mention_rate = (
                    round(first_mention_count / prompt_count, 4)
                    if prompt_count > 0
                    else 0.0
                )
                top3_mention_rate = (
                    round(top3_mention_count / prompt_count, 4)
                    if prompt_count > 0
                    else 0.0
                )

                metrics.append(
                    {
                        "brand": row[0],
                        "mention_rate": mention_rate,
                        "first_mention_rate": first_mention_rate,
                        "top3_mention_rate": top3_mention_rate,
                        "prompt_count": prompt_count,
                        "keyword_coverage": keyword_coverage,
                    }
                )

            return metrics
    except Exception as e:
        logger.error("查询品牌总指标数据失败", error=str(e))
        raise Exception(f"查询品牌总指标数据失败: {str(e)}") from e


def query_platform_metrics_by_brand(
    engine,
    tenant_key: str,
    job_id: str,
    brand: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> List[Dict[str, Any]]:
    try:
        with engine.connect() as conn:
            columns = get_columns(conn, "qa_brand_state")

            if "is_mentioned" not in columns:
                raise Exception("qa_brand_state 表缺少 is_mentioned 字段")

            if "platform" not in columns:
                raise Exception("qa_brand_state 表缺少 platform 字段")

            where_sql = " AND ".join(
                [
                    "tenant_key = :tenant_key",
                    "job_id = :job_id",
                    "brand = :brand",
                    "date BETWEEN :start_date AND :end_date",
                ]
            )
            params: Dict[str, Any] = {
                "tenant_key": tenant_key,
                "job_id": job_id,
                "brand": brand,
                "start_date": start_date,
                "end_date": end_date,
            }

            query = f"""
            SELECT
                platform,
                SUM(is_mentioned) AS mention_count,
                COUNT(*) AS total_count
            FROM qa_brand_state
            WHERE {where_sql}
            GROUP BY platform
            ORDER BY platform ASC
            """

            rows = conn.execute(text(query), params).fetchall()
            if not rows:
                return []

            result: List[Dict[str, Any]] = []
            for platform, mention_count, total_count in rows:
                mention_count_int = int(mention_count) if mention_count else 0
                total_count_int = int(total_count) if total_count else 0
                mention_rate = (
                    round(mention_count_int / total_count_int, 4) if total_count_int > 0 else 0.0
                )
                result.append({"platform": platform, "mention_rate": mention_rate})

            return result
    except Exception as e:
        logger.error("查询平台指标数据失败", error=str(e))
        raise Exception(f"查询平台指标数据失败: {str(e)}") from e
