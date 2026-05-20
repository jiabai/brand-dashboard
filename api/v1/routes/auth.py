from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from api.v1.dependencies.auth import (
    TENANT_ROLE_TO_PRODUCT_ROLE,
    CurrentUser,
    get_current_user,
    require_platform_admin,
)
from api.v1.repositories.auth import (
    activate_admin_account,
    authenticate_user,
    create_tenant_with_admin,
    register_employee,
    verify_invite_code,
)
from api.v1.repositories.connection import get_db, get_engine
from api.v1.repositories.tenants import (
    list_platform_tenant_summaries,
    list_user_tenant_summaries,
)
from api.v1.utils.platform_roles import get_platform_roles_for_email

router = APIRouter()


class TenantCreateRequest(BaseModel):
    tenantName: str = Field(..., min_length=1)
    companyLegalName: str | None = None
    registrationNo: str | None = None
    industry: str = Field(..., min_length=1)
    companyType: str | None = None
    adminName: str = Field(..., min_length=1)
    adminEmail: str = Field(..., min_length=1)
    adminPhone: str | None = None
    planType: str | None = None
    billingCycle: str | None = None
    contractStartDate: str | None = None
    contractEndDate: str | None = None
    maxUsers: int | None = None
    preferredSubdomain: str | None = None
    salesPersonId: str | None = None


class ActivationRequest(BaseModel):
    token: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    confirmPassword: str = Field(..., min_length=8)


class VerifyInviteCodeRequest(BaseModel):
    code: str = Field(..., min_length=1)


class RegisterEmployeeRequest(BaseModel):
    inviteCode: str = Field(..., min_length=1)
    realName: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    phoneNumber: str | None = None


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


TENANT_STATUSES = {"active", "inactive", "suspended"}
TENANT_PLAN_TYPES = {"trial", "basic", "pro", "enterprise"}


def _isoformat_or_none(value):
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _platform_tenant_item(row):
    return {
        "tenantKey": row[0],
        "tenantName": row[1],
        "companyLegalName": row[2],
        "industry": row[3],
        "status": row[4],
        "planType": row[5],
        "maxUsers": row[6],
        "billingCycle": row[7],
        "contractStartDate": _isoformat_or_none(row[8]),
        "contractEndDate": _isoformat_or_none(row[9]),
        "adminEmail": row[10],
        "adminStatus": row[11],
        "memberCount": int(row[12] or 0),
        "createdAt": _isoformat_or_none(row[13]),
    }


@router.post("/platform/tenants")
def create_tenant(
    request: TenantCreateRequest,
    engine: Engine = Depends(get_engine),
    _platform_admin: CurrentUser = Depends(require_platform_admin),
):
    try:
        result = create_tenant_with_admin(engine, request.model_dump())
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    return {"status": "success", "data": result, "message": "租户创建成功", "code": 200}


@router.get("/platform/tenants")
def list_platform_tenants(
    q: Annotated[str | None, Query(max_length=100)] = None,
    status: Annotated[str | None, Query()] = None,
    plan_type: Annotated[str | None, Query(alias="planType")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
    _platform_admin: CurrentUser = Depends(require_platform_admin),
):
    if status and status not in TENANT_STATUSES:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "租户状态无效", "code": 400},
        )
    if plan_type and plan_type not in TENANT_PLAN_TYPES:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "订阅计划无效", "code": 400},
        )

    result = list_platform_tenant_summaries(
        db,
        q=q,
        status=status,
        plan_type=plan_type,
        page=page,
        page_size=page_size,
    )
    total = result["total"]
    total_pages = (total + page_size - 1) // page_size
    return {
        "status": "success",
        "code": 200,
        "message": "获取租户列表成功",
        "data": {
            "items": [_platform_tenant_item(row) for row in result["items"]],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": total_pages,
            },
        },
    }


@router.post("/public/auth/activate")
def activate_admin(request: ActivationRequest, engine: Engine = Depends(get_engine)):
    if request.password != request.confirmPassword:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "两次密码不一致", "code": 400},
        )
    try:
        result = activate_admin_account(engine, request.token, request.password)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    return {"status": "success", "data": result, "message": "账号激活成功", "code": 200}


@router.post("/public/users/verify-invite-code")
def verify_invite_code_handler(
    request: VerifyInviteCodeRequest, engine: Engine = Depends(get_engine)
):
    try:
        result = verify_invite_code(engine, request.code)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    return {"status": "success", "data": result, "message": "邀请码有效", "code": 200}


@router.post("/public/users/register")
def register_employee_handler(
    request: RegisterEmployeeRequest, engine: Engine = Depends(get_engine)
):
    try:
        result = register_employee(engine, request.model_dump())
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    return {"status": "success", "data": result, "message": "注册成功", "code": 200}


@router.post("/public/auth/login")
def login_handler(request: LoginRequest, engine: Engine = Depends(get_engine)):
    try:
        result = authenticate_user(engine, request.email, request.password)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    return {"status": "success", "data": result, "message": "登录成功", "code": 200}


@router.get("/auth/me")
def get_me_handler(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tenants = [
        {
            "tenantKey": row[0],
            "tenantName": row[1],
            "role": TENANT_ROLE_TO_PRODUCT_ROLE.get(row[2], row[2]),
            "status": row[3],
            "tenantStatus": row[4],
        }
        for row in list_user_tenant_summaries(db, current_user.user_id)
    ]
    return {
        "status": "success",
        "data": {
            "user": {
                "userId": current_user.user_id,
                "email": current_user.email,
                "tenants": tenants,
                "platformRoles": get_platform_roles_for_email(current_user.email),
            }
        },
        "message": "获取当前用户成功",
        "code": 200,
    }
