from pathlib import Path

from launcher import choose_ui_port


def _write_ui_contract(root: Path, ui_text: str, schema_text: str = "schema") -> None:
    app_dir = root / "backend" / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "gradio_ui.py").write_text(ui_text, encoding="utf-8")
    (app_dir / "schemas.py").write_text(schema_text, encoding="utf-8")


def test_ui_event_contract_change_gets_a_different_origin_port(tmp_path: Path):
    _write_ui_contract(tmp_path, "inputs = [intent, model, mode, checkbox, slider]")
    old_port, old_revision = choose_ui_port(tmp_path)

    _write_ui_contract(
        tmp_path,
        "inputs = [intent, model, mode, detail_level, checkbox, slider]",
    )
    new_port, new_revision = choose_ui_port(tmp_path)

    assert old_revision != new_revision
    assert old_port != new_port
    assert old_port > 0
    assert new_port > 0
