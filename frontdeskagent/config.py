from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AppConfig:
    host: str
    port: int
    secret_key: str
    database_path: str
    business_name: str
    business_type: str
    business_phone: str
    business_email: str
    business_timezone: str
    service_areas: str
    opening_hours: str
    escalation_phone: str
    escalation_email: str
    llm_backend: str
    ollama_url: str
    ollama_model: str
    llamacpp_url: str
    openai_compat_url: str
    openai_compat_api_key: str
    openai_compat_model: str
    openzero_llm_url: str
    openzero_model: str
    openzero_api_key: str
    llm_timeout_seconds: int
    openzero_webhook_url: str
    webhook_shared_secret: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from: str
    smtp_use_tls: bool
    public_base_url: str = ""
    admin_username: str = "admin"
    admin_password: str = ""
    admin_auth_enabled: bool = False
    sms_provider: str = "none"
    sms_from: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_validate_signatures: bool = True
    telnyx_api_key: str = ""
    telnyx_messaging_profile_id: str = ""
    sms_webhook_url: str = ""
    auto_sms_on_lead: bool = False
    customer_sms_template: str = "Thanks, your enquiry has been logged. The team will review it and contact you as soon as possible."
    escalation_sms_enabled: bool = False
    outbound_call_provider: str = "none"
    outbound_caller_id: str = ""
    outbound_webhook_url: str = ""
    voice_greeting: str = "Thanks for calling. Please briefly say your name, phone number, and what you need help with."
    transfer_urgent_calls: bool = False
    crm_webhook_url: str = ""
    crm_api_key: str = ""
    calendar_feed_token: str = ""
    booking_webhook_url: str = ""
    booking_api_key: str = ""
    website_import_max_chars: int = 12000


def load_config() -> AppConfig:
    load_dotenv()
    database_path = os.getenv("DATABASE_PATH", "./data/frontdeskagent.sqlite")
    Path(database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    return AppConfig(
        host=os.getenv("APP_HOST", "0.0.0.0"),
        port=int(os.getenv("APP_PORT", "8088")),
        secret_key=os.getenv("SECRET_KEY", "dev-only-change-me"),
        database_path=database_path,
        business_name=os.getenv("BUSINESS_NAME", "FrontDeskAgent Demo"),
        business_type=os.getenv("BUSINESS_TYPE", "general"),
        business_phone=os.getenv("BUSINESS_PHONE", ""),
        business_email=os.getenv("BUSINESS_EMAIL", ""),
        business_timezone=os.getenv("BUSINESS_TIMEZONE", "Europe/London"),
        service_areas=os.getenv("SERVICE_AREAS", "Local area"),
        opening_hours=os.getenv("OPENING_HOURS", "Monday-Friday 09:00-17:00"),
        escalation_phone=os.getenv("ESCALATION_PHONE", ""),
        escalation_email=os.getenv("ESCALATION_EMAIL", ""),
        llm_backend=os.getenv("LLM_BACKEND", "rules").strip().lower(),
        ollama_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/"),
        ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
        llamacpp_url=os.getenv("LLAMACPP_URL", "http://127.0.0.1:8080/v1/chat/completions"),
        openai_compat_url=os.getenv("OPENAI_COMPAT_URL", ""),
        openai_compat_api_key=os.getenv("OPENAI_COMPAT_API_KEY", ""),
        openai_compat_model=os.getenv("OPENAI_COMPAT_MODEL", ""),
        openzero_llm_url=os.getenv("OPENZERO_LLM_URL", "http://127.0.0.1:1024/v1/chat/completions"),
        openzero_model=os.getenv("OPENZERO_MODEL", "local"),
        openzero_api_key=os.getenv("OPENZERO_API_KEY", ""),
        llm_timeout_seconds=int(os.getenv("LLM_TIMEOUT_SECONDS", "45")),
        openzero_webhook_url=os.getenv("OPENZERO_WEBHOOK_URL", ""),
        webhook_shared_secret=os.getenv("WEBHOOK_SHARED_SECRET", ""),
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_from=os.getenv("SMTP_FROM", ""),
        smtp_use_tls=_bool(os.getenv("SMTP_USE_TLS"), True),
        public_base_url=os.getenv("PUBLIC_BASE_URL", "").rstrip("/"),
        admin_username=os.getenv("ADMIN_USERNAME", "admin"),
        admin_password=os.getenv("ADMIN_PASSWORD", ""),
        admin_auth_enabled=_bool(os.getenv("ADMIN_AUTH_ENABLED"), bool(os.getenv("ADMIN_PASSWORD", ""))),
        sms_provider=os.getenv("SMS_PROVIDER", "none").strip().lower(),
        sms_from=os.getenv("SMS_FROM", ""),
        twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
        twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
        twilio_validate_signatures=_bool(os.getenv("TWILIO_VALIDATE_SIGNATURES"), True),
        telnyx_api_key=os.getenv("TELNYX_API_KEY", ""),
        telnyx_messaging_profile_id=os.getenv("TELNYX_MESSAGING_PROFILE_ID", ""),
        sms_webhook_url=os.getenv("SMS_WEBHOOK_URL", ""),
        auto_sms_on_lead=_bool(os.getenv("AUTO_SMS_ON_LEAD"), False),
        customer_sms_template=os.getenv(
            "CUSTOMER_SMS_TEMPLATE",
            "Thanks, your enquiry has been logged. The team will review it and contact you as soon as possible.",
        ),
        escalation_sms_enabled=_bool(os.getenv("ESCALATION_SMS_ENABLED"), False),
        outbound_call_provider=os.getenv("OUTBOUND_CALL_PROVIDER", "none").strip().lower(),
        outbound_caller_id=os.getenv("OUTBOUND_CALLER_ID", ""),
        outbound_webhook_url=os.getenv("OUTBOUND_WEBHOOK_URL", ""),
        voice_greeting=os.getenv(
            "VOICE_GREETING",
            "Thanks for calling. Please briefly say your name, phone number, and what you need help with.",
        ),
        transfer_urgent_calls=_bool(os.getenv("TRANSFER_URGENT_CALLS"), False),
        crm_webhook_url=os.getenv("CRM_WEBHOOK_URL", ""),
        crm_api_key=os.getenv("CRM_API_KEY", ""),
        calendar_feed_token=os.getenv("CALENDAR_FEED_TOKEN", ""),
        booking_webhook_url=os.getenv("BOOKING_WEBHOOK_URL", ""),
        booking_api_key=os.getenv("BOOKING_API_KEY", ""),
        website_import_max_chars=int(os.getenv("WEBSITE_IMPORT_MAX_CHARS", "12000")),
    )


def public_config(config: AppConfig) -> dict:
    return {
        "business_name": config.business_name,
        "business_type": config.business_type,
        "business_phone": config.business_phone,
        "business_email": config.business_email,
        "business_timezone": config.business_timezone,
        "service_areas": config.service_areas,
        "opening_hours": config.opening_hours,
        "llm_backend": config.llm_backend,
        "ollama_model": config.ollama_model,
        "openzero_enabled": bool(config.openzero_webhook_url or config.llm_backend == "openzero"),
        "sms_enabled": sms_enabled(config),
        "crm_enabled": bool(config.crm_webhook_url),
        "calendar_enabled": bool(config.calendar_feed_token),
        "public_base_url": config.public_base_url,
    }


def sms_enabled(config: AppConfig) -> bool:
    if config.sms_provider == "twilio":
        return bool(config.twilio_account_sid and config.twilio_auth_token and config.sms_from)
    if config.sms_provider == "telnyx":
        return bool(config.telnyx_api_key and config.sms_from)
    if config.sms_provider == "webhook":
        return bool(config.sms_webhook_url)
    return False
