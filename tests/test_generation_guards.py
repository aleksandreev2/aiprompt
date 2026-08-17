from pathlib import Path

import pytest

from backend.app.compiler import compile_plan
from backend.app.knowledge import KnowledgeBase
from backend.app.lmstudio import LMStudioClient, LMStudioInvalidJSON
from backend.app.prompting import build_system
from backend.app.schemas import ModelPlan, PromptPart

ROOT = Path(__file__).parents[1]


def test_russian_intent_does_not_pad_with_unrelated_tags():
    kb = KnowledgeBase(ROOT / "knowledge")
    intent = "девушка опирается руками к окну, за окном размыто школьный двор"
    assert kb.select_tags(intent, limit=8) == []
    system = build_system(kb, intent, 8, "balanced", True)
    assert "No local vocabulary rows lexically matched" in system
    assert "OPTIONAL MATCHED VOCABULARY" not in system
    tail = system.split("No local vocabulary rows lexically matched", 1)[1]
    assert "blue eyes" not in tail
    assert "lowres" not in tail


def test_exact_english_matches_stay_narrow():
    kb = KnowledgeBase(ROOT / "knowledge")
    tags = [r.canonical_tag for r in kb.select_tags("black hair, from below, green eyes", limit=8)]
    assert tags == ["black hair", "from below", "green eyes"]


def test_uc_concepts_are_diverted_from_positive_prompt():
    kb = KnowledgeBase(ROOT / "knowledge")
    plan = ModelPlan(
        base_parts=[
            PromptPart(text="from below", kind="tag", block="camera"),
            PromptPart(text="lowres", kind="tag", block="details"),
        ]
    )
    result = compile_plan(plan, kb, "test")
    assert "from below" in result.base_prompt
    assert "lowres" not in result.base_prompt
    assert "lowres" in result.undesired_content
    assert any("moved out of positive" in warning for warning in result.warnings)


def test_invalid_structured_content_is_classified():
    with pytest.raises(LMStudioInvalidJSON):
        LMStudioClient._decode_content('{"base_parts": [')


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
            base_parts=[PromptPart(text="indoors", kind="tag", block="scene")],
            characters=[
                {
                    "label": "Character 1",
                    "parts": [
                        {"text": "1girl", "kind": "tag", "block": "subject"},
                        {"text": "black hair", "kind": "tag", "block": "appearance"},
                    ],
                }
            ],
        )

    monkeypatch.setattr(gradio_ui.lm, "plan", fake_plan)
    result = asyncio.run(
        gradio_ui.generate_prompt(
            "девушка с черными волосами в помещении",
            "huihui-qwen3-8b-abliterated-v2",
            "Balanced — теги + prose",
            True,
            8,
        )
    )
    assert calls["n"] == 2
    assert "indoors" in result[0]
    assert "black hair" in result[2]["value"]
    assert result[-1].startswith("🟢")
