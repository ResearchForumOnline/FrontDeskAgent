# FrontDeskAgent

FrontDeskAgent is a self-hosted AI receptionist and front desk console for small businesses, clinics, trades, education teams, hotels, agencies, and any organisation that needs calls, messages, leads, bookings, and handoffs captured reliably.

It is built CPU-first: SQLite, Flask, simple HTML, and local model backends that work with Ollama, llama.cpp server, OpenAI-compatible endpoints, or OpenZero. A rule-based fallback is included so the product still runs before a model is installed.

Public site: https://frontdeskagent.online/

Companion playbooks: https://github.com/ResearchForumOnline/FrontDeskAgent-Playbooks

## What It Does

- Captures caller or web-chat details into a local SQLite lead inbox.
- Runs industry-specific intake flows for plumbers, clinics, admissions, hotels, professional firms, and general front desks.
- Uses a local knowledge base for business hours, services, prices, service areas, policies, and escalation rules.
- Imports public website pages into the knowledge base for website-trained answers.
- Generates receptionist replies through Ollama, llama.cpp server, OpenAI-compatible APIs, OpenZero, or a no-model fallback.
- Creates appointment requests and staff handoff summaries.
- Exposes webhook endpoints for telephony, forms, CRM tools, and OpenZero.
- Sends events to OpenZero when configured, so OpenZero can supervise or extend the workflow.
- Ships with install scripts, Docker support, systemd examples, and deployment docs.

## CPU-First Model Options

Recommended first path:

```bash
ollama serve
ollama pull qwen2.5:3b
```

Then set:

```env
LLM_BACKEND=ollama
OLLAMA_MODEL=qwen2.5:3b
```

Other options:

- `LLM_BACKEND=llamacpp` for a local llama.cpp OpenAI-compatible server.
- `LLM_BACKEND=openai_compat` for any OpenAI-compatible endpoint.
- `LLM_BACKEND=openzero` to route through a local OpenZero node.
- `LLM_BACKEND=rules` for zero-model testing.

## Quick Start

```bash
git clone https://github.com/ResearchForumOnline/FrontDeskAgent.git
cd FrontDeskAgent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m frontdeskagent.setup_wizard
python -m frontdeskagent.app
```

Open:

```text
http://localhost:8088
```

## One-Line Server Install

Review before running:

```bash
curl -fsSL https://raw.githubusercontent.com/ResearchForumOnline/FrontDeskAgent/main/install.sh -o install-frontdeskagent.sh
less install-frontdeskagent.sh
bash install-frontdeskagent.sh
```

## OpenZero Integration

FrontDeskAgent can publish lead, booking, handoff, and health events to OpenZero:

```env
OPENZERO_WEBHOOK_URL=http://127.0.0.1:1024/api/frontdeskagent/event
OPENZERO_API_KEY=
```

It can also use OpenZero as the LLM bridge:

```env
LLM_BACKEND=openzero
OPENZERO_LLM_URL=http://127.0.0.1:1024/v1/chat/completions
OPENZERO_MODEL=local
```

See `docs/OPENZERO_INTEGRATION.md`.

## Real Integrations Included

- Inbound voice: Twilio-compatible voice webhook at `/voice/twilio`.
- Inbound SMS: Twilio webhook at `/sms/twilio` and generic JSON webhook at `/api/webhook/sms`.
- Outbound SMS: Twilio, Telnyx, or any custom webhook.
- Outbound calls: Twilio call API or a custom webhook.
- Email: SMTP lead summaries and handoff emails.
- Email intake: generic email webhook for mail parsers, n8n, Zapier, Make, or an internal mail gateway.
- Calendar: token-protected `.ics` feed for appointment requests.
- Booking systems: optional booking webhook for Cal.com, n8n, CRM booking flows, or internal APIs.
- CRM/automation: generic webhook for n8n, Zapier, Make, CRM systems, or internal APIs.
- OpenZero: event bridge plus `/api/openzero/context`.

All integrations are optional. The app still works with only SQLite and the built-in rules backend.

## Industry Playbooks

Use the companion playbook library for ready-made intake structures covering plumbing, clinics, hotels, university admissions, estate agents, and agency discovery calls:

https://github.com/ResearchForumOnline/FrontDeskAgent-Playbooks

## Repository Boundary

This repository is the open-source self-hosted app. It does not include production phone numbers, live credentials, private customer data, voice-clone data, hosted service secrets, or model weights.

Keep `.env`, SQLite runtime databases, uploads, transcripts, call recordings, and private customer data out of Git.

## License

MIT License. See `LICENSE`.
