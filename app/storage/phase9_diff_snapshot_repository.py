from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import re
from typing import Callable

from app.models.test_run import TestRun


class Phase9EvidenceError(ValueError):
    pass


class MissingDiffSnapshotError(Phase9EvidenceError):
    pass


class IncompleteWriteError(Phase9EvidenceError):
    pass


class SummaryOnlyDiffError(Phase9EvidenceError):
    pass


class CorruptedDiffFormatError(Phase9EvidenceError):
    pass


class MetadataBlobMismatchError(Phase9EvidenceError):
    pass


class EvidenceInconsistencyError(Phase9EvidenceError):
    pass


class LegacyDataUnsupportedError(Phase9EvidenceError):
    pass


class VersionConsistencyError(Phase9EvidenceError):
    pass


class EvidenceReuseError(Phase9EvidenceError):
    pass


class DiffSnapshotWriteError(RuntimeError):
    pass


class InMemoryPhase9DiffSnapshotRepository:
    CURRENT_SCHEMA_VERSION = 1
    _DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.MULTILINE)
    _COMMIT_RE = re.compile(r"^commit ([0-9a-f]{7,40})$", re.MULTILINE)

    def __init__(self, *, supported_schema_version: int = CURRENT_SCHEMA_VERSION) -> None:
        self._supported_schema_version = supported_schema_version
        self._runs: dict[str, TestRun] = {}
        self._snapshot_by_key: dict[tuple[str, str], dict[str, object]] = {}
        self._snapshot_key_by_run_id: dict[str, tuple[str, str]] = {}

    def save_run_with_diff_snapshot(
        self,
        run: TestRun,
        *,
        pr_url: str,
        commit_sha: str,
        diff_body: str,
        expected_size_bytes: int,
        file_count: int,
        task_log_files: tuple[str, ...],
        write_guard: Callable[[], None] | None = None,
    ) -> None:
        if not diff_body or not diff_body.strip():
            raise MissingDiffSnapshotError("diff snapshot is required")
        if not pr_url.strip() or not commit_sha.strip():
            raise MetadataBlobMismatchError("pr_url and commit_sha are required")

        observed_size = len(diff_body.encode("utf-8"))
        if expected_size_bytes != observed_size:
            raise IncompleteWriteError("expected_size_bytes does not match diff_body size")

        parsed_files = self._extract_files(diff_body)
        if not parsed_files:
            raise CorruptedDiffFormatError("diff_body has no valid diff file headers")
        if file_count != len(parsed_files):
            raise MetadataBlobMismatchError("file_count does not match parsed diff file count")

        blob_commit_sha = self._extract_commit_sha(diff_body)
        if blob_commit_sha and blob_commit_sha != commit_sha:
            raise MetadataBlobMismatchError("commit_sha does not match raw diff metadata")

        self._ensure_not_summary_only(diff_body, parsed_files)
        self._validate_task_log_files(task_log_files, parsed_files)

        snapshot_id = self._make_snapshot_id(pr_url, commit_sha)
        snapshot_record: dict[str, object] = {
            "snapshot_id": snapshot_id,
            "schema_version": self.CURRENT_SCHEMA_VERSION,
            "pr_url": pr_url,
            "commit_sha": commit_sha,
            "file_paths": parsed_files,
            "file_count": file_count,
            "expected_size_bytes": expected_size_bytes,
            "diff_body": diff_body,
            "checksum_sha256": sha256(diff_body.encode("utf-8")).hexdigest(),
        }

        if write_guard is not None:
            write_guard()

        run_with_link = replace(run, pr_url=pr_url, commit_sha=commit_sha, diff_snapshot_id=snapshot_id)
        self._snapshot_by_key[(pr_url, commit_sha)] = snapshot_record
        self._snapshot_key_by_run_id[run.run_id] = (pr_url, commit_sha)
        self._runs[run.run_id] = run_with_link

    def get_run_by_id(self, run_id: str) -> TestRun | None:
        run = self._runs.get(run_id)
        if run is None:
            return None
        return deepcopy(run)

    def get_snapshot_by_pr_and_sha(self, *, pr_url: str, commit_sha: str) -> dict[str, object] | None:
        if not pr_url or not commit_sha:
            raise MetadataBlobMismatchError("pr_url and commit_sha are mandatory")
        snapshot = self._snapshot_by_key.get((pr_url, commit_sha))
        if snapshot is None:
            return None
        self._assert_supported_schema(snapshot)
        self._assert_integrity(snapshot)
        return deepcopy(snapshot)

    def get_snapshot_for_run(self, run_id: str) -> dict[str, object] | None:
        key = self._snapshot_key_by_run_id.get(run_id)
        if key is None:
            return None
        snapshot = self._snapshot_by_key.get(key)
        if snapshot is None:
            return None
        self._assert_supported_schema(snapshot)
        self._assert_integrity(snapshot)
        return deepcopy(snapshot)

    def set_supported_schema_version(self, schema_version: int) -> None:
        self._supported_schema_version = schema_version

    def _assert_supported_schema(self, snapshot: dict[str, object]) -> None:
        schema_version = snapshot.get("schema_version")
        if schema_version != self._supported_schema_version:
            raise LegacyDataUnsupportedError(
                f"unsupported schema_version={schema_version}, expected={self._supported_schema_version}"
            )

    def _assert_integrity(self, snapshot: dict[str, object]) -> None:
        diff_body = snapshot.get("diff_body")
        expected_size = snapshot.get("expected_size_bytes")
        if not isinstance(diff_body, str) or not isinstance(expected_size, int):
            raise CorruptedDiffFormatError("snapshot structure is corrupted")

        observed_size = len(diff_body.encode("utf-8"))
        if observed_size != expected_size:
            raise IncompleteWriteError("stored snapshot is incomplete")

    @staticmethod
    def _make_snapshot_id(pr_url: str, commit_sha: str) -> str:
        return f"{pr_url}::{commit_sha}"

    @classmethod
    def _extract_files(cls, diff_body: str) -> tuple[str, ...]:
        return tuple(match.group(2) for match in cls._DIFF_HEADER_RE.finditer(diff_body))

    @classmethod
    def _extract_commit_sha(cls, diff_body: str) -> str | None:
        match = cls._COMMIT_RE.search(diff_body)
        if match is None:
            return None
        return match.group(1)

    @classmethod
    def _ensure_not_summary_only(cls, diff_body: str, parsed_files: tuple[str, ...]) -> None:
        if "diff --git" not in diff_body:
            raise CorruptedDiffFormatError("diff_body does not contain unified diff headers")

        for file_path in parsed_files:
            if not cls._file_has_hunk(diff_body, file_path):
                raise SummaryOnlyDiffError(f"missing hunks for file: {file_path}")

    @staticmethod
    def _file_has_hunk(diff_body: str, file_path: str) -> bool:
        marker = f"diff --git a/{file_path} b/{file_path}"
        start = diff_body.find(marker)
        if start == -1:
            return False
        next_start = diff_body.find("\ndiff --git ", start + len(marker))
        block = diff_body[start:] if next_start == -1 else diff_body[start:next_start]
        return "@@" in block

    @staticmethod
    def _validate_task_log_files(task_log_files: tuple[str, ...], diff_files: tuple[str, ...]) -> None:
        diff_file_set = set(diff_files)
        missing = [path for path in task_log_files if path not in diff_file_set]
        if missing:
            raise EvidenceInconsistencyError(f"task log files missing from diff snapshot: {missing}")


class IndependentEvidenceRegistry:
    def __init__(self) -> None:
        self._risk_by_evidence: dict[str, str] = {}

    def bind(self, *, risk_id: str, evidence_id: str) -> None:
        bound_risk = self._risk_by_evidence.get(evidence_id)
        if bound_risk is None:
            self._risk_by_evidence[evidence_id] = risk_id
            return
        if bound_risk != risk_id:
            raise EvidenceReuseError(
                f"evidence_id '{evidence_id}' already bound to risk '{bound_risk}', cannot reuse for '{risk_id}'"
            )
