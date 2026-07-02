from __future__ import annotations

from pathlib import Path

from flask import Flask, Response, jsonify, redirect, render_template, request, url_for

from .config import AppConfig, load_config, public_config
from .db import Database
from .integrations import (
    build_sms_twiml,
    build_voice_gather_twiml,
    build_voice_handoff_twiml,
    compact_payload,
    integration_status,
    make_calendar_ics,
    place_outbound_call,
    send_crm_event,
    send_sms,
    verify_twilio_signature,
)
from .intake import detect_urgency, extract_contact, lead_summary
from .llm import build_client, model_status, safe_reply
from .mail import send_summary_email
from .openzero import send_openzero_event


def create_app(config: AppConfig | None = None) -> Flask:
    config = config or load_config()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.secret_key
    app.config["FDA_CONFIG"] = config
    app.config["FDA_DB"] = Database(config.database_path)
    app.config["FDA_LLM"] = build_client(config)
    seed_default_knowledge(app.config["FDA_DB"], config)
    install_auth_guard(app, config)

    @app.get("/")
    def dashboard():
        db: Database = app.config["FDA_DB"]
        return render_template(
            "dashboard.html",
            config=public_config(config),
            stats=db.stats(),
            leads=db.list_leads(8),
            events=db.list_events(8),
            model=model_status(config),
            integrations=integration_status(config),
        )

    @app.get("/playground")
    def playground():
        return render_template("playground.html", config=public_config(config))

    @app.post("/api/chat")
    def api_chat():
        db: Database = app.config["FDA_DB"]
        user_text = (request.json or {}).get("message", "").strip()
        if not user_text:
            return jsonify({"error": "message is required"}), 400
        knowledge = db.search_knowledge(user_text)
        reply, error = safe_reply(app.config["FDA_LLM"], config, user_text, knowledge)
        urgency = detect_urgency(user_text)
        db.add_event("chat.reply", compact_payload({"message": user_text, "reply": reply, "urgency": urgency, "error": error}))
        return jsonify({"reply": reply, "urgency": urgency, "model_error": error})

    @app.get("/leads")
    def leads():
        db: Database = app.config["FDA_DB"]
        return render_template("leads.html", config=public_config(config), leads=db.list_leads(100))

    @app.post("/leads")
    def create_lead():
        db: Database = app.config["FDA_DB"]
        form = request.form.to_dict()
        combined = " ".join(str(value) for value in form.values())
        contact = extract_contact(combined)
        data = {
            "name": form.get("name", ""),
            "phone": form.get("phone") or contact["phone"],
            "email": form.get("email") or contact["email"],
            "company": form.get("company", ""),
            "reason": form.get("reason", ""),
            "urgency": form.get("urgency") or detect_urgency(combined),
            "preferred_time": form.get("preferred_time", ""),
            "postcode": form.get("postcode") or contact["postcode"],
            "source": form.get("source", "manual"),
        }
        data["summary"] = lead_summary(data)
        handle_new_lead(app, data, "lead.created")
        return redirect(url_for("leads"))

    @app.post("/api/webhook/call")
    def call_webhook():
        if config.webhook_shared_secret:
            provided = request.headers.get("X-FrontDeskAgent-Secret", "")
            if provided != config.webhook_shared_secret:
                return jsonify({"error": "invalid webhook secret"}), 403
        payload = request.get_json(silent=True) or {}
        transcript = str(payload.get("transcript") or payload.get("message") or "")
        contact = extract_contact(transcript)
        data = {
            "name": payload.get("name", ""),
            "phone": payload.get("phone") or contact["phone"],
            "email": payload.get("email") or contact["email"],
            "company": payload.get("company", ""),
            "reason": payload.get("reason") or transcript[:500],
            "urgency": payload.get("urgency") or detect_urgency(transcript),
            "preferred_time": payload.get("preferred_time", ""),
            "postcode": payload.get("postcode") or contact["postcode"],
            "source": payload.get("source", "call_webhook"),
            "transcript": transcript,
        }
        data["summary"] = lead_summary(data)
        result = handle_new_lead(app, data, "call.lead_created")
        return jsonify({"ok": True, **result})

    @app.post("/api/webhook/sms")
    def sms_webhook():
        if config.webhook_shared_secret:
            provided = request.headers.get("X-FrontDeskAgent-Secret", "")
            if provided != config.webhook_shared_secret:
                return jsonify({"error": "invalid webhook secret"}), 403
        payload = request.get_json(silent=True) or {}
        text = str(payload.get("body") or payload.get("message") or payload.get("text") or "")
        from_phone = str(payload.get("from") or payload.get("phone") or "")
        contact = extract_contact(text)
        data = {
            "name": payload.get("name", ""),
            "phone": from_phone or contact["phone"],
            "email": payload.get("email") or contact["email"],
            "company": payload.get("company", ""),
            "reason": payload.get("reason") or text[:500],
            "urgency": payload.get("urgency") or detect_urgency(text),
            "preferred_time": payload.get("preferred_time", ""),
            "postcode": payload.get("postcode") or contact["postcode"],
            "source": payload.get("source", "sms_webhook"),
            "transcript": text,
        }
        data["summary"] = lead_summary(data)
        result = handle_new_lead(app, data, "sms.lead_created")
        return jsonify({"ok": True, **result})

    @app.route("/voice/twilio", methods=["GET", "POST"])
    def twilio_voice():
        if not twilio_request_is_valid(config):
            return Response("Invalid Twilio signature.", status=403, mimetype="text/plain")
        return xml(build_voice_gather_twiml(config))

    @app.post("/voice/twilio/collect")
    def twilio_voice_collect():
        if not twilio_request_is_valid(config):
            return Response("Invalid Twilio signature.", status=403, mimetype="text/plain")
        transcript = request.form.get("SpeechResult") or request.form.get("Digits") or ""
        from_phone = request.form.get("From", "")
        contact = extract_contact(transcript)
        data = {
            "name": request.form.get("CallerName", ""),
            "phone": from_phone or contact["phone"],
            "email": contact["email"],
            "reason": transcript[:500] or "Inbound phone call",
            "urgency": detect_urgency(transcript),
            "postcode": contact["postcode"],
            "source": "twilio_voice",
            "transcript": transcript,
        }
        data["summary"] = lead_summary(data)
        result = handle_new_lead(app, data, "voice.lead_created")
        reply = "Thanks. I have logged the details and the team will review them."
        if data["urgency"] == "urgent":
            reply = "Thanks. This has been marked urgent and sent to the team."
        return xml(build_voice_handoff_twiml(config, reply, urgent=data["urgency"] == "urgent"))

    @app.post("/sms/twilio")
    def twilio_sms():
        if not twilio_request_is_valid(config):
            return Response("Invalid Twilio signature.", status=403, mimetype="text/plain")
        text = request.form.get("Body", "")
        from_phone = request.form.get("From", "")
        contact = extract_contact(text)
        data = {
            "name": request.form.get("ProfileName", ""),
            "phone": from_phone or contact["phone"],
            "email": contact["email"],
            "reason": text[:500],
            "urgency": detect_urgency(text),
            "postcode": contact["postcode"],
            "source": "twilio_sms",
            "transcript": text,
        }
        data["summary"] = lead_summary(data)
        handle_new_lead(app, data, "sms.lead_created", customer_sms=False)
        return xml(build_sms_twiml(config.customer_sms_template))

    @app.get("/appointments")
    def appointments():
        db: Database = app.config["FDA_DB"]
        return render_template(
            "appointments.html",
            config=public_config(config),
            full_config=config,
            appointments=db.list_appointments(100),
            leads=db.list_leads(100),
        )

    @app.post("/appointments")
    def create_appointment():
        db: Database = app.config["FDA_DB"]
        lead_id_raw = request.form.get("lead_id", "").strip()
        lead_id = int(lead_id_raw) if lead_id_raw.isdigit() else None
        appointment_id = db.create_appointment(lead_id, request.form.get("requested_time", ""), request.form.get("notes", ""))
        lead = db.get_lead(lead_id) if lead_id else None
        payload = {"appointment_id": appointment_id, "lead_id": lead_id, "requested_time": request.form.get("requested_time", ""), "notes": request.form.get("notes", "")}
        db.add_event("appointment.requested", compact_payload(payload))
        send_openzero_event(config, "appointment.requested", payload)
        record_external_result(db, "crm.appointment", safe_external(send_crm_event, config, "appointment.requested", payload))
        if lead and lead.get("phone"):
            sms_result = safe_external(send_sms, config, lead["phone"], f"Your appointment request has been logged: {payload['requested_time']}.")
            record_external_result(db, "sms.appointment_confirmation", sms_result)
        return redirect(url_for("appointments"))

    @app.get("/calendar.ics")
    def calendar_feed():
        if not config.calendar_feed_token:
            return Response("Calendar feed token is not configured.", status=403, mimetype="text/plain")
        if request.args.get("token", "") != config.calendar_feed_token:
            return Response("Invalid calendar token.", status=403, mimetype="text/plain")
        db: Database = app.config["FDA_DB"]
        return Response(make_calendar_ics(config, db.list_appointments(500)), mimetype="text/calendar")

    @app.get("/knowledge")
    def knowledge():
        db: Database = app.config["FDA_DB"]
        return render_template("knowledge.html", config=public_config(config), items=db.list_knowledge(100))

    @app.post("/knowledge")
    def add_knowledge():
        db: Database = app.config["FDA_DB"]
        db.add_knowledge(request.form.get("title", ""), request.form.get("body", ""), request.form.get("tags", ""))
        db.add_event("knowledge.added", compact_payload({"title": request.form.get("title", "")}))
        return redirect(url_for("knowledge"))

    @app.get("/settings")
    def settings():
        return render_template("settings.html", config=public_config(config), full_config=config, integrations=integration_status(config))

    @app.get("/integrations")
    def integrations():
        return render_template("integrations.html", config=public_config(config), full_config=config, integrations=integration_status(config))

    @app.post("/leads/<int:lead_id>/callback")
    def lead_callback(lead_id: int):
        db: Database = app.config["FDA_DB"]
        lead = db.get_lead(lead_id)
        if not lead:
            return jsonify({"error": "lead not found"}), 404
        message = request.form.get("message") or f"Hello from {config.business_name}. We received your enquiry and will follow up shortly."
        result = safe_external(place_outbound_call, config, lead.get("phone", ""), message)
        db.add_event("outbound.callback", compact_payload({"lead_id": lead_id, "result": result}))
        return redirect(url_for("leads"))

    @app.post("/api/outbound/callback")
    def api_outbound_callback():
        if config.webhook_shared_secret:
            provided = request.headers.get("X-FrontDeskAgent-Secret", "")
            if provided != config.webhook_shared_secret:
                return jsonify({"error": "invalid webhook secret"}), 403
        payload = request.get_json(silent=True) or {}
        result = safe_external(place_outbound_call, config, payload.get("phone", ""), payload.get("message", ""))
        app.config["FDA_DB"].add_event("outbound.api_callback", compact_payload({"request": payload, "result": result}))
        return jsonify(result)

    @app.get("/api/openzero/context")
    def openzero_context():
        db: Database = app.config["FDA_DB"]
        return jsonify({
            "service": "frontdeskagent",
            "config": public_config(config),
            "stats": db.stats(),
            "recent_leads": db.list_leads(5),
            "capabilities": [
                "lead_capture",
                "appointment_request",
                "knowledge_base",
                "call_webhook",
                "openzero_event_bridge",
                "cpu_first_llm_backend",
                "twilio_voice_webhook",
                "twilio_sms_webhook",
                "generic_sms_webhook",
                "crm_webhook",
                "calendar_ics_feed",
                "outbound_callback",
            ],
            "integrations": integration_status(config),
        })

    @app.get("/api/healthz")
    def healthz():
        db: Database = app.config["FDA_DB"]
        return jsonify({"ok": True, "stats": db.stats(), "model": model_status(config), "integrations": integration_status(config)})

    return app


def install_auth_guard(app: Flask, config: AppConfig) -> None:
    if not (config.admin_auth_enabled and config.admin_password):
        return

    public_prefixes = ("/api/webhook/", "/voice/", "/sms/", "/api/healthz")

    @app.before_request
    def require_basic_auth():
        if request.path.startswith(public_prefixes):
            return None
        auth = request.authorization
        if auth and auth.username == config.admin_username and auth.password == config.admin_password:
            return None
        return Response(
            "Authentication required",
            401,
            {"WWW-Authenticate": 'Basic realm="FrontDeskAgent"'},
        )


def handle_new_lead(app: Flask, data: dict, event_type: str, customer_sms: bool = True) -> dict:
    config: AppConfig = app.config["FDA_CONFIG"]
    db: Database = app.config["FDA_DB"]
    lead_id = db.create_lead(data)
    payload = {"lead_id": lead_id, **data}
    db.add_event(event_type, compact_payload(payload))
    openzero = safe_external(send_openzero_event, config, event_type, payload)
    email = safe_external(send_summary_email, config, f"New FrontDeskAgent lead #{lead_id}", data.get("summary", ""))
    crm = safe_external(send_crm_event, config, event_type, payload)
    record_external_result(db, "openzero.result", openzero)
    record_external_result(db, "email.result", email)
    record_external_result(db, "crm.result", crm)
    sms = {"sent": False, "reason": "auto SMS disabled"}
    if customer_sms and config.auto_sms_on_lead and data.get("phone"):
        sms = safe_external(send_sms, config, data["phone"], config.customer_sms_template)
        record_external_result(db, "sms.customer_confirmation", sms)
    escalation_sms = {"sent": False, "reason": "not urgent or disabled"}
    if data.get("urgency") == "urgent" and config.escalation_sms_enabled and config.escalation_phone:
        escalation_sms = safe_external(send_sms, config, config.escalation_phone, f"Urgent FrontDeskAgent lead #{lead_id}: {data.get('summary', '')[:900]}")
        record_external_result(db, "sms.escalation", escalation_sms)
    return {"lead_id": lead_id, "openzero": openzero, "email": email, "crm": crm, "sms": sms, "escalation_sms": escalation_sms}


def safe_external(func, *args, **kwargs) -> dict:
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        return {"sent": False, "placed": False, "error": f"{type(exc).__name__}: {exc}"}


def record_external_result(db: Database, event_type: str, result: dict) -> None:
    db.add_event(event_type, compact_payload(result))


def xml(text: str) -> Response:
    return Response(text, mimetype="text/xml")


def twilio_request_is_valid(config: AppConfig) -> bool:
    path = request.full_path.rstrip("?")
    url = f"{config.public_base_url}{path}" if config.public_base_url else request.url
    form_items = request.form.to_dict(flat=True) if request.method == "POST" else {}
    return verify_twilio_signature(config, url, form_items, request.headers.get("X-Twilio-Signature", ""))


def seed_default_knowledge(db: Database, config: AppConfig) -> None:
    if db.stats()["knowledge"] > 0:
        return
    db.add_knowledge(
        "Default greeting",
        f"Thank callers for contacting {config.business_name}. Ask for name, phone, reason, urgency, and preferred callback time.",
        "default,greeting",
    )
    db.add_knowledge(
        "Urgent handoff",
        "Urgent, sensitive, safety-critical, complaint, payment, legal, or medical matters should be captured clearly and handed to a human.",
        "urgent,handoff,safety",
    )
    db.add_knowledge(
        "Booking policy",
        "If no calendar integration is connected, log an appointment request rather than claiming the booking is confirmed.",
        "booking,calendar",
    )


app = create_app()


if __name__ == "__main__":
    cfg = app.config["FDA_CONFIG"]
    Path(cfg.database_path).parent.mkdir(parents=True, exist_ok=True)
    app.run(host=cfg.host, port=cfg.port, debug=False)
