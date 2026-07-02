# Contributing

Useful contributions:

- Better industry playbooks.
- New LLM adapters.
- Calendar/CRM integrations.
- Telephony webhook examples.
- OpenZero bridge improvements.
- CPU model benchmarks.
- Accessibility and mobile UI improvements.

Before submitting:

```bash
python -m compileall frontdeskagent
python -m pytest
```

Never commit `.env`, SQLite databases, call recordings, transcripts, private phone numbers, customer data, model weights, or API keys.
