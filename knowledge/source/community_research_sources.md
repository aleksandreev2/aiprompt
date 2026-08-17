# Community research sources

This file documents external/community sources used by the local retrieval and evaluation layers. None of these sources automatically promote vocabulary to canonical Danbooru or verified NovelAI status.

## TravelingRobot / NAI_Community_Research

Source: `https://github.com/TravelingRobot/NAI_Community_Research`

Classification: **COMMUNITY_RESEARCH / HISTORICAL**.

The repository describes itself as a log/archive of personal NovelAI findings and old Discord community research. Its visible repository material is from the early NovelAI era and is not a current V4.5 image-mechanics authority. The useful transferable lesson for this project is experimental discipline: treat a community observation as a hypothesis, compare controlled variants, repeat tests, and record failures rather than promoting a result after one attractive sample.

Use for:
- methodology for A/B/regression experiments;
- provenance for historical community research practices.

Do not use for:
- current V4/V4.5 image syntax without independent verification;
- canonical Danbooru tag status;
- current sampler/model behavior.

## AI ANIME PROMPTS AND TOOLS spreadsheet

Source: `https://docs.google.com/spreadsheets/d/1YHaT_UgD1clHIkICQ1GQRir1HoUDhZ6_42PZ8782II0/edit`

Classification: **COMMUNITY_PROMPT_CORPUS / LOW-TRUST FOR CANONICALITY**.

The prompt sheet contains a large mixed corpus: useful subject/pose/camera/environment combinations coexist with duplicated quality walls, prose, Stable-Diffusion-specific syntax, malformed or legacy weighting, subjective filler, and unverified tags. It is therefore useful for retrieval of composition patterns and for negative examples in the evaluator, but it must never be treated as a canonical tag database.

Use for:
- co-occurrence/pattern mining;
- few-shot composition structure;
- identifying common prompt-bloat and mixed-syntax failure modes;
- evaluation examples.

Do not use for:
- automatic tag promotion;
- alias/deprecation claims;
- NovelAI-specific mechanics unless independently verified.

## Project Telegram corpus

Classification: **OBSERVED CORPUS / SOURCE-AWARE**.

The project Telegram export remains a high-value source for the dialect actually used by the target workflow. It supplies observed prompt construction patterns, but occurrence alone is not canonical proof. Keep general, adult-local, bot-specific and experimental evidence logically separate during retrieval.

## Authority order

1. Current official NovelAI documentation for NovelAI mechanics.
2. Primary canonical tag metadata for Danbooru/tag semantics.
3. Project verified/normalization libraries.
4. Reproducible observed generation evidence.
5. Curated community research and prompt corpora.
6. Raw community prompts as discovery-only evidence.
