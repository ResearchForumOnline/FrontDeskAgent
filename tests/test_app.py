from __future__ import annotations

from pathlib import Path

from frontdeskagent.app import create_app
from frontdeskagent.config import AppConfig


def test_dashboard_and_health(tmp_path: Path):
    app = create_app(make_config(tmp_path))
    client = app.test_client()
    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert b"Front desk overview" in dashboard.data
    health = client.get("/api/healthz")
    assert health.status_code == 200
    assert health.json["ok"] is True


def test_chat_rules_backend(tmp_path: Path):
    app = create_app(make_config(tmp_path))
    client = app.test_client()
    response = client.post("/api/chat", json={"message": "I have an urgent leak today"})
    assert response.status_code == 200
    assert response.json["urgency"] == "urgent"
    assert "urgent" in response.json["reply"].lower()


def test_call_webhook_creates_lead(tmp_path: Path):
    app = create_app(make_config(tmp_path))
    client = app.test_client()
    response = client.post(
        "/api/webhook/call",
        json={"name": "Alex", "phone": "+441234567890", "transcript": "Need appointment tomorrow"},
    )
    assert response.status_code == 200
    assert response.json["ok"] is True
    leads = client.get("/api/openzero/context").json["recent_leads"]
    assert leads[0]["name"] == "Alex"


def test_twilio_voice_collect_creates_lead(tmp_path: Path):
    app = create_app(make_config(tmp_path))
    client = app.test_client()
    response = client.post("/voice/twilio/collect", data={"From": "+441234567890", "SpeechResult": "urgent leak in M14"})
    assert response.status_code == 200
    assert response.mimetype == "text/xml"
    leads = client.get("/api/openzero/context").json["recent_leads"]
    assert leads[0]["source"] == "twilio_voice"
    assert leads[0]["urgency"] == "urgent"


def test_twilio_sms_creates_lead_and_returns_twiml(tmp_path: Path):
    app = create_app(make_config(tmp_path))
    client = app.test_client()
    response = client.post("/sms/twilio", data={"From": "+441234567890", "Body": "Need appointment tomorrow"})
    assert response.status_code == 200
    assert b"<Message>" in response.data
    leads = client.get("/api/openzero/context").json["recent_leads"]
    assert leads[0]["source"] == "twilio_sms"


def test_calendar_feed_requires_token_and_exports_ics(tmp_path: Path):
    config = make_config(tmp_path)
    config = config.__class__(**{**config.__dict__, "calendar_feed_token": "test-token"})
    app = create_app(config)
    client = app.test_client()
    client.post("/appointments", data={"requested_time": "2026-07-10 10:30", "notes": "Demo"})
    denied = client.get("/calendar.ics?token=bad")
    assert denied.status_code == 403
    feed = client.get("/calendar.ics?token=test-token")
    assert feed.status_code == 200
    assert b"BEGIN:VCALENDAR" in feed.data
    assert b"BEGIN:VEVENT" in feed.data


def make_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        host="127.0.0.1",
        port=8088,
        secret_key="test",
        database_path=str(tmp_path / "frontdeskagent.sqlite"),
        business_name="Test Desk",
        business_type="plumber",
        business_phone="",
        business_email="",
        business_timezone="Europe/London",
        service_areas="Manchester",
        opening_hours="Always",
        escalation_phone="",
        escalation_email="",
        llm_backend="rules",
        ollama_url="http://127.0.0.1:11434",
        ollama_model="qwen2.5:3b",
        llamacpp_url="http://127.0.0.1:8080/v1/chat/completions",
        openai_compat_url="",
        openai_compat_api_key="",
        openai_compat_model="",
        openzero_llm_url="http://127.0.0.1:1024/v1/chat/completions",
        openzero_model="local",
        openzero_api_key="",
        llm_timeout_seconds=1,
        openzero_webhook_url="",
        webhook_shared_secret="",
        smtp_host="",
        smtp_port=587,
        smtp_username="",
        smtp_password="",
        smtp_from="",
        smtp_use_tls=True,
    )
