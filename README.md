# IMPORTANT — Windows startup

Use **`START.bat`**. It is the supported launcher. LM Studio is not required for the UI to start. If anything fails, the console stays open and the traceback is written to `logs/startup.log`.

# NovelAI Prompt Lab Local

Local **natural-language → NovelAI prompt compiler** for **LM Studio**, with a **Gradio UI** and a curated NovelAI/Danbooru knowledge base.

Describe the image in normal Russian or English, let the local LLM interpret the scene, then validate every claimed tag against the local verified database before assembling the final NovelAI prompt.

## Recommended local model for RTX 3060 Ti 8 GB

Start with **Huihui Qwen3 8B Abliterated v2 — Q4_K_M**. The app itself is model-agnostic: load any compatible chat GGUF in LM Studio and the model selector discovers it from `/v1/models`.

Suggested starting settings:

- Quant: **Q4_K_M**
- GPU offload: **Max**
- Context: **4096** for normal use; **8192** only for long/complex prompts
- Flash Attention: **On**
- Max Concurrent Predictions: **1**
- Qwen3: non-thinking mode is requested by the runtime system prompt (`/no_think`)

See [`docs/PERFORMANCE.md`](docs/PERFORMANCE.md) for the low-load profile.

## What the Gradio interface provides

- Large free-form scene/instruction field.
- Live LM Studio connection status and model discovery.
- Loaded-model diagnostics (`context`, `parallel`, Flash Attention) when LM Studio exposes them.
- `Balanced`, `Strict Tags`, and `Prose Fallback` compiler modes.
- `Add Quality Tags` awareness.
- Adjustable verified-tag retrieval budget.
- Separate **Base Prompt** and **Undesired Content** outputs.
- Up to six dynamically shown **Character Prompts**.
- Copy buttons on prompt fields.
- Validation warnings when the LLM claims an unknown tag.
- Lists of verified tags actually used and prose fallbacks.

## Run on Windows

LM Studio **does not need to be running** when the app starts. The Gradio UI is offline-first and opens independently.

Double-click:

```text
START.bat
```

The launcher creates `.venv` on first launch, installs dependencies only when they are missing, and opens the Gradio interface automatically. It uses the first free local port starting around `7860`.

You may then open LM Studio, load the GGUF, and start **Developer → Local Server** at any time. The UI polls for it every 30 seconds and can also be refreshed manually. If the server is stopped later, the Gradio app remains alive.

## Pipeline

```text
Natural-language intent
        ↓
Gradio UI
        ↓
Small local knowledge lookup
        ↓
LM Studio / OpenAI-compatible API
        ↓
Compact JSON-schema prompt plan
        ↓
Deterministic tag validator/compiler
        ↓
Base Prompt + Character Prompts + UC
```

## Why this is not just a giant system prompt

The LLM is responsible for understanding intent and relations. Exact tag validity is checked by code against `knowledge/verified_tags.csv`.

If the model returns something as `kind="tag"` but that string is absent from the verified database, the compiler automatically downgrades it to prose and exposes a warning. The model never receives the entire tag database as a checklist.

## Project layout

```text
app.py                         # compatibility entry point
launcher.py                    # robust Windows-friendly launcher
backend/app/
  gradio_ui.py                 # UI + callbacks
  lmstudio.py                  # LM Studio API client
  knowledge.py                 # local retrieval / tag lookup
  prompting.py                 # runtime system contract
  compiler.py                  # deterministic validation + assembly
  schemas.py                   # compact structured-output schema
knowledge/
  verified_tags.csv
  source/                      # curated reference material
docs/
  PERFORMANCE.md
scripts/
tests/
```

## Configuration

Copy `.env.example` to `.env` only if you need to override defaults:

```env
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_MODEL=
NAI_KNOWLEDGE_DIR=knowledge
```

Leaving `LMSTUDIO_MODEL` blank is recommended; the Gradio selector uses the chat models currently exposed by LM Studio.

## Repository policy

Raw Telegram exports stay outside the repository. Only curated/production knowledge and code are committed here.

## 4K-context / runaway-output fix

The first prototype could inject too much vocabulary and allowed **2200 completion tokens**. A small local model could start enumerating the vocabulary until it hit the hard limit, producing truncated JSON and unnecessarily running the GPU for tens of seconds.

This version:

- never pads retrieval with unrelated tags;
- defaults to only **6 exact-match vocabulary rows** at most;
- uses hard JSON-schema array caps;
- uses **512 max completion tokens** for ordinary requests (700 only for long descriptions);
- retries once with zero vocabulary and a **420-token** budget if structured output is truncated/invalid;
- moves known UC concepts out of the positive prompt deterministically;
- reports runtime failures in `logs/runtime.log` instead of calling every parse failure an offline server.

**4096 context is the recommended default for ordinary requests on 8 GB VRAM.** Use 8192 only when a long multi-character description actually needs the extra room.
