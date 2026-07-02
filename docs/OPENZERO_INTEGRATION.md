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

## OpenZero As LLM Bridge

Set:

```env
LLM_BACKEND=openzero
OPENZERO_LLM_URL=http://127.0.0.1:1024/v1/chat/completions
OPENZERO_MODEL=local
OPENZERO_API_KEY=
```

This lets OpenZero decide whether to use a local model, remote provider, or its own routing logic.

## Useful Combined Workflows

- FrontDeskAgent captures a lead, OpenZero creates a deeper staff brief.
- FrontDeskAgent logs a booking request, OpenZero checks local files or CRM exports.
- FrontDeskAgent handles first reply, OpenZero watches for missed handoffs.
- OpenZero can periodically call `/api/openzero/context` and produce an operator digest.
