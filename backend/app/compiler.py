from __future__ import annotations

from .knowledge import KnowledgeBase, norm
from .schemas import CompiledCharacter, GenerateResponse, ModelPlan, PromptPart


def render_part(part: PromptPart) -> str:
    text = part.text.strip()
    if not text:
        return ""
    if abs(part.weight - 1.0) < 0.001:
        return text
    return f"{part.weight:g}::{text} ::"


def validate_parts(
    parts: list[PromptPart],
    kb: KnowledgeBase,
    warnings: list[str],
    used: list[str],
    prose: list[str],
    *,
    positive: bool,
    diverted_uc: list[PromptPart],
) -> list[PromptPart]:
    out: list[PromptPart] = []
    seen: set[tuple[str, str]] = set()

    for part in parts:
        text = part.text.strip().strip(",")
        if not text:
            continue

        if part.kind == "tag":
            rec = kb.resolve(text)
            if rec is None:
                warnings.append(f"Unknown tag converted to prose: {text}")
                part = part.model_copy(update={"text": text, "kind": "prose", "weight": 1.0})
                prose.append(text)
            else:
                part = part.model_copy(update={"text": rec.canonical_tag})
                if positive and kb.is_uc_record(rec):
                    warnings.append(f"UC concept moved out of positive prompt: {rec.canonical_tag}")
                    diverted_uc.append(part.model_copy(update={"weight": 1.0}))
                    continue
                used.append(rec.canonical_tag)
        else:
            prose.append(text)

        key = (part.kind, norm(part.text))
        if key in seen:
            continue
        seen.add(key)
        out.append(part)

    return out


def _dedupe_parts(parts: list[PromptPart]) -> list[PromptPart]:
    out: list[PromptPart] = []
    seen: set[tuple[str, str]] = set()
    for p in parts:
        key = (p.kind, norm(p.text))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def compile_plan(plan: ModelPlan, kb: KnowledgeBase, model: str) -> GenerateResponse:
    warnings: list[str] = []
    used: list[str] = []
    prose: list[str] = []
    diverted_uc: list[PromptPart] = []

    base = validate_parts(
        plan.base_parts, kb, warnings, used, prose,
        positive=True, diverted_uc=diverted_uc,
    )

    chars: list[CompiledCharacter] = []
    for char in plan.characters:
        parts = validate_parts(
            char.parts, kb, warnings, used, prose,
            positive=True, diverted_uc=diverted_uc,
        )
        prompt = ", ".join(filter(None, (render_part(p) for p in parts)))
        if prompt:
            chars.append(CompiledCharacter(label=char.label, prompt=prompt))

    uc = validate_parts(
        plan.uc_parts, kb, warnings, used, prose,
        positive=False, diverted_uc=diverted_uc,
    )
    uc = _dedupe_parts(uc + diverted_uc)

    return GenerateResponse(
        base_prompt=", ".join(filter(None, (render_part(p) for p in base))),
        characters=chars,
        undesired_content=", ".join(filter(None, (render_part(p) for p in uc))),
        warnings=list(dict.fromkeys(warnings)),
        notes=plan.notes,
        verified_tags_used=list(dict.fromkeys(used)),
        prose_fallbacks=list(dict.fromkeys(prose)),
        model=model,
    )
