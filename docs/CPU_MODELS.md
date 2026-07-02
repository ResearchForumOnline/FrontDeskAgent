# CPU Model Guide

FrontDeskAgent can work without a model, but a small local LLM makes the receptionist more natural. Fresh installs use `LLM_BACKEND=auto`, which tries local routes first and keeps hosted APIs optional.

## Recommended Backend Order

1. `auto` for local-first routing with a safe fallback.
2. `openzero` when you want to force a local OpenZero LLM bridge.
3. `ollama` for the easiest CPU-first local model setup.
4. `llamacpp` when you already run a llama.cpp server with GGUF files.
5. `openai_compat` for a hosted or private compatible endpoint.
6. `rules` for zero-model testing.

## Ollama

```bash
ollama serve
ollama pull qwen2.5:3b
```

`.env`:

```env
LLM_BACKEND=auto
OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:3b
```

## llama.cpp Server

Start a llama.cpp server with your chosen GGUF model:

```bash
llama-server -m ./models/model.gguf --host 127.0.0.1 --port 8080
```

`.env`:

```env
LLM_BACKEND=auto
LLAMACPP_URL=http://127.0.0.1:8080/v1/chat/completions
OPENAI_COMPAT_MODEL=local-gguf
```

## Choosing Models

For CPU servers, start small. A useful receptionist usually needs reliable short answers more than huge reasoning depth.

- 1B to 3B models: very low-resource first tests.
- 4B to 8B models: better language quality if RAM allows.
- Quantized GGUF Q4/Q5 style files are usually the practical CPU lane.

Do not commit model files to GitHub. Keep them under `models/` or the model server's own store.

See `docs/AI_ROUTING.md` for OpenZero, local model, hosted API, and no-model fallback details.
