from __future__ import annotations

import os

import pytest

from app.models.tc_list_entry import TCListEntry
from app.models.test_run import TestRun
from app.services.phase9_audit_engine import Phase9AuditEngine
from app.storage.phase9_diff_snapshot_repository import (
    CorruptedDiffFormatError,
    DiffSnapshotWriteError,
    EvidenceInconsistencyError,
    EvidenceReuseError,
    InMemoryPhase9DiffSnapshotRepository,
    IncompleteWriteError,
    IndependentEvidenceRegistry,
    LegacyDataUnsupportedError,
    MetadataBlobMismatchError,
    MissingDiffSnapshotError,
    SummaryOnlyDiffError,
    VersionConsistencyError,
)


def _run(run_id: str) -> TestRun:
    return TestRun(
        run_id=run_id,
        cycle_id="cycle-1",
        run_name="Phase9 Run",
        cycle_snapshot_entries=(
            TCListEntry(
                suite_id="suite-1",
                suite_name="Suite",
                testcase_id="TC-1",
                testcase_name="Case",
            ),
        ),
    )


def _valid_diff(
    *,
    file_path: str = "app/logic.py",
    commit_sha: str | None = None,
    include_hunk: bool = True,
) -> str:
    commit_prefix = "" if commit_sha is None else f"commit {commit_sha}\n"
    hunk = "@@ -1 +1 @@\n-print('old')\n+print('new')\n" if include_hunk else ""
    return (
        f"{commit_prefix}"
        f"diff --git a/{file_path} b/{file_path}\n"
        f"--- a/{file_path}\n"
        f"+++ b/{file_path}\n"
        f"{hunk}"
    )


def test_risk1_atomic_save_rejects_missing_diff_and_rolls_back_run() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    run = _run("run-risk1")

    with pytest.raises(MissingDiffSnapshotError):
        repository.save_run_with_diff_snapshot(
            run,
            pr_url="https://github.com/acme/repo/pull/1",
            commit_sha="a" * 40,
            diff_body="",
            expected_size_bytes=0,
            file_count=0,
            task_log_files=(),
        )

    assert repository.get_run_by_id("run-risk1") is None

    diff = _valid_diff(commit_sha="a" * 40)
    with pytest.raises(DiffSnapshotWriteError):
        repository.save_run_with_diff_snapshot(
            run,
            pr_url="https://github.com/acme/repo/pull/1",
            commit_sha="a" * 40,
            diff_body=diff,
            expected_size_bytes=len(diff.encode("utf-8")),
            file_count=1,
            task_log_files=("app/logic.py",),
            write_guard=lambda: (_ for _ in ()).throw(DiffSnapshotWriteError("db timeout")),
        )

    assert repository.get_run_by_id("run-risk1") is None


def test_risk2_partial_diff_persistence_rejected_by_size_validation() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    diff = _valid_diff(commit_sha="b" * 40)

    with pytest.raises(IncompleteWriteError):
        repository.save_run_with_diff_snapshot(
            _run("run-risk2"),
            pr_url="https://github.com/acme/repo/pull/2",
            commit_sha="b" * 40,
            diff_body=diff,
            expected_size_bytes=1_000_000,
            file_count=1,
            task_log_files=("app/logic.py",),
        )


def test_risk3_summary_only_diff_rejected_for_missing_hunks() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    diff = _valid_diff(commit_sha="c" * 40, include_hunk=False)

    with pytest.raises(SummaryOnlyDiffError):
        repository.save_run_with_diff_snapshot(
            _run("run-risk3"),
            pr_url="https://github.com/acme/repo/pull/3",
            commit_sha="c" * 40,
            diff_body=diff,
            expected_size_bytes=len(diff.encode("utf-8")),
            file_count=1,
            task_log_files=("app/logic.py",),
        )


def test_risk4_snapshot_lookup_requires_exact_pr_url_and_commit_sha_match() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    diff = _valid_diff(commit_sha="d" * 40)
    repository.save_run_with_diff_snapshot(
        _run("run-risk4"),
        pr_url="https://github.com/acme/repo/pull/4",
        commit_sha="d" * 40,
        diff_body=diff,
        expected_size_bytes=len(diff.encode("utf-8")),
        file_count=1,
        task_log_files=("app/logic.py",),
    )

    assert (
        repository.get_snapshot_by_pr_and_sha(
            pr_url="https://github.com/acme/repo/pull/4",
            commit_sha="e" * 40,
        )
        is None
    )

    with pytest.raises(MetadataBlobMismatchError):
        repository.get_snapshot_by_pr_and_sha(pr_url="https://github.com/acme/repo/pull/4", commit_sha="")


def test_risk5_stale_snapshot_rejected_by_sha_handshake() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    old_sha = "f" * 40
    new_sha = "1" * 40
    diff = _valid_diff(commit_sha=old_sha)

    repository.save_run_with_diff_snapshot(
        _run("run-risk5"),
        pr_url="https://github.com/acme/repo/pull/5",
        commit_sha=old_sha,
        diff_body=diff,
        expected_size_bytes=len(diff.encode("utf-8")),
        file_count=1,
        task_log_files=("app/logic.py",),
    )

    stored_run = repository.get_run_by_id("run-risk5")
    assert stored_run is not None
    repository._runs["run-risk5"] = TestRun(
        run_id=stored_run.run_id,
        cycle_id=stored_run.cycle_id,
        run_name=stored_run.run_name,
        cycle_snapshot_entries=stored_run.cycle_snapshot_entries,
        pr_url=stored_run.pr_url,
        commit_sha=new_sha,
        diff_snapshot_id=stored_run.diff_snapshot_id,
    )

    engine = Phase9AuditEngine(repository)
    with pytest.raises(VersionConsistencyError):
        engine.audit_run("run-risk5")


def test_risk6_task_log_files_must_be_subset_of_diff_file_list() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    diff = _valid_diff(file_path="README.md", commit_sha="2" * 40)

    with pytest.raises(EvidenceInconsistencyError):
        repository.save_run_with_diff_snapshot(
            _run("run-risk6"),
            pr_url="https://github.com/acme/repo/pull/6",
            commit_sha="2" * 40,
            diff_body=diff,
            expected_size_bytes=len(diff.encode("utf-8")),
            file_count=1,
            task_log_files=("app/logic.py",),
        )


def test_risk7_audit_uses_stored_evidence_only_without_git_directory() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    diff = _valid_diff(commit_sha="3" * 40)
    repository.save_run_with_diff_snapshot(
        _run("run-risk7"),
        pr_url="https://github.com/acme/repo/pull/7",
        commit_sha="3" * 40,
        diff_body=diff,
        expected_size_bytes=len(diff.encode("utf-8")),
        file_count=1,
        task_log_files=("app/logic.py",),
    )

    old_git_dir = os.environ.get("GIT_DIR")
    os.environ["GIT_DIR"] = "/tmp/definitely-missing-git-dir"
    try:
        report = Phase9AuditEngine(repository).audit_run("run-risk7")
    finally:
        if old_git_dir is None:
            os.environ.pop("GIT_DIR", None)
        else:
            os.environ["GIT_DIR"] = old_git_dir

    assert report["run_id"] == "run-risk7"
    assert report["commit_sha"] == "3" * 40


def test_risk8_schema_version_drift_fails_read_instead_of_partial_deserialize() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository(supported_schema_version=1)
    diff = _valid_diff(commit_sha="4" * 40)
    repository.save_run_with_diff_snapshot(
        _run("run-risk8"),
        pr_url="https://github.com/acme/repo/pull/8",
        commit_sha="4" * 40,
        diff_body=diff,
        expected_size_bytes=len(diff.encode("utf-8")),
        file_count=1,
        task_log_files=("app/logic.py",),
    )

    repository.set_supported_schema_version(2)
    with pytest.raises(LegacyDataUnsupportedError):
        repository.get_snapshot_by_pr_and_sha(
            pr_url="https://github.com/acme/repo/pull/8",
            commit_sha="4" * 40,
        )


def test_risk9_metadata_mismatch_and_corrupted_diff_are_rejected() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    diff = _valid_diff(file_path="file_a.py", commit_sha="5" * 40)

    with pytest.raises(MetadataBlobMismatchError):
        repository.save_run_with_diff_snapshot(
            _run("run-risk9-a"),
            pr_url="https://github.com/acme/repo/pull/9",
            commit_sha="5" * 40,
            diff_body=diff,
            expected_size_bytes=len(diff.encode("utf-8")),
            file_count=2,
            task_log_files=("file_a.py",),
        )

    corrupted = "this is not a valid unified diff"
    with pytest.raises(CorruptedDiffFormatError):
        repository.save_run_with_diff_snapshot(
            _run("run-risk9-b"),
            pr_url="https://github.com/acme/repo/pull/9",
            commit_sha="5" * 40,
            diff_body=corrupted,
            expected_size_bytes=len(corrupted.encode("utf-8")),
            file_count=1,
            task_log_files=("file_a.py",),
        )


def test_risk10_execution_evidence_reuse_is_rejected() -> None:
    registry = IndependentEvidenceRegistry()
    registry.bind(risk_id="risk-1", evidence_id="exec-001")

    with pytest.raises(EvidenceReuseError):
        registry.bind(risk_id="risk-2", evidence_id="exec-001")
