from __future__ import annotations

from .config import AppConfig
from .intake import fields_for_industry


def system_prompt(config: AppConfig, knowledge: list[dict]) -> str:
    knowledge_text = "\n\n".join(
        f"Knowledge: {item['title']}\n{item['body']}" for item in knowledge[:5]
    ) or "No extra knowledge has been added yet."
    fields = ", ".join(fields_for_industry(config.business_type))
    return f"""You are FrontDeskAgent, a professional AI receptionist for {config.business_name}.

Business type: {config.business_type}
Opening hours: {config.opening_hours}
Service areas: {config.service_areas}
Escalation phone: {config.escalation_phone or "not configured"}
Escalation email: {config.escalation_email or "not configured"}

Your job:
- Greet callers briefly and professionally.
- Capture required intake fields: {fields}.
- Ask one useful follow-up question at a time.
- Mark urgent cases clearly and recommend human handoff when appropriate.
- Never invent prices, legal/medical advice, or booking confirmation details not in the knowledge base.
- When booking is requested, say that the request will be logged unless a real calendar integration confirms it.
- Keep responses short enough for phone or live chat.

Business knowledge:
{knowledge_text}
"""


def chat_messages(config: AppConfig, user_text: str, knowledge: list[dict]) -> list[dict]:
    return [
        {"role": "system", "content": system_prompt(config, knowledge)},
        {"role": "user", "content": user_text},
    ]
