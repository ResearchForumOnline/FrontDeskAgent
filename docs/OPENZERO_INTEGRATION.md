# OpenZero Integration

FrontDeskAgent is useful by itself, but it is designed to sit beside OpenZero.

## Event Bridge

Set:

```env
OPENZERO_WEBHOOK_URL=http://127.0.0.1:1024/api/frontdeskagent/event
OPENZERO_API_KEY=
```

FrontDeskAgent sends events such as:

- `lead.created`
- `call.lead_created`
- `appointment.requested`
- `knowledge.added`

The payload includes lead details, urgency, source, and summary.

## Context Endpoint

OpenZero can read:

```text
GET http://127.0.0.1:8088/api/openzero/context
```

This returns current stats, recent leads, public config, and capabilities.

## OpenZero As The First LLM Bridge

Fresh installs can keep `LLM_BACKEND=auto`. In auto mode, FrontDeskAgent tries the OpenZero local LLM bridge before Ollama, llama.cpp, hosted APIs, or rules mode:

```env
LLM_BACKEND=auto
OPENZERO_LLM_URL=http://127.0.0.1:1024/v1/chat/completions
OPENZERO_MODEL=local
OPENZERO_API_KEY=
```

This lets OpenZero decide whether to use a local model, remote provider, or its own routing logic. If OpenZero is not reachable, FrontDeskAgent continues down the local-first route order instead of failing the chat.

Use `LLM_BACKEND=openzero` only when you want to force every model request through OpenZero.

## Useful Combined Workflows

- FrontDeskAgent captures a lead, OpenZero creates a deeper staff brief.
- FrontDeskAgent logs a booking request, OpenZero checks local files or CRM exports.
- FrontDeskAgent handles first reply, OpenZero watches for missed handoffs.
- OpenZero can periodically call `/api/openzero/context` and produce an operator digest.
- OpenZero can call `/api/voice/speak` when Voicebox is enabled so important front-desk events can speak locally without a cloud voice provider.

## Website Receptionist Demo Pattern

The public FrontDeskAgent Online website demonstrates the idea with a small browser widget. Visitors can type or speak to a receptionist-style agent, receive an OpenZero-backed answer through the shared CallChat bridge, and hear a server Voicebox reply with browser speech as fallback. The public demo currently allows 200 AI asks per visitor per site per day with per-minute abuse controls, while production installs should use their own approved limits and business knowledge.

For production use, keep the public website demo separate from the private business agent:

- Public demo: short, rate-limited, product-aware, no secrets, no real customer records.
- Production agent: private knowledge base, approved scripts, real call/SMS/email/booking/CRM integrations, staff handoff rules, and customer-data controls.
- OpenZero route: use a local or private OpenZero-compatible endpoint for business-specific reasoning where possible.
- Voicebox route: use local Voicebox speech for staff alerts or demos when configured.

Do not expose private API keys, webhook secrets, call recordings, transcripts, customer details, or production OpenZero admin endpoints in public browser JavaScript.
