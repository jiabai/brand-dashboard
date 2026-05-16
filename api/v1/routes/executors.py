from datetime import UTC, datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from api.v1.models.schemas import (
    ExecutorCreate,
    ExecutorListItem,
    ExecutorRegistrationResponse,
    ExecutorResponse,
)
from api.v1.repositories.connection import get_db
from api.v1.repositories.executors import (
    deactivate_executor as deactivate_executor_record,
)
from api.v1.repositories.executors import (
    get_active_executor_by_ip,
    insert_executor,
)
from api.v1.repositories.executors import (
    list_executors as list_executor_records,
)
from api.v1.utils.security import generate_api_key, generate_executor_id

router = APIRouter()

@router.post("/", response_model=ExecutorResponse)
async def create_executor(
    executor_in: ExecutorCreate,
    db: Session = Depends(get_db)
):
    """
    管理员手动创建一个新的执行器记录，并预设其允许的 IP 地址。
    """
    executor_id = generate_executor_id()
    api_key = generate_api_key()

    now = datetime.now(UTC)
    try:
        insert_executor(
            db,
            executor_id=executor_id,
            name=executor_in.name,
            executor_type=executor_in.type,
            ip_address=executor_in.ip_address,
            api_key=api_key,
            now=now,
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建执行器失败: {str(e)}") from e

    return ExecutorResponse(
        executor_id=executor_id,
        name=executor_in.name,
        type=executor_in.type,
        ip_address=executor_in.ip_address,
        status='active',
        created_at=now
    )

@router.post("/register", response_model=ExecutorRegistrationResponse)
async def register_executor(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    执行器注册接口。
    直接根据请求方的 IP 地址查找并返回对应的执行器凭据。
    如果该 IP 未在系统中预设为 active 状态，则拒绝注册。
    """
    client_ip = request.client.host

    executor = get_active_executor_by_ip(db, client_ip)

    if not executor:
        raise HTTPException(
            status_code=403, 
            detail="注册失败：当前 IP 未被授权。请联系管理员。"
        )

    return ExecutorRegistrationResponse(
        executor_id=executor.executor_id,
        api_key=executor.api_key
    )

@router.get("/", response_model=List[ExecutorListItem])
async def list_executors(
    db: Session = Depends(get_db)
):
    """
    获取所有执行器列表（包含 IP 地址，不返回 api_key）。
    """
    result = list_executor_records(db)

    return [
        ExecutorListItem(
            executor_id=row.executor_id,
            name=row.name,
            type=row.type,
            status=row.status,
            ip_address=row.ip_address,
            created_at=row.created_at
        ) for row in result
    ]

@router.delete("/{executor_id}")
async def deactivate_executor(
    executor_id: str,
    db: Session = Depends(get_db)
):
    """
    禁用执行器（逻辑删除，将状态设为 inactive）。
    """
    now = datetime.now(UTC)

    rowcount = deactivate_executor_record(db, executor_id, now)
    db.commit()

    if rowcount == 0:
        raise HTTPException(status_code=404, detail="未找到该执行器")

    return {"success": True, "message": f"执行器 {executor_id} 已禁用"}
