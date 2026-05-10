from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import Engine

from api.v1.repositories.auth import (
    activate_admin_account,
    authenticate_user,
    create_tenant_with_admin,
    register_employee,
    verify_invite_code,
)
from api.v1.repositories.connection import get_engine

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


@router.post("/platform/tenants")
def create_tenant(request: TenantCreateRequest, engine: Engine = Depends(get_engine)):
    try:
        result = create_tenant_with_admin(engine, request.model_dump())
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    return {"status": "success", "data": result, "message": "租户创建成功", "code": 200}


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
