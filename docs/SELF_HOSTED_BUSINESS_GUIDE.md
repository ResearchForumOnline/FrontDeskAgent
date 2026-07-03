# Self-Hosted Business Guide

FrontDeskAgent is built for small businesses and organisations that need enquiries handled consistently.

It can be used by:

- trades and emergency service businesses;
- clinics and wellness teams;
- hotels and guest services;
- property and estate agents;
- university admissions teams;
- agencies and consultancies;
- local service businesses with repeated enquiry patterns.

## What To Prepare

Before going live, collect:

- opening hours;
- service areas;
- products and services;
- pricing notes;
- booking rules;
- escalation contacts;
- emergency rules;
- privacy wording;
- cancellation policies;
- common questions;
- staff handoff email/SMS destinations.

## Recommended Launch Path

1. Install FrontDeskAgent.
2. Run the setup wizard.
3. Add business knowledge.
4. Pick an industry playbook.
5. Test the playground.
6. Add one public intake channel.
7. Review every lead for a week.
8. Add SMS/email/call integrations after the workflow is proven.
9. Connect OpenZero if you want a local/self-hosted AI route.

## Local AI Path

FrontDeskAgent can run without a model using the built-in rules fallback. For AI replies, start with the local-first route:

```env
LLM_BACKEND=auto
OPENZERO_LLM_URL=http://127.0.0.1:1024/v1/chat/completions
OLLAMA_URL=http://127.0.0.1:11434/api/generate
```

Use hosted APIs only when deliberately configured.

## Operational Safety

Do not commit:

- `.env`;
- SQLite runtime databases;
- call recordings;
- transcripts;
- private customer data;
- API keys;
- staff phone numbers;
- production webhooks.

## Good First Automation

The best first automation is simple:

- capture name, contact details, need, urgency, preferred time, and location;
- write the lead clearly;
- notify staff;
- ask for missing details;
- avoid making promises the business cannot keep.

