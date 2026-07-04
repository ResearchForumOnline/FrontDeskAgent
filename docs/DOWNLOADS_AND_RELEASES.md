# Downloads And Releases

FrontDeskAgent is a CPU-first, self-hosted AI receptionist. It can run with OpenZero, Ollama, llama.cpp, OpenAI-compatible APIs, or the built-in fallback route.

## Public Links

| Need | Link |
| --- | --- |
| Website | <https://frontdeskagent.online/> |
| GitHub repository | <https://github.com/ResearchForumOnline/FrontDeskAgent> |
| Source ZIP | <https://github.com/ResearchForumOnline/FrontDeskAgent/archive/refs/heads/main.zip> |
| GitHub releases | <https://github.com/ResearchForumOnline/FrontDeskAgent/releases> |
| Companion playbooks | <https://github.com/ResearchForumOnline/FrontDeskAgent-Playbooks> |
| OpenZero | <https://github.com/ResearchForumOnline/OpenZero> |

## Local Install

```bash
git clone https://github.com/ResearchForumOnline/FrontDeskAgent.git
cd FrontDeskAgent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m frontdeskagent.setup_wizard
python -m frontdeskagent.app
```

## Server Install

Review first:

```bash
curl -fsSL https://raw.githubusercontent.com/ResearchForumOnline/FrontDeskAgent/main/install.sh -o install-frontdeskagent.sh
less install-frontdeskagent.sh
bash install-frontdeskagent.sh
```

## Release Notes Should Cover

- install changes;
- model/backend changes for OpenZero, Ollama, llama.cpp, or hosted OpenAI-compatible providers;
- webhook changes for phone, SMS, email, CRM, booking, or calendar integrations;
- admin security changes;
- migration notes for existing leads, appointments, and knowledge-base data.

## Search-Friendly Summary

FrontDeskAgent is for self-hosted AI receptionist, AI front desk, local business chatbot, CPU-first AI agent, Twilio voice webhook, SMS intake, appointment request logging, OpenZero integration, Voicebox local voice output, Ollama receptionist, and local-first customer intake workflows.
