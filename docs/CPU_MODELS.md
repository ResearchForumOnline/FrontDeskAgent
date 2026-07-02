# CPU Model Guide

FrontDeskAgent can work without a model, but a small local LLM makes the receptionist more natural.

## Recommended Backend Order

1. `rules` for first boot and smoke tests.
2. `ollama` for the easiest CPU-first local model setup.
3. `llamacpp` when you already run a llama.cpp server with GGUF files.
4. `openzero` when OpenZero is the local AI bridge.
5. `openai_compat` for any compatible endpoint.

## Ollama

```bash
ollama serve
ollama pull qwen2.5:3b
```

`.env`:

```env
LLM_BACKEND=ollama
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
LLM_BACKEND=llamacpp
LLAMACPP_URL=http://127.0.0.1:8080/v1/chat/completions
OPENAI_COMPAT_MODEL=local-gguf
```

## Choosing Models

For CPU servers, start small. A useful receptionist usually needs reliable short answers more than huge reasoning depth.

- 1B to 3B models: very low-resource first tests.
- 4B to 8B models: better language quality if RAM allows.
- Quantized GGUF Q4/Q5 style files are usually the practical CPU lane.

Do not commit model files to GitHub. Keep them under `models/` or the model server's own store.
