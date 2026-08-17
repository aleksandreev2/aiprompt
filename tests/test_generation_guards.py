from pathlib import Path

import pytest

from backend.app.compiler import compile_plan
from backend.app.knowledge import KnowledgeBase
from backend.app.lmstudio import LMStudioClient, LMStudioInvalidJSON
from backend.app.prompting import build_system
from backend.app.schemas import ModelPlan

ROOT = Path(__file__).parents[1]


def test_russian_intent_does_not_pad_verified_lookup_with_unrelated_tags():
    kb = KnowledgeBase(ROOT / "knowledge")
    intent = "девушка опирается руками к окну, за окном размыто школьный двор"
    assert kb.select_tags(intent, limit=8) == []
    system = build_system(kb, intent, 8, "balanced", True, "rich")
    assert "No verified vocabulary rows lexically matched" in system
    assert "OPTIONAL EXACT-MATCH VERIFIED VOCABULARY" not in system
    tail = system.split("No verified vocabulary rows lexically matched", 1)[1]
    assert "blue eyes" not in tail
    assert "lowres" not in tail


def test_rich_tag_mode_loads_observed_corpus_dialect_without_making_it_canonical():
    kb = KnowledgeBase(ROOT / "knowledge")
    system = build_system(kb, "простая сцена", 0, "strict_tags", True, "rich")
    assert "PROJECT CORPUS DIALECT" in system
    assert "OBSERVED, NOT CANONICAL" in system
    assert "PROMPT ATOMS, NOT DESCRIPTIVE SENTENCES" in system
    assert "interaction" in system
    assert "BODY STATE + ORIENTATION + LIMB ACTION" in system
    assert "Do not auto-add generic anatomy" in system


def test_corpus_reference_is_separate_from_verified_database():
    kb = KnowledgeBase(ROOT / "knowledge")
    assert kb.prompt_dialect
    assert "sex from behind" in kb.prompt_dialect
    # Corpus occurrence must not silently become VERIFIED_TAG_SOURCE.
    assert kb.resolve("sex from behind") is None


def test_exact_english_verified_matches_stay_narrow():
    kb = KnowledgeBase(ROOT / "knowledge")
    tags = [r.canonical_tag for r in kb.select_tags("black hair, from below, green eyes", limit=8)]
    assert tags == ["black hair", "from below", "green eyes"]


def test_uc_concepts_are_diverted_from_positive_prompt():
    kb = KnowledgeBase(ROOT / "knowledge")
    plan = ModelPlan(
        camera=["from below"],
        rendering=["lowres"],
    )
    result = compile_plan(plan, kb, "test")
    assert "from below" in result.base_prompt
    assert "lowres" not in result.base_prompt
    assert "lowres" in result.undesired_content
    assert any("moved out of positive" in warning for warning in result.warnings)


def test_invalid_structured_content_is_classified():
    with pytest.raises(LMStudioInvalidJSON):
        LMStudioClient._decode_content('{"style": [')


def test_generate_prompt_retries_after_truncated_json(monkeypatch):
    import asyncio
    from backend.app import gradio_ui
    from backend.app.lmstudio import LMStudioTruncatedOutput

    calls = {"n": 0}

    async def fake_plan(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise LMStudioTruncatedOutput("simulated 4k context truncation")
        return ModelPlan(
            scene=["indoors"],
            characters=[
                {
                    "label": "Character 1",
                    "identity_appearance": ["1girl", "black hair"],
                }
            ],
        )

    monkeypatch.setattr(gradio_ui.lm, "plan", fake_plan)
    result = asyncio.run(
        gradio_ui.generate_prompt(
            "девушка с черными волосами в помещении",
            "huihui-qwen3-8b-abliterated-v2",
            "Tag-heavy — максимум тегов",
            "Rich — полноценный production prompt",
            True,
            8,
        )
    )
    assert calls["n"] == 2
    assert "indoors" in result[0]
    assert "black hair" in result[2]["value"]
    assert result[-1].startswith("🟢")
