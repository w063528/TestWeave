from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Iterable, Mapping

from app.models.extracted_testcase import ExtractedTestCase
from app.models.extracted_testsuite import ExtractedTestSuite

_TC_MARKER_RE = re.compile(r"\b(TC-\d+)\b")
_WHITESPACE_RE = re.compile(r"\s+")
_SLUG_INVALID_RE = re.compile(r"[^a-z0-9]+")


def extract_test_suites(parsed: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> list[ExtractedTestSuite]:
    suites: list[ExtractedTestSuite] = []
    for parsed_entry in _coerce_parsed_entries(parsed):
        suite_name = _normalize_suite_name(parsed_entry.get("suite_name"))
        source_file_path = _normalize_source_path(parsed_entry.get("source_file_path"))
        suite_id = _build_suite_id(suite_name, source_file_path)
        suites.append(
            ExtractedTestSuite(
                suite_id=suite_id,
                suite_name=suite_name,
                source_file_path=source_file_path,
            )
        )
    return suites


def extract_test_cases(parsed: Mapping[str, Any] | Iterable[Mapping[str, Any]]) -> list[ExtractedTestCase]:
    extracted_cases: list[ExtractedTestCase] = []
    for parsed_entry in _coerce_parsed_entries(parsed):
        suite_name = _normalize_suite_name(parsed_entry.get("suite_name"))
        source_file_path = _normalize_source_path(parsed_entry.get("source_file_path"))
        suite_id = _build_suite_id(suite_name, source_file_path)
        seen_testcase_ids: set[str] = set()

        for block in _coerce_blocks(parsed_entry.get("testcase_blocks")):
            testcase_id = _extract_testcase_id(block)
            if testcase_id is None:
                continue
            if testcase_id in seen_testcase_ids:
                raise ValueError(f"Duplicate testcase_id in suite {suite_id}: {testcase_id}")

            testcase_name = _extract_testcase_name(block, testcase_id)
            extracted_cases.append(
                ExtractedTestCase(
                    testcase_id=testcase_id,
                    testcase_name=testcase_name,
                    suite_id=suite_id,
                    source_file_path=source_file_path,
                )
            )
            seen_testcase_ids.add(testcase_id)

    return extracted_cases


def _coerce_parsed_entries(
    parsed: Mapping[str, Any] | Iterable[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    if isinstance(parsed, Mapping):
        return [parsed]
    return list(parsed)


def _coerce_blocks(raw_blocks: Any) -> list[Mapping[str, Any]]:
    if isinstance(raw_blocks, list):
        return [block for block in raw_blocks if isinstance(block, Mapping)]
    return []


def _normalize_suite_name(value: Any) -> str:
    suite_name = str(value or "").strip()
    suite_name = _WHITESPACE_RE.sub(" ", suite_name)
    if not suite_name:
        raise ValueError("Missing required suite_name in parsed structure")
    return suite_name


def _normalize_source_path(value: Any) -> str:
    source_file_path = str(value or "").strip()
    if not source_file_path:
        raise ValueError("Missing required source_file_path in parsed structure")
    return Path(source_file_path).as_posix()


def _build_suite_id(suite_name: str, source_file_path: str) -> str:
    normalized_name = suite_name.lower()
    slug = _SLUG_INVALID_RE.sub("-", normalized_name).strip("-") or "suite"
    digest_source = f"{normalized_name}|{source_file_path}".encode("utf-8")
    digest = hashlib.sha1(digest_source).hexdigest()[:10]
    return f"suite-{slug}-{digest}"


def _extract_testcase_id(block: Mapping[str, Any]) -> str | None:
    explicit_id = block.get("testcase_id")
    if isinstance(explicit_id, str) and explicit_id.strip():
        return explicit_id.strip()

    marker = block.get("testcase_marker")
    if isinstance(marker, str) and marker.strip():
        return marker.strip()

    title = block.get("title")
    if isinstance(title, str):
        title_match = _TC_MARKER_RE.search(title)
        if title_match:
            return title_match.group(1)

    for raw_line in block.get("raw_lines", []):
        if isinstance(raw_line, str):
            line_match = _TC_MARKER_RE.search(raw_line)
            if line_match:
                return line_match.group(1)

    return None


def _extract_testcase_name(block: Mapping[str, Any], testcase_id: str) -> str:
    scenario = block.get("scenario")
    if isinstance(scenario, str) and scenario.strip():
        return _WHITESPACE_RE.sub(" ", scenario).strip()

    title = block.get("title")
    if isinstance(title, str) and title.strip():
        return _WHITESPACE_RE.sub(" ", title).strip()

    for raw_line in block.get("raw_lines", []):
        if not isinstance(raw_line, str):
            continue
        text = raw_line.strip().lstrip("-").strip()
        text = _WHITESPACE_RE.sub(" ", text)
        if text and _TC_MARKER_RE.search(text) is None:
            return text

    return testcase_id
