from pathlib import Path

import pytest

from backend.app.compiler import compile_plan
from backend.app.knowledge import KnowledgeBase, norm
from backend.app.lmstudio import LMStudioClient, LMStudioInvalidJSON
from backend.app.prompting import build_prompt_context
from backend.app.schemas import ModelPlan

ROOT = Path(__file__).parents[1]


def test_russian_intent_retrieves_hard_requirements_and_locks():
    kb = KnowledgeBase(ROOT / "knowledge")
    intent = "девушку трахают в анус, она прижимается руками к окну, за окном размыто школьный двор"
    pack = kb.retrieve(intent, limit=8)
    required = {x.canonical for x in pack.required}
    assert "1girl" in required
    assert "anal" in required
    assert "hands pressed against window" in required
    assert "blurry background" in required
    assert "schoolyard" in required
    assert pack.locks["appearance"] == "UNSPECIFIED_DO_NOT_INVENT"
    assert pack.locks["partner_gender"] == "UNSPECIFIED_DO_NOT_INFER"
    assert pack.locks["camera"] == "UNSPECIFIED_NO_DECORATIVE_CAMERA"


def test_system_uses_compact_retrieval_pack_not_whole_corpus_dump():
    kb = KnowledgeBase(ROOT / "knowledge")
    intent = "девушка прижимает ладони к стеклу, за окном размытый школьный двор"
    system, pack = build_prompt_context(kb, intent, 8, "strict_tags", True, "rich")
    assert "RETRIEVAL / INTENT PACK" in system
    assert "REQUIRED USER CONCEPTS" in system
    assert "hands pressed against window" in system
    assert "schoolyard" in system
    assert "LOCKS:" in system
    assert "PROJECT CORPUS DIALECT" not in system
    assert len(system) < 15000
    assert pack.required


def test_observed_adult_anchor_stays_separate_from_verified_core():
    kb = KnowledgeBase(ROOT / "knowledge")
    assert kb.resolve("anal") is None
    concept = kb.resolve_concept("трахают в анус")
    assert concept is not None
    assert concept.canonical == "anal"
    assert concept.evidence == "OBSERVED_CORPUS"


def test_exact_english_verified_matches_stay_available():
    kb = KnowledgeBase(ROOT / "knowledge")
    tags = [r.canonical_tag for r in kb.select_tags("black hair, from below, green eyes", limit=8)]
    assert "black hair" in tags
    assert "from below" in tags
    assert "green eyes" in tags


def test_bad_generic_plan_is_normalized_for_window_regression():
    kb = KnowledgeBase(ROOT / "knowledge")
    intent = "девушку трахают в анус, она прижимается руками к окну, за окном размыто школьный двор"
    retrieval = kb.retrieve(intent, limit=8)
    plan = ModelPlan(
        style=["realistic"],
        subject=["girl"],
        interaction=["being fucked in the anus"],
        pose=["hands pressed against window"],
        camera=["wide angle"],
        critical_details=["female genitalia"],
        rendering=["intense", "high detail"],
        lighting=["soft lighting"],
        scene=["schoolyard"],
    )
    result = compile_plan(
        plan,
        kb,
        "test",
        intent=intent,
        retrieval=retrieval,
        mode="strict_tags",
    )
    prompt = result.base_prompt
    normalized = norm(prompt)
    assert "1girl" in normalized
    assert "anal" in normalized
    assert "hands pressed against window" in normalized
    assert "blurry background" in normalized
    assert "schoolyard" in normalized
    assert "realistic" not in normalized
    assert "wide angle" not in normalized
    assert "female genitalia" not in normalized
    assert "intense" not in normalized
    assert "high detail" not in normalized
    assert "soft lighting" not in normalized
    assert all(not item.startswith("MISS:") for item in result.coverage)


def test_uc_concepts_are_diverted_from_positive_prompt():
    kb = KnowledgeBase(ROOT / "knowledge")
    plan = ModelPlan(camera=["from below"], rendering=["lowres"])
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
