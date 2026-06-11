"""LLM查询任务相关API路由."""

import datetime
import hmac
import json
from datetime import UTC
from typing import Any, Dict, Iterable, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from api.v1.dependencies.auth import (
    CurrentTenantContext,
    get_current_tenant,
    require_current_tenant,
)
from api.v1.models.schemas import (
    FetchQueryJobResponse,
    LoadQueryJobsRequest,
    LoadQueryJobsResponse,
    QueryJobDetail,
    QueryJobStatusItem,
    QueryJobStatusResponse,
    ReportQueryJobResponse,
)
from api.v1.repositories.connection import get_db
from api.v1.repositories.executors import get_executor_credentials
from api.v1.repositories.projects import get_project
from api.v1.repositories.query_jobs import (
    executor_has_job_scope,
    fetch_next_query_job,
    get_query_job_runs,
    increment_query_job_runs,
    insert_query_jobs,
    query_job_has_loaded_conversation,
)
from api.v1.repositories.query_jobs import (
    list_query_jobs_status as list_query_jobs_status_records,
)
from api.v1.repositories.query_jobs import (
    sync_query_jobs_status as sync_query_jobs_status_records,
)
from api.v1.repositories.tenants import tenant_exists
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
        sync_query_jobs_status_records(db, now)
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

    executor = get_executor_credentials(db, executor_id)

    if not executor:
        raise HTTPException(status_code=404, detail="执行器不存在")

    if executor.status != 'active':
        raise HTTPException(status_code=403, detail="执行器已被禁用")

    if not hmac.compare_digest(executor.api_key, x_executor_key):
        raise HTTPException(status_code=401, detail="执行器密钥错误")

    return executor_id


def verify_executor_job_scope(
    db: Session,
    *,
    executor_id: str,
    tenant_key: str,
    job_id: str,
) -> None:
    if not executor_has_job_scope(
        db,
        executor_id=executor_id,
        tenant_key=tenant_key,
        job_id=job_id,
    ):
        raise HTTPException(status_code=403, detail="执行器无权访问该租户任务")

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

    result = fetch_next_query_job(
        db,
        executor_id=executor_id,
        tenant_key=normalized_tenant_key,
        job_id=normalized_job_id,
    )

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
        project_id=getattr(result, "project_id", None),
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
    query_job = get_query_job_runs(db, record_id=id, executor_id=executor_id)

    if not query_job:
        raise HTTPException(status_code=404, detail="任务记录不存在或不属于该执行器")

    if query_job.executed_runs >= query_job.total_runs:
        return ReportQueryJobResponse(success=False, message="任务执行次数已达上限")

    # 兼容期缺少 attempt_id，只能用任务粒度字段确认结果已入库。
    if not query_job_has_loaded_conversation(
        db,
        record_id=id,
        executor_id=executor_id,
    ):
        return ReportQueryJobResponse(
            success=False,
            message="任务结果尚未成功入库，不能上报完成",
        )

    try:
        # 2. 更新任务执行次数，并根据次数自动更新状态为 2 (已完成)
        now = datetime.datetime.now(UTC)
        rowcount = increment_query_job_runs(
            db,
            record_id=id,
            executor_id=executor_id,
            today=now.date(),
            now=now,
        )

        if rowcount == 0:
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
    project_id: Optional[str] = Query(None, description="可选：仅查询指定项目的任务"),
    include_deleted: bool = Query(False, description="是否包含已删除任务"),
    tenant: CurrentTenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
):
    tenant_key = tenant.tenant_key
    # 同步任务状态
    sync_query_jobs_status(db)

    if not tenant_exists(db, tenant_key):
        raise HTTPException(status_code=400, detail=f"租户不存在: {tenant_key}")

    normalized_job_id = job_id.strip() if job_id else None
    if not normalized_job_id:
        normalized_job_id = None

    normalized_project_id = project_id.strip() if project_id else None
    if not normalized_project_id:
        normalized_project_id = None

    rows = list_query_jobs_status_records(
        db,
        tenant_key=tenant_key,
        job_id=normalized_job_id,
        project_id=normalized_project_id,
        include_deleted=include_deleted,
    )

    jobs = [
        QueryJobStatusItem(
            tenant_key=row.tenant_key,
            job_id=row.job_id,
            project_id=getattr(row, "project_id", None),
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
    project_id: Optional[str],
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
                "project_id": project_id,
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
    tenant: CurrentTenantContext = Depends(require_current_tenant("admin")),
    db: Session = Depends(get_db),
):
    """
    接收原始JSON数据并加载到llm_query_jobs数据库表中.
    """
    if request.tenant_key != tenant.tenant_key:
        raise HTTPException(status_code=400, detail="租户上下文不一致")

    project_id = request.project_id.strip() if request.project_id else None
    if project_id and not get_project(
        db,
        tenant_key=tenant.tenant_key,
        project_id=project_id,
    ):
        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")

    # 1. 验证租户是否存在
    if not tenant_exists(db, tenant.tenant_key):
        raise HTTPException(
            status_code=400, 
            detail=f"租户不存在: {tenant.tenant_key}"
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
                project_id=project_id,
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

        inserted_rows = insert_query_jobs(db, rows)
        db.commit()

        return LoadQueryJobsResponse(
            success=True,
            inserted_rows=inserted_rows,
            message="LLM查询任务加载成功",
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"加载LLM查询任务失败: {str(e)}") from e
