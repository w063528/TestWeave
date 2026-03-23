from pathlib import Path

_ALLOWED_SUFFIXES = {".feature", ".md"}


def discover_spec_files(root_dir: str | Path) -> list[Path]:
    """Recursively return .feature and .md files under root_dir."""
    root_path = Path(root_dir)
    if not root_path.exists() or not root_path.is_dir():
        return []

    matched_files = [
        file_path
        for file_path in root_path.rglob("*")
        if file_path.is_file() and file_path.suffix.lower() in _ALLOWED_SUFFIXES
    ]
    return sorted(matched_files)
