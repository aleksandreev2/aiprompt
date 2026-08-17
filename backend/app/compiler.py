from __future__ import annotations

import re

from .knowledge import KnowledgeBase, norm
from .schemas import CompiledCharacter, GenerateResponse, ModelPlan

_WEIGHT_RE = re.compile(r"^\s*(-?(?:\d+(?:\.\d+)?|\.\d+))::\s*(.*?)\s*::\s*$", re.S)


def _split_weight(text: str) -> tuple[str | None, str]:
    """Return (weight_text, inner_text) for NovelAI numeric emphasis."""
    m = _WEIGHT_RE.match(text)
    if not m:
        return None, text.strip()
    return m.group(1), m.group(2).strip()


def _render_weight(weight: str | None, text: str) -> str:
    if weight is None:
        return text
    return f"{weight}::{text} ::"


def _clean_atom(value: str) -> str:
    return value.strip().strip(",").strip()


def validate_atoms(
    atoms: list[str],
    kb: KnowledgeBase,
    warnings: list[str],
    used: list[str],
    fallbacks: list[str],
    *,
    positive: bool,
    diverted_uc: list[str],
) -> list[str]:
    """Validate what we can without turning the fast verified core into an allowlist."""
    out: list[str] = []
    seen: set[str] = set()

    for raw in atoms:
        text = _clean_atom(str(raw))
        if not text:
            continue

        weight, inner = _split_weight(text)
        lookup = inner if weight is not None else text
        rec = kb.resolve(lookup)

        if rec is not None:
            canonical = rec.canonical_tag
            rendered = _render_weight(weight, canonical)
            key = norm(canonical)

            if positive and kb.is_uc_record(rec):
                warnings.append(f"UC concept moved out of positive prompt: {canonical}")
                diverted_uc.append(rendered)
                continue

            used.append(canonical)
        else:
            rendered = text
            key = norm(inner if weight is not None else text)
            fallbacks.append(text)

        if not key or key in seen:
            continue
        seen.add(key)
        out.append(rendered)

    return out


def _dedupe_strings(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        weight, inner = _split_weight(item)
        key = norm(inner if weight is not None else item)
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _base_atoms(plan: ModelPlan) -> list[str]:
    # Production order intentionally keeps different steering dimensions visible:
    # style/quality -> subject -> interaction -> posture/limbs -> camera -> gaze/
    # expression -> only critical details -> render/effects -> light -> environment.
    return [
        *plan.style,
        *plan.subject,
        *plan.interaction,
        *plan.pose,
        *plan.camera,
        *plan.expression_gaze,
        *plan.critical_details,
        *plan.rendering,
        *plan.lighting,
        *plan.scene,
    ]


def _character_atoms(char) -> list[str]:
    return [
        *char.identity_appearance,
        *char.outfit,
        *char.expression_gaze,
        *char.interaction,
        *char.pose,
        *char.critical_details,
    ]


def compile_plan(plan: ModelPlan, kb: KnowledgeBase, model: str) -> GenerateResponse:
    warnings: list[str] = []
    used: list[str] = []
    fallbacks: list[str] = []
    diverted_uc: list[str] = []

    base = validate_atoms(
        _base_atoms(plan), kb, warnings, used, fallbacks,
        positive=True, diverted_uc=diverted_uc,
    )

    chars: list[CompiledCharacter] = []
    for char in plan.characters:
        parts = validate_atoms(
            _character_atoms(char), kb, warnings, used, fallbacks,
            positive=True, diverted_uc=diverted_uc,
        )
        prompt = ", ".join(parts)
        if prompt:
            chars.append(
                CompiledCharacter(
                    label=char.label.strip() or "Character",
                    prompt=prompt,
                )
            )

    uc = validate_atoms(
        plan.uc, kb, warnings, used, fallbacks,
        positive=False, diverted_uc=diverted_uc,
    )
    uc = _dedupe_strings(uc + diverted_uc)

    return GenerateResponse(
        base_prompt=", ".join(_dedupe_strings(base)),
        characters=chars,
        undesired_content=", ".join(uc),
        warnings=list(dict.fromkeys(warnings)),
        notes=plan.notes,
        verified_tags_used=list(dict.fromkeys(used)),
        prose_fallbacks=list(dict.fromkeys(fallbacks)),
        model=model,
    )
