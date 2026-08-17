# Architecture

## Goal
Natural-language visual intent in; validated NovelAI prompt structure out.

## Runtime pipeline
1. **Gradio UI** accepts free-form Russian/English intent and compiler options.
2. **Model discovery** reads the currently served LM Studio models from `/v1/models`.
3. **Knowledge selector** performs conservative local lookup and exposes only a few genuinely matched records to the LLM. It never pads the prompt with unrelated tags.
4. **LM Studio** receives a compact runtime contract plus the user's intent and returns JSON constrained by a Pydantic-derived schema.
5. **Deterministic compiler** validates every item marked as a tag against the verified CSV shards under `knowledge/tags/`.
6. Unknown tag claims are downgraded to prose and surfaced as warnings instead of being silently invented.
7. Known UC concepts emitted in positive sections are moved to UC deterministically.
8. Final Base Prompt, up to six Character Prompts, and Undesired Content are assembled locally.

## Why Gradio
The app is an AI control panel rather than a conventional website. Gradio gives us mature text inputs, controls, tabs, accordions, progress/error handling and copy actions with little frontend plumbing while keeping the project Python-first.

## Why two intelligence layers
The LLM is good at understanding intent, scene relations and natural language. Code is better at exact vocabulary, deduplication and invariants. The application deliberately does not trust the model to decide whether a string is a canonical tag.

## Performance principle
The model should interpret intent, not scan a database. Ordinary inference is capped at 512 completion tokens, the schema has hard array limits, and Gradio queues only one generation at a time. If structured output is truncated or invalid, one compact retry runs with no injected vocabulary and a 420-token budget.

## Knowledge policy
- `knowledge/tags/*.csv` is the fast production vocabulary.
- Curated references live under `knowledge/source/`.
- Raw Telegram exports stay outside the runtime repository.
- Unverified concepts may be preserved as prose, but must not be silently upgraded to canonical tags.

## Next layers
- SQLite/FTS tag index instead of linear CSV lookup.
- Alias/implication tables and explicit deprecation handling.
- Conflict matrix enforced in code.
- Character cards and presets.
- Seed-linked iteration history and Minimal Patch mode.
- Reference-image tag extraction as a separate optional module.
- Optional Tauri wrapper only after the browser/Gradio workflow stabilizes.
