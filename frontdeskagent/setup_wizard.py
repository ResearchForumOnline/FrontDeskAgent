from __future__ import annotations

import argparse
import secrets
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a beginner-friendly FrontDeskAgent .env file.")
    parser.add_argument("--env", default=".env", help="Path to write. Defaults to .env")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing file")
    args = parser.parse_args()

    env_path = Path(args.env)
    if env_path.exists() and not args.force:
        print(f"{env_path} already exists. Use --force to overwrite it.")
        return 1

    print("FrontDeskAgent setup wizard")
    print("Press Enter to accept a default. You can edit .env later.\n")

    public_url = ask("Public URL for this server", "http://localhost:8088").rstrip("/")
    business_name = ask("Business name", "FrontDeskAgent Demo")
    business_type = ask("Business type", "general")
    business_email = ask("Business email", "")
    escalation_phone = ask("Escalation phone for urgent calls/SMS", "")
    escalation_email = ask("Escalation email", business_email)
    service_areas = ask("Service areas", "Local area")
    opening_hours = ask("Opening hours", "Monday-Friday 09:00-17:00")

    admin_user = ask("Admin username", "admin")
    admin_password = ask_secret("Admin password", token_urlsafe(18))

    llm_backend = ask_choice("LLM backend", ["auto", "openzero", "ollama", "llamacpp", "openai_compat", "rules"], "auto")
    ollama_model = ask("Ollama model", "qwen2.5:3b")

    sms_provider = ask_choice("SMS provider", ["none", "twilio", "telnyx", "webhook"], "none")
    sms_from = ""
    twilio_sid = ""
    twilio_token = ""
    telnyx_key = ""
    telnyx_profile = ""
    sms_webhook = ""
    if sms_provider == "twilio":
        sms_from = ask("Twilio phone number", "")
        twilio_sid = ask("Twilio Account SID", "")
        twilio_token = ask_secret("Twilio Auth Token", "")
    elif sms_provider == "telnyx":
        sms_from = ask("Telnyx from number", "")
        telnyx_key = ask_secret("Telnyx API key", "")
        telnyx_profile = ask("Telnyx messaging profile ID", "")
    elif sms_provider == "webhook":
        sms_webhook = ask("SMS webhook URL", "")

    crm_webhook = ask("CRM/n8n/Zapier/Make webhook URL", "")
    booking_webhook = ask("Booking/calendar webhook URL", "")
    openzero_webhook = ask("OpenZero event webhook URL", "")
    voice_tts_provider = ask_choice("Local voice output", ["none", "voicebox"], "none")
    voicebox_url = "http://127.0.0.1:17493"
    voicebox_profile = ""
    voicebox_alert_on_lead = "false"
    if voice_tts_provider == "voicebox":
        voicebox_url = ask("Voicebox URL", "http://127.0.0.1:17493").rstrip("/")
        voicebox_profile = ask("Voicebox profile name or ID", "")
        voicebox_alert_on_lead = "true" if ask_choice("Speak new lead alerts", ["false", "true"], "false") == "true" else "false"

    values = {
        "APP_HOST": "0.0.0.0",
        "APP_PORT": "8088",
        "PUBLIC_BASE_URL": public_url,
        "SECRET_KEY": token_urlsafe(32),
        "DATABASE_PATH": "./data/frontdeskagent.sqlite",
        "ADMIN_AUTH_ENABLED": "true",
        "ADMIN_USERNAME": admin_user,
        "ADMIN_PASSWORD": admin_password,
        "BUSINESS_NAME": business_name,
        "BUSINESS_TYPE": business_type,
        "BUSINESS_PHONE": "",
        "BUSINESS_EMAIL": business_email,
        "BUSINESS_TIMEZONE": "Europe/London",
        "SERVICE_AREAS": service_areas,
        "OPENING_HOURS": opening_hours,
        "ESCALATION_PHONE": escalation_phone,
        "ESCALATION_EMAIL": escalation_email,
        "LLM_BACKEND": llm_backend,
        "OLLAMA_URL": "http://127.0.0.1:11434",
        "OLLAMA_MODEL": ollama_model,
        "LLAMACPP_URL": "http://127.0.0.1:8080/v1/chat/completions",
        "OPENAI_COMPAT_URL": "",
        "OPENAI_COMPAT_API_KEY": "",
        "OPENAI_COMPAT_MODEL": "",
        "OPENZERO_LLM_URL": "http://127.0.0.1:1024/v1/chat/completions",
        "OPENZERO_MODEL": "local",
        "OPENZERO_API_KEY": "",
        "LLM_TIMEOUT_SECONDS": "45",
        "OPENZERO_WEBHOOK_URL": openzero_webhook,
        "WEBHOOK_SHARED_SECRET": token_urlsafe(24),
        "SMS_PROVIDER": sms_provider,
        "SMS_FROM": sms_from,
        "TWILIO_ACCOUNT_SID": twilio_sid,
        "TWILIO_AUTH_TOKEN": twilio_token,
        "TWILIO_VALIDATE_SIGNATURES": "true",
        "TELNYX_API_KEY": telnyx_key,
        "TELNYX_MESSAGING_PROFILE_ID": telnyx_profile,
        "SMS_WEBHOOK_URL": sms_webhook,
        "AUTO_SMS_ON_LEAD": "true" if sms_provider != "none" else "false",
        "CUSTOMER_SMS_TEMPLATE": "Thanks, your enquiry has been logged. The team will review it and contact you as soon as possible.",
        "ESCALATION_SMS_ENABLED": "true" if escalation_phone and sms_provider != "none" else "false",
        "OUTBOUND_CALL_PROVIDER": "twilio" if sms_provider == "twilio" else "none",
        "OUTBOUND_CALLER_ID": sms_from,
        "OUTBOUND_WEBHOOK_URL": "",
        "VOICE_GREETING": "Thanks for calling. Please briefly say your name, phone number, and what you need help with.",
        "TRANSFER_URGENT_CALLS": "false",
        "VOICE_TTS_PROVIDER": voice_tts_provider,
        "VOICEBOX_URL": voicebox_url,
        "VOICEBOX_PROFILE": voicebox_profile,
        "VOICEBOX_CLIENT_ID": "frontdeskagent",
        "VOICEBOX_TIMEOUT_SECONDS": "20",
        "VOICEBOX_ALERT_ON_LEAD": voicebox_alert_on_lead,
        "CRM_WEBHOOK_URL": crm_webhook,
        "CRM_API_KEY": "",
        "CALENDAR_FEED_TOKEN": token_urlsafe(24),
        "BOOKING_WEBHOOK_URL": booking_webhook,
        "BOOKING_API_KEY": "",
        "WEBSITE_IMPORT_MAX_CHARS": "12000",
        "SMTP_HOST": "",
        "SMTP_PORT": "587",
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
        "SMTP_FROM": "",
        "SMTP_USE_TLS": "true",
    }

    env_path.write_text(render_env(values), encoding="utf-8")
    print(f"\nWrote {env_path}")
    print("\nStart the app:")
    print("  python -m frontdeskagent.app")
    print("\nUseful URLs:")
    print(f"  Dashboard: {public_url}/")
    print(f"  Twilio Voice webhook: {public_url}/voice/twilio")
    print(f"  Twilio SMS webhook: {public_url}/sms/twilio")
    print(f"  Generic SMS webhook: {public_url}/api/webhook/sms")
    print(f"  Voice speak API: {public_url}/api/voice/speak")
    print(f"  OpenZero context: {public_url}/api/openzero/context")
    print(f"  Calendar feed: {public_url}/calendar.ics?token={values['CALENDAR_FEED_TOKEN']}")
    return 0


def ask(label: str, default: str) -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def ask_secret(label: str, default: str) -> str:
    suffix = " [generated]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def ask_choice(label: str, choices: list[str], default: str) -> str:
    value = ask(f"{label} ({'/'.join(choices)})", default).lower()
    return value if value in choices else default


def token_urlsafe(length: int) -> str:
    return secrets.token_urlsafe(length)


def render_env(values: dict[str, str]) -> str:
    return "\n".join(f"{key}={quote_env(value)}" for key, value in values.items()) + "\n"


def quote_env(value: str) -> str:
    value = str(value)
    if not value or any(char.isspace() for char in value) or "#" in value:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


if __name__ == "__main__":
    raise SystemExit(main())
