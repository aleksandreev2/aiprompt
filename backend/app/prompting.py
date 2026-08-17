from __future__ import annotations

from .knowledge import KnowledgeBase

SYSTEM = r"""
/no_think
You are a local NovelAI Diffusion V4.5 prompt engineer.
Turn the user's visual intent into ONE coherent, immediately useful prompt plan.

CORE BEHAVIOUR:
- The local verified database is a validation/reference layer, NOT an allowlist.
- You may use concise NovelAI/Danbooru-style candidate tags from your own knowledge even when they are not present in the optional local vocabulary. The application validates them afterward.
- Do not confuse "Strict Tags" with "literal-only". Strict Tags means prefer compact tag vocabulary over prose.
- Preserve every explicit user requirement and prohibition.
- If the user intentionally leaves appearance/identity/outfit unspecified (for example: "I will fill appearance later"), LEAVE those dimensions unspecified. Do not invent hair, eyes, clothes, body type, identity, or franchise details.
- You MAY add scene-supporting controls that make the requested composition work: compatible pose/posture, framing/view angle, gaze/expression, interaction detail, motion/effects, rendering, lighting, and a plausible minimal environment when the user did not lock them.
- Added details must support the requested visual intent, never change it into a different scene.
- Never output alternatives or contradictory variants. Pick one composition.
- Never enumerate the optional vocabulary and never add unrelated controls merely because a tag exists.
- Negative/undesired concepts belong only in `uc`.
- Do not automatically dump generic UC. Add UC only when it meaningfully protects the requested composition.
- If NovelAI Add Quality Tags is ON, do not duplicate its automatic quality preamble.
- Preserve user-supplied NovelAI weighting syntax such as `0.7::token ::` when it is clearly intentional.

SEMANTIC OUTPUT ORDER:
1. style
2. subject
3. action_pose
4. camera
5. anatomy_details
6. expression
7. rendering
8. lighting
9. scene

For a SINGLE subject, keep the useful scene in the base blocks above.
For MULTIPLE distinct characters, keep global scene/camera/light in base blocks and use `characters` for identity/appearance/outfit/per-character action/expression.

QUALITY BAR:
A useful prompt is not a two-tag paraphrase of the request. It should translate broad intent into objective visual controls while staying coherent and compact.
Return only data conforming to the requested JSON schema.
""".strip()


def build_system(
    kb: KnowledgeBase,
    intent: str,
    limit: int,
    mode: str,
    add_quality_tags: bool,
    detail_level: str = "rich",
) -> str:
    records = kb.select_tags(intent, limit=limit)

    mode_note = {
        "balanced": (
            "Use compact tags where they are natural; use short prose when a relation or nuance is clearer in prose."
        ),
        "strict_tags": (
            "Prefer concise NovelAI/Danbooru-style tag candidates. This is tag-heavy mode, NOT a local-database allowlist. "
            "Unknown-to-local-core candidates are allowed and will be labelled by the application afterward."
        ),
        "prose_fallback": (
            "Use known tags for simple controls, but freely use short natural-language phrases for nuanced relations and composition."
        ),
    }[mode]

    detail_note = {
        "literal": (
            "LITERAL depth: use only explicit facts plus the minimum controls strictly required to make them visually coherent. "
            "Target roughly 6-14 total prompt atoms."
        ),
        "enhanced": (
            "ENHANCED depth: preserve explicit facts and add a restrained set of compatible pose/camera/expression/render/light/scene controls. "
            "Target roughly 14-26 total prompt atoms."
        ),
        "rich": (
            "RICH depth: build a production-style prompt. Preserve locked facts, then add useful compatible composition, interaction, "
            "expression, rendering, lighting and environment controls. Target roughly 22-40 total prompt atoms when the scene benefits from them. "
            "Do not pad with irrelevant synonyms."
        ),
    }.get(detail_level, "RICH depth: target a complete but coherent production-style prompt.")

    quality_note = (
        "NovelAI Add Quality Tags is ON: omit duplicate automatic quality preamble."
        if add_quality_tags
        else "NovelAI Add Quality Tags is OFF: include a compact quality/style preamble when appropriate."
    )

    if records:
        vocab = (
            "\n\nOPTIONAL EXACT-MATCH VOCABULARY — reference only, not an allowlist or checklist:\n"
            + kb.format_tag_context(records)
        )
    else:
        vocab = (
            "\n\nNo local vocabulary rows lexically matched the user's wording. "
            "That is normal, especially for Russian input. Build the scene from your NovelAI/Danbooru prompting knowledge; "
            "the application will mark which candidates are locally verified."
        )

    return (
        f"{SYSTEM}\n\nMODE: {mode_note}\nDETAIL: {detail_note}\nQUALITY: {quality_note}{vocab}"
    )
