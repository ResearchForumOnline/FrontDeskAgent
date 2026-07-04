from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from frontdeskagent.app import create_app
from frontdeskagent.config import AppConfig
from frontdeskagent.integrations import speak_with_voicebox
from frontdeskagent.llm import model_status
from frontdeskagent.web_ingest import TextExtractor


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


def test_auto_backend_falls_back_to_rules(tmp_path: Path):
    config = replace(
        make_config(tmp_path),
        llm_backend="auto",
        openzero_llm_url="http://127.0.0.1:9/v1/chat/completions",
        ollama_url="http://127.0.0.1:9",
        llamacpp_url="",
        openai_compat_url="",
        openai_compat_model="",
    )
    app = create_app(config)
    client = app.test_client()
    response = client.post("/api/chat", json={"message": "I have an urgent leak today"})
    assert response.status_code == 200
    assert response.json["urgency"] == "urgent"
    assert "urgent" in response.json["reply"].lower()


def test_auto_model_status_reports_route_order(tmp_path: Path):
    config = replace(
        make_config(tmp_path),
        llm_backend="auto",
        openzero_llm_url="http://127.0.0.1:9/v1/chat/completions",
        ollama_url="http://127.0.0.1:9",
        llamacpp_url="",
    )
    status = model_status(config)
    assert status["backend"] == "auto"
    assert status["routes"][-1]["backend"] == "rules"
    assert status["routes"][-1]["ok"] is True


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


def test_voicebox_speak_posts_to_local_api(tmp_path: Path, monkeypatch):
    config = replace(
        make_config(tmp_path),
        voice_tts_provider="voicebox",
        voicebox_url="http://voicebox.local:17493",
        voicebox_profile="Morgan",
        voicebox_client_id="frontdeskagent-test",
        voicebox_timeout_seconds=3,
    )
    seen = {}

    class DummyResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return DummyResponse()

    monkeypatch.setattr("frontdeskagent.integrations.requests.post", fake_post)
    result = speak_with_voicebox(config, "New lead received.")
    assert result["spoken"] is True
    assert seen["url"] == "http://voicebox.local:17493/speak"
    assert seen["headers"]["X-Voicebox-Client-Id"] == "frontdeskagent-test"
    assert seen["json"] == {"text": "New lead received.", "profile": "Morgan"}
    assert seen["timeout"] == 3


def test_voice_speak_api_requires_text(tmp_path: Path):
    app = create_app(make_config(tmp_path))
    client = app.test_client()
    response = client.post("/api/voice/speak", json={})
    assert response.status_code == 400
    assert response.json["error"] == "text is required"


def test_voicebox_alert_on_lead(tmp_path: Path, monkeypatch):
    config = replace(
        make_config(tmp_path),
        voice_tts_provider="voicebox",
        voicebox_url="http://voicebox.local:17493",
        voicebox_alert_on_lead=True,
    )
    calls = []

    class DummyResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"ok": True}

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append({"url": url, "json": json})
        return DummyResponse()

    monkeypatch.setattr("frontdeskagent.integrations.requests.post", fake_post)
    app = create_app(config)
    client = app.test_client()
    response = client.post(
        "/api/webhook/call",
        json={"name": "Alex", "phone": "+441234567890", "transcript": "urgent leak in M14"},
    )
    assert response.status_code == 200
    assert response.json["voice_alert"]["spoken"] is True
    assert calls[0]["url"] == "http://voicebox.local:17493/speak"
    assert "New urgent FrontDeskAgent lead" in calls[0]["json"]["text"]


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


def test_email_webhook_creates_lead(tmp_path: Path):
    app = create_app(make_config(tmp_path))
    client = app.test_client()
    response = client.post(
        "/api/webhook/email",
        json={"from": "caller@example.com", "subject": "Quote request", "body": "Please call +441234567890 tomorrow"},
    )
    assert response.status_code == 200
    leads = client.get("/api/openzero/context").json["recent_leads"]
    assert leads[0]["source"] == "email_webhook"
    assert leads[0]["email"] == "caller@example.com"


def test_text_extractor_ignores_scripts():
    parser = TextExtractor()
    parser.feed("<html><title>Services</title><script>bad()</script><h1>Emergency plumber</h1><p>Open 24/7.</p></html>")
    assert parser.title == "Services"
    assert "Emergency plumber" in "\n".join(parser.parts)
    assert "bad()" not in "\n".join(parser.parts)


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
