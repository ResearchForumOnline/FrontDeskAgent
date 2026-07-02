from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .config import AppConfig


def send_summary_email(config: AppConfig, subject: str, body: str, to_email: str | None = None) -> dict:
    recipient = to_email or config.escalation_email or config.business_email
    if not (config.smtp_host and config.smtp_from and recipient):
        return {"sent": False, "reason": "SMTP is not configured"}

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.smtp_from
    message["To"] = recipient
    message.set_content(body)

    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10) as smtp:
        if config.smtp_use_tls:
            smtp.starttls()
        if config.smtp_username:
            smtp.login(config.smtp_username, config.smtp_password)
        smtp.send_message(message)
    return {"sent": True, "to": recipient}
