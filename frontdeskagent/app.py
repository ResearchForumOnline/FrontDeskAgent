from __future__ import annotations

import json
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

from .config import AppConfig, load_config, public_config
from .db import Database
from .intake import detect_urgency, extract_contact, lead_summary
from .llm import build_client, compact_json, model_status, safe_reply
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
        db.add_event("chat.reply", compact_json({"message": user_text, "reply": reply, "urgency": urgency, "error": error}))
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
        lead_id = db.create_lead(data)
        payload = {"lead_id": lead_id, **data}
        db.add_event("lead.created", compact_json(payload))
        send_openzero_event(config, "lead.created", payload)
        send_summary_email(config, f"New FrontDeskAgent lead #{lead_id}", data["summary"])
        return redirect(url_for("leads"))

    @app.post("/api/webhook/call")
    def call_webhook():
        if config.webhook_shared_secret:
            provided = request.headers.get("X-FrontDeskAgent-Secret", "")
            if provided != config.webhook_shared_secret:
                return jsonify({"error": "invalid webhook secret"}), 403
        payload = request.json or {}
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
        db: Database = app.config["FDA_DB"]
        lead_id = db.create_lead(data)
        event_payload = {"lead_id": lead_id, **data}
        db.add_event("call.lead_created", compact_json(event_payload))
        openzero = send_openzero_event(config, "call.lead_created", event_payload)
        return jsonify({"ok": True, "lead_id": lead_id, "openzero": openzero})

    @app.get("/appointments")
    def appointments():
        db: Database = app.config["FDA_DB"]
        return render_template("appointments.html", config=public_config(config), appointments=db.list_appointments(100), leads=db.list_leads(100))

    @app.post("/appointments")
    def create_appointment():
        db: Database = app.config["FDA_DB"]
        lead_id_raw = request.form.get("lead_id", "").strip()
        lead_id = int(lead_id_raw) if lead_id_raw.isdigit() else None
        appointment_id = db.create_appointment(lead_id, request.form.get("requested_time", ""), request.form.get("notes", ""))
        payload = {"appointment_id": appointment_id, "lead_id": lead_id, "requested_time": request.form.get("requested_time", "")}
        db.add_event("appointment.requested", compact_json(payload))
        send_openzero_event(config, "appointment.requested", payload)
        return redirect(url_for("appointments"))

    @app.get("/knowledge")
    def knowledge():
        db: Database = app.config["FDA_DB"]
        return render_template("knowledge.html", config=public_config(config), items=db.list_knowledge(100))

    @app.post("/knowledge")
    def add_knowledge():
        db: Database = app.config["FDA_DB"]
        db.add_knowledge(request.form.get("title", ""), request.form.get("body", ""), request.form.get("tags", ""))
        db.add_event("knowledge.added", compact_json({"title": request.form.get("title", "")}))
        return redirect(url_for("knowledge"))

    @app.get("/settings")
    def settings():
        return render_template("settings.html", config=public_config(config), full_config=config)

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
            ],
        })

    @app.get("/api/healthz")
    def healthz():
        db: Database = app.config["FDA_DB"]
        return jsonify({"ok": True, "stats": db.stats(), "model": model_status(config)})

    return app


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
