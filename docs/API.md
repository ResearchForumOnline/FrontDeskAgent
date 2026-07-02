# API

## Health

```http
GET /api/healthz
```

## Chat

```http
POST /api/chat
Content-Type: application/json

{"message":"I need an urgent plumber today in M14"}
```

## Call Webhook

```http
POST /api/webhook/call
Content-Type: application/json
X-FrontDeskAgent-Secret: optional-shared-secret

{
  "name": "Alex Customer",
  "phone": "+441234567890",
  "transcript": "Leak under sink, water still running, Manchester M14."
}
```

Returns:

```json
{"ok": true, "lead_id": 1}
```

## OpenZero Context

```http
GET /api/openzero/context
```

Returns public config, stats, recent leads, and capabilities.
