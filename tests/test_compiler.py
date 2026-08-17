from pathlib import Path

from backend.app.compiler import compile_plan
from backend.app.knowledge import KnowledgeBase
from backend.app.schemas import ModelPlan


def test_unknown_candidate_is_kept_as_fallback():
    kb = KnowledgeBase(Path(__file__).parents[1] / "knowledge")
    plan = ModelPlan(
        camera=["from below"],
        critical_details=["not_a_real_tag_123"],
    )
    out = compile_plan(plan, kb, "test")
    assert "from below" in out.verified_tags_used
    assert "not_a_real_tag_123" in out.prose_fallbacks
    assert "from below" in out.base_prompt
    assert "not_a_real_tag_123" in out.base_prompt


def test_weighted_candidate_is_preserved():
    kb = KnowledgeBase(Path(__file__).parents[1] / "knowledge")
    plan = ModelPlan(style=["0.7::custom style token ::"])
    out = compile_plan(plan, kb, "test")
    assert "0.7::custom style token ::" in out.base_prompt
    assert "0.7::custom style token ::" in out.prose_fallbacks


def test_interaction_pose_camera_order_is_stable():
    kb = KnowledgeBase(Path(__file__).parents[1] / "knowledge")
    plan = ModelPlan(
        subject=["1girl"],
        interaction=["hug"],
        pose=["leaning forward"],
        camera=["from side"],
        rendering=["blurry background"],
        scene=["indoors"],
    )
    out = compile_plan(plan, kb, "test")
    atoms = [x.strip() for x in out.base_prompt.split(",")]
    assert atoms.index("1girl") < atoms.index("hug")
    assert atoms.index("hug") < atoms.index("leaning_forward")
    assert atoms.index("leaning_forward") < atoms.index("from side")
    assert atoms.index("from side") < atoms.index("blurry_background")
    assert atoms.index("blurry_background") < atoms.index("indoors")
