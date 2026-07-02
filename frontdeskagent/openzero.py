from __future__ import annotations

import requests

from .config import AppConfig


def send_openzero_event(config: AppConfig, event_type: str, payload: dict) -> dict:
    if not config.openzero_webhook_url:
        return {"sent": False, "reason": "OPENZERO_WEBHOOK_URL is not configured"}
    headers = {"Content-Type": "application/json"}
    if config.openzero_api_key:
        headers["Authorization"] = f"Bearer {config.openzero_api_key}"
    body = {"source": "frontdeskagent", "event_type": event_type, "payload": payload}
    response = requests.post(config.openzero_webhook_url, headers=headers, json=body, timeout=8)
    return {"sent": response.ok, "status_code": response.status_code, "response": response.text[:300]}
