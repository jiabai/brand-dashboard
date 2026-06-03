import unittest
from unittest.mock import MagicMock, patch

from api.v1.dependencies.auth import CurrentUser, require_platform_admin
from api.v1.repositories import auth as auth_repository
from api.v1.routes import auth
from api.v1.utils.security import hash_password
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestPlatformTenantApi(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(auth.router, prefix="/api/v1")
        app.dependency_overrides[require_platform_admin] = lambda: CurrentUser(
            user_id=1,
            email="platform@example.com",
            status="active",
        )
        self.client = TestClient(app)

    def test_create_tenant_returns_payload(self):
        payload = {
            "tenantName": "阿里巴巴集团",
            "companyLegalName": "阿里巴巴（中国）网络技术有限公司",
            "industry": "互联网/电子商务",
            "adminName": "张三",
            "adminEmail": "zhangsan@alibaba.com",
        }
        service_result = {
            "tenantKey": "tn_test",
            "tenantName": "阿里巴巴集团",
            "adminEmail": "zhangsan@alibaba.com",
            "activationToken": "token",
            "activationUrl": "https://alibaba.yourplatform.com/activate?token=token",
            "inviteCode": "ABC123",
        }
        with patch(
            "api.v1.routes.auth.create_tenant_with_admin",
            return_value=service_result,
        ), patch(
            "api.v1.routes.auth.send_admin_activation_email",
            return_value={
                "status": "sent",
                "to": "zhangsan@alibaba.com",
                "message": "激活邮件已发送",
            },
        ) as send_email:
            response = self.client.post("/api/v1/platform/tenants", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["tenantKey"], "tn_test")
        self.assertEqual(body["data"]["inviteCode"], "ABC123")
        self.assertIn("activationUrl", body["data"])
        self.assertEqual(body["data"]["emailDelivery"]["status"], "sent")
        send_email.assert_called_once_with(service_result)

    def test_create_tenant_keeps_success_when_activation_email_fails(self):
        payload = {
            "tenantName": "阿里巴巴集团",
            "industry": "互联网/电子商务",
            "adminName": "张三",
            "adminEmail": "zhangsan@alibaba.com",
        }
        service_result = {
            "tenantKey": "tn_test",
            "tenantName": "阿里巴巴集团",
            "adminEmail": "zhangsan@alibaba.com",
            "activationUrl": "https://alibaba.yourplatform.com/activate?token=token",
            "inviteCode": "ABC123",
        }
        with patch(
            "api.v1.routes.auth.create_tenant_with_admin",
            return_value=service_result,
        ), patch(
            "api.v1.routes.auth.send_admin_activation_email",
            side_effect=RuntimeError("smtp-secret leaked in raw exception"),
        ):
            response = self.client.post("/api/v1/platform/tenants", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["tenantKey"], "tn_test")
        self.assertEqual(body["data"]["emailDelivery"]["status"], "failed")
        self.assertEqual(
            body["data"]["emailDelivery"]["message"],
            "激活邮件发送失败，请复制激活链接人工发送",
        )
        self.assertNotIn("smtp-secret", response.text)

    def test_create_tenant_returns_error_response(self):
        payload = {
            "tenantName": "阿里巴巴集团",
            "industry": "互联网/电子商务",
            "adminName": "张三",
            "adminEmail": "zhangsan@alibaba.com",
        }
        with patch(
            "api.v1.routes.auth.create_tenant_with_admin",
            side_effect=ValueError("企业名称已被使用"),
        ):
            response = self.client.post("/api/v1/platform/tenants", json=payload)

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["message"], "企业名称已被使用")
        self.assertEqual(body["code"], 400)


class TestPlatformTenantAuth(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(auth.router, prefix="/api/v1")
        self.client = TestClient(app)

    def test_create_tenant_requires_platform_admin(self):
        payload = {
            "tenantName": "阿里巴巴集团",
            "industry": "互联网/电子商务",
            "adminName": "张三",
            "adminEmail": "zhangsan@alibaba.com",
        }
        with patch(
            "api.v1.routes.auth.create_tenant_with_admin",
            return_value={"tenantKey": "tn_test"},
        ):
            response = self.client.post("/api/v1/platform/tenants", json=payload)

        self.assertEqual(response.status_code, 401)


class TestActivationApi(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(auth.router, prefix="/api/v1")
        self.client = TestClient(app)

    def test_activate_admin_returns_payload(self):
        payload = {
            "token": "token",
            "password": "Admin1234",
            "confirmPassword": "Admin1234",
        }
        service_result = {
            "userId": 10,
            "email": "zhangsan@alibaba.com",
            "tenantKey": "tn_test",
        }
        with patch(
            "api.v1.routes.auth.activate_admin_account",
            return_value=service_result,
        ):
            response = self.client.post("/api/v1/public/auth/activate", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["userId"], 10)

    def test_activate_admin_password_mismatch_returns_error_response(self):
        payload = {
            "token": "token",
            "password": "Admin1234",
            "confirmPassword": "Admin12345",
        }
        response = self.client.post("/api/v1/public/auth/activate", json=payload)

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["message"], "两次密码不一致")
        self.assertEqual(body["code"], 400)


class TestInviteCodeApi(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(auth.router, prefix="/api/v1")
        self.client = TestClient(app)

    def test_verify_invite_code_returns_payload(self):
        payload = {"code": "ABC123"}
        service_result = {
            "tenantKey": "tn_test",
            "tenantName": "阿里巴巴集团",
            "expiresAt": "2026-03-01T00:00:00Z",
        }
        with patch(
            "api.v1.routes.auth.verify_invite_code",
            return_value=service_result,
        ):
            response = self.client.post("/api/v1/public/users/verify-invite-code", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["tenantKey"], "tn_test")


class TestRegisterEmployeeApi(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(auth.router, prefix="/api/v1")
        self.client = TestClient(app)

    def test_register_employee_returns_payload(self):
        payload = {
            "inviteCode": "ABC123",
            "realName": "李四",
            "email": "lisi@example.com",
            "password": "User12345",
        }
        service_result = {
            "userId": 11,
            "tenantKey": "tn_test",
            "tenantName": "阿里巴巴集团",
        }
        with patch(
            "api.v1.routes.auth.register_employee",
            return_value=service_result,
        ):
            response = self.client.post("/api/v1/public/users/register", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["userId"], 11)


class TestLoginApi(unittest.TestCase):
    def setUp(self):
        app = FastAPI()
        app.include_router(auth.router, prefix="/api/v1")
        self.client = TestClient(app)

    def test_login_returns_payload(self):
        payload = {"email": "lisi@example.com", "password": "User12345"}
        service_result = {
            "accessToken": "token",
            "user": {
                "userId": 11,
                "email": "lisi@example.com",
                "tenants": [{"tenantKey": "tn_test", "tenantName": "阿里巴巴集团"}],
            },
        }
        with patch(
            "api.v1.routes.auth.authenticate_user",
            return_value=service_result,
        ):
            response = self.client.post("/api/v1/public/auth/login", json=payload)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "success")
        self.assertEqual(body["data"]["accessToken"], "token")


class TestAuthenticateUserRepository(unittest.TestCase):
    def test_authenticate_user_returns_standard_jwt_and_tenant_roles(self):
        password_hash = hash_password("User12345")

        def fake_execute(statement, params=None):
            sql = str(statement)
            if "FROM users" in sql and "WHERE email" in sql:
                result = MagicMock()
                result.fetchone.return_value = (11, "lisi@example.com", password_hash, "active")
                return result
            if "FROM user_tenants" in sql and "JOIN tenants" in sql:
                result = MagicMock()
                result.fetchall.return_value = [
                    ("tn_test", "阿里巴巴集团", "admin", "active"),
                ]
                return result
            raise AssertionError(f"unexpected SQL: {sql}")

        conn = MagicMock()
        conn.execute.side_effect = fake_execute

        class _ConnCtx:
            def __enter__(self):
                return conn

            def __exit__(self, exc_type, exc, tb):
                return False

        engine_mock = MagicMock()
        engine_mock.begin.return_value = _ConnCtx()

        with patch.dict(
            "os.environ",
            {
                "AUTH_SECRET": "test-secret-with-at-least-32-bytes",
                "PLATFORM_ADMIN_EMAILS": "lisi@example.com",
            },
        ):
            result = auth_repository.authenticate_user(
                engine_mock,
                "lisi@example.com",
                "User12345",
            )

        self.assertEqual(result["tokenType"], "Bearer")
        self.assertEqual(result["expiresIn"], 43200)
        self.assertEqual(len(result["accessToken"].split(".")), 3)
        self.assertEqual(result["user"]["platformRoles"], ["platform_admin"])
        self.assertEqual(result["user"]["tenants"][0]["role"], "tenant_admin")
        self.assertEqual(result["user"]["tenants"][0]["status"], "active")


class TestCreateTenantRepository(unittest.TestCase):
    def test_create_tenant_reuses_existing_user(self):
        payload = {
            "tenantName": "阿里巴巴集团",
            "companyLegalName": "阿里巴巴（中国）网络技术有限公司",
            "industry": "互联网/电子商务",
            "adminName": "张三",
            "adminEmail": "zhangsan@alibaba.com",
            "preferredSubdomain": "alibaba",
        }

        tenant_result = MagicMock()
        tenant_result.lastrowid = 10

        def fake_execute(statement, params=None):
            sql = str(statement)
            if "SELECT id FROM tenants WHERE tenant_name" in sql:
                result = MagicMock()
                result.fetchone.return_value = None
                return result
            if "SELECT id, status FROM users WHERE email" in sql:
                result = MagicMock()
                result.fetchone.return_value = (123, "active")
                return result
            if "SELECT id FROM tenants WHERE subdomain" in sql:
                result = MagicMock()
                result.fetchone.return_value = None
                return result
            if "INSERT INTO tenants" in sql:
                return tenant_result
            if "INSERT INTO users" in sql:
                raise AssertionError("should not insert user when email exists")
            if "INSERT INTO user_tenants" in sql:
                result = MagicMock()
                result.fetchone.return_value = None
                return result
            if "SELECT 1 FROM invitation_codes" in sql:
                result = MagicMock()
                result.fetchone.return_value = None
                return result
            if "INSERT INTO invitation_codes" in sql:
                result = MagicMock()
                result.fetchone.return_value = None
                return result
            raise AssertionError(f"unexpected SQL: {sql}")

        conn = MagicMock()
        conn.execute.side_effect = fake_execute

        class _ConnCtx:
            def __enter__(self):
                return conn

            def __exit__(self, exc_type, exc, tb):
                return False

        engine_mock = MagicMock()
        engine_mock.begin.return_value = _ConnCtx()

        result = auth_repository.create_tenant_with_admin(engine_mock, payload)

        self.assertEqual(result["tenantName"], "阿里巴巴集团")
        self.assertEqual(result["adminEmail"], "zhangsan@alibaba.com")
