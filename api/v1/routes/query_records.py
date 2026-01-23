"""LLM查询任务相关API路由."""

import datetime
import json
from typing import Any, Dict, Iterable, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.v1.models.schemas import LoadQueryJobsRequest, LoadQueryJobsResponse
from api.v1.repositories.database import get_db

router = APIRouter()

async def verify_executor(
    request: LoadQueryJobsRequest,
    db: Session = Depends(get_db),
    x_executor_key: Optional[str] = Header(None),
):
    """
    验证执行器身份。
    通过 Header 中的 X-Executor-Key 和请求体中的 executor_id 进行校验。
    """
    if not x_executor_key:
        raise HTTPException(status_code=401, detail="缺少执行器密钥 (X-Executor-Key)")

    # 在数据库中查找执行器及其 API Key
    query = text("SELECT api_key, status FROM executors WHERE executor_id = :executor_id")
    executor = db.execute(query, {"executor_id": request.executor_id}).first()

    if not executor:
        raise HTTPException(status_code=404, detail="执行器不存在")

    if executor.status != 'active':
        raise HTTPException(status_code=403, detail="执行器已被禁用")

    if executor.api_key != x_executor_key:
        raise HTTPException(status_code=401, detail="执行器密钥错误")

    return request


def iter_query_records(
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
    """遍历原始数据，生成用于数据库插入的查询记录字典流。"""
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
    try:
        now = datetime.datetime.now()

        # 使用 request.data (QueryJobData)
        data_dict = request.data.dict()

        rows = list(
            iter_query_records(
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
