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
cp .env.example .env
python -m frontdeskagent.app
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
- Put the app behind HTTPS.
- Protect admin access with your reverse proxy, VPN, or network rules.
- Keep `.env`, SQLite, transcripts, recordings, and customer data private.
- Use `WEBHOOK_SHARED_SECRET` for telephony and CRM webhooks.
