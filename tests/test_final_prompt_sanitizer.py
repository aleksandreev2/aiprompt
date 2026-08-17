from backend.app.schemas import CompiledCharacter, GenerateResponse, sanitize_final_prompt


def test_internal_retrieval_metadata_never_reaches_final_prompt():
    dirty = (
        "1girl, hands pressed against window | pose | PROSE_RELATION, "
        "basic view, blurry background | rendering | VERIFIED_TAG_SOURCE, "
        "schoolyard | scene | PROSE_SCENE_CONCEPT"
    )

    clean = sanitize_final_prompt(dirty)

    assert clean == "1girl, hands pressed against window, blurry background, schoolyard"
    assert "|" not in clean
    assert "PROSE_" not in clean
    assert "VERIFIED_" not in clean
    assert "basic view" not in clean


def test_response_boundary_sanitizes_base_uc_and_character_prompts():
    response = GenerateResponse(
        base_prompt="window | scene | PROSE_SCENE_CONCEPT, blurry background",
        characters=[
            CompiledCharacter(
                label="Character",
                prompt="looking at viewer | expression_gaze | VERIFIED_TAG_SOURCE",
            )
        ],
        undesired_content="lowres | rendering | DOCUMENTED_UC_CONCEPT",
        warnings=[],
        notes=[],
        verified_tags_used=[],
        prose_fallbacks=[],
        model="test",
    )

    assert response.base_prompt == "window, blurry background"
    assert response.characters[0].prompt == "looking at viewer"
    assert response.undesired_content == "lowres"
    assert "|" not in response.base_prompt
