import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any, Dict

EMAIL_SENT_MESSAGE = "激活邮件已发送"
EMAIL_NOT_CONFIGURED_MESSAGE = "SMTP 未配置，未发送激活邮件"
EMAIL_FAILED_MESSAGE = "激活邮件发送失败，请复制激活链接人工发送"


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str
    use_tls: bool
    timeout: int = 10


def _env_enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _load_smtp_config() -> SmtpConfig | None:
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM")

    if not all([host, port, username, password, sender]):
        return None

    return SmtpConfig(
        host=host,
        port=int(port),
        username=username,
        password=password,
        sender=sender,
        use_tls=_env_enabled(os.getenv("SMTP_USE_TLS")),
        timeout=int(os.getenv("SMTP_TIMEOUT", "10")),
    )


def _build_activation_message(config: SmtpConfig, tenant_result: Dict[str, Any]) -> EmailMessage:
    tenant_name = tenant_result.get("tenantName") or "Brand Dashboard"
    admin_email = tenant_result.get("adminEmail") or ""
    activation_url = tenant_result.get("activationUrl") or ""
    login_url = tenant_result.get("loginUrl") or ""

    message = EmailMessage()
    message["From"] = config.sender
    message["To"] = admin_email
    message["Subject"] = f"Brand Dashboard 管理员账号激活 - {tenant_name}"
    message.set_content(
        "\n".join(
            [
                f"您好，{tenant_name} 的管理员账号已创建。",
                "",
                f"管理员邮箱：{admin_email}",
                "",
                "请在 7 天内打开以下链接设置密码并完成账号激活：",
                activation_url,
                "",
                "激活后可通过以下地址登录：",
                login_url,
                "",
                "如果您未申请开通 Brand Dashboard，请忽略此邮件。",
            ]
        )
    )
    return message


def _send_message(config: SmtpConfig, message: EmailMessage) -> None:
    if config.use_tls and config.port == 465:
        with smtplib.SMTP_SSL(config.host, config.port, timeout=config.timeout) as smtp:
            smtp.login(config.username, config.password)
            smtp.send_message(message)
        return

    with smtplib.SMTP(config.host, config.port, timeout=config.timeout) as smtp:
        if config.use_tls:
            smtp.starttls(context=ssl.create_default_context())
        smtp.login(config.username, config.password)
        smtp.send_message(message)


def send_admin_activation_email(tenant_result: Dict[str, Any]) -> Dict[str, str | None]:
    admin_email = tenant_result.get("adminEmail")
    try:
        config = _load_smtp_config()
        if not config:
            return {
                "status": "not_configured",
                "to": admin_email,
                "message": EMAIL_NOT_CONFIGURED_MESSAGE,
            }

        message = _build_activation_message(config, tenant_result)
        _send_message(config, message)
        return {
            "status": "sent",
            "to": admin_email,
            "message": EMAIL_SENT_MESSAGE,
        }
    except Exception:
        return {
            "status": "failed",
            "to": admin_email,
            "message": EMAIL_FAILED_MESSAGE,
        }
