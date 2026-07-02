from __future__ import annotations

import json
from typing import Protocol
from urllib.parse import urlparse

import requests

from .config import AppConfig
from .intake import detect_urgency
from .prompts import chat_messages


class LLMClient(Protocol):
    def reply(self, user_text: str, knowledge: list[dict]) -> str:
        ...


class RuleBasedClient:
    def __init__(self, config: AppConfig):
        self.config = config

    def reply(self, user_text: str, knowledge: list[dict]) -> str:
        urgency = detect_urgency(user_text)
        greeting = f"Thanks for contacting {self.config.business_name}."
        if urgency == "urgent":
            return (
                f"{greeting} This sounds urgent, so I will capture the key details for fast handoff. "
                "Please send your name, best phone number, location or postcode, and what is happening right now."
            )
        if "book" in user_text.lower() or "appointment" in user_text.lower():
            return (
                f"{greeting} I can log an appointment request. What day or time works best, "
                "and what should the team prepare for?"
            )
        if knowledge:
            return (
                f"{greeting} I found relevant business notes. Please share your name, phone number, "
                "reason for contacting us, and your preferred time for a reply."
            )
        return (
            f"{greeting} I can help capture the enquiry and route it to the right person. "
            "What is your name, best contact number, and what do you need help with?"
        )


class OllamaClient:
    def __init__(self, config: AppConfig, timeout_seconds: int | None = None):
        self.config = config
        self.timeout_seconds = timeout_seconds or config.llm_timeout_seconds

    def reply(self, user_text: str, knowledge: list[dict]) -> str:
        messages = chat_messages(self.config, user_text, knowledge)
        response = requests.post(
            f"{self.config.ollama_url}/api/chat",
            json={"model": self.config.ollama_model, "messages": messages, "stream": False},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "").strip() or RuleBasedClient(self.config).reply(user_text, knowledge)


class OpenAICompatibleClient:
    def __init__(self, config: AppConfig, url: str, model: str, api_key: str = "", timeout_seconds: int | None = None):
        self.config = config
        self.url = url
        self.model = model or "local"
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds or config.llm_timeout_seconds

    def reply(self, user_text: str, knowledge: list[dict]) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = requests.post(
            self.url,
            headers=headers,
            json={"model": self.model, "messages": chat_messages(self.config, user_text, knowledge), "temperature": 0.3},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "").strip() or RuleBasedClient(self.config).reply(user_text, knowledge)


class AutoRouterClient:
    """Prefer self-hosted AI routes and keep paid APIs as an explicit fallback."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.local_timeout_seconds = max(2, min(config.llm_timeout_seconds, 8))
        self.api_timeout_seconds = max(4, min(config.llm_timeout_seconds, 18))

    def reply(self, user_text: str, knowledge: list[dict]) -> str:
        for _name, client in self._clients():
            try:
                return client.reply(user_text, knowledge)
            except Exception:
                continue
        return RuleBasedClient(self.config).reply(user_text, knowledge)

    def _clients(self) -> list[tuple[str, LLMClient]]:
        clients: list[tuple[str, LLMClient]] = []
        if self.config.openzero_llm_url and _endpoint_reachable(self.config.openzero_llm_url):
            clients.append(
                (
                    "openzero",
                    OpenAICompatibleClient(
                        self.config,
                        self.config.openzero_llm_url,
                        self.config.openzero_model,
                        self.config.openzero_api_key,
                        self.local_timeout_seconds,
                    ),
                )
            )
        if self.config.ollama_url and _ollama_reachable(self.config.ollama_url):
            clients.append(("ollama", OllamaClient(self.config, self.local_timeout_seconds)))
        if self.config.llamacpp_url and _endpoint_reachable(self.config.llamacpp_url):
            clients.append(
                (
                    "llamacpp",
                    OpenAICompatibleClient(
                        self.config,
                        self.config.llamacpp_url,
                        self.config.openai_compat_model or self.config.ollama_model,
                        timeout_seconds=self.local_timeout_seconds,
                    ),
                )
            )
        if self.config.openai_compat_url and self.config.openai_compat_model:
            clients.append(
                (
                    "openai_compat",
                    OpenAICompatibleClient(
                        self.config,
                        self.config.openai_compat_url,
                        self.config.openai_compat_model,
                        self.config.openai_compat_api_key,
                        self.api_timeout_seconds,
                    ),
                )
            )
        clients.append(("rules", RuleBasedClient(self.config)))
        return clients


def build_client(config: AppConfig) -> LLMClient:
    if config.llm_backend == "auto":
        return AutoRouterClient(config)
    if config.llm_backend == "ollama":
        return OllamaClient(config)
    if config.llm_backend == "llamacpp":
        return OpenAICompatibleClient(config, config.llamacpp_url, config.openai_compat_model or config.ollama_model)
    if config.llm_backend == "openai_compat":
        return OpenAICompatibleClient(
            config,
            config.openai_compat_url,
            config.openai_compat_model,
            config.openai_compat_api_key,
        )
    if config.llm_backend == "openzero":
        return OpenAICompatibleClient(config, config.openzero_llm_url, config.openzero_model, config.openzero_api_key)
    return RuleBasedClient(config)


def safe_reply(client: LLMClient, config: AppConfig, user_text: str, knowledge: list[dict]) -> tuple[str, str | None]:
    try:
        return client.reply(user_text, knowledge), None
    except Exception as exc:
        fallback = RuleBasedClient(config).reply(user_text, knowledge)
        return fallback, f"{type(exc).__name__}: {exc}"


def model_status(config: AppConfig) -> dict:
    if config.llm_backend == "auto":
        routes = [
            _route_status("openzero", config.openzero_llm_url, "local OpenZero LLM bridge"),
            _route_status("ollama", f"{config.ollama_url}/api/tags", f"Ollama model {config.ollama_model}"),
            _route_status("llamacpp", config.llamacpp_url, "local llama.cpp OpenAI-compatible server"),
            {
                "backend": "openai_compat",
                "ok": bool(config.openai_compat_url and config.openai_compat_model),
                "detail": "configured hosted/API fallback" if config.openai_compat_url and config.openai_compat_model else "not configured",
            },
            {"backend": "rules", "ok": True, "detail": "built-in no-model fallback"},
        ]
        ready = next((route["backend"] for route in routes if route["ok"]), "rules")
        return {"backend": "auto", "ok": True, "detail": f"Ready route: {ready}", "routes": routes}
    if config.llm_backend == "ollama":
        try:
            response = requests.get(f"{config.ollama_url}/api/tags", timeout=3)
            return {"backend": "ollama", "ok": response.ok, "detail": response.text[:300]}
        except Exception as exc:
            return {"backend": "ollama", "ok": False, "detail": str(exc)}
    if config.llm_backend in {"llamacpp", "openai_compat", "openzero"}:
        return {"backend": config.llm_backend, "ok": True, "detail": "OpenAI-compatible endpoint configured"}
    return {"backend": "rules", "ok": True, "detail": "No model required"}


def compact_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=True, sort_keys=True)


def _endpoint_reachable(url: str) -> bool:
    root = _root_url(url)
    if not root:
        return False
    try:
        response = requests.get(root, timeout=1.5)
        return response.status_code < 500
    except Exception:
        return False


def _ollama_reachable(url: str) -> bool:
    try:
        response = requests.get(f"{url.rstrip('/')}/api/tags", timeout=1.5)
        return response.ok
    except Exception:
        return False


def _route_status(name: str, url: str, detail: str) -> dict:
    if not url:
        return {"backend": name, "ok": False, "detail": "not configured"}
    ok = _ollama_reachable(url.removesuffix("/api/tags")) if name == "ollama" else _endpoint_reachable(url)
    return {"backend": name, "ok": ok, "detail": detail if ok else "not reachable yet"}


def _root_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"
