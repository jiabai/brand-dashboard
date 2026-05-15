from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from api.v1.repositories.dialect import get_columns
from api.v1.utils import get_logger

logger = get_logger(__name__)


def get_available_dates(engine, tenant_key: str, job_id: Optional[str] = None) -> List[str]:
    """
    获取 qa_brand_state 表中有数据的所有日期

    Args:
        engine: SQLAlchemy engine
        tenant_key: 租户键
        job_id: 任务ID (可选)

    Returns:
        日期列表 (格式: YYYY-MM-DD), 按日期降序排列
    """
    query = """
    SELECT DISTINCT date 
    FROM qa_brand_state 
    WHERE tenant_key = :tenant_key 
    """
    params = {"tenant_key": tenant_key}

    if job_id:
        query += " AND job_id = :job_id "
        params["job_id"] = job_id

    query += " ORDER BY date DESC"

    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), params)
            return [
                row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])
                for row in result.fetchall()
            ]
    except Exception as e:
        logger.error(f"获取有数据日期失败: {str(e)}")
        return []


def query_filter_metadata(
    engine,
    tenant_key: str,
    job_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    def parse_date(date_value: str) -> datetime.date:
        try:
            return datetime.strptime(date_value, "%Y%m%d").date()
        except ValueError as exc:
            raise ValueError("日期格式错误，应为YYYYMMDD") from exc

    start_value = parse_date(start_date) if start_date else None
    end_value = parse_date(end_date) if end_date else None

    if start_value and end_value and start_value > end_value:
        raise ValueError("开始日期不能晚于结束日期")

    try:
        with engine.connect() as conn:
            columns = get_columns(conn, "qa_brand_state")
            required_columns = {"platform", "keyword", "date"}
            missing_columns = required_columns - columns
            if missing_columns:
                raise Exception(f"qa_brand_state 表缺少字段: {', '.join(sorted(missing_columns))}")

            if start_value is None or end_value is None:
                range_row = conn.execute(
                    text(
                        """
                        SELECT MIN(date) AS min_date, MAX(date) AS max_date
                        FROM qa_brand_state
                        WHERE tenant_key = :tenant_key
                          AND job_id = :job_id
                        """
                    ),
                    {"tenant_key": tenant_key, "job_id": job_id},
                ).fetchone()

                if not range_row or range_row[0] is None or range_row[1] is None:
                    return []

                if start_value is None:
                    start_value = range_row[0]
                if end_value is None:
                    end_value = range_row[1]

            rows = conn.execute(
                text(
                    """
                    SELECT DISTINCT platform, keyword
                    FROM qa_brand_state
                    WHERE tenant_key = :tenant_key
                      AND job_id = :job_id
                      AND date BETWEEN :start_date AND :end_date
                    ORDER BY platform ASC, keyword ASC
                    """
                ),
                {
                    "tenant_key": tenant_key,
                    "job_id": job_id,
                    "start_date": start_value,
                    "end_date": end_value,
                },
            ).fetchall()

            if not rows:
                return []

            return [{"platform": row[0], "keyword": row[1]} for row in rows]
    except ValueError:
        raise
    except Exception as e:
        logger.error("查询筛选元数据失败", error=str(e))
        raise Exception(f"查询筛选元数据失败: {str(e)}") from e


def query_keyword_platform_brand_rates(
    engine,
    tenant_key: str,
    job_id: str,
    start_date,
    end_date,
) -> List[Dict[str, Any]]:
    try:
        with engine.connect() as conn:
            columns = get_columns(conn, "qa_brand_state")

            if "keyword" not in columns:
                raise Exception("qa_brand_state 表缺少 keyword 字段")

            if "platform" not in columns:
                raise Exception("qa_brand_state 表缺少 platform 字段")

            if "brand" not in columns:
                raise Exception("qa_brand_state 表缺少 brand 字段")

            if "is_mentioned" not in columns:
                raise Exception("qa_brand_state 表缺少 is_mentioned 字段")

            if "is_first_mentioned" not in columns:
                raise Exception("qa_brand_state 表缺少 is_first_mentioned 字段")
            first_mention_column = "is_first_mentioned"

            if "is_top3_mentioned" not in columns:
                raise Exception("qa_brand_state 表缺少 is_top3_mentioned 字段")
            top3_mention_column = "is_top3_mentioned"

            query = f"""
            SELECT
                keyword,
                platform,
                brand,
                ROUND(
                    SUM(is_mentioned) * 1.0 / NULLIF(COUNT(DISTINCT conversation_id), 0),
                    4
                ) AS mention_rate,
                ROUND(
                    SUM({first_mention_column}) * 1.0 / NULLIF(COUNT(DISTINCT conversation_id), 0),
                    4
                ) AS first_mention_rate,
                ROUND(
                    SUM({top3_mention_column}) * 1.0 / NULLIF(COUNT(DISTINCT conversation_id), 0),
                    4
                ) AS top3_mention_rate
            FROM qa_brand_state
            WHERE tenant_key = :tenant_key
              AND job_id = :job_id
              AND date BETWEEN :start_date AND :end_date
            GROUP BY keyword, platform, brand
            ORDER BY keyword ASC, platform ASC, mention_rate DESC
            """

            rows = conn.execute(
                text(query),
                {
                    "tenant_key": tenant_key,
                    "job_id": job_id,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            ).fetchall()

            if not rows:
                return []

            result: List[Dict[str, Any]] = []
            for (
                keyword,
                platform,
                brand,
                mention_rate,
                first_mention_rate,
                top3_mention_rate,
            ) in rows:
                result.append(
                    {
                        "keyword": keyword,
                        "platform": platform,
                        "brand": brand,
                        "mention_rate": float(mention_rate) if mention_rate is not None else 0.0,
                        "first_mention_rate": (
                            float(first_mention_rate) if first_mention_rate is not None else 0.0
                        ),
                        "top3_mention_rate": (
                            float(top3_mention_rate) if top3_mention_rate is not None else 0.0
                        ),
                    }
                )

            return result
    except Exception as e:
        logger.error("查询 keyword-platform-brand rates 失败", error=str(e))
        raise Exception(f"查询 keyword-platform-brand rates 失败: {str(e)}") from e