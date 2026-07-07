# Changelog

## 2026-07-06

- Added public-site live receptionist demo notes for frontdeskagent.online.
- Added documentation for the hosted local Vosk speech-to-text fallback used when browser speech recognition is unavailable.
- Documented the upgraded demo boundary: OpenZero-backed answers through the shared CallChat bridge, server Voicebox audio first, browser speech fallback, public abuse controls, and production phone flows handled through real approved integrations.
- Clarified that production deployments should connect Twilio or custom call webhooks, private business knowledge, CRM/booking routes, staff handoff rules, and optional Voicebox local speech.

## 2026-07-04

- Aligned the Voicebox integration with the current public Voicebox REST API: default `POST /generate`, `profile_id`, and `language`.
- Added `VOICEBOX_ENDPOINT` and `VOICEBOX_LANGUAGE` configuration.
- Hardened numeric environment parsing so malformed timeout/port values fall back safely.
- Protected `/api/voice/speak` with `X-FrontDeskAgent-Secret` when `WEBHOOK_SHARED_SECRET` is configured.
- Added optional Voicebox local voice output for staff alerts and `/api/voice/speak`.
- Added Voicebox lead-alert automation with `VOICEBOX_ALERT_ON_LEAD=true`.
- Documented the open-source voice route across README, API, integrations, OpenZero integration, and release discovery docs.
- Expanded public project documentation.
- Added roadmap and self-hosted business deployment guide.
- Added GitHub issue and pull request templates.
- Clarified the open-source repository boundary for private customer data, API keys, call recordings, and premium hosted services.

## 2026-07-02

- Added local-first AI routing documentation.
- Added OpenZero integration notes.
- Added CPU model guidance.
- Added integrations, deployment, API, and industry playbook documentation.
