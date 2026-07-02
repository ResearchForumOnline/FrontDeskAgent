from __future__ import annotations

import html
import base64
import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta, timezone

import requests

from .config import AppConfig, sms_enabled


def integration_status(config: AppConfig) -> dict:
    return {
        "admin_auth": bool(config.admin_auth_enabled and config.admin_password),
        "sms": sms_enabled(config),
        "sms_provider": config.sms_provider,
        "email": bool(config.smtp_host and config.smtp_from),
        "crm": bool(config.crm_webhook_url),
        "calendar_feed": bool(config.calendar_feed_token),
        "openzero": bool(config.openzero_webhook_url or config.llm_backend == "openzero"),
        "outbound_calls": outbound_enabled(config),
        "voice_webhook": bool(config.public_base_url),
        "twilio_signature_validation": bool(config.twilio_validate_signatures and config.twilio_auth_token),
    }


def send_sms(config: AppConfig, to_phone: str, body: str) -> dict:
    to_phone = (to_phone or "").strip()
    body = (body or "").strip()
    if not to_phone:
        return {"sent": False, "reason": "recipient phone is missing"}
    if not body:
        return {"sent": False, "reason": "message body is missing"}

    if config.sms_provider == "twilio":
        if not (config.twilio_account_sid and config.twilio_auth_token and config.sms_from):
            return {"sent": False, "reason": "Twilio SMS is not configured"}
        url = f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Messages.json"
        response = requests.post(
            url,
            data={"To": to_phone, "From": config.sms_from, "Body": body[:1500]},
            auth=(config.twilio_account_sid, config.twilio_auth_token),
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        return {"sent": True, "provider": "twilio", "sid": payload.get("sid")}

    if config.sms_provider == "telnyx":
        if not (config.telnyx_api_key and config.sms_from):
            return {"sent": False, "reason": "Telnyx SMS is not configured"}
        payload = {"from": config.sms_from, "to": to_phone, "text": body[:1500]}
        if config.telnyx_messaging_profile_id:
            payload["messaging_profile_id"] = config.telnyx_messaging_profile_id
        response = requests.post(
            "https://api.telnyx.com/v2/messages",
            headers={"Authorization": f"Bearer {config.telnyx_api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=12,
        )
        response.raise_for_status()
        data = response.json()
        return {"sent": True, "provider": "telnyx", "id": data.get("data", {}).get("id")}

    if config.sms_provider == "webhook":
        if not config.sms_webhook_url:
            return {"sent": False, "reason": "SMS webhook is not configured"}
        response = requests.post(config.sms_webhook_url, json={"to": to_phone, "body": body}, timeout=12)
        response.raise_for_status()
        return {"sent": True, "provider": "webhook", "status": response.status_code}

    return {"sent": False, "reason": "SMS provider is off"}


def send_crm_event(config: AppConfig, event_type: str, payload: dict) -> dict:
    if not config.crm_webhook_url:
        return {"sent": False, "reason": "CRM webhook is not configured"}
    headers = {"Content-Type": "application/json"}
    if config.crm_api_key:
        headers["Authorization"] = f"Bearer {config.crm_api_key}"
    body = {"service": "frontdeskagent", "event_type": event_type, "payload": payload}
    response = requests.post(config.crm_webhook_url, headers=headers, json=body, timeout=12)
    response.raise_for_status()
    return {"sent": True, "status": response.status_code}


def outbound_enabled(config: AppConfig) -> bool:
    if config.outbound_call_provider == "twilio":
        return bool(config.twilio_account_sid and config.twilio_auth_token and (config.outbound_caller_id or config.sms_from))
    if config.outbound_call_provider == "webhook":
        return bool(config.outbound_webhook_url)
    return False


def place_outbound_call(config: AppConfig, to_phone: str, message: str) -> dict:
    to_phone = (to_phone or "").strip()
    message = (message or "").strip()
    if not to_phone:
        return {"placed": False, "reason": "recipient phone is missing"}
    if not message:
        return {"placed": False, "reason": "message is missing"}

    if config.outbound_call_provider == "twilio":
        if not outbound_enabled(config):
            return {"placed": False, "reason": "Twilio outbound calling is not configured"}
        twiml = build_say_twiml(message)
        response = requests.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{config.twilio_account_sid}/Calls.json",
            data={"To": to_phone, "From": config.outbound_caller_id or config.sms_from, "Twiml": twiml},
            auth=(config.twilio_account_sid, config.twilio_auth_token),
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        return {"placed": True, "provider": "twilio", "sid": payload.get("sid")}

    if config.outbound_call_provider == "webhook":
        if not config.outbound_webhook_url:
            return {"placed": False, "reason": "outbound webhook is not configured"}
        response = requests.post(config.outbound_webhook_url, json={"to": to_phone, "message": message}, timeout=12)
        response.raise_for_status()
        return {"placed": True, "provider": "webhook", "status": response.status_code}

    return {"placed": False, "reason": "outbound calling is off"}


def build_voice_gather_twiml(config: AppConfig) -> str:
    action = f"{config.public_base_url}/voice/twilio/collect" if config.public_base_url else "/voice/twilio/collect"
    prompt = html.escape(config.voice_greeting)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        f'<Gather input="speech dtmf" action="{html.escape(action)}" method="POST" speechTimeout="auto" timeout="7">'
        f"<Say>{prompt}</Say>"
        "</Gather>"
        "<Say>We did not receive the details. Please call again or send a text message.</Say>"
        "</Response>"
    )


def build_voice_handoff_twiml(config: AppConfig, reply: str, urgent: bool = False) -> str:
    safe_reply = html.escape(reply[:1200])
    transfer = ""
    if urgent and config.transfer_urgent_calls and config.escalation_phone:
        transfer = f"<Say>Connecting you to the team now.</Say><Dial>{html.escape(config.escalation_phone)}</Dial>"
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>{safe_reply}</Say>{transfer}</Response>'


def build_sms_twiml(message: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{html.escape(message[:1200])}</Message></Response>'


def build_say_twiml(message: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Say>{html.escape(message[:1200])}</Say></Response>'


def make_calendar_ics(config: AppConfig, appointments: list[dict]) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//FrontDeskAgent//Self Hosted Calendar//EN",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{_ics_text(config.business_name)} FrontDeskAgent Requests",
    ]
    for item in appointments:
        start = _parse_requested_time(item.get("requested_time", ""), item.get("created_at", ""))
        end = start + timedelta(minutes=30)
        uid = f"frontdeskagent-{item.get('id')}@local"
        summary = f"FrontDeskAgent request: {item.get('lead_name') or item.get('lead_phone') or 'Manual'}"
        description = "\n".join(
            part
            for part in [
                f"Requested time: {item.get('requested_time', '')}",
                f"Status: {item.get('status', '')}",
                f"Lead phone: {item.get('lead_phone', '')}",
                f"Notes: {item.get('notes', '')}",
            ]
            if part.strip()
        )
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_ics_text(uid)}",
                f"DTSTAMP:{_ics_dt(datetime.now(timezone.utc))}",
                f"DTSTART:{_ics_dt(start)}",
                f"DTEND:{_ics_dt(end)}",
                f"SUMMARY:{_ics_text(summary)}",
                f"DESCRIPTION:{_ics_text(description)}",
                "STATUS:TENTATIVE",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def _parse_requested_time(value: str, fallback: str) -> datetime:
    text = value or fallback
    iso_match = re.search(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}):(\d{2}))?", text)
    if iso_match:
        hour = int(iso_match.group(2) or "9")
        minute = int(iso_match.group(3) or "0")
        return datetime.fromisoformat(f"{iso_match.group(1)}T{hour:02d}:{minute:02d}:00").replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(fallback.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc) + timedelta(days=1)


def _ics_dt(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ics_text(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace(",", "\\,").replace(";", "\\;")


def compact_payload(data: dict) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True)


def verify_twilio_signature(config: AppConfig, url: str, form_items: dict, signature: str) -> bool:
    if not (config.twilio_validate_signatures and config.twilio_auth_token):
        return True
    signed = url + "".join(f"{key}{value}" for key, value in sorted(form_items.items()))
    digest = hmac.new(config.twilio_auth_token.encode("utf-8"), signed.encode("utf-8"), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, signature or "")
