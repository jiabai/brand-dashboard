import logging
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
    change_password,
    create_tenant_with_admin,
    regenerate_admin_activation,
    register_employee,
    request_password_reset,
    reset_password_with_token,
    verify_invite_code,
)
from api.v1.repositories.connection import get_db, get_engine
from api.v1.repositories.platform_health import (
    get_platform_collection_health as load_platform_collection_health,
)
from api.v1.repositories.tenant_members import (
    TenantMemberGovernanceError,
    list_tenant_members,
    tenant_exists,
    update_tenant_member,
)
from api.v1.repositories.tenants import (
    get_platform_tenant_summary,
    get_user_tenant_membership,
    list_platform_tenant_summaries,
    list_user_tenant_summaries,
)
from api.v1.services import projects as project_service
from api.v1.services.email_sender import (
    EMAIL_FAILED_MESSAGE,
    send_admin_activation_email,
    send_password_reset_email,
)
from api.v1.utils.platform_roles import get_platform_roles_for_email

router = APIRouter()

logger = logging.getLogger(__name__)


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


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., min_length=1)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    confirmPassword: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    currentPassword: str = Field(..., min_length=1)
    newPassword: str = Field(..., min_length=8)
    confirmPassword: str = Field(..., min_length=8)


class RegisterEmployeeRequest(BaseModel):
    inviteCode: str = Field(..., min_length=1)
    realName: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
    phoneNumber: str | None = None


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TenantMemberUpdateRequest(BaseModel):
    role: str | None = None
    status: str | None = None
    reason: str | None = None


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


def _concat_name(first_name, last_name):
    first = (first_name or "").strip()
    last = (last_name or "").strip()
    if first and last:
        return first + last
    return first or last


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
    item = row._mapping
    latest_job = None
    if item["latest_job_id"]:
        latest_job = {
            "jobId": item["latest_job_id"],
            "brand": item["latest_job_brand"],
            "category": item["latest_job_category"],
            "queryStatus": (
                int(item["latest_job_query_status"])
                if item["latest_job_query_status"] is not None
                else None
            ),
            "effectiveFrom": _isoformat_or_none(item["latest_job_effective_from"]),
            "effectiveTo": _isoformat_or_none(item["latest_job_effective_to"]),
            "createdAt": _isoformat_or_none(item["latest_job_created_at"]),
        }

    return {
        "tenantKey": item["tenant_key"],
        "tenantName": item["tenant_name"],
        "companyLegalName": item["company_legal_name"],
        "industry": item["industry"],
        "status": item["tenant_status"],
        "planType": item["plan_type"],
        "maxUsers": item["max_users"],
        "billingCycle": item["billing_cycle"],
        "contractStartDate": _isoformat_or_none(item["contract_start_date"]),
        "contractEndDate": _isoformat_or_none(item["contract_end_date"]),
        "adminName": _concat_name(item.get("admin_first_name"), item.get("admin_last_name")),
        "adminEmail": item["admin_email"],
        "adminPhone": item["admin_phone"],
        "adminStatus": item["admin_status"],
        "memberCount": int(item["member_count"] or 0),
        "createdAt": _isoformat_or_none(item["created_at"]),
        "jobCount": int(item["job_count"] or 0),
        "activeJobCount": int(item["active_job_count"] or 0),
        "latestJob": latest_job,
    }


def _tenant_member_item(row):
    item = row._mapping if hasattr(row, "_mapping") else row
    return {
        "userId": item["user_id"],
        "email": item["email"],
        "firstName": item["first_name"],
        "lastName": item["last_name"],
        "phoneNumber": item["phone_number"],
        "userStatus": item["user_status"],
        "role": item["role"],
        "status": item["member_status"],
        "createdAt": _isoformat_or_none(item["created_at"]),
    }


def _require_tenant_admin_for_path(
    *,
    tenant_key: str,
    current_user: CurrentUser,
    db: Session,
) -> None:
    membership = get_user_tenant_membership(
        db,
        user_id=current_user.user_id,
        tenant_key=tenant_key,
    )
    if not membership:
        raise HTTPException(status_code=403, detail="无权访问该租户")

    _, _, tenant_status, role, member_status = membership
    if tenant_status != "active":
        raise HTTPException(status_code=403, detail="租户不可用")
    if member_status != "active":
        raise HTTPException(status_code=403, detail="租户成员关系不可用")
    if role != "admin":
        raise HTTPException(status_code=403, detail="需要租户管理员权限")


def _member_governance_error(exc: TenantMemberGovernanceError):
    return JSONResponse(
        status_code=400,
        content={"status": "error", "message": str(exc), "code": 400},
    )


@router.get("/tenants/{tenant_key}/members")
def list_tenant_members_handler(
    tenant_key: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_tenant_admin_for_path(
        tenant_key=tenant_key,
        current_user=current_user,
        db=db,
    )
    members = list_tenant_members(db, tenant_key=tenant_key)
    return {
        "status": "success",
        "code": 200,
        "message": "获取租户成员成功",
        "data": {"members": [_tenant_member_item(row) for row in members]},
    }


@router.patch("/tenants/{tenant_key}/members/{user_id}")
def update_tenant_member_handler(
    tenant_key: str,
    user_id: int,
    request: TenantMemberUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _require_tenant_admin_for_path(
        tenant_key=tenant_key,
        current_user=current_user,
        db=db,
    )
    try:
        member = update_tenant_member(
            db,
            tenant_key=tenant_key,
            target_user_id=user_id,
            actor_user_id=current_user.user_id,
            actor_scope="tenant",
            role=request.role,
            status=request.status,
            reason=request.reason,
        )
        db.commit()
    except TenantMemberGovernanceError as exc:
        return _member_governance_error(exc)

    return {
        "status": "success",
        "code": 200,
        "message": "更新租户成员成功",
        "data": {"member": _tenant_member_item(member)},
    }


@router.patch("/platform/tenants/{tenant_key}/members/{user_id}")
def platform_update_tenant_member_handler(
    tenant_key: str,
    user_id: int,
    request: TenantMemberUpdateRequest,
    current_user: CurrentUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    if not (request.reason or "").strip():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "平台应急修改必须填写 reason", "code": 400},
        )
    try:
        member = update_tenant_member(
            db,
            tenant_key=tenant_key,
            target_user_id=user_id,
            actor_user_id=current_user.user_id,
            actor_scope="platform",
            role=request.role,
            status=request.status,
            reason=request.reason,
        )
        db.commit()
    except TenantMemberGovernanceError as exc:
        return _member_governance_error(exc)

    return {
        "status": "success",
        "code": 200,
        "message": "平台应急更新租户成员成功",
        "data": {"member": _tenant_member_item(member)},
    }


@router.get("/platform/tenants/{tenant_key}/members")
def list_platform_tenant_members_handler(
    tenant_key: str,
    db: Session = Depends(get_db),
    _platform_admin: CurrentUser = Depends(require_platform_admin),
):
    if not tenant_exists(db, tenant_key=tenant_key):
        raise HTTPException(status_code=404, detail="租户不存在")

    members = list_tenant_members(db, tenant_key=tenant_key)
    return {
        "status": "success",
        "code": 200,
        "message": "获取平台租户成员成功",
        "data": {"members": [_tenant_member_item(row) for row in members]},
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


@router.post("/platform/tenants/{tenant_key}/resend-activation")
def resend_tenant_activation(
    tenant_key: str,
    engine: Engine = Depends(get_engine),
    _platform_admin: CurrentUser = Depends(require_platform_admin),
):
    try:
        result = regenerate_admin_activation(engine, tenant_key)
    except LookupError as exc:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": str(exc), "code": 404},
        )
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
    return {
        "status": "success",
        "data": result,
        "message": "激活令牌已重新签发",
        "code": 200,
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


FORGOT_PASSWORD_MESSAGE = "如果该邮箱已注册并激活，重置邮件已发送"


@router.post("/public/auth/forgot-password")
def forgot_password_handler(
    request: ForgotPasswordRequest, engine: Engine = Depends(get_engine)
):
    reset_payload = request_password_reset(engine, request.email)
    if reset_payload is not None:
        try:
            delivery = send_password_reset_email(reset_payload)
            if delivery.get("status") != "sent":
                logger.warning(
                    "密码重置邮件未发送: status=%s to=%s",
                    delivery.get("status"),
                    delivery.get("to"),
                )
        except Exception:
            # 防枚举兜底：即使发送环节异常，响应也不得改变。
            pass
    return {
        "status": "success",
        "data": None,
        "message": FORGOT_PASSWORD_MESSAGE,
        "code": 200,
    }


@router.post("/public/auth/reset-password")
def reset_password_handler(
    request: ResetPasswordRequest, engine: Engine = Depends(get_engine)
):
    if request.password != request.confirmPassword:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "两次密码不一致", "code": 400},
        )
    try:
        reset_password_with_token(engine, request.token, request.password)
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    return {"status": "success", "data": None, "message": "密码已重置", "code": 200}


@router.post("/auth/change-password")
def change_password_handler(
    request: ChangePasswordRequest,
    engine: Engine = Depends(get_engine),
    current_user: CurrentUser = Depends(get_current_user),
):
    if request.newPassword != request.confirmPassword:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "两次密码不一致", "code": 400},
        )
    try:
        change_password(
            engine, current_user.user_id, request.currentPassword, request.newPassword
        )
    except ValueError as exc:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": str(exc), "code": 400},
        )
    return {"status": "success", "data": None, "message": "密码已修改", "code": 200}


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
