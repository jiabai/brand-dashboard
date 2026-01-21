"""LLM查询记录相关API路由."""

import datetime
import json
from typing import Any, Dict, Iterable

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.models.schemas import LoadQueryRecordsRequest, LoadQueryRecordsResponse
from api.repositories.database import get_db

router = APIRouter()

def iter_query_records(
    data_dict: Dict[str, Any],
    tenant_key: str,
    job_id: str,
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
                "created_at": created_at,
                "updated_at": updated_at,
            }


@router.post("/load", response_model=LoadQueryRecordsResponse)
async def load_query_records(
    request: LoadQueryRecordsRequest,
    db: Session = Depends(get_db),
):
    """
    接收原始JSON数据并加载到llm_query_record数据库表中.
    """
    try:
        now = datetime.datetime.now()

        # 使用 request.data (QueryRecordData)
        data_dict = request.data.dict()

        rows = list(
            iter_query_records(
                data_dict,
                tenant_key=request.tenant_key,
                job_id=request.job_id,
                created_at=now,
                updated_at=now,
            )
        )

        if not rows:
            return LoadQueryRecordsResponse(
                success=True,
                inserted_rows=0,
                message="没有生成任何记录",
            )

        sql = text(
            """
        INSERT INTO llm_query_record (
          tenant_key,
          job_id,
          category,
          brand,
          competitor,
          keyword,
          query_content,
          query_status,
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
          :created_at,
          :updated_at
        )
        """
        )

        result = db.execute(sql, rows)
        db.commit()

        return LoadQueryRecordsResponse(
            success=True,
            inserted_rows=result.rowcount,
            message="LLM查询记录加载成功",
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"加载LLM查询记录失败: {str(e)}") from e
