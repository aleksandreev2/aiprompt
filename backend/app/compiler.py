from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .knowledge import KnowledgeBase, RetrievalPack, norm, phrase_present
from .schemas import CompiledCharacter, GenerateResponse, ModelPlan

if TYPE_CHECKING:
    from collections.abc import Iterable

_WEIGHT_RE = re.compile(r"^\s*(-?(?:\d+(?:\.\d+)?|\.\d+))::\s*(.*?)\s*::\s*$", re.S)

_ALWAYS_FILLER = {
    "intense",
    "high detail",
    "highly detailed",
    "ultra detailed",
    "extremely detailed",
    "beautiful scene",
    "dynamic composition",
    "perfect anatomy",
    "masterpiece body",
    "perfect body",
}
_STYLE_FILLER = {"realistic", "photorealistic"}
_LIGHT_FILLER = {"soft lighting", "cinematic lighting", "dramatic lighting", "perfect lighting"}
_DECORATIVE_CAMERA = {"wide angle", "dynamic angle", "dutch angle", "fisheye", "fish eye"}
_GENERIC_ANATOMY = {"female genitalia", "male genitalia", "genitalia", "genitals", "detailed anatomy", "anatomy"}
_PARTNER_SPECIFIC = {"penis", "erect penis", "male genitalia"}

_CONFLICT_GROUPS = (
    ("posture", {"standing", "sitting", "lying", "kneeling"}),
    ("mouth state", {"open mouth", "closed mouth"}),
    ("view angle", {"from above", "from below", "from side", "from behind"}),
)

_CATEGORY_TO_BLOCK = {
    "style": "style",
    "subject": "subject",
    "interaction": "interaction",
    "pose": "pose",
    "camera": "camera",
    "expression_gaze": "expression_gaze",
    "critical_details": "critical_details",
    "rendering": "rendering",
    "lighting": "lighting",
    "scene": "scene",
}


def _split_weight(text: str) -> tuple[str | None, str]:
    m = _WEIGHT_RE.match(text)
    if not m:
        return None, text.strip()
    return m.group(1), m.group(2).strip()


def _render_weight(weight: str | None, text: str) -> str:
    if weight is None:
        return text
    return f"{weight}::{text} ::"


def _clean_atom(value: str) -> str:
    return str(value).strip().strip(",").strip()


def _intent_mentions(intent: str, text: str) -> bool:
    return phrase_present(intent, text)


def _should_remove_atom(
    text: str,
    *,
    intent: str,
    retrieval: RetrievalPack | None,
    positive: bool,
) -> str | None:
    if not positive:
        return None
    key = norm(text)
    if not key:
        return "empty"

    if key in _ALWAYS_FILLER and not _intent_mentions(intent, text):
        return "generic filler"

    locks = retrieval.locks if retrieval else {}
    if key in _STYLE_FILLER and locks.get("style") == "UNSPECIFIED_DO_NOT_INVENT" and not _intent_mentions(intent, text):
        return "unrequested style"
    if key in _LIGHT_FILLER and locks.get("lighting") == "UNSPECIFIED_DO_NOT_INVENT" and not _intent_mentions(intent, text):
        return "unrequested lighting"
    if key in _DECORATIVE_CAMERA and locks.get("camera") == "UNSPECIFIED_NO_DECORATIVE_CAMERA" and not _intent_mentions(intent, text):
        return "decorative camera invention"
    if key in _GENERIC_ANATOMY and not _intent_mentions(intent, text):
        return "generic anatomy filler"
    if key in _PARTNER_SPECIFIC and locks.get("partner_gender") == "UNSPECIFIED_DO_NOT_INFER" and not _intent_mentions(intent, text):
        return "partner-specific anatomy inferred from an unspecified partner"
    return None


def _classify_record(kb: KnowledgeBase, lookup: str) -> tuple[str, str, str] | None:
    """Return (canonical, class, evidence), where class is verified/observed/prose."""
    tag = kb.resolve(lookup)
    if tag is not None:
        return tag.canonical_tag, "verified", tag.evidence_type

    concept = kb.resolve_concept(lookup)
    if concept is None:
        return None

    canonical_tag = kb.resolve(concept.canonical)
    if canonical_tag is not None:
        return canonical_tag.canonical_tag, "verified", canonical_tag.evidence_type

    evidence = concept.evidence.upper()
    if evidence.startswith("VERIFIED") or evidence.startswith("DOCUMENTED") or evidence.startswith("NAI_"):
        return concept.canonical, "verified", concept.evidence
    if evidence.startswith("PROSE"):
        return concept.canonical, "prose", concept.evidence
    if "OBSERVED" in evidence or "COMMUNITY" in evidence or "EXPERIMENTAL" in evidence:
        return concept.canonical, "observed", concept.evidence
    return concept.canonical, "unknown", concept.evidence


def _represented(kb: KnowledgeBase, atoms: list[str], canonical: str) -> bool:
    target = norm(canonical)
    for raw in atoms:
        _, inner = _split_weight(_clean_atom(raw))
        if not inner:
            continue
        if norm(inner) == target or phrase_present(inner, canonical):
            return True
        concept = kb.resolve_concept(inner)
        if concept is not None and norm(concept.canonical) == target:
            return True
        tag = kb.resolve(inner)
        if tag is not None and norm(tag.canonical_tag) == target:
            return True
    return False


def _base_blocks(plan: ModelPlan) -> dict[str, list[str]]:
    return {
        "style": list(plan.style),
        "subject": list(plan.subject),
        "interaction": list(plan.interaction),
        "pose": list(plan.pose),
        "camera": list(plan.camera),
        "expression_gaze": list(plan.expression_gaze),
        "critical_details": list(plan.critical_details),
        "rendering": list(plan.rendering),
        "lighting": list(plan.lighting),
        "scene": list(plan.scene),
    }


def _inject_required(
    blocks: dict[str, list[str]],
    kb: KnowledgeBase,
    retrieval: RetrievalPack | None,
) -> None:
    if retrieval is None:
        return
    all_atoms = [x for values in blocks.values() for x in values]
    for item in retrieval.required:
        block = _CATEGORY_TO_BLOCK.get(item.category)
        if block is None:
            continue
        if _represented(kb, all_atoms, item.canonical):
            continue
        blocks[block].append(item.canonical)
        all_atoms.append(item.canonical)


def _flatten_blocks(blocks: dict[str, list[str]]) -> list[str]:
    return [
        *blocks["style"],
        *blocks["subject"],
        *blocks["interaction"],
        *blocks["pose"],
        *blocks["camera"],
        *blocks["expression_gaze"],
        *blocks["critical_details"],
        *blocks["rendering"],
        *blocks["lighting"],
        *blocks["scene"],
    ]


def validate_atoms(
    atoms: list[str],
    kb: KnowledgeBase,
    warnings: list[str],
    used: list[str],
    observed: list[str],
    unknown: list[str],
    fallbacks: list[str],
    removed: list[str],
    *,
    positive: bool,
    diverted_uc: list[str],
    intent: str = "",
    retrieval: RetrievalPack | None = None,
    mode: str = "balanced",
) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    for raw in atoms:
        text = _clean_atom(raw)
        if not text:
            continue

        weight, inner = _split_weight(text)
        lookup = inner if weight is not None else text

        removal_reason = _should_remove_atom(
            lookup,
            intent=intent,
            retrieval=retrieval,
            positive=positive,
        )
        if removal_reason:
            removed.append(text)
            warnings.append(f"Removed {removal_reason}: {text}")
            continue

        classified = _classify_record(kb, lookup)
        if classified is not None:
            canonical, cls, _evidence = classified
            rendered = _render_weight(weight, canonical)
            key = norm(canonical)

            tag = kb.resolve(canonical)
            if positive and tag is not None and kb.is_uc_record(tag):
                warnings.append(f"UC concept moved out of positive prompt: {canonical}")
                diverted_uc.append(rendered)
                continue

            if cls == "verified":
                used.append(canonical)
            elif cls == "observed":
                observed.append(canonical)
            elif cls == "prose":
                fallbacks.append(canonical)
            else:
                unknown.append(canonical)
        else:
            rendered = text
            key = norm(inner if weight is not None else text)
            word_count = len(key.split())
            if mode == "prose_fallback" or word_count >= 4:
                fallbacks.append(text)
            else:
                unknown.append(text)

        if not key or key in seen:
            continue
        seen.add(key)
        out.append(rendered)

    return out


def _required_keys(retrieval: RetrievalPack | None) -> set[str]:
    if retrieval is None:
        return set()
    return {norm(x.canonical) for x in retrieval.required}


def _resolve_conflicts(
    items: list[str],
    retrieval: RetrievalPack | None,
    warnings: list[str],
    removed: list[str],
) -> list[str]:
    out = list(items)
    required = _required_keys(retrieval)

    for label, group in _CONFLICT_GROUPS:
        matches: list[tuple[int, str]] = []
        for idx, item in enumerate(out):
            _, inner = _split_weight(item)
            key = norm(inner)
            if key in group:
                matches.append((idx, key))
        if len(matches) <= 1:
            continue

        preferred_idx = next((idx for idx, key in matches if key in required), matches[0][0])
        remove_indexes = {idx for idx, _ in matches if idx != preferred_idx}
        removed_values = [out[idx] for idx in sorted(remove_indexes)]
        if removed_values:
            warnings.append(
                f"Resolved conflicting {label}: kept {out[preferred_idx]}; removed {', '.join(removed_values)}"
            )
            removed.extend(removed_values)
            out = [item for idx, item in enumerate(out) if idx not in remove_indexes]

    return out


def _dedupe_strings(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        _, inner = _split_weight(item)
        key = norm(inner)
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _character_atoms(char) -> list[str]:
    return [
        *char.identity_appearance,
        *char.outfit,
        *char.expression_gaze,
        *char.interaction,
        *char.pose,
        *char.critical_details,
    ]


def _coverage(
    retrieval: RetrievalPack | None,
    base: list[str],
    chars: list[CompiledCharacter],
) -> tuple[list[str], list[str]]:
    if retrieval is None or not retrieval.required:
        return [], []
    joined = ", ".join(base + [char.prompt for char in chars])
    coverage: list[str] = []
    missing: list[str] = []
    for item in retrieval.required:
        if phrase_present(joined, item.canonical):
            coverage.append(f"OK: {item.canonical}")
        else:
            coverage.append(f"MISS: {item.canonical}")
            missing.append(item.canonical)
    return coverage, missing


def compile_plan(
    plan: ModelPlan,
    kb: KnowledgeBase,
    model: str,
    *,
    intent: str = "",
    retrieval: RetrievalPack | None = None,
    mode: str = "balanced",
) -> GenerateResponse:
    warnings: list[str] = []
    used: list[str] = []
    observed: list[str] = []
    unknown: list[str] = []
    fallbacks: list[str] = []
    removed: list[str] = []
    diverted_uc: list[str] = []

    blocks = _base_blocks(plan)
    _inject_required(blocks, kb, retrieval)

    base = validate_atoms(
        _flatten_blocks(blocks),
        kb,
        warnings,
        used,
        observed,
        unknown,
        fallbacks,
        removed,
        positive=True,
        diverted_uc=diverted_uc,
        intent=intent,
        retrieval=retrieval,
        mode=mode,
    )
    base = _resolve_conflicts(base, retrieval, warnings, removed)
    base = _dedupe_strings(base)

    chars: list[CompiledCharacter] = []
    for char in plan.characters:
        parts = validate_atoms(
            _character_atoms(char),
            kb,
            warnings,
            used,
            observed,
            unknown,
            fallbacks,
            removed,
            positive=True,
            diverted_uc=diverted_uc,
            intent=intent,
            retrieval=retrieval,
            mode=mode,
        )
        parts = _resolve_conflicts(parts, retrieval, warnings, removed)
        prompt = ", ".join(_dedupe_strings(parts))
        if prompt:
            chars.append(
                CompiledCharacter(
                    label=char.label.strip() or "Character",
                    prompt=prompt,
                )
            )

    uc = validate_atoms(
        plan.uc,
        kb,
        warnings,
        used,
        observed,
        unknown,
        fallbacks,
        removed,
        positive=False,
        diverted_uc=diverted_uc,
        intent=intent,
        retrieval=retrieval,
        mode=mode,
    )
    uc = _dedupe_strings(uc + diverted_uc)

    coverage, missing = _coverage(retrieval, base, chars)
    if missing:
        warnings.append("Missing required user concepts after compilation: " + ", ".join(missing))

    return GenerateResponse(
        base_prompt=", ".join(base),
        characters=chars,
        undesired_content=", ".join(uc),
        warnings=list(dict.fromkeys(warnings)),
        notes=plan.notes,
        verified_tags_used=list(dict.fromkeys(used)),
        observed_candidates=list(dict.fromkeys(observed)),
        unverified_candidates=list(dict.fromkeys(unknown)),
        prose_fallbacks=list(dict.fromkeys(fallbacks)),
        coverage=coverage,
        conflicts_removed=list(dict.fromkeys(removed)),
        model=model,
    )
