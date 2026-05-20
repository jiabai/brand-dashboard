import os


def get_platform_roles_for_email(email: str) -> list[str]:
    admin_emails = {
        value.strip().lower()
        for value in os.getenv("PLATFORM_ADMIN_EMAILS", "").split(",")
        if value.strip()
    }
    if email.lower() in admin_emails:
        return ["platform_admin"]
    return []
