from typing import Literal
from pydantic import BaseModel, Field

DetailLevel = Literal["literal", "enhanced", "rich"]


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
