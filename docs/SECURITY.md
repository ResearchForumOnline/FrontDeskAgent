# Security

FrontDeskAgent handles business enquiries and may process personal data. Treat the deployment like a production CRM or ticketing system.

## Do

- Use HTTPS.
- Change `SECRET_KEY`.
- Set `WEBHOOK_SHARED_SECRET`.
- Restrict admin access by VPN, reverse proxy auth, firewall, or trusted network.
- Keep `.env`, SQLite databases, transcripts, recordings, and backups out of Git.
- Use SMTP credentials with the least access needed.
- Review install scripts before running them.

## Do Not

- Commit customer data.
- Expose the dashboard directly to the public internet without access control.
- Claim a booking is confirmed unless a real calendar confirms it.
- Use cloned voices without written permission from the person whose voice is used.
- Use the agent for legal, medical, or financial advice without human review and proper compliance.
