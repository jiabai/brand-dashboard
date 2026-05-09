import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from api.v1.utils import get_logger
from api.v1.utils.url_domain_resolver import get_chinese_name

# 加载.env文件
# 获取当前文件所在的目录 (api/v1/repositories)
current_dir = Path(__file__).resolve().parent
# 获取api目录 (api/.env)
env_path = current_dir.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

logger = get_logger(__name__)

# 数据库配置
_is_production = os.getenv("ENV", "development") == "production"

_db_password = os.getenv("DB_PASSWORD")
if not _db_password:
    if _is_production:
        raise RuntimeError("DB_PASSWORD environment variable is required in production")
    _db_password = "devpassword"

DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": _db_password,
    "database": os.getenv("DB_NAME", "geo"),
    "charset": os.getenv("DB_CHARSET", "utf8mb4"),
}

# 创建数据库引擎和连接池
engine = create_engine(
    f"mysql+pymysql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@"
    f"{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/"
    f"{DATABASE_CONFIG['database']}?charset={DATABASE_CONFIG['charset']}",
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_date_range(
    timeframe: str, specific_date: Optional[str] = None
) -> tuple[datetime.date, datetime.date]:
    """
    根据timeframe参数计算查询的日期范围
    
    Args:
        timeframe: 时间范围 ('yesterday', '7days', '30days', 'specific_day')
        specific_date: 指定日期 (格式: YYYYMMDD)
    
    Returns:
        tuple: (start_date, end_date)
    """
    if specific_date:
        # 如果指定了具体日期
        try:
            end_date = datetime.strptime(specific_date, "%Y%m%d").date()
        except ValueError as exc:
            raise ValueError('日期格式错误，应为YYYYMMDD') from exc
    else:
        end_date = datetime.now(UTC).date()

    if timeframe == "specific_day":
        start_date = end_date
    elif timeframe == "yesterday":
        start_date = end_date - timedelta(days=1)
        end_date = start_date  # 昨天就是单天
    elif timeframe == "7days":
        start_date = end_date - timedelta(days=6)  # 包含今天，所以是6天前
    elif timeframe == "30days":
        start_date = end_date - timedelta(days=29)  # 包含今天，所以是29天前
    else:
        raise ValueError(f"不支持的时间范围: {timeframe}")

    return start_date, end_date

def get_previous_date_range(timeframe: str, specific_date: Optional[str] = None) -> tuple:
    """
    获取上一周期的时间范围
    
    Args:
        timeframe: 时间范围 ('yesterday', '7days', '30days', 'specific_day')
        specific_date: 指定日期 (格式: YYYYMMDD)
    
    Returns:
        tuple: (prev_start_date, prev_end_date)
    """
    current_start, current_end = get_date_range(timeframe, specific_date)

    if timeframe == "specific_day":
        prev_start = current_start - timedelta(days=1)
        prev_end = current_end - timedelta(days=1)
    elif timeframe == "yesterday":
        # 昨天的上一周期是前天
        prev_start = current_start - timedelta(days=1)
        prev_end = current_end - timedelta(days=1)
    elif timeframe == "7days":
        # 当前7天的上一周期是前7天
        days_diff = (current_end - current_start).days + 1
        prev_start = current_start - timedelta(days=days_diff)
        prev_end = current_end - timedelta(days=days_diff)
    elif timeframe == "30days":
        # 当前30天的上一周期是前30天
        days_diff = (current_end - current_start).days + 1
        prev_start = current_start - timedelta(days=days_diff)
        prev_end = current_end - timedelta(days=days_diff)
    else:
        raise ValueError(f"不支持的时间范围: {timeframe}")

    return prev_start, prev_end

def query_brand_mention_data(
    tenant_key: str,
    job_id: str,
    brand: str,
    timeframe: str,
    specific_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询品牌提及率数据
    
    Args:
        tenant_key: 租户键
        job_id: 任务ID
        brand: 品牌名称
        timeframe: 时间范围
        specific_date: 指定日期
    
    Returns:
        包含提及率数据的字典
        
    Note:
        如果品牌不存在，返回空数据（所有计数为0）
    """
    start_date, end_date = get_date_range(timeframe, specific_date)

    query = """
    SELECT 
        SUM(question_count) as total_questions,
        SUM(mention_count) as total_mentions,
        SUM(first_mention_count) as total_first_mentions,
        MAX(date) as latest_date
    FROM qa_brand_summary 
    WHERE tenant_key = :tenant_key
    AND job_id = :job_id
    AND brand = :brand 
    AND date BETWEEN :start_date AND :end_date
    """

    try:
        with engine.connect() as conn:
            # 检查品牌是否存在
            check_brand_query = text(
                """
                SELECT 1
                FROM qa_brand_summary
                WHERE tenant_key = :tenant_key
                  AND job_id = :job_id
                  AND brand = :brand
                LIMIT 1
                """
            )
            brand_exists = conn.execute(
                check_brand_query,
                {"tenant_key": tenant_key, "job_id": job_id, "brand": brand},
            ).fetchone()

            # 如果品牌不存在，返回空数据
            if not brand_exists:
                return {
                    "mention_rate": 0.0,
                    "rank": 1,
                    "change": 0.0,
                    "question_count": 0,
                    "mention_count": 0,
                    "first_mention_count": 0,
                    "analysis_date": end_date.isoformat(),
                    "last_updated": datetime.now(UTC).isoformat()
                }

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

            if not row or row[0] == 0:
                # 如果没有数据，返回默认值
                return {
                    "mention_rate": 0.0,
                    "rank": 1,
                    "change": 0.0,
                    "question_count": 0,
                    "mention_count": 0,
                    "first_mention_count": 0,
                    "analysis_date": end_date.isoformat(),
                    "last_updated": datetime.now(UTC).isoformat()
                }

            # 提取数据
            question_count = int(row[0]) if row[0] else 0
            mention_count = int(row[1]) if row[1] else 0
            first_mention_count = int(row[2]) if row[2] else 0
            latest_date = row[3] or end_date

            mention_rate = (mention_count / question_count) if question_count > 0 else 0.0

            # 计算排名
            # 这里简单处理，实际上可能需要更复杂的排名逻辑
            rank_query = """
            SELECT COUNT(*) + 1
            FROM (
                SELECT brand, SUM(mention_count) / SUM(question_count) as rate
                FROM qa_brand_summary
                WHERE tenant_key = :tenant_key
                AND job_id = :job_id
                AND date BETWEEN :start_date AND :end_date
                GROUP BY brand
                HAVING rate > :my_rate
            ) as ranks
            """

            rank_result = conn.execute(
                text(rank_query),
                {
                    "tenant_key": tenant_key,
                    "job_id": job_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "my_rate": mention_rate
                }
            )
            rank = rank_result.scalar()

            # 计算变化率
            prev_start, prev_end = get_previous_date_range(timeframe, specific_date)
            
            prev_query = """
            SELECT SUM(mention_count), SUM(question_count)
            FROM qa_brand_summary
            WHERE tenant_key = :tenant_key
            AND job_id = :job_id
            AND brand = :brand
            AND date BETWEEN :prev_start AND :prev_end
            """
            
            prev_result = conn.execute(
                text(prev_query),
                {
                    "tenant_key": tenant_key,
                    "job_id": job_id,
                    "brand": brand,
                    "prev_start": prev_start,
                    "prev_end": prev_end
                }
            )
            prev_row = prev_result.fetchone()
            if prev_row and prev_row[1] and prev_row[1] > 0:
                prev_rate = float(prev_row[0]) / float(prev_row[1])
            else:
                prev_rate = 0.0
            
            change = (mention_rate - prev_rate) * 100


            analysis_date = (
                latest_date.isoformat()
                if hasattr(latest_date, "isoformat")
                else str(latest_date)
            )
            return {
                "mention_rate": round(mention_rate, 2),
                "rank": rank,
                "change": round(change, 2),
                "question_count": question_count,
                "mention_count": mention_count,
                "first_mention_count": first_mention_count,
                "analysis_date": analysis_date,
                "last_updated": datetime.now(UTC).isoformat()
            }
            
    except Exception as e:
        logger.error("查询品牌提及率数据失败", error=str(e))
        raise

def query_post_citation_rate(
    tenant_key: str,
    job_id: str,
    brand: str,
    start_date: datetime.date,
    end_date: datetime.date
) -> Dict[str, Any]:
    """
    查询品牌发文引用率数据
    
    Args:
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
    tenant_key: str,
    job_id: str,
    brand: str,
    start_date: datetime.date,
    end_date: datetime.date,
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
    # 基础过滤条件（用于分母）
    base_where = """
    WHERE tenant_key = :tenant_key
    AND job_id = :job_id
    AND brand = :brand
    AND domain IS NOT NULL
    AND date BETWEEN :start_date AND :end_date
    """
    
    # 分母 SQL：锁定在平台层级，不随 keyword 变化
    denominator_where = base_where
    if platform:
        denominator_where += "\n    AND platform = :platform"

    # 分子 SQL：随 keyword 和 platform 变化
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
    tenant_key: str,
    job_id: str,
    keyword: str,
    domain: str,
    start_date: datetime.date,
    end_date: datetime.date
) -> List[Dict[str, Any]]:
    """
    查询引用URL的统计数据
    
    Args:
        tenant_key: 租户键
        job_id: 任务ID
        timeframe: 时间范围 ('yesterday', '7days', '30days')
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        包含引用URL统计数据的列表，按引用次数降序排列
    """

    # 查询引用URL统计
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

    # 查询总提问数
    total_questions_query = """
    SELECT COUNT(DISTINCT conversation_id) AS total_questions 
    FROM qa_reference 
    WHERE tenant_key = :tenant_key
    AND job_id = :job_id
    AND date BETWEEN :start_date AND :end_date
    """

    try:
        with engine.connect() as conn:
            # 获取引用URL统计数据
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

            # 获取总提问数
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

            # 构建结果列表
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
    tenant_key: str,
    job_id: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> tuple[Dict[str, int], List[Dict[str, Any]]]:
    """
    查询引用类型占比统计数据
    
    Args:
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


def get_available_dates(tenant_key: str, job_id: Optional[str] = None) -> List[str]:
    """
    获取 qa_brand_state 表中有数据的所有日期
    
    Args:
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
            columns_result = conn.execute(text("SHOW COLUMNS FROM qa_brand_state")).fetchall()
            columns = {row[0] for row in columns_result}
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

def query_brand_platform_keyword_daily_mention_rates(
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
            columns_result = conn.execute(text("SHOW COLUMNS FROM qa_brand_state")).fetchall()
            columns = {row[0] for row in columns_result}

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

def query_brand_platform_mention_data(
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
            columns_result = conn.execute(text("SHOW COLUMNS FROM qa_brand_state")).fetchall()
            columns = {row[0] for row in columns_result}

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

def query_brand_metrics(
    tenant_key: str,
    job_id: str,
    start_date: datetime.date,
    end_date: datetime.date,
    brand: Optional[str] = None,
    platform: Optional[str] = None,
) -> List[Dict[str, Any]]:
    try:
        with engine.connect() as conn:
            columns_result = conn.execute(text("SHOW COLUMNS FROM qa_brand_state")).fetchall()
            columns = {row[0] for row in columns_result}

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
    tenant_key: str,
    job_id: str,
    brand: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> List[Dict[str, Any]]:
    try:
        with engine.connect() as conn:
            columns_result = conn.execute(text("SHOW COLUMNS FROM qa_brand_state")).fetchall()
            columns = {row[0] for row in columns_result}

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

def query_domain_citation_summary(
    tenant_key: str,
    job_id: str,
    brand: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> List[Dict[str, Any]]:
    """
    查询域名维度的引用率汇总数据（按域名聚合）

    Args:
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


def query_keyword_platform_brand_rates(
    tenant_key: str,
    job_id: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> List[Dict[str, Any]]:
    try:
        with engine.connect() as conn:
            columns_result = conn.execute(text("SHOW COLUMNS FROM qa_brand_state")).fetchall()
            columns = {row[0] for row in columns_result}

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
