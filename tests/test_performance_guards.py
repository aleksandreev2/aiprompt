import asyncio

from backend.app import gradio_ui
from backend.app.lmstudio import LMStudioClient
from backend.app.schemas import ModelPlan


def test_schema_stays_compact_but_allows_rich_prompts():
    schema = ModelPlan.model_json_schema()
    assert schema["properties"]["style"]["maxItems"] == 10
    assert schema["properties"]["action_pose"]["maxItems"] == 16
    assert schema["properties"]["anatomy_details"]["maxItems"] == 16
    assert schema["properties"]["uc"]["maxItems"] == 10
    assert schema["$defs"]["CharacterPlan"]["properties"]["action_pose"]["maxItems"] == 14


def test_request_defaults_are_low_cost():
    import inspect
    sig = inspect.signature(LMStudioClient.plan)
    assert sig.parameters["max_tokens"].default == 512
    assert sig.parameters["temperature"].default == 0.30


def test_simple_rich_ui_generation_uses_520_budget(monkeypatch):
    seen = {}

    async def fake_plan(**kwargs):
        seen.update(kwargs)
        return ModelPlan(scene=["indoors"])

    monkeypatch.setattr(gradio_ui.lm, "plan", fake_plan)
    result = asyncio.run(gradio_ui.generate_prompt(
        "девушка стоит у окна",
        "huihui-qwen3-8b-abliterated-v2",
        "Tag-heavy — максимум тегов",
        "Rich — полноценный production prompt",
        True,
        6,
    ))
    assert seen["max_tokens"] == 520
    assert result[-1].startswith("🟢")


def test_literal_mode_uses_320_budget(monkeypatch):
    seen = {}

    async def fake_plan(**kwargs):
        seen.update(kwargs)
        return ModelPlan(camera=["from below"])

    monkeypatch.setattr(gradio_ui.lm, "plan", fake_plan)
    asyncio.run(gradio_ui.generate_prompt(
        "камера снизу",
        "huihui-qwen3-8b-abliterated-v2",
        "Balanced — теги + prose",
        "Literal — только сказанное",
        True,
        4,
    ))
    assert seen["max_tokens"] == 320
