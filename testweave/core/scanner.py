from __future__ import annotations

from dataclasses import dataclass, asdict
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

# NOTE:
# - Step 3 서버(/api/scan)는 testweave.core.scanner에 scan_workspace/scan이 있기를 기대합니다.
# - 이 파일은 "로컬 스캔 + 최소 파싱"을 제공하여 서버 MVP를 우선 완성합니다.
# - 후속 Step에서 parsers/* 및 models/* 과 더 강하게 통합해도 됩니다.


DEFAULT_GLOBS: list[str] = [
    "**/*.feature",
    "**/*.md",
    "**/*.csv",
    "**/*.xlsx",
    "**/*.xls",
]

DEFAULT_EXCLUDE_DIRS: set[str] = {
    ".git",
    ".qa",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    "node_modules",
    ".idea",
    ".vscode",
}


def _try_extract_tc_id(text: str) -> str | None:
    """
    Try to extract TC ID from a line/title using core.tcid if available.
    Fallback to a conservative regex if needed.
    """
    # Prefer project tcid implementation (tests already pass with it)
    try:
        from testweave.core.tcid import extract_tc_id  # type: ignore

        v = extract_tc_id(text)
        return v
    except Exception:
        pass

    # Fallback regex:
    # - TC-TS10-100, TC-TS1-1, TC-TS02-001
    # - TC-007, TC-34, TC-014, TC-100
    # - C1, C02, C123 (A/B/etc 확장 가능하게)
    import re

    rx = re.compile(
        r"\b("
        r"TC-[A-Z]{2}\d{1,2}-\d{1,3}"  # TC-TS10-100
        r"|TC-\d{1,3}"  # TC-007
        r"|[A-Z]\d{1,3}"  # C123, A01, B9 ...
        r")\b"
    )
    m = rx.search(text)
    return m.group(1) if m else None


@dataclass(frozen=True)
class ScannedCase:
    tc_id: str
    title: str
    feature: str | None
    uri: str
    line1: int  # 1-based


def _iter_files(workspace: Path, globs: list[str]) -> list[Path]:
    workspace = workspace.resolve()
    files: list[Path] = []

    # Walk and filter by fnmatch against relative posix path
    for p in workspace.rglob("*"):
        if not p.is_file():
            continue

        rel_parts = p.relative_to(workspace).parts
        if any(part in DEFAULT_EXCLUDE_DIRS for part in rel_parts):
            continue
        if any(part.startswith(".") and part not in (".", "..") for part in rel_parts):
            # hide dot folders/files except normal dots
            # (keeps behavior conservative)
            pass

        rel_posix = p.relative_to(workspace).as_posix()
        if any(fnmatch(rel_posix, g) for g in globs):
            files.append(p)

    return files


def _parse_feature_file(path: Path) -> list[ScannedCase]:
    cases: list[ScannedCase] = []
    feature_name: str | None = None

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return cases

    for idx, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()

        # Feature:
        if line.lower().startswith("feature:"):
            feature_name = line.split(":", 1)[1].strip() or feature_name
            continue

        # Scenario / Scenario Outline
        low = line.lower()
        if low.startswith("scenario:") or low.startswith("scenario outline:"):
            title = line.split(":", 1)[1].strip()
            tc_id = _try_extract_tc_id(title)
            if not tc_id:
                continue
            cases.append(
                ScannedCase(
                    tc_id=tc_id,
                    title=title,
                    feature=feature_name,
                    uri=str(path.resolve()),
                    line1=idx,
                )
            )

    return cases


def _parse_markdown_file(path: Path) -> list[ScannedCase]:
    """
    Minimal markdown TC extraction:

    Examples supported:
      * [unknown] C3 그런데 말입니다
      - [pass] TC-007 로그인 검증
      ## TC-014 - something
      ### C02 something
    """
    cases: list[ScannedCase] = []
    feature_name: str | None = None  # use nearest heading as a "feature-ish" group

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return cases

    for idx, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()

        # Heading as feature group
        stripped = line.strip()
        if stripped.startswith("#"):
            # "# Title" => feature group
            feature_name = stripped.lstrip("#").strip() or feature_name
            continue

        # Bullet patterns
        s = stripped
        if not s:
            continue

        # Common bullet prefixes
        if s.startswith(("* ", "- ", "+ ")):
            body = s[2:].strip()

            # Optional "[status]" prefix
            if body.startswith("[") and "]" in body:
                body = body.split("]", 1)[1].strip()

            tc_id = _try_extract_tc_id(body)
            if not tc_id:
                continue

            cases.append(
                ScannedCase(
                    tc_id=tc_id,
                    title=body,
                    feature=feature_name,
                    uri=str(path.resolve()),
                    line1=idx,
                )
            )
            continue

        # Also allow headings like "## TC-014 ..."
        tc_id = _try_extract_tc_id(stripped)
        if tc_id:
            cases.append(
                ScannedCase(
                    tc_id=tc_id,
                    title=stripped.lstrip("#").strip(),
                    feature=feature_name,
                    uri=str(path.resolve()),
                    line1=idx,
                )
            )

    return cases


def _parse_csv_file(path: Path) -> list[ScannedCase]:
    """
    Very minimal CSV parsing:
    - scans each row text and tries to find a tc_id anywhere.
    - title becomes the whole row string.
    """
    import csv

    cases: list[ScannedCase] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.reader(f)
            for idx, row in enumerate(reader, start=1):
                row_text = " | ".join(row).strip()
                tc_id = _try_extract_tc_id(row_text)
                if not tc_id:
                    continue
                cases.append(
                    ScannedCase(
                        tc_id=tc_id,
                        title=row_text,
                        feature=None,
                        uri=str(path.resolve()),
                        line1=idx,
                    )
                )
    except Exception:
        return cases

    return cases


def _parse_excel_file(path: Path) -> list[ScannedCase]:
    """
    Minimal Excel parsing:
    - reads first sheet only
    - scans each row cells joined into one text
    """
    cases: list[ScannedCase] = []
    try:
        import openpyxl  # type: ignore
    except Exception:
        return cases

    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.worksheets[0]
        for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            row_text = " | ".join("" if v is None else str(v) for v in row).strip()
            if not row_text:
                continue
            tc_id = _try_extract_tc_id(row_text)
            if not tc_id:
                continue
            cases.append(
                ScannedCase(
                    tc_id=tc_id,
                    title=row_text,
                    feature=None,
                    uri=str(path.resolve()),
                    line1=idx,
                )
            )
        wb.close()
    except Exception:
        return cases

    return cases


def _parse_file(path: Path) -> list[ScannedCase]:
    suf = path.suffix.lower()
    if suf == ".feature":
        return _parse_feature_file(path)
    if suf == ".md":
        return _parse_markdown_file(path)
    if suf == ".csv":
        return _parse_csv_file(path)
    if suf in (".xlsx", ".xls"):
        return _parse_excel_file(path)
    return []


def scan_workspace(workspace: Path | str, globs: list[str] | None = None) -> dict[str, Any]:
    """
    Main API for server MVP.
    Returns JSON-serializable dict.
    """
    ws = Path(workspace).expanduser().resolve()
    if not ws.exists() or not ws.is_dir():
        raise ValueError(f"Invalid workspace: {ws}")

    patterns = globs or DEFAULT_GLOBS
    files = _iter_files(ws, patterns)

    all_cases: list[ScannedCase] = []
    for f in files:
        all_cases.extend(_parse_file(f))

    # Group by feature name (for UI convenience)
    features: dict[str, list[ScannedCase]] = {}
    for c in all_cases:
        key = (c.feature or "(no feature)")
        features.setdefault(key, []).append(c)

    # sort within each feature for stability
    for k in list(features.keys()):
        features[k] = sorted(features[k], key=lambda x: (x.uri, x.line1, x.tc_id))

    payload = {
        "workspace": str(ws),
        "globs": patterns,
        "filesScanned": len(files),
        "casesCount": len(all_cases),
        "features": [
            {
                "name": fname,
                "cases": [asdict(c) for c in cases],
            }
            for fname, cases in sorted(features.items(), key=lambda kv: kv[0].lower())
        ],
    }
    return payload


def scan(workspace: Path | str, globs: list[str] | None = None) -> dict[str, Any]:
    """
    Alias for compatibility.
    """
    return scan_workspace(workspace, globs=globs)