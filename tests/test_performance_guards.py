import asyncio

from backend.app import gradio_ui
from backend.app.lmstudio import LMStudioClient
from backend.app.schemas import ModelPlan, PromptPart


def test_schema_caps_are_small():
    schema = ModelPlan.model_json_schema()
    assert schema["properties"]["base_parts"]["maxItems"] == 10
    assert schema["$defs"]["CharacterPlan"]["properties"]["parts"]["maxItems"] == 10
    assert schema["properties"]["uc_parts"]["maxItems"] == 4


def test_request_defaults_are_low_cost():
    import inspect
    sig = inspect.signature(LMStudioClient.plan)
    assert sig.parameters["max_tokens"].default == 512
    assert sig.parameters["temperature"].default == 0.30


def test_simple_ui_generation_uses_512_budget(monkeypatch):
    seen = {}

    async def fake_plan(**kwargs):
        seen.update(kwargs)
        return ModelPlan(base_parts=[PromptPart(text="indoors", kind="tag")])

    monkeypatch.setattr(gradio_ui.lm, "plan", fake_plan)
    result = asyncio.run(gradio_ui.generate_prompt(
        "девушка стоит у окна",
        "huihui-qwen3-8b-abliterated-v2",
        "Balanced — теги + prose",
        True,
        6,
    ))
    assert seen["max_tokens"] == 512
    assert result[-1].startswith("🟢")
