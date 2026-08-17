from pathlib import Path

from launcher import missing_project_assets


def _make_required_non_tag_files(root: Path) -> None:
    (root / "knowledge" / "source").mkdir(parents=True, exist_ok=True)
    (root / "knowledge" / "source" / "model_profile_v45.md").write_text("ok", encoding="utf-8")
    (root / "backend" / "app").mkdir(parents=True, exist_ok=True)
    (root / "backend" / "app" / "gradio_ui.py").write_text("# ok", encoding="utf-8")


def test_launcher_accepts_current_sharded_tag_layout(tmp_path: Path):
    _make_required_non_tag_files(tmp_path)
    tag_dir = tmp_path / "knowledge" / "tags"
    tag_dir.mkdir(parents=True, exist_ok=True)
    (tag_dir / "verified_001.csv").write_text("canonical_tag\nsolo\n", encoding="utf-8")

    assert missing_project_assets(tmp_path) == []


def test_launcher_accepts_legacy_single_tag_file(tmp_path: Path):
    _make_required_non_tag_files(tmp_path)
    (tmp_path / "knowledge" / "verified_tags.csv").write_text(
        "canonical_tag\nsolo\n", encoding="utf-8"
    )

    assert missing_project_assets(tmp_path) == []


def test_launcher_reports_missing_tag_database(tmp_path: Path):
    _make_required_non_tag_files(tmp_path)

    missing = missing_project_assets(tmp_path)
    assert len(missing) == 1
    assert "knowledge" in missing[0]
    assert "tags" in missing[0]
