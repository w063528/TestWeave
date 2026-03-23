from app.core.file_discovery import discover_spec_files


def test_discover_spec_files_returns_only_feature_and_md_files(tmp_path):
    (tmp_path / "a.feature").write_text("", encoding="utf-8")
    (tmp_path / "b.md").write_text("", encoding="utf-8")
    (tmp_path / "c.txt").write_text("", encoding="utf-8")
    (tmp_path / "d.csv").write_text("", encoding="utf-8")

    files = discover_spec_files(tmp_path)

    assert files == [tmp_path / "a.feature", tmp_path / "b.md"]


def test_discover_spec_files_scans_subdirectories(tmp_path):
    nested = tmp_path / "specs" / "features"
    nested.mkdir(parents=True)
    (nested / "flow.feature").write_text("", encoding="utf-8")
    (nested / "notes.md").write_text("", encoding="utf-8")
    (nested / "ignore.json").write_text("", encoding="utf-8")

    files = discover_spec_files(tmp_path)

    assert files == [nested / "flow.feature", nested / "notes.md"]


def test_discover_spec_files_returns_empty_for_missing_directory(tmp_path):
    missing = tmp_path / "does-not-exist"

    files = discover_spec_files(missing)

    assert files == []
