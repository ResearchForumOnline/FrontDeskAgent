from __future__ import annotations

import re


URGENCY_WORDS = {
    "emergency",
    "urgent",
    "leak",
    "flood",
    "no heating",
    "locked out",
    "same day",
    "today",
    "asap",
    "complaint",
}


INDUSTRY_FIELDS = {
    "plumber": ["postcode", "problem", "water running", "access details", "preferred time"],
    "clinic": ["patient name", "contact number", "appointment type", "preferred clinician", "preferred time"],
    "education": ["student name", "course", "question", "deadline", "contact email"],
    "hotel": ["guest name", "dates", "room type", "special request", "callback number"],
    "legal": ["name", "matter type", "deadline", "conflict check notes", "callback number"],
    "general": ["name", "phone", "reason", "urgency", "preferred time"],
}


def detect_urgency(text: str) -> str:
    haystack = text.lower()
    if any(word in haystack for word in URGENCY_WORDS):
        return "urgent"
    return "normal"


def extract_contact(text: str) -> dict:
    email_match = re.search(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}", text)
    phone_match = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text)
    postcode_match = re.search(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b", text.upper())
    return {
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(0).strip() if phone_match else "",
        "postcode": postcode_match.group(0) if postcode_match else "",
    }


def fields_for_industry(industry: str) -> list[str]:
    key = industry.strip().lower()
    return INDUSTRY_FIELDS.get(key, INDUSTRY_FIELDS["general"])


def lead_summary(data: dict) -> str:
    parts = [
        f"Name: {data.get('name') or 'Unknown'}",
        f"Phone: {data.get('phone') or 'Not captured'}",
        f"Email: {data.get('email') or 'Not captured'}",
        f"Reason: {data.get('reason') or 'Not captured'}",
        f"Urgency: {data.get('urgency') or 'normal'}",
        f"Preferred time: {data.get('preferred_time') or 'Not captured'}",
        f"Postcode: {data.get('postcode') or 'Not captured'}",
    ]
    return "\n".join(parts)
