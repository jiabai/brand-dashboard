from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

from api.v1.models.schemas import (
    ExecutorCreate, 
    ExecutorResponse, 
    ExecutorListItem,
    ExecutorRegistrationResponse
)
from api.v1.repositories.database import get_db
from api.v1.utils.security import generate_executor_id, generate_api_key

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

    now = datetime.now()
    query = text("""
        INSERT INTO executors (executor_id, name, type, status, ip_address, api_key, created_at, updated_at)
        VALUES (:executor_id, :name, :type, 'active', :ip_address, :api_key, :now, :now)
    """)

    try:
        db.execute(query, {
            "executor_id": executor_id,
            "name": executor_in.name,
            "type": executor_in.type,
            "ip_address": executor_in.ip_address,
            "api_key": api_key,
            "now": now
        })
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

    # 直接根据 IP 地址查找 active 状态的执行器
    query = text("""
        SELECT executor_id, api_key, name 
        FROM executors 
        WHERE ip_address = :ip_address AND status = 'active'
    """)
    executor = db.execute(query, {"ip_address": client_ip}).first()

    if not executor:
        raise HTTPException(
            status_code=403, 
            detail=f"注册失败：IP {client_ip} 未被授权或未预设。请联系管理员添加此 IP。"
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
    query = text("SELECT executor_id, name, type, status, ip_address, created_at FROM executors")
    result = db.execute(query).fetchall()

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
    query = text(
        "UPDATE executors SET status = 'inactive', updated_at = :now "
        "WHERE executor_id = :executor_id"
    )
    now = datetime.now()

    result = db.execute(query, {"executor_id": executor_id, "now": now})
    db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="未找到该执行器")

    return {"success": True, "message": f"执行器 {executor_id} 已禁用"}
