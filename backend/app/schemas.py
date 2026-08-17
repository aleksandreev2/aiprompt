from typing import Literal
from pydantic import BaseModel, Field

BlockName = Literal[
    "style", "scene", "subject", "identity", "appearance", "outfit",
    "expression", "action", "pose", "camera", "lighting", "details", "other"
]


class PromptPart(BaseModel):
    text: str = Field(min_length=1, max_length=140)
    kind: Literal["tag", "prose"] = "tag"
    block: BlockName = "other"
    weight: float = Field(default=1.0, ge=-3.0, le=3.0)


class CharacterPlan(BaseModel):
    label: str = Field(default="Character", max_length=60)
    parts: list[PromptPart] = Field(default_factory=list, max_length=10)


class ModelPlan(BaseModel):
    # Hard caps prevent a local model from turning the schema into a vocabulary
    # enumeration task. Six characters remain supported, but each plan stays small.
    base_parts: list[PromptPart] = Field(default_factory=list, max_length=10)
    characters: list[CharacterPlan] = Field(default_factory=list, max_length=6)
    uc_parts: list[PromptPart] = Field(default_factory=list, max_length=4)
    notes: list[str] = Field(default_factory=list, max_length=2)


class GenerateRequest(BaseModel):
    intent: str = Field(min_length=1, max_length=12000)
    model: str | None = None
    mode: Literal["balanced", "strict_tags", "prose_fallback"] = "balanced"
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
    prose_fallbacks: list[str]
    model: str
