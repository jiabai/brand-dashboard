from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
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
from api.v1.repositories.platform_health import (
    get_platform_collection_health as load_platform_collection_health,
)
from api.v1.repositories.tenants import (
    get_platform_tenant_summary,
    list_platform_tenant_summaries,
    list_user_tenant_summaries,
)
from api.v1.services import projects as project_service
from api.v1.services.email_sender import (
    EMAIL_FAILED_MESSAGE,
    send_admin_activation_email,
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
    value_text = str(value)
    if " " in value_text and "T" not in value_text:
        return value_text.replace(" ", "T", 1)
    return value_text


def _int_or_zero(value):
    return int(value or 0)


def _platform_collection_summary(row):
    item = row._mapping
    return {
        "executorCount": _int_or_zero(item["executor_count"]),
        "activeExecutorCount": _int_or_zero(item["active_executor_count"]),
        "inactiveExecutorCount": _int_or_zero(item["inactive_executor_count"]),
        "pendingTaskCount": _int_or_zero(item["pending_task_count"]),
        "reservedTaskCount": _int_or_zero(item["reserved_task_count"]),
        "runningTaskCount": _int_or_zero(item["running_task_count"]),
        "failedTaskCount": _int_or_zero(item["failed_task_count"]),
        "retryableFailedTaskCount": _int_or_zero(item["retryable_failed_task_count"]),
        "expiredLeaseTaskCount": _int_or_zero(item["expired_lease_task_count"]),
    }


def _executor_health_status(row):
    item = row._mapping
    if item["status"] != "active":
        return "inactive"
    if _int_or_zero(item["failed_attempt_count"]) > 0:
        return "error"
    if (
        _int_or_zero(item["active_lease_count"]) > 0
        or _int_or_zero(item["running_attempt_count"]) > 0
    ):
        return "active"
    return "idle"


def _platform_executor_health_item(row):
    item = row._mapping
    return {
        "executorId": item["executor_id"],
        "name": item["name"],
        "type": item["type"],
        "status": item["status"],
        "healthStatus": _executor_health_status(row),
        "ipAddress": item["ip_address"],
        "activeLeaseCount": _int_or_zero(item["active_lease_count"]),
        "runningAttemptCount": _int_or_zero(item["running_attempt_count"]),
        "failedAttemptCount": _int_or_zero(item["failed_attempt_count"]),
        "latestAttemptAt": _isoformat_or_none(item["latest_attempt_at"]),
        "createdAt": _isoformat_or_none(item["created_at"]),
        "updatedAt": _isoformat_or_none(item["updated_at"]),
    }


def _platform_collection_queue_item(row):
    item = row._mapping
    return {
        "tenantKey": item["tenant_key"],
        "tenantName": item["tenant_name"],
        "projectId": item["project_id"],
        "projectName": item["project_name"],
        "collectionJobId": item["collection_job_id"],
        "collectionJobStatus": item["collection_job_status"],
        "totalTaskCount": _int_or_zero(item["total_task_count"]),
        "pendingTaskCount": _int_or_zero(item["pending_task_count"]),
        "reservedTaskCount": _int_or_zero(item["reserved_task_count"]),
        "runningTaskCount": _int_or_zero(item["running_task_count"]),
        "succeededTaskCount": _int_or_zero(item["succeeded_task_count"]),
        "failedTaskCount": _int_or_zero(item["failed_task_count"]),
        "retryableFailedTaskCount": _int_or_zero(item["retryable_failed_task_count"]),
        "expiredLeaseTaskCount": _int_or_zero(item["expired_lease_task_count"]),
    }


def _platform_failed_collection_task_item(row):
    item = row._mapping
    return {
        "tenantKey": item["tenant_key"],
        "tenantName": item["tenant_name"],
        "projectId": item["project_id"],
        "projectName": item["project_name"],
        "collectionJobId": item["collection_job_id"],
        "collectionTaskId": item["collection_task_id"],
        "platform": item["platform"],
        "keyword": item["keyword"],
        "queryContent": item["query_content"],
        "attemptCount": _int_or_zero(item["attempt_count"]),
        "maxAttempts": _int_or_zero(item["max_attempts"]),
        "isRetryable": _int_or_zero(item["attempt_count"]) < _int_or_zero(item["max_attempts"]),
        "lastErrorCode": item["last_error_code"],
        "lastErrorMessage": item["last_error_message"],
        "leaseOwner": item["lease_owner"],
        "updatedAt": _isoformat_or_none(item["updated_at"]),
    }


def _platform_tenant_item(row):
    latest_job = None
    if row[16]:
        latest_job = {
            "jobId": row[16],
            "brand": row[17],
            "category": row[18],
            "queryStatus": int(row[19]) if row[19] is not None else None,
            "effectiveFrom": _isoformat_or_none(row[20]),
            "effectiveTo": _isoformat_or_none(row[21]),
            "createdAt": _isoformat_or_none(row[22]),
        }

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
        "jobCount": int(row[14] or 0),
        "activeJobCount": int(row[15] or 0),
        "latestJob": latest_job,
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
    try:
        email_delivery = send_admin_activation_email(result)
    except Exception:
        email_delivery = {
            "status": "failed",
            "to": result.get("adminEmail"),
            "message": EMAIL_FAILED_MESSAGE,
        }
    result = {**result, "emailDelivery": email_delivery}
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


@router.get("/platform/tenants/{tenant_key}")
def get_platform_tenant_detail(
    tenant_key: str,
    db: Session = Depends(get_db),
    _platform_admin: CurrentUser = Depends(require_platform_admin),
):
    row = get_platform_tenant_summary(db, tenant_key=tenant_key)
    if row is None:
        raise HTTPException(status_code=404, detail="租户不存在")

    tenant = _platform_tenant_item(row)
    projects = project_service.list_project_summaries(
        db,
        tenant_key=tenant["tenantKey"],
    )
    return {
        "status": "success",
        "code": 200,
        "message": "获取租户详情成功",
        "data": {
            **tenant,
            "projects": [
                project.model_dump(mode="json") for project in projects
            ],
        },
    }


@router.get("/platform/collection-health")
def get_platform_collection_health(
    failed_task_limit: Annotated[
        int, Query(alias="failedTaskLimit", ge=1, le=100)
    ] = 20,
    db: Session = Depends(get_db),
    _platform_admin: CurrentUser = Depends(require_platform_admin),
):
    now = datetime.now(UTC)
    health = load_platform_collection_health(
        db,
        now=now,
        failed_task_limit=failed_task_limit,
    )
    return {
        "status": "success",
        "code": 200,
        "message": "获取采集健康度成功",
        "data": {
            "generatedAt": now.isoformat(),
            "summary": _platform_collection_summary(health["summary"]),
            "executors": [
                _platform_executor_health_item(row) for row in health["executors"]
            ],
            "queues": [
                _platform_collection_queue_item(row) for row in health["queues"]
            ],
            "failedTasks": [
                _platform_failed_collection_task_item(row)
                for row in health["failed_tasks"]
            ],
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
