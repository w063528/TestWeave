from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import re
from typing import Callable, Protocol

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


@dataclass(frozen=True, slots=True)
class DiffFileEntry:
    file_path: str
    status: str
    patch_content: str
    before_content: str
    after_content: str


@dataclass(frozen=True, slots=True)
class DiffSnapshot:
    snapshot_id: str
    schema_version: int
    pr_url: str
    commit_sha: str
    file_paths: tuple[str, ...]
    file_count: int
    expected_size_bytes: int
    diff_body: str
    checksum_sha256: str
    file_entries: tuple[DiffFileEntry, ...]


@dataclass(frozen=True, slots=True)
class StoredRunEvidence:
    run: TestRun
    pr_url: str
    commit_sha: str
    diff_snapshot_id: str


class EvidenceProvider(Protocol):
    def get_run_evidence(self, run_id: str) -> StoredRunEvidence | None: ...

    def get_snapshot_for_run(self, run_id: str) -> DiffSnapshot | None: ...


class InMemoryPhase9DiffSnapshotRepository(EvidenceProvider):
    CURRENT_SCHEMA_VERSION = 1
    _DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.MULTILINE)
    _COMMIT_RE = re.compile(r"^commit ([0-9a-f]{7,40})$", re.MULTILINE)

    def __init__(
        self,
        *,
        supported_schema_version: int = CURRENT_SCHEMA_VERSION,
        max_diff_bytes: int | None = None,
    ) -> None:
        self._supported_schema_version = supported_schema_version
        self._max_diff_bytes = max_diff_bytes
        self._snapshot_by_key: dict[tuple[str, str], DiffSnapshot] = {}
        self._snapshot_key_by_run_id: dict[str, tuple[str, str]] = {}
        self._run_evidence_by_run_id: dict[str, StoredRunEvidence] = {}

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
        if self._max_diff_bytes is not None and observed_size > self._max_diff_bytes:
            raise IncompleteWriteError("diff snapshot exceeds configured storage buffer")
        if expected_size_bytes != observed_size:
            raise IncompleteWriteError("expected_size_bytes does not match diff_body size")

        file_entries = self._parse_file_entries(diff_body)
        if not file_entries:
            raise CorruptedDiffFormatError("diff_body has no valid diff file headers")
        if file_count != len(file_entries):
            raise MetadataBlobMismatchError("file_count does not match parsed diff file count")

        blob_commit_sha = self._extract_commit_sha(diff_body)
        if blob_commit_sha is not None and blob_commit_sha != commit_sha:
            raise MetadataBlobMismatchError("commit_sha does not match raw diff metadata")

        self._ensure_not_summary_only(file_entries)
        file_paths = tuple(entry.file_path for entry in file_entries)
        self._validate_task_log_files(task_log_files, file_paths)

        snapshot = DiffSnapshot(
            snapshot_id=self._make_snapshot_id(pr_url, commit_sha),
            schema_version=self.CURRENT_SCHEMA_VERSION,
            pr_url=pr_url,
            commit_sha=commit_sha,
            file_paths=file_paths,
            file_count=file_count,
            expected_size_bytes=expected_size_bytes,
            diff_body=diff_body,
            checksum_sha256=sha256(diff_body.encode("utf-8")).hexdigest(),
            file_entries=file_entries,
        )
        run_evidence = StoredRunEvidence(
            run=deepcopy(run),
            pr_url=pr_url,
            commit_sha=commit_sha,
            diff_snapshot_id=snapshot.snapshot_id,
        )

        if write_guard is not None:
            write_guard()

        self._snapshot_by_key[(pr_url, commit_sha)] = snapshot
        self._snapshot_key_by_run_id[run.run_id] = (pr_url, commit_sha)
        self._run_evidence_by_run_id[run.run_id] = run_evidence

    def get_run_by_id(self, run_id: str) -> TestRun | None:
        run_evidence = self._run_evidence_by_run_id.get(run_id)
        if run_evidence is None:
            return None
        return deepcopy(run_evidence.run)

    def get_run_evidence(self, run_id: str) -> StoredRunEvidence | None:
        run_evidence = self._run_evidence_by_run_id.get(run_id)
        if run_evidence is None:
            return None
        return deepcopy(run_evidence)

    def get_snapshot_by_pr_and_sha(self, *, pr_url: str, commit_sha: str) -> DiffSnapshot | None:
        if not pr_url or not commit_sha:
            raise MetadataBlobMismatchError("pr_url and commit_sha are mandatory")
        snapshot = self._snapshot_by_key.get((pr_url, commit_sha))
        if snapshot is None:
            return None
        self._assert_supported_schema(snapshot)
        self._assert_integrity(snapshot)
        return deepcopy(snapshot)

    def get_snapshot_for_run(self, run_id: str) -> DiffSnapshot | None:
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

    def _assert_supported_schema(self, snapshot: DiffSnapshot) -> None:
        if snapshot.schema_version != self._supported_schema_version:
            raise LegacyDataUnsupportedError(
                f"unsupported schema_version={snapshot.schema_version}, "
                f"expected={self._supported_schema_version}"
            )

    def _assert_integrity(self, snapshot: DiffSnapshot) -> None:
        observed_size = len(snapshot.diff_body.encode("utf-8"))
        if observed_size != snapshot.expected_size_bytes:
            raise IncompleteWriteError("stored snapshot is incomplete")
        if snapshot.file_count != len(snapshot.file_paths) or snapshot.file_count != len(snapshot.file_entries):
            raise MetadataBlobMismatchError("stored snapshot file_count metadata is corrupted")
        if tuple(entry.file_path for entry in snapshot.file_entries) != snapshot.file_paths:
            raise MetadataBlobMismatchError("stored snapshot file list does not match file entries")
        if sha256(snapshot.diff_body.encode("utf-8")).hexdigest() != snapshot.checksum_sha256:
            raise CorruptedDiffFormatError("stored snapshot checksum does not match diff body")
        self._ensure_not_summary_only(snapshot.file_entries)

    @staticmethod
    def _make_snapshot_id(pr_url: str, commit_sha: str) -> str:
        return f"{pr_url}::{commit_sha}"

    @classmethod
    def _extract_commit_sha(cls, diff_body: str) -> str | None:
        match = cls._COMMIT_RE.search(diff_body)
        if match is None:
            return None
        return match.group(1)

    @classmethod
    def _parse_file_entries(cls, diff_body: str) -> tuple[DiffFileEntry, ...]:
        matches = list(cls._DIFF_HEADER_RE.finditer(diff_body))
        entries: list[DiffFileEntry] = []
        for index, match in enumerate(matches):
            block_start = match.start()
            block_end = matches[index + 1].start() if index + 1 < len(matches) else len(diff_body)
            block = diff_body[block_start:block_end]
            file_path = match.group(2)
            patch_content = cls._extract_patch_content(block)
            before_content, after_content = cls._extract_before_after_content(patch_content)
            entries.append(
                DiffFileEntry(
                    file_path=file_path,
                    status=cls._detect_status(block),
                    patch_content=patch_content,
                    before_content=before_content,
                    after_content=after_content,
                )
            )
        return tuple(entries)

    @staticmethod
    def _detect_status(block: str) -> str:
        if "new file mode" in block or "--- /dev/null" in block:
            return "added"
        if "deleted file mode" in block or "+++ /dev/null" in block:
            return "deleted"
        return "modified"

    @staticmethod
    def _extract_patch_content(block: str) -> str:
        patch_lines: list[str] = []
        inside_hunk = False
        for line in block.splitlines():
            if line.startswith("@@"):
                inside_hunk = True
            if inside_hunk:
                patch_lines.append(line)
        return "\n".join(patch_lines)

    @staticmethod
    def _extract_before_after_content(patch_content: str) -> tuple[str, str]:
        before_lines: list[str] = []
        after_lines: list[str] = []
        for line in patch_content.splitlines():
            if line.startswith("@@") or line.startswith("\\"):
                continue
            if not line:
                before_lines.append("")
                after_lines.append("")
                continue
            prefix = line[0]
            content = line[1:]
            if prefix == "-":
                before_lines.append(content)
            elif prefix == "+":
                after_lines.append(content)
            elif prefix == " ":
                before_lines.append(content)
                after_lines.append(content)
        return "\n".join(before_lines), "\n".join(after_lines)

    @staticmethod
    def _ensure_not_summary_only(file_entries: tuple[DiffFileEntry, ...]) -> None:
        for entry in file_entries:
            if entry.status in {"modified", "added"} and not entry.patch_content.strip():
                raise SummaryOnlyDiffError(f"missing hunks for file: {entry.file_path}")

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
                f"evidence_id '{evidence_id}' already bound to risk '{bound_risk}', "
                f"cannot reuse for '{risk_id}'"
            )
