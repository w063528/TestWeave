from __future__ import annotations

import re
from pathlib import Path

_FEATURE_LINE_RE = re.compile(r"^\s*(Feature|Background|Scenario)\s*:\s*(.*)$")
_STEP_LINE_RE = re.compile(r"^\s*(Given|When|Then|And|But)\b(.*)$")
_MARKDOWN_TC_RE = re.compile(r"^\s*###\s*(TC-\d+)\b(.*)$")
_MARKDOWN_SCENARIO_RE = re.compile(r"^\s*\*\*Scenario\*\*\s*(.*)$")
_MARKDOWN_PRECONDITION_RE = re.compile(
    r"^\s*\*\*(Given|Given\s*\(전제조건\)|Pre-condition)\*\*\s*(.*)$"
)
_MARKDOWN_ACTION_RE = re.compile(r"^\s*\*\*(When\d*)[^*]*\*\*\s*(.*)$")
_MARKDOWN_EXPECTED_RE = re.compile(r"^\s*\*\*(Then\d*)[^*]*\*\*\s*(.*)$")
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.*)$")
_H1_RE = re.compile(r"^\s*#\s+(.*)$")


def _read_lines(path: str | Path) -> tuple[Path, list[str]]:
    resolved = Path(path)
    content = resolved.read_text(encoding="utf-8")
    return resolved, content.splitlines()


def parse_feature_file(path: str | Path) -> dict:
    resolved, lines = _read_lines(path)

    parsed: dict = {
        "source_file_path": str(resolved),
        "source_format": "feature",
        "suite_name": None,
        "background_steps": [],
        "testcase_blocks": [],
    }

    active_section: str | None = None
    current_case: dict | None = None

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line.strip():
            continue

        section_match = _FEATURE_LINE_RE.match(line)
        if section_match:
            section_name, section_value = section_match.group(1), section_match.group(2).strip()
            active_section = section_name
            if section_name == "Feature":
                parsed["suite_name"] = section_value or None
                current_case = None
            elif section_name == "Background":
                current_case = None
            elif section_name == "Scenario":
                current_case = {
                    "title": section_value,
                    "steps": [],
                    "raw_lines": [line.strip()],
                }
                marker_match = re.search(r"\b(TC-\d+)\b", section_value)
                if marker_match:
                    current_case["testcase_marker"] = marker_match.group(1)
                parsed["testcase_blocks"].append(current_case)
            continue

        step_match = _STEP_LINE_RE.match(line)
        if not step_match:
            continue

        keyword = step_match.group(1)
        text = step_match.group(2).strip()
        step_entry = {"keyword": keyword, "text": text}

        if active_section == "Background":
            parsed["background_steps"].append(step_entry)
            continue

        if current_case is not None:
            current_case["steps"].append(step_entry)
            current_case["raw_lines"].append(line.strip())

    return parsed


def parse_markdown_file(path: str | Path) -> dict:
    resolved, lines = _read_lines(path)

    parsed: dict = {
        "source_file_path": str(resolved),
        "source_format": "markdown",
        "suite_name": None,
        "testcase_blocks": [],
    }

    current_case: dict | None = None
    pending_action: dict[str, str] = {}
    pending_expected_index: int | None = None
    active_section: str | None = None
    first_h1_found = False

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        if not stripped:
            continue

        if not first_h1_found:
            h1_match = _H1_RE.match(stripped)
            if h1_match:
                parsed["suite_name"] = h1_match.group(1).strip() or None
                first_h1_found = True
                continue

        tc_match = _MARKDOWN_TC_RE.match(stripped)
        if tc_match:
            current_case = {
                "testcase_marker": tc_match.group(1),
                "title_suffix": tc_match.group(2).strip() or None,
                "scenario": None,
                "preconditions": [],
                "action_expected_pairs": [],
                "raw_lines": [stripped],
            }
            pending_action = {}
            pending_expected_index = None
            active_section = None
            parsed["testcase_blocks"].append(current_case)
            continue

        if current_case is None:
            continue

        current_case["raw_lines"].append(stripped)

        scenario_match = _MARKDOWN_SCENARIO_RE.match(stripped)
        if scenario_match:
            scenario_text = scenario_match.group(1).strip()
            if scenario_text.startswith("-"):
                scenario_text = scenario_text[1:].strip()
            current_case["scenario"] = scenario_text or None
            continue

        precondition_match = _MARKDOWN_PRECONDITION_RE.match(stripped)
        if precondition_match:
            active_section = "precondition"
            inline_value = precondition_match.group(2).strip()
            if inline_value:
                current_case["preconditions"].append(inline_value)
            continue

        bullet_match = _BULLET_RE.match(stripped)
        if bullet_match:
            bullet_text = bullet_match.group(1).strip()
            if active_section == "action" and pending_action:
                pending_action["action"] = bullet_text
            elif active_section == "expected" and pending_expected_index is not None:
                current_case["action_expected_pairs"][pending_expected_index]["expected"] = bullet_text
            elif active_section == "precondition":
                current_case["preconditions"].append(bullet_text)
            continue

        action_match = _MARKDOWN_ACTION_RE.match(stripped)
        if action_match:
            active_section = "action"
            pending_expected_index = None
            action_key = action_match.group(1)
            action_text = action_match.group(2).strip()
            pending_action = {
                "action_key": action_key,
                "action": action_text or None,
            }
            continue

        expected_match = _MARKDOWN_EXPECTED_RE.match(stripped)
        if expected_match:
            active_section = "expected"
            expected_key = expected_match.group(1)
            expected_text = expected_match.group(2).strip()
            pair = {
                "action_key": pending_action.get("action_key"),
                "action": pending_action.get("action"),
                "expected_key": expected_key,
                "expected": expected_text or None,
            }
            current_case["action_expected_pairs"].append(pair)
            pending_expected_index = len(current_case["action_expected_pairs"]) - 1
            pending_action = {}
            continue

    return parsed


def parse_spec_file(path: str | Path) -> dict:
    resolved = Path(path)
    suffix = resolved.suffix.lower()
    if suffix == ".feature":
        return parse_feature_file(resolved)
    if suffix == ".md":
        return parse_markdown_file(resolved)
    raise ValueError(f"Unsupported spec file type: {suffix}")
