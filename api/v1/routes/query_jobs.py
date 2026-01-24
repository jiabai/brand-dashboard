"""LLM查询任务相关API路由."""

import datetime
import json
from typing import Any, Dict, Iterable, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Header, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.v1.models.schemas import (
    FetchQueryJobResponse,
    LoadQueryJobsRequest,
    LoadQueryJobsResponse,
    QueryJobDetail,
    ReportQueryJobResponse,
)
from api.v1.repositories.database import get_db

router = APIRouter()

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

    if executor.api_key != x_executor_key:
        raise HTTPException(status_code=401, detail="执行器密钥错误")

    return executor_id

@router.get("/fetch", response_model=FetchQueryJobResponse)
async def fetch_query_job(
    executor_id: str = Depends(verify_executor),
    db: Session = Depends(get_db),
):
    """
    执行器获取待执行任务。
    采用 Round-Robin 策略：优先选取已执行次数最少的任务，且按物理顺序排列。
    """
    sql = text(
        """
        SELECT 
            id, job_id, tenant_key, category, brand, competitor, keyword, query_content 
        FROM llm_query_jobs
        WHERE executor_id = :executor_id
          AND query_status = 1           -- 1. 索引等值过滤
          AND is_deleted = 0             -- 2. 简单状态过滤
          AND executed_runs < total_runs -- 3. 简单数值比较
          AND CURRENT_TIMESTAMP >= effective_from -- 4. 时间范围开始
          AND (effective_to IS NULL OR CURRENT_TIMESTAMP <= effective_to) -- 5. 时间范围结束
          AND (last_executed_date IS NULL OR last_executed_date <= CURRENT_DATE) -- 6. 复杂 OR/日期逻辑放最后
        ORDER BY 
          executed_runs ASC,             -- 优先级1：跑得最少的轮次优先
          id ASC                         -- 优先级2：物理顺序优先
        LIMIT 1;
        """
    )

    result = db.execute(sql, {"executor_id": executor_id}).first()

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
        text("SELECT executed_runs, total_runs FROM llm_query_jobs WHERE id = :id AND executor_id = :executor_id"),
        {"id": id, "executor_id": executor_id}
    ).first()

    if not query_job:
        raise HTTPException(status_code=404, detail="任务记录不存在或不属于该执行器")

    if query_job.executed_runs >= query_job.total_runs:
        return ReportQueryJobResponse(success=False, message="任务执行次数已达上限")

    try:
        # 2. 更新任务执行次数，增加条件确保并发安全
        result = db.execute(
            text(
                "UPDATE llm_query_jobs SET executed_runs = executed_runs + 1, "
                "last_executed_date = :today, updated_at = :now "
                "WHERE id = :id AND executed_runs < total_runs"
            ),
            {
                "today": datetime.date.today(),
                "now": datetime.datetime.now(),
                "id": id
            }
        )

        if result.rowcount == 0:
            db.rollback()
            return ReportQueryJobResponse(success=False, message="上报失败：任务执行次数已满或状态已变更")

        db.commit()
        return ReportQueryJobResponse(success=True, message="上报成功")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"上报失败: {str(e)}") from e


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
                "query_status": 1,
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
        now = datetime.datetime.now()

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
