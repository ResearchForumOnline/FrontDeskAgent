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
{"ok": true, "lead_id": 1, "sms": {"sent": false}}
```

## SMS Webhooks

Generic JSON:

```http
POST /api/webhook/sms
Content-Type: application/json
X-FrontDeskAgent-Secret: optional-shared-secret

{"from":"+441234567890","body":"Need a callback for an urgent leak in M14"}
```

## Email Webhook

```http
POST /api/webhook/email
Content-Type: application/json
X-FrontDeskAgent-Secret: optional-shared-secret

{"from":"caller@example.com","subject":"Quote request","body":"Can you call me tomorrow?"}
```

Use this with an email parser, n8n, Zapier, Make, or a mail gateway to turn inbound email into leads.

Twilio Messaging webhook:

```text
POST /sms/twilio
```

Use this as the inbound message webhook in Twilio. It returns TwiML and creates a lead.

## Voice Webhook

Twilio Voice:

```text
POST /voice/twilio
```

Set this as a Twilio Voice webhook. The first route asks the caller to speak. Twilio posts the speech result to `/voice/twilio/collect`, where FrontDeskAgent creates the lead, sends configured handoffs, and optionally transfers urgent calls.

## Outbound Callback

```http
POST /api/outbound/callback
Content-Type: application/json
X-FrontDeskAgent-Secret: optional-shared-secret

{"phone":"+441234567890","message":"Hello, your enquiry has been received."}
```

Works with `OUTBOUND_CALL_PROVIDER=twilio` or `OUTBOUND_CALL_PROVIDER=webhook`.

## Website Knowledge Import

```http
POST /knowledge/import-url
Content-Type: application/x-www-form-urlencoded

url=https://company.example/services
```

Fetches public HTML, extracts readable page text, and stores it in the local knowledge base for review.

## Calendar Feed

```http
GET /calendar.ics?token=your-calendar-token
```

Subscribe from Google Calendar, Outlook, Apple Calendar, or Nextcloud. Entries are appointment requests and stay tentative unless a connected human or booking system confirms them.

## OpenZero Context

```http
GET /api/openzero/context
```

Returns public config, stats, recent leads, integration status, and capabilities.
