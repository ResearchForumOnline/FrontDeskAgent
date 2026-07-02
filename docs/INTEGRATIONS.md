# Integrations

FrontDeskAgent works without paid APIs in rules mode. Add providers only when you want phone numbers, SMS, email, CRM automation, or outbound callbacks.

## SMS

Set:

```env
SMS_PROVIDER=twilio
SMS_FROM=+15551234567
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
AUTO_SMS_ON_LEAD=true
```

Alternatives:

```env
SMS_PROVIDER=telnyx
TELNYX_API_KEY=...
SMS_FROM=+15551234567
```

or:

```env
SMS_PROVIDER=webhook
SMS_WEBHOOK_URL=https://your-n8n-or-api.example/sms
```

## Inbound Phone Calls

Use Twilio Voice webhook:

```text
https://your-domain.example/voice/twilio
```

The app asks the caller to speak, saves the captured speech as a lead, sends configured handoffs, and can transfer urgent calls when:

```env
TRANSFER_URGENT_CALLS=true
ESCALATION_PHONE=+15559876543
```

Twilio signatures are checked when `TWILIO_AUTH_TOKEN` is set and `TWILIO_VALIDATE_SIGNATURES=true`. Keep `PUBLIC_BASE_URL` exactly matched to the HTTPS URL Twilio calls.

## Outbound Calls

Twilio:

```env
OUTBOUND_CALL_PROVIDER=twilio
OUTBOUND_CALLER_ID=+15551234567
```

Generic webhook:

```env
OUTBOUND_CALL_PROVIDER=webhook
OUTBOUND_WEBHOOK_URL=https://your-voice-system.example/call
```

## Email

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM=frontdesk@example.com
ESCALATION_EMAIL=team@example.com
```

## CRM / Automation

Use `CRM_WEBHOOK_URL` for n8n, Zapier, Make, a CRM, or an internal API:

```env
CRM_WEBHOOK_URL=https://automation.example/webhook/frontdeskagent
CRM_API_KEY=
```

FrontDeskAgent posts lead and appointment events as JSON.

## Calendar

Set:

```env
CALENDAR_FEED_TOKEN=long-random-token
```

Subscribe to:

```text
https://your-domain.example/calendar.ics?token=long-random-token
```

Calendar entries are appointment requests, not confirmed bookings, unless your own calendar or CRM workflow confirms them.
