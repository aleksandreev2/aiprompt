from pathlib import Path
from backend.app.knowledge import KnowledgeBase
from backend.app.compiler import compile_plan
from backend.app.schemas import ModelPlan, PromptPart


def test_unknown_tag_becomes_prose():
    kb = KnowledgeBase(Path(__file__).parents[1] / "knowledge")
    plan = ModelPlan(base_parts=[PromptPart(text="from below", kind="tag", block="camera"), PromptPart(text="not_a_real_tag_123", kind="tag")])
    out = compile_plan(plan, kb, "test")
    assert "from below" in out.verified_tags_used
    assert "not_a_real_tag_123" in out.prose_fallbacks
    assert out.warnings
