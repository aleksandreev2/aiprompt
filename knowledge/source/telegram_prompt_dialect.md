# Telegram prompt dialect — compact runtime reference

Status: **OBSERVED CORPUS PATTERNS**, not canonical Danbooru/NovelAI proof.
Source: Telegram export `Гайд тур от Ахи`, reviewed 2026-08-17.

## Why this exists

The raw corpus consistently builds images from short control atoms rather than translating the user's Russian request into descriptive English sentences. Runtime generation should imitate that *prompt structure* while keeping canonical-tag certainty separate.

## Core construction pattern

For a tag-heavy prompt, decompose the scene into independent dimensions:

`SUBJECT / RELATION -> INTERACTION ANCHORS -> POSE / ORIENTATION -> LIMB ACTION -> CAMERA -> EXPRESSION / GAZE -> CRITICAL DETAILS -> RENDER / MOTION -> ENVIRONMENT / DEPTH / LIGHT`

Do not collapse interaction + pose + camera into one prose sentence.

## Observed adult-scene co-occurrence patterns

The export contains examples where act anchors such as `anal`, `sex`, `sex from behind` are combined with separate posture/orientation controls such as `all fours`, `lying`, `on stomach`, `standing`; separate camera controls such as `from side`; and render/environment controls such as `motion lines`, `sweat`, `blurry background`, `indoors`, `on bed`.

Another observed pattern combines relation/count, view/framing, an act anchor, environment and light in the same compact prompt rather than using a sentence-like description.

These are **corpus observations only**. They may be emitted as candidate prompt atoms when semantically appropriate, but must not be labelled canonical merely because they occurred in Telegram.

## Runtime rules derived from the corpus + cleaned project guidance

- Prefer `1girl`, `1boy`, `2boys`, etc. over generic `girl`/`boy` when subject count is known.
- Do not infer an unspecified partner's gender merely from the act.
- Prefer a known/observed short act anchor over sentence prose such as `being ...` when tag-heavy mode is selected.
- Keep interaction, posture, limb placement, framing/view angle and gaze as separate controls.
- A hand/limb requirement from the user is a high-priority pose control; preserve it literally if no reliable canonical tag is known.
- Do not fill a generic anatomy bucket just because the schema has room. Add anatomy/body details only when requested or necessary to disambiguate the requested visual interaction.
- Do not auto-add `realistic`, `high detail`, `intense`, `soft lighting`, `cinematic lighting`, etc. Generic aesthetic filler is not a substitute for scene controls.
- If appearance is intentionally unspecified, do not invent hair, eyes, clothes, body type, identity or franchise.
- For a blurred outside/background request, prefer separate depth/focus controls such as `blurry background` / `depth of field` when appropriate, plus the actual environment cue.
- One dominant camera/view instruction is better than a random camera adjective.
- Rich mode means more *useful semantic dimensions*, not a wall of synonyms.
