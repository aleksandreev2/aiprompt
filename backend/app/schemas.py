import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

DetailLevel = Literal["literal", "enhanced", "rich"]

_INTERNAL_BLOCKS = {
    "style",
    "subject",
    "interaction",
    "pose",
    "camera",
    "expression_gaze",
    "critical_details",
    "rendering",
    "lighting",
    "scene",
    "verified",
}
_INTERNAL_EVIDENCE_RE = re.compile(r"^[A-Z][A-Z0-9_/-]*$")
_FINAL_FILLER = {"basic view"}


def sanitize_final_prompt(value: str) -> str:
    """Remove retrieval/evidence annotations if a local model leaks them.

    Retrieval context intentionally contains diagnostic triples such as
    ``concept | pose | PROSE_RELATION``. They are useful to the model but are
    never valid final NovelAI prompt syntax. Keep this guard at the response
    boundary so neither Base Prompt nor Character Prompt can expose them.
    """
    if not value:
        return ""

    cleaned: list[str] = []
    seen: set[str] = set()
    for raw_atom in str(value).split(","):
        atom = raw_atom.strip()
        if not atom:
            continue

        parts = [part.strip() for part in atom.split("|")]
        if (
            len(parts) >= 3
            and parts[1].lower() in _INTERNAL_BLOCKS
            and _INTERNAL_EVIDENCE_RE.fullmatch(parts[2])
        ):
            atom = parts[0].strip()

        key = " ".join(atom.lower().replace("_", " ").split())
        if not key or key in _FINAL_FILLER or key in seen:
            continue
        seen.add(key)
        cleaned.append(atom)

    return ", ".join(cleaned)


class CharacterPlan(BaseModel):
    """Compact per-character plan for V4/V4.5 character prompt boxes."""

    label: str = Field(default="Character", max_length=60)
    identity_appearance: list[str] = Field(default_factory=list, max_length=12)
    outfit: list[str] = Field(default_factory=list, max_length=10)
    expression_gaze: list[str] = Field(default_factory=list, max_length=10)
    interaction: list[str] = Field(default_factory=list, max_length=12)
    pose: list[str] = Field(default_factory=list, max_length=12)
    critical_details: list[str] = Field(default_factory=list, max_length=10)


class ModelPlan(BaseModel):
    """Token-efficient semantic prompt plan.

    Each list represents a different steering dimension. Keeping interaction,
    pose, camera and details separate prevents small local models from collapsing
    a whole scene into one descriptive English sentence.
    """

    style: list[str] = Field(default_factory=list, max_length=10)
    subject: list[str] = Field(default_factory=list, max_length=8)
    interaction: list[str] = Field(default_factory=list, max_length=16)
    pose: list[str] = Field(default_factory=list, max_length=14)
    camera: list[str] = Field(default_factory=list, max_length=10)
    expression_gaze: list[str] = Field(default_factory=list, max_length=12)
    critical_details: list[str] = Field(default_factory=list, max_length=14)
    rendering: list[str] = Field(default_factory=list, max_length=12)
    lighting: list[str] = Field(default_factory=list, max_length=10)
    scene: list[str] = Field(default_factory=list, max_length=10)
    characters: list[CharacterPlan] = Field(default_factory=list, max_length=6)
    uc: list[str] = Field(default_factory=list, max_length=10)
    notes: list[str] = Field(default_factory=list, max_length=3)


class GenerateRequest(BaseModel):
    intent: str = Field(min_length=1, max_length=12000)
    model: str | None = None
    mode: Literal["balanced", "strict_tags", "prose_fallback"] = "balanced"
    detail_level: DetailLevel = "rich"
    add_quality_tags: bool = True
    max_context_tags: int = Field(default=6, ge=0, le=16)


class CompiledCharacter(BaseModel):
    label: str
    prompt: str

    @field_validator("prompt", mode="before")
    @classmethod
    def _sanitize_prompt(cls, value):
        return sanitize_final_prompt(str(value or ""))


class GenerateResponse(BaseModel):
    base_prompt: str
    characters: list[CompiledCharacter]
    undesired_content: str
    warnings: list[str]
    notes: list[str]
    verified_tags_used: list[str]
    observed_candidates: list[str] = Field(default_factory=list)
    unverified_candidates: list[str] = Field(default_factory=list)
    prose_fallbacks: list[str]
    coverage: list[str] = Field(default_factory=list)
    conflicts_removed: list[str] = Field(default_factory=list)
    model: str

    @field_validator("base_prompt", "undesired_content", mode="before")
    @classmethod
    def _sanitize_prompt_fields(cls, value):
        return sanitize_final_prompt(str(value or ""))
