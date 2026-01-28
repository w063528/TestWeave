from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkspaceConfig:
    workspace: str


def _qa_dir(root: Path) -> Path:
    return root / ".qa"


def _workspace_file(root: Path) -> Path:
    return _qa_dir(root) / "workspace.json"


def load_workspace(root: Path) -> Path:
    """
    Load workspace path from <root>/.qa/workspace.json.
    If not found, default to <root>.
    """
    root = root.resolve()
    wf = _workspace_file(root)
    if not wf.exists():
        return root

    try:
        data = json.loads(wf.read_text(encoding="utf-8"))
        ws = (data.get("workspace") or "").strip()
        if not ws:
            return root
        p = Path(ws).expanduser().resolve()
        return p if p.exists() and p.is_dir() else root
    except Exception:
        return root


def save_workspace(root: Path, workspace: Path) -> None:
    root = root.resolve()
    workspace = workspace.expanduser().resolve()

    qa = _qa_dir(root)
    qa.mkdir(parents=True, exist_ok=True)

    wf = _workspace_file(root)
    wf.write_text(
        json.dumps({"workspace": str(workspace)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )