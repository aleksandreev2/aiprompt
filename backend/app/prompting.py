from __future__ import annotations

from .knowledge import KnowledgeBase, RetrievalPack

SYSTEM = r"""
/no_think
You are a local NovelAI Diffusion V4.5 prompt compiler.
Convert the user's visual intent into ONE coherent, compact prompt plan.

NON-NEGOTIABLE:
- REQUIRED USER CONCEPTS from the retrieval pack are hard requirements. Preserve them.
- LOCKS are constraints. `UNSPECIFIED_DO_NOT_INVENT` means do not fill that dimension.
- `UNSPECIFIED_NO_DECORATIVE_CAMERA` means do not add wide-angle/fisheye/dutch/dynamic-angle decoration. Add a basic view only when truly necessary to make the requested spatial relation legible.
- `UNSPECIFIED_DO_NOT_INFER` means do not infer a partner's gender/identity.
- Suggested controls and construction patterns are optional context, never a checklist.
- Evidence labels matter: community/observed/prose items are useful candidates but are not canonical proof.
- Never emit alternatives or contradictory variants.
- Negative/undesired concepts belong only in `uc`.
- If NovelAI Add Quality Tags is ON, do not duplicate the automatic quality preamble.

PROMPT LANGUAGE:
- In Tag-heavy mode, output PROMPT ATOMS, not descriptive English sentences.
- Prefer compact known/observed controls such as `1girl`, `from side`, `blurry background` over sentence prose.
- When a required spatial/limb relation has no reliable compact tag, use ONE short precise prose atom.
- Do not invent pseudo-tags merely to avoid prose.
- Never pad with `intense`, `high detail`, `beautiful scene`, `perfect anatomy`, `dynamic composition`, or unrequested `realistic`/`soft lighting`.
- Do not fill generic anatomy merely because the schema has a details block.

SEMANTIC DECOMPOSITION:
1. style — only requested quality/style/mesh controls
2. subject — count/type/relation
3. interaction — actual action/interaction anchors
4. pose — body state + orientation + limb relation
5. camera — framing + at most one dominant compatible view angle
6. expression_gaze — expression, mouth/eye state, gaze
7. critical_details — only details necessary for the requested visual result
8. rendering — focus/depth/motion/material/effects
9. lighting — small purposeful light set
10. scene — location/background/time/object cues

Keep interaction, pose, camera, gaze and rendering as separate dimensions.
For multiple distinct characters, keep global scene/camera/light in base blocks and use character blocks for character-specific identity/outfit/action when useful.
Rich means semantic coverage, not synonym count. Every emitted atom must have a job.

Return only data conforming to the requested JSON schema.
""".strip()


def build_prompt_context(
    kb: KnowledgeBase,
    intent: str,
    limit: int,
    mode: str,
    add_quality_tags: bool,
    detail_level: str = "rich",
) -> tuple[str, RetrievalPack]:
    pack = kb.retrieve(intent, limit=max(4, min(int(limit), 16)))

    mode_note = {
        "balanced": (
            "Use compact tags where natural; use a short precise prose atom for nuanced relations when that is more faithful."
        ),
        "strict_tags": (
            "Prefer concise NovelAI/Danbooru-style atoms. Sentence grammar is a fallback, not the default. "
            "Unknown-to-fast-core candidates are allowed when supported by the retrieval pack or are necessary precise prose."
        ),
        "prose_fallback": (
            "Use known tags for simple controls; short natural-language atoms are allowed for nuanced relations. "
            "Still avoid full descriptive sentences."
        ),
    }[mode]

    detail_note = {
        "literal": (
            "LITERAL: explicit facts plus only the minimum controls needed for visual coherence. Do not beautify or reinterpret."
        ),
        "enhanced": (
            "ENHANCED: preserve explicit facts and add only restrained compatible controls that improve spatial clarity."
        ),
        "rich": (
            "RICH: production-style semantic coverage, usually 12-28 useful atoms, but stop as soon as the requested scene is controlled. "
            "Do not invent locked dimensions and do not pad to a quota."
        ),
    }.get(detail_level, "Build a complete but non-padded production prompt.")

    quality_note = (
        "NovelAI Add Quality Tags is ON: omit duplicate automatic quality preamble."
        if add_quality_tags
        else "NovelAI Add Quality Tags is OFF: a compact quality/style preamble is allowed when appropriate."
    )

    return (
        f"{SYSTEM}\n\nMODE: {mode_note}\nDETAIL: {detail_note}\nQUALITY: {quality_note}\n\n"
        + pack.format_for_model(),
        pack,
    )


def build_system(
    kb: KnowledgeBase,
    intent: str,
    limit: int,
    mode: str,
    add_quality_tags: bool,
    detail_level: str = "rich",
) -> str:
    system, _ = build_prompt_context(
        kb,
        intent,
        limit,
        mode,
        add_quality_tags,
        detail_level,
    )
    return system
