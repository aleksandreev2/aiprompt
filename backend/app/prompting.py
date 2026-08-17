from __future__ import annotations

from .knowledge import KnowledgeBase

SYSTEM = r"""
/no_think
You are a local NovelAI Diffusion V4.5 prompt compiler.
Translate the user's visual intent into a SMALL structured prompt plan.

NON-NEGOTIABLE RULES:
- Include ONLY visual facts explicitly requested or strictly necessary to express the request.
- NEVER enumerate, summarize, or "use up" candidate vocabulary. It is a lookup aid, not a checklist.
- Do NOT invent extra hair colors, eye colors, clothes, body traits, poses, environments, defects, or styles.
- Prefer 5-12 useful controls for a simple scene. Fewer is better than unrelated filler.
- base_parts: aim for <= 10 items. Each character: aim for <= 10 items. uc_parts: aim for <= 5 items.
- A part marked kind='tag' is only a candidate claim; the application verifies it against its local database afterward.
- If a concept is nuanced or you are not confident it is a canonical tag, use kind='prose'.
- Keep blocks semantically separate: style, scene, subject, identity, appearance, outfit, expression, action, pose, camera, lighting, details.
- For multiple characters, put global scene/camera/light in base_parts and character-specific identity/appearance/action in character entries.
- Negative/undesired concepts belong ONLY in uc_parts. Never put lowres, bad quality, artistic error, jpeg artifacts, watermark, or similar defects in positive parts.
- If Add Quality Tags is ON, do not duplicate NovelAI's automatic quality preamble.
- Use weights only when explicitly useful. Default weight is 1.0.
- Do not output alternatives. Choose one coherent interpretation of the user's request.
- Return only data conforming to the requested JSON schema.
""".strip()


def build_system(
    kb: KnowledgeBase,
    intent: str,
    limit: int,
    mode: str,
    add_quality_tags: bool,
) -> str:
    records = kb.select_tags(intent, limit=limit)
    mode_note = {
        "balanced": "Use verified/common tags for precise controls; use prose for nuanced or uncertain concepts.",
        "strict_tags": "Prefer tag candidates when confident, but NEVER add a concept merely because a tag exists.",
        "prose_fallback": "Prefer natural-language prose for nuanced relations; use tags only for precise obvious controls.",
    }[mode]
    quality_note = "Add Quality Tags is ON." if add_quality_tags else "Add Quality Tags is OFF."

    if records:
        vocab = (
            "\n\nOPTIONAL MATCHED VOCABULARY — reference only; output an item only if the user requested that concept:\n"
            + kb.format_tag_context(records)
        )
    else:
        vocab = (
            "\n\nNo local vocabulary rows lexically matched the user's wording. "
            "Propose only a few obvious English NovelAI/Danbooru tag candidates; "
            "the application will verify every tag after generation."
        )

    return f"{SYSTEM}\n\nMODE: {mode_note}\n{quality_note}{vocab}"
