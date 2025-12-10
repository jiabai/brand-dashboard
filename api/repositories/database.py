import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# 数据库配置
DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
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

def get_date_range(timeframe: str, specific_date: Optional[str] = None) -> tuple:
    """
    根据timeframe参数计算查询的日期范围
    
    Args:
        timeframe: 时间范围 ('yesterday', '7days', '30days')
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
        end_date = datetime.now().date()

    if timeframe == "yesterday":
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
        timeframe: 时间范围 ('yesterday', '7days', '30days')
        specific_date: 指定日期 (格式: YYYYMMDD)
    
    Returns:
        tuple: (prev_start_date, prev_end_date)
    """
    current_start, current_end = get_date_range(timeframe, specific_date)

    if timeframe == "yesterday":
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
    brand: str,
    timeframe: str,
    specific_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询品牌提及率数据
    
    Args:
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
        MAX(date) as latest_date,
        AVG(mention_rate) as avg_mention_rate
    FROM qa_brand_summary 
    WHERE brand = :brand 
    AND date BETWEEN :start_date AND :end_date
    """

    try:
        with engine.connect() as conn:
            # 检查品牌是否存在
            check_brand_query = text("SELECT 1 FROM qa_brand_summary WHERE brand = :brand LIMIT 1")
            brand_exists = conn.execute(check_brand_query, {"brand": brand}).fetchone()

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
                    "last_updated": datetime.now().isoformat()
                }

            result = conn.execute(
                text(query),
                {
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
                    "last_updated": datetime.now().isoformat()
                }

            # 提取数据
            question_count = int(row[0]) if row[0] else 0
            mention_count = int(row[1]) if row[1] else 0
            first_mention_count = int(row[2]) if row[2] else 0
            latest_date = row[3] or end_date
            mention_rate = float(row[4]) if row[4] else 0.0

            # 计算变化百分比 - 查询上一周期的数据
            change = 0.0
            try:
                prev_start_date, prev_end_date = get_previous_date_range(timeframe, specific_date)

                prev_query = """
                SELECT 
                    AVG(mention_rate) as prev_avg_mention_rate
                FROM qa_brand_summary 
                WHERE brand = :brand 
                AND date BETWEEN :prev_start_date AND :prev_end_date
                """

                prev_result = conn.execute(
                    text(prev_query),
                    {
                        "brand": brand,
                        "prev_start_date": prev_start_date,
                        "prev_end_date": prev_end_date
                    }
                )

                prev_row = prev_result.fetchone()
                if prev_row and prev_row[0] is not None:
                    prev_mention_rate = float(prev_row[0])
                    if prev_mention_rate > 0:  # 避免除零错误
                        change = round(
                            (mention_rate - prev_mention_rate) / prev_mention_rate * 100,
                            2
                        )
            except Exception as e:
                logger.warning("计算变化百分比时出错: %s", str(e))
                change = 0.0

            return {
                "mention_rate": round(mention_rate, 2),
                "rank": 1,  # 默认排名
                "change": change,  # 变化百分比
                "question_count": question_count,
                "mention_count": mention_count,
                "first_mention_count": first_mention_count,
                "analysis_date": latest_date.isoformat(),
                "last_updated": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error("数据库查询失败: %s", str(e))
        raise Exception(f"数据库查询失败: {str(e)}") from e

def query_reference_url_stats(
    timeframe: str,
    specific_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    查询引用URL的统计数据
    
    Args:
        timeframe: 时间范围 ('yesterday', '7days', '30days')
        specific_date: 指定日期 (格式: YYYYMMDD)
    
    Returns:
        包含引用URL统计数据的列表，按引用次数降序排列
    """
    start_date, end_date = get_date_range(timeframe, specific_date)

    # 查询引用URL统计
    url_query = """
    SELECT 
        answer_reference_url, 
        COUNT(*) AS reference_count 
    FROM qa_reference 
    WHERE answer_reference_url IS NOT NULL 
    AND date BETWEEN :start_date AND :end_date 
    GROUP BY answer_reference_url 
    ORDER BY reference_count DESC
    """

    # 查询总提问数
    total_questions_query = """
    SELECT COUNT(DISTINCT question_id) AS total_questions 
    FROM qa_reference 
    WHERE date BETWEEN :start_date AND :end_date
    """

    try:
        with engine.connect() as conn:
            # 获取引用URL统计数据
            url_result = conn.execute(
                text(url_query),
                {
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            url_rows = url_result.fetchall()

            # 获取总提问数
            total_result = conn.execute(
                text(total_questions_query),
                {
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
            reference_data = []
            for row in url_rows:
                reference_url = row[0]
                reference_count = int(row[1]) if row[1] else 0

                reference_data.append({
                    "answer_reference_url": reference_url,
                    "reference_count": reference_count,
                    "total_questions": total_questions
                })

            return reference_data
    except Exception as e:
        logger.error("查询引用URL统计数据失败: %s", str(e))
        raise Exception(f"查询引用URL统计数据失败: {str(e)}") from e

def query_brand_platform_mention_data(
    brand: str,
    timeframe: str,
    specific_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    查询品牌在各平台的提及率数据
    
    Args:
        brand: 品牌名称
        timeframe: 时间范围
        specific_date: 指定日期
    
    Returns:
        包含各平台提及率数据的列表
        
    Note:
        如果品牌不存在，返回空列表
    """
    start_date, end_date = get_date_range(timeframe, specific_date)

    query = """
    SELECT 
        platform,
        SUM(question_count) as total_questions,
        SUM(mention_count) as total_mentions,
        SUM(first_mention_count) as total_first_mentions,
        MAX(date) as latest_date,
        AVG(mention_rate) as avg_mention_rate
    FROM qa_brand_summary 
    WHERE brand = :brand 
    AND date BETWEEN :start_date AND :end_date
    GROUP BY platform
    ORDER BY avg_mention_rate DESC
    """

    try:
        with engine.connect() as conn:
            # 检查品牌是否存在
            check_brand_query = text("SELECT 1 FROM qa_brand_summary WHERE brand = :brand LIMIT 1")
            brand_exists = conn.execute(check_brand_query, {"brand": brand}).fetchone()

            # 如果品牌不存在，返回空列表
            if not brand_exists:
                return []

            result = conn.execute(
                text(query),
                {
                    "brand": brand,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )

            rows = result.fetchall()

            if not rows:
                # 如果没有数据，返回空列表
                return []

            # 构建结果列表
            platform_data = []
            for index, row in enumerate(rows):
                platform = row[0]
                question_count = int(row[1]) if row[1] else 0
                mention_count = int(row[2]) if row[2] else 0
                first_mention_count = int(row[3]) if row[3] else 0
                latest_date = row[4] or end_date
                mention_rate = float(row[5]) if row[5] else 0.0

                platform_data.append({
                    "platform": platform,
                    "mention_rate": round(mention_rate, 2),
                    "rank": index + 1,  # 按提及率排序的排名
                    "question_count": question_count,
                    "mention_count": mention_count,
                    "first_mention_count": first_mention_count,
                    "analysis_date": latest_date.isoformat(),
                    "last_updated": datetime.now().isoformat()
                })

            return platform_data
    except Exception as e:
        logger.error("数据库查询失败: %s", str(e))
        raise Exception(f"数据库查询失败: {str(e)}") from e
