# IMPORTANT — Windows startup

Use **`START.bat`**. LM Studio is not required for the UI to start. If startup fails, the console stays open and the traceback is written to `logs/startup.log`.

# NovelAI Prompt Lab Local

Local **natural-language → NovelAI prompt compiler** for **LM Studio**, with a **Gradio UI**, source-aware knowledge retrieval and deterministic prompt validation.

The app is designed for normal Russian or English input. The LLM is no longer expected to remember the whole NovelAI/Danbooru dialect by itself: the runtime first extracts relevant concepts, requirements, locks, rules and composition patterns, then asks the local model for a compact structured plan, and finally validates/normalizes that plan in code.

## Recommended local model for RTX 3060 Ti 8 GB

Start with **Huihui Qwen3 8B Abliterated v2 — Q4_K_M**.

Suggested starting settings:

- Quant: **Q4_K_M**
- GPU offload: **Max**
- Context: **4096** for normal use; **8192** only for genuinely long/complex inputs
- Flash Attention: **On**
- Max Concurrent Predictions: **1**
- Qwen3 non-thinking mode is requested by the runtime (`/no_think`)

See [`docs/PERFORMANCE.md`](docs/PERFORMANCE.md).

## Retrieval Engine v2

The old runtime did almost-literal English tag matching. Russian requests therefore often gave the LLM little useful context and produced generic filler such as `realistic`, `high detail`, random camera adjectives or sentence-like action prose.

The v2 runtime uses several layers:

```text
Russian / English intent
        ↓
Exact canonical lookup
        +
Multilingual aliases / normalized concepts
        +
SQLite FTS5 retrieval
        +
Relevant semantic rules
        +
2–3 source-aware construction patterns
        ↓
RETRIEVAL / INTENT PACK
        ↓
LM Studio structured JSON plan
        ↓
Deterministic compiler
        ├── requirement preservation
        ├── canonical normalization
        ├── evidence classification
        ├── generic filler filtering
        ├── random camera/anatomy filtering
        ├── conflict resolution
        └── coverage check
        ↓
Base Prompt + Character Prompts + UC
```

Explicitly matched user concepts become **hard requirements**. Unspecified appearance, outfit, style, partner gender and decorative camera choices become **locks**, so a small local model has less room to invent arbitrary details.

## Evidence classes

The app deliberately keeps different sources separate:

- **Verified** — current project fast core / official NovelAI / verified tag-source evidence.
- **Observed/community candidate** — useful corpus vocabulary or patterns, but not canonical proof.
- **Precise prose fallback** — a relation or scene concept better kept as short natural language than converted into a fake tag.
- **Unverified candidate** — emitted by the LLM without enough local evidence; shown separately in the UI.

Community frequency never automatically promotes a token into the verified core.

## Community research sources

`knowledge/source/community_research_sources.md` records the trust policy for additional research sources, including:

- `TravelingRobot/NAI_Community_Research` — used for experimental/A-B methodology, not current V4.5 mechanics.
- `AI ANIME PROMPTS AND TOOLS` spreadsheet — used as a low-trust composition/failure corpus, not a canonical tag database.
- the project Telegram corpus — used as source-aware observed prompting dialect/pattern evidence.

The raw prompt sheet is intentionally **not copied wholesale** into the repository. We keep compact normalized concepts and reusable construction patterns instead of importing its duplicated quality walls, mixed Stable-Diffusion syntax and unverified vocabulary.

## What the Gradio interface provides

- Free-form Russian/English scene input.
- Offline-first startup; LM Studio may be started later.
- Live model discovery and loaded-model diagnostics.
- `Balanced`, `Tag-heavy`, and `Prose Fallback` modes.
- `Literal`, `Enhanced`, and `Rich` depth.
- Add Quality Tags awareness.
- Adjustable **Retrieval context** budget.
- Base Prompt, UC and up to six Character Prompts.
- Validation / coverage diagnostics.
- Verified controls, observed candidates, unverified candidates and precise prose fallbacks shown separately.
- Deterministic reporting of removed filler/conflicts.

## Run on Windows

Double-click:

```text
START.bat
```

The launcher creates `.venv` on first launch, installs dependencies only when needed and opens Gradio automatically. LM Studio can be started before or after the UI.

## Project layout

```text
app.py
launcher.py
backend/app/
  gradio_ui.py                 # UI + generation pipeline
  lmstudio.py                  # OpenAI-compatible LM Studio client
  knowledge.py                 # aliases + SQLite FTS5 + evidence retrieval
  prompting.py                 # compact runtime contract + retrieval pack
  compiler.py                  # normalization/conflicts/coverage/assembly
  schemas.py                   # structured-output schema
knowledge/
  tags/                        # verified fast-core shards
  retrieval/
    concepts.csv               # multilingual concepts + evidence
    rules.csv                  # semantic/compiler rules
    examples.csv               # compact source-aware patterns
  source/                      # provenance / curated references
docs/
scripts/
tests/
```

## Performance profile

The original prototype could generate **2200 output tokens**, keeping the GPU busy for roughly forty seconds on a trivial request. The current pipeline intentionally spends more work in cheap local retrieval/code and less in autoregressive generation.

Current normal output budgets:

- **Literal:** 280 tokens
- **Enhanced:** 360 tokens
- **Rich:** 460 tokens
- one compact retry only when structured output fails

Retrieval uses local SQLite/CSV data and does **not** require a second LLM or embedding-model call by default. This keeps the RTX 3060 Ti workload concentrated into one short chat inference.

## Configuration

Optional `.env` overrides:

```env
LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1
LMSTUDIO_MODEL=
NAI_KNOWLEDGE_DIR=knowledge
```

Leaving `LMSTUDIO_MODEL` blank is recommended.

## Repository policy

Raw Telegram exports and large third-party prompt corpora stay outside the repository. Production code stores only curated/normalized knowledge, provenance and regression cases. New global rules should be accompanied by regression tests.
