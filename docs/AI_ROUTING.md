# AI Routing

FrontDeskAgent is local-first by default. A fresh install uses:

```env
LLM_BACKEND=auto
```

`auto` mode keeps the system usable on normal CPU servers and avoids forcing a paid API key. It tries routes in this order:

1. `OPENZERO_LLM_URL` for a local OpenZero LLM bridge.
2. `OLLAMA_URL` and `OLLAMA_MODEL` for an Ollama CPU model.
3. `LLAMACPP_URL` for a local llama.cpp server with GGUF models.
4. `OPENAI_COMPAT_URL`, `OPENAI_COMPAT_API_KEY`, and `OPENAI_COMPAT_MODEL` for an optional hosted API fallback.
5. Built-in rules mode when no model route is available.

The dashboard and `/api/healthz` show the active route status.

## Recommended Local Path

Install Ollama on the same machine or a LAN host:

```bash
ollama serve
ollama pull qwen2.5:3b
```

Then keep:

```env
LLM_BACKEND=auto
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

Small 3B to 9B instruct models are the right starting point for CPU-only servers. Larger models can work on stronger machines, but front desk routing should stay fast and reliable.

## OpenZero Local Route

When OpenZero exposes an OpenAI-compatible local endpoint:

```env
LLM_BACKEND=auto
OPENZERO_LLM_URL=http://127.0.0.1:1024/v1/chat/completions
OPENZERO_MODEL=local
OPENZERO_API_KEY=
```

FrontDeskAgent checks that local endpoint first. If it is not reachable, it moves to Ollama, llama.cpp, optional hosted API, and then rules mode.

## llama.cpp GGUF Route

Run a llama.cpp OpenAI-compatible server, then set:

```env
LLM_BACKEND=auto
LLAMACPP_URL=http://127.0.0.1:8080/v1/chat/completions
OPENAI_COMPAT_MODEL=qwen-local
```

Use quantized GGUF models that fit your server RAM. Keep response speed more important than model size for receptionist work.

## Optional Hosted API Fallback

Hosted APIs should be secondary, not mandatory. Configure them only when you want a paid fallback:

```env
LLM_BACKEND=auto
OPENAI_COMPAT_URL=https://api.openai.com/v1/chat/completions
OPENAI_COMPAT_API_KEY=sk-your-key
OPENAI_COMPAT_MODEL=gpt-5.5
```

Any OpenAI-compatible provider can be used with the same three variables. Check provider pricing, privacy terms, rate limits, and model availability before production use.

## No-Model Fallback

If every model route is unavailable, FrontDeskAgent still returns a safe receptionist reply. The fallback can:

- Detect urgent wording.
- Ask for name, phone, location, reason, and preferred callback time.
- Recognise booking or appointment intent.
- Capture enough context for a staff handoff.

This keeps the front desk alive during setup, provider outages, local model restarts, or low-resource deployments.
