import os
import unittest
from unittest.mock import MagicMock, patch

from api.v1.services.email_sender import (
    send_admin_activation_email,
    send_password_reset_email,
)


class TestActivationEmailSender(unittest.TestCase):
    def test_returns_not_configured_when_smtp_settings_are_missing(self):
        tenant_result = {
            "tenantName": "Acme 中国",
            "adminEmail": "admin@acme.test",
            "activationUrl": "https://acme.example.com/activate?token=token",
        }

        with patch.dict(os.environ, {}, clear=True):
            result = send_admin_activation_email(tenant_result)

        self.assertEqual(result["status"], "not_configured")
        self.assertEqual(result["to"], "admin@acme.test")
        self.assertEqual(result["message"], "SMTP 未配置，未发送激活邮件")

    def test_sends_activation_email_with_ssl_smtp_when_port_465_uses_tls(self):
        tenant_result = {
            "tenantName": "Acme 中国",
            "adminEmail": "admin@acme.test",
            "activationUrl": "https://acme.example.com/activate?token=token",
            "loginUrl": "https://acme.example.com/login",
        }
        smtp_instance = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = smtp_instance
        smtp_context.__exit__.return_value = False

        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.163.com",
                "SMTP_PORT": "465",
                "SMTP_USERNAME": "sender@example.com",
                "SMTP_PASSWORD": "smtp-secret",
                "SMTP_FROM": "sender@example.com",
                "SMTP_USE_TLS": "true",
            },
            clear=True,
        ), patch(
            "api.v1.services.email_sender.smtplib.SMTP_SSL",
            return_value=smtp_context,
        ) as smtp_ssl:
            result = send_admin_activation_email(tenant_result)

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["to"], "admin@acme.test")
        smtp_ssl.assert_called_once_with("smtp.163.com", 465, timeout=10)
        smtp_instance.login.assert_called_once_with("sender@example.com", "smtp-secret")
        smtp_instance.send_message.assert_called_once()
        message = smtp_instance.send_message.call_args.args[0]
        self.assertEqual(message["From"], "sender@example.com")
        self.assertEqual(message["To"], "admin@acme.test")
        self.assertIn("Brand Dashboard 管理员账号激活", message["Subject"])
        body = message.get_content()
        self.assertIn("Acme 中国", body)
        self.assertIn("admin@acme.test", body)
        self.assertIn("https://acme.example.com/activate?token=token", body)
        self.assertIn("7 天内", body)

    def test_returns_failed_without_leaking_smtp_exception_details(self):
        tenant_result = {
            "tenantName": "Acme 中国",
            "adminEmail": "admin@acme.test",
            "activationUrl": "https://acme.example.com/activate?token=token",
        }

        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.163.com",
                "SMTP_PORT": "465",
                "SMTP_USERNAME": "sender@example.com",
                "SMTP_PASSWORD": "smtp-secret",
                "SMTP_FROM": "sender@example.com",
                "SMTP_USE_TLS": "true",
            },
            clear=True,
        ), patch(
            "api.v1.services.email_sender.smtplib.SMTP_SSL",
            side_effect=RuntimeError("smtp-secret leaked in raw exception"),
        ):
            result = send_admin_activation_email(tenant_result)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["to"], "admin@acme.test")
        self.assertEqual(result["message"], "激活邮件发送失败，请复制激活链接人工发送")
        self.assertNotIn("smtp-secret", str(result))


class TestPasswordResetEmailSender(unittest.TestCase):
    def test_returns_not_configured_when_smtp_settings_are_missing(self):
        reset_result = {
            "email": "user@acme.test",
            "resetUrl": "https://example.com/reset-password?token=token",
        }

        with patch.dict(os.environ, {}, clear=True):
            result = send_password_reset_email(reset_result)

        self.assertEqual(result["status"], "not_configured")
        self.assertEqual(result["to"], "user@acme.test")
        self.assertEqual(result["message"], "SMTP 未配置，未发送重置邮件")

    def test_sends_reset_email_with_url_and_expiry_hint(self):
        reset_result = {
            "email": "user@acme.test",
            "resetUrl": "https://example.com/reset-password?token=token",
        }
        smtp_instance = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = smtp_instance
        smtp_context.__exit__.return_value = False

        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.163.com",
                "SMTP_PORT": "465",
                "SMTP_USERNAME": "sender@example.com",
                "SMTP_PASSWORD": "smtp-secret",
                "SMTP_FROM": "sender@example.com",
                "SMTP_USE_TLS": "true",
            },
            clear=True,
        ), patch(
            "api.v1.services.email_sender.smtplib.SMTP_SSL",
            return_value=smtp_context,
        ):
            result = send_password_reset_email(reset_result)

        self.assertEqual(result["status"], "sent")
        smtp_instance.send_message.assert_called_once()
        message = smtp_instance.send_message.call_args.args[0]
        self.assertEqual(message["To"], "user@acme.test")
        self.assertIn("密码重置", message["Subject"])
        body = message.get_content()
        self.assertIn("https://example.com/reset-password?token=token", body)
        self.assertIn("1 小时内", body)
        self.assertIn("请忽略此邮件", body)

    def test_returns_failed_without_leaking_smtp_exception_details(self):
        reset_result = {
            "email": "user@acme.test",
            "resetUrl": "https://example.com/reset-password?token=token",
        }

        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "smtp.163.com",
                "SMTP_PORT": "465",
                "SMTP_USERNAME": "sender@example.com",
                "SMTP_PASSWORD": "smtp-secret",
                "SMTP_FROM": "sender@example.com",
                "SMTP_USE_TLS": "true",
            },
            clear=True,
        ), patch(
            "api.v1.services.email_sender.smtplib.SMTP_SSL",
            side_effect=RuntimeError("smtp-secret leaked in raw exception"),
        ):
            result = send_password_reset_email(reset_result)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["message"], "重置邮件发送失败")
        self.assertNotIn("smtp-secret", str(result))
