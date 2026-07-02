# Deployment

FrontDeskAgent is designed for normal CPU servers. A small VPS can run the dashboard, SQLite, webhooks, and rule-based fallback. Add a local model only when the machine has enough RAM.

## Minimum Practical Server

- 1 to 2 vCPU
- 1 GB RAM for rule-based mode
- 4 GB RAM for very small local models
- 8 GB RAM or more for a smoother local LLM setup
- Ubuntu, Debian, Mint, or compatible Linux

## Install

```bash
git clone https://github.com/ResearchForumOnline/FrontDeskAgent.git
cd FrontDeskAgent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m frontdeskagent.setup_wizard
python -m frontdeskagent.app
```

For a one-line server install:

```bash
curl -fsSL https://raw.githubusercontent.com/ResearchForumOnline/FrontDeskAgent/main/install.sh -o install-frontdeskagent.sh
bash install-frontdeskagent.sh
```

## Reverse Proxy

Example Caddy:

```caddyfile
frontdeskagent.example.com {
  reverse_proxy 127.0.0.1:8088
}
```

Example nginx:

```nginx
server {
  server_name frontdeskagent.example.com;
  location / {
    proxy_pass http://127.0.0.1:8088;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

## Production Notes

- Change `SECRET_KEY`.
- Enable `ADMIN_AUTH_ENABLED=true` and set `ADMIN_PASSWORD` before exposing the dashboard.
- Put the app behind HTTPS.
- Protect admin access with your reverse proxy, VPN, or network rules.
- Keep `.env`, SQLite, transcripts, recordings, and customer data private.
- Use `WEBHOOK_SHARED_SECRET` for telephony and CRM webhooks.
- Set `PUBLIC_BASE_URL` so Twilio and other providers can call the right HTTPS URL.
- Use `CALENDAR_FEED_TOKEN` if the calendar feed is exposed.

## What To Paste Into Providers

Assuming `PUBLIC_BASE_URL=https://frontdesk.example.com`:

- Twilio Voice webhook: `https://frontdesk.example.com/voice/twilio`
- Twilio SMS webhook: `https://frontdesk.example.com/sms/twilio`
- Generic SMS webhook: `https://frontdesk.example.com/api/webhook/sms`
- Generic call webhook: `https://frontdesk.example.com/api/webhook/call`
- OpenZero context: `https://frontdesk.example.com/api/openzero/context`
- Calendar feed: `https://frontdesk.example.com/calendar.ics?token=...`
