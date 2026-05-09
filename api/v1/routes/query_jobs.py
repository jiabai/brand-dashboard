"""LLM查询任务相关API路由."""

import datetime
import hmac
import json
from datetime import UTC
from typing import Any, Dict, Iterable, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.v1.models.schemas import (
    FetchQueryJobResponse,
    LoadQueryJobsRequest,
    LoadQueryJobsResponse,
    QueryJobDetail,
    QueryJobStatusItem,
    QueryJobStatusResponse,
    ReportQueryJobResponse,
)
from api.v1.repositories.database import get_db
from api.v1.utils import get_logger

router = APIRouter()

logger = get_logger(__name__)


def sync_query_jobs_status(db: Session):
    """
    同步任务状态逻辑：
    1. 0 (未生效) -> 1 (生效中): 当当前时间 >= effective_from 时。
    2. 1 (生效中) -> 3 (已失效): 当 effective_to 不为空且当前时间 > effective_to 时。
    """
    now = datetime.datetime.now(UTC)
    try:
        db.execute(
            text(
                """
                UPDATE llm_query_jobs 
                SET query_status = CASE 
                    WHEN query_status = 0 AND effective_from <= :now THEN 1
                    WHEN query_status = 1 AND effective_to IS NOT NULL 
                         AND effective_to < :now THEN 3
                    ELSE query_status
                END,
                updated_at = :now
                WHERE (query_status = 0 AND effective_from <= :now)
                   OR (query_status = 1 AND effective_to IS NOT NULL AND effective_to < :now)
                """
            ),
            {"now": now}
        )
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Error syncing query job statuses: %s", e)

async def verify_executor(
    executor_id: str = Query(..., description="执行器唯一ID"),
    x_executor_key: Optional[str] = Header(None, alias="X-Executor-Key"),
    db: Session = Depends(get_db),
):
    """
    验证执行器身份。
    通过 Header 中的 X-Executor-Key 和 Query Param 中的 executor_id 进行校验。
    """
    if not x_executor_key:
        raise HTTPException(status_code=401, detail="缺少执行器密钥 (X-Executor-Key)")

    # 在数据库中查找执行器及其 API Key
    query = text("SELECT api_key, status FROM executors WHERE executor_id = :executor_id")
    executor = db.execute(query, {"executor_id": executor_id}).first()

    if not executor:
        raise HTTPException(status_code=404, detail="执行器不存在")

    if executor.status != 'active':
        raise HTTPException(status_code=403, detail="执行器已被禁用")

    if not hmac.compare_digest(executor.api_key, x_executor_key):
        raise HTTPException(status_code=401, detail="执行器密钥错误")

    return executor_id

@router.get("/fetch", response_model=FetchQueryJobResponse)
async def fetch_query_job(
    tenant_key: Optional[str] = Query(None, description="可选：仅拉取指定租户的任务"),
    job_id: Optional[str] = Query(None, description="可选：仅拉取指定 job_id 的任务"),
    executor_id: str = Depends(verify_executor),
    db: Session = Depends(get_db),
):
    """
    执行器获取待执行任务。
    采用 Round-Robin 策略：优先选取已执行次数最少的任务，且按物理顺序排列。
    """
    # 同步任务状态
    sync_query_jobs_status(db)

    normalized_tenant_key = tenant_key.strip() if tenant_key else None
    if not normalized_tenant_key:
        normalized_tenant_key = None

    normalized_job_id = job_id.strip() if job_id else None
    if not normalized_job_id:
        normalized_job_id = None

    params: Dict[str, Any] = {"executor_id": executor_id}

    where_clauses = ["executor_id = :executor_id"]

    if normalized_tenant_key is not None:
        where_clauses.append("tenant_key = :tenant_key")
        params["tenant_key"] = normalized_tenant_key

    if normalized_job_id is not None:
        where_clauses.append("job_id = :job_id")
        params["job_id"] = normalized_job_id

    where_clauses.extend(
        [
            "query_status = 1",
            "is_deleted = 0",
            "executed_runs < total_runs",
            "CURRENT_TIMESTAMP >= effective_from",
            "(effective_to IS NULL OR CURRENT_TIMESTAMP <= effective_to)",
            # 此处使用 <= CURRENT_DATE 是为了允许同一个任务在同一天内被多次拉取并执行，
            # 只要总执行次数 executed_runs 未达到 total_runs 即可。
            "(last_executed_date IS NULL OR last_executed_date <= CURRENT_DATE)",
        ]
    )

    sql = text(
        f"""
        SELECT
          id, job_id, tenant_key, category, brand, competitor, keyword, query_content
        FROM llm_query_jobs
        WHERE {" AND ".join(where_clauses)}
        ORDER BY
          executed_runs ASC,
          id ASC
        LIMIT 1;
        """
    )

    result = db.execute(sql, params).first()

    if not result:
        return FetchQueryJobResponse(success=True, count=0, jobs=None)

    # 处理 competitor JSON 字符串
    competitor = None
    if result.competitor:
        try:
            competitor = json.loads(result.competitor)
        except Exception:
            competitor = [result.competitor]

    job_detail = QueryJobDetail(
        id=result.id,
        job_id=result.job_id,
        tenant_key=result.tenant_key,
        category=result.category,
        brand=result.brand,
        competitor=competitor,
        keyword=result.keyword,
        query_content=result.query_content,
    )

    return FetchQueryJobResponse(success=True, count=1, jobs=job_detail)

@router.post("/report", response_model=ReportQueryJobResponse)
async def report_query_job(
    id: int = Body(..., embed=True, description="任务记录唯一主键ID"),
    executor_id: str = Depends(verify_executor),
    db: Session = Depends(get_db),
):
    """
    执行器上报任务执行结果。
    仅更新 llm_query_jobs 表中的执行次数和日期。
    """
    # 1. 查找对应的任务记录，并校验执行器及执行次数
    query_job = db.execute(
        text(
            """
            SELECT executed_runs, total_runs
            FROM llm_query_jobs
            WHERE id = :id AND executor_id = :executor_id
            """
        ),
        {"id": id, "executor_id": executor_id},
    ).first()

    if not query_job:
        raise HTTPException(status_code=404, detail="任务记录不存在或不属于该执行器")

    if query_job.executed_runs >= query_job.total_runs:
        return ReportQueryJobResponse(success=False, message="任务执行次数已达上限")

    try:
        # 2. 更新任务执行次数，并根据次数自动更新状态为 2 (已完成)
        result = db.execute(
            text(
                """
                UPDATE llm_query_jobs 
                SET executed_runs = executed_runs + 1,
                    query_status = CASE 
                        WHEN executed_runs + 1 >= total_runs THEN 2 
                        ELSE query_status 
                    END,
                    last_executed_date = :today, 
                    updated_at = :now 
                WHERE id = :id AND executed_runs < total_runs
                """
            ),
            {
                "today": datetime.date.today(),
                "now": datetime.datetime.now(UTC),
                "id": id
            }
        )

        if result.rowcount == 0:
            db.rollback()
            return ReportQueryJobResponse(
                success=False,
                message="上报失败：任务执行次数已满或状态已变更",
            )

        db.commit()
        return ReportQueryJobResponse(success=True, message="上报成功")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上报失败: {str(e)}") from e


@router.get("/status", response_model=QueryJobStatusResponse)
async def list_query_jobs_status(
    tenant_key: str = Query(..., description="租户Key"),
    job_id: Optional[str] = Query(None, description="可选：仅查询指定 job_id 的任务"),
    include_deleted: bool = Query(False, description="是否包含已删除任务"),
    db: Session = Depends(get_db),
):
    # 同步任务状态
    sync_query_jobs_status(db)

    tenant_check = db.execute(
        text("SELECT 1 FROM tenants WHERE tenant_key = :tenant_key"),
        {"tenant_key": tenant_key},
    ).first()

    if not tenant_check:
        raise HTTPException(status_code=400, detail=f"租户不存在: {tenant_key}")

    normalized_job_id = job_id.strip() if job_id else None
    if not normalized_job_id:
        normalized_job_id = None

    params: Dict[str, Any] = {"tenant_key": tenant_key}

    where_clauses = ["tenant_key = :tenant_key"]
    if normalized_job_id is not None:
        where_clauses.append("job_id = :job_id")
        params["job_id"] = normalized_job_id

    if not include_deleted:
        where_clauses.append("is_deleted = 0")

    sql = text(
        f"""
        SELECT
          tenant_key,
          job_id,
          brand,
          competitor,
          query_content,
          query_status,
          effective_from,
          effective_to
        FROM llm_query_jobs
        WHERE {" AND ".join(where_clauses)}
        ORDER BY id DESC
        """
    )

    rows = db.execute(sql, params).fetchall()

    jobs = [
        QueryJobStatusItem(
            tenant_key=row.tenant_key,
            job_id=row.job_id,
            brand=row.brand,
            competitor=json.loads(row.competitor) if row.competitor else None,
            query_content=row.query_content,
            query_status=row.query_status,
            effective_from=row.effective_from,
            effective_to=row.effective_to,
        )
        for row in rows
    ]

    return QueryJobStatusResponse(success=True, count=len(jobs), jobs=jobs)


def iter_query_jobs(
    data_dict: Dict[str, Any],
    tenant_key: str,
    job_id: str,
    effective_from: datetime.datetime,
    effective_to: Optional[datetime.datetime],
    executor_id: str,
    total_runs: int,
    executed_runs: int,
    last_executed_date: datetime.date,
    created_at: datetime.datetime,
    updated_at: datetime.datetime,
) -> Iterable[Dict[str, Any]]:
    """遍历原始数据，生成用于数据库插入的查询任务字典流。"""
    category = data_dict.get("category")
    brand = data_dict.get("brand")
    competitor = data_dict.get("competitor")
    content = data_dict.get("content")

    competitor_str = None
    if competitor is not None:
        # 将 Python 列表序列化为 JSON 字符串，以适配数据库的 JSON 字段类型
        competitor_str = json.dumps(competitor, ensure_ascii=False)

    # 根据生效开始时间设置初始状态：如果开始时间在未来，则为 0 (未生效)，否则为 1 (生效中)
    now = datetime.datetime.now(UTC)
    initial_status = 1 if effective_from <= now else 0

    for item in content:
        keyword = item.get("keyword")
        queries = item.get("query_content")
        for q in queries:
            yield {
                "tenant_key": tenant_key,
                "job_id": job_id,
                "category": category,
                "brand": brand,
                "competitor": competitor_str,
                "keyword": keyword,
                "query_content": q,
                "query_status": initial_status,
                "executor_id": executor_id,
                "total_runs": total_runs,
                "executed_runs": executed_runs,
                "last_executed_date": last_executed_date,
                "effective_from": effective_from,
                "effective_to": effective_to,
                "created_at": created_at,
                "updated_at": updated_at,
            }

@router.post("/load", response_model=LoadQueryJobsResponse)
async def load_query_jobs(
    request: LoadQueryJobsRequest,
    db: Session = Depends(get_db),
):
    """
    接收原始JSON数据并加载到llm_query_jobs数据库表中.
    """
    # 1. 验证租户是否存在
    tenant_check = db.execute(
        text("SELECT 1 FROM tenants WHERE tenant_key = :tenant_key"),
        {"tenant_key": request.tenant_key}
    ).first()

    if not tenant_check:
        raise HTTPException(
            status_code=400, 
            detail=f"租户不存在: {request.tenant_key}"
        )

    try:
        now = datetime.datetime.now(UTC)

        # 使用 request.data (QueryJobData)
        data_dict = request.data.dict()

        rows = list(
            iter_query_jobs(
                data_dict,
                tenant_key=request.tenant_key,
                job_id=request.job_id,
                effective_from=request.effective_from,
                effective_to=request.effective_to,
                executor_id=request.executor_id,
                total_runs=request.total_runs,
                executed_runs=request.executed_runs,
                last_executed_date=request.last_executed_date,
                created_at=now,
                updated_at=now,
            )
        )

        if not rows:
            return LoadQueryJobsResponse(
                success=True,
                inserted_rows=0,
                message="没有生成任何记录",
            )

        sql = text(
            """
        INSERT INTO llm_query_jobs (
          tenant_key,
          job_id,
          category,
          brand,
          competitor,
          keyword,
          query_content,
          query_status,
          executor_id,
          total_runs,
          executed_runs,
          last_executed_date,
          effective_from,
          effective_to,
          created_at,
          updated_at
        )
        VALUES (
          :tenant_key,
          :job_id,
          :category,
          :brand,
          :competitor,
          :keyword,
          :query_content,
          :query_status,
          :executor_id,
          :total_runs,
          :executed_runs,
          :last_executed_date,
          :effective_from,
          :effective_to,
          :created_at,
          :updated_at
        )
        """
        )

        result = db.execute(sql, rows)
        db.commit()

        return LoadQueryJobsResponse(
            success=True,
            inserted_rows=result.rowcount,
            message="LLM查询任务加载成功",
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"加载LLM查询任务失败: {str(e)}") from e
