from __future__ import annotations

from dataclasses import replace

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


def _large_diff(*, file_total: int, commit_sha: str) -> str:
    payload = "x" * 12_000
    blocks = [f"commit {commit_sha}\n"]
    for index in range(file_total):
        file_path = f"app/generated_{index}.py"
        blocks.append(
            "\n".join(
                (
                    f"diff --git a/{file_path} b/{file_path}",
                    f"--- a/{file_path}",
                    f"+++ b/{file_path}",
                    "@@ -1 +1 @@",
                    f"-print('{payload}{index}')",
                    f"+print('{payload}{index} updated')",
                    "",
                )
            )
        )
    return "".join(blocks)


def test_risk1_atomic_save_rejects_missing_diff_and_rolls_back_run() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    run = _run("run-risk1")

    with pytest.raises(MissingDiffSnapshotError, match="diff snapshot is required"):
        repository.save_run_with_diff_snapshot(
            run,
            pr_url="https://github.com/acme/repo/pull/1",
            commit_sha="a" * 40,
            diff_body="",
            expected_size_bytes=0,
            file_count=0,
            task_log_files=(),
        )

    diff = _valid_diff(commit_sha="a" * 40)
    with pytest.raises(DiffSnapshotWriteError, match="db timeout"):
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

    print("risk1_observed: run=None snapshot=None after missing diff and write timeout")
    assert repository.get_run_by_id("run-risk1") is None
    assert repository.get_snapshot_for_run("run-risk1") is None


def test_risk2_partial_diff_persistence_rejected_by_size_validation() -> None:
    large_diff = _large_diff(file_total=100, commit_sha="b" * 40)
    repository = InMemoryPhase9DiffSnapshotRepository(max_diff_bytes=1_000_000)

    with pytest.raises(IncompleteWriteError, match="exceeds configured storage buffer"):
        repository.save_run_with_diff_snapshot(
            _run("run-risk2-oversized"),
            pr_url="https://github.com/acme/repo/pull/2",
            commit_sha="b" * 40,
            diff_body=large_diff,
            expected_size_bytes=len(large_diff.encode("utf-8")),
            file_count=100,
            task_log_files=tuple(f"app/generated_{index}.py" for index in range(100)),
        )

    diff = _valid_diff(commit_sha="b" * 40)
    repository_ok = InMemoryPhase9DiffSnapshotRepository()
    repository_ok.save_run_with_diff_snapshot(
        _run("run-risk2-read"),
        pr_url="https://github.com/acme/repo/pull/2",
        commit_sha="b" * 40,
        diff_body=diff,
        expected_size_bytes=len(diff.encode("utf-8")),
        file_count=1,
        task_log_files=("app/logic.py",),
    )

    key = ("https://github.com/acme/repo/pull/2", "b" * 40)
    repository_ok._snapshot_by_key[key] = replace(
        repository_ok._snapshot_by_key[key],
        expected_size_bytes=repository_ok._snapshot_by_key[key].expected_size_bytes + 1,
    )

    with pytest.raises(IncompleteWriteError, match="stored snapshot is incomplete"):
        repository_ok.get_snapshot_by_pr_and_sha(
            pr_url="https://github.com/acme/repo/pull/2",
            commit_sha="b" * 40,
        )

    print(
        "risk2_observed: oversized_bytes="
        f"{len(large_diff.encode('utf-8'))} readback_size_mismatch_detected=True"
    )


def test_risk3_summary_only_diff_rejected_for_missing_hunks() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    diff = _valid_diff(commit_sha="c" * 40, include_hunk=False)

    with pytest.raises(SummaryOnlyDiffError, match="missing hunks for file: app/logic.py"):
        repository.save_run_with_diff_snapshot(
            _run("run-risk3"),
            pr_url="https://github.com/acme/repo/pull/3",
            commit_sha="c" * 40,
            diff_body=diff,
            expected_size_bytes=len(diff.encode("utf-8")),
            file_count=1,
            task_log_files=("app/logic.py",),
        )

    print("risk3_observed: missing hunks for app/logic.py rejected")


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

    snapshot = repository.get_snapshot_by_pr_and_sha(
        pr_url="https://github.com/acme/repo/pull/4",
        commit_sha="d" * 40,
    )

    assert snapshot is not None
    assert snapshot.file_entries[0].before_content == "print('old')"
    assert snapshot.file_entries[0].after_content == "print('new')"
    assert (
        repository.get_snapshot_by_pr_and_sha(
            pr_url="https://github.com/acme/repo/pull/4",
            commit_sha="e" * 40,
        )
        is None
    )

    with pytest.raises(MetadataBlobMismatchError, match="pr_url and commit_sha are mandatory"):
        repository.get_snapshot_by_pr_and_sha(
            pr_url="https://github.com/acme/repo/pull/4",
            commit_sha="",
        )

    print(
        "risk4_observed: exact_lookup_before=print('old') "
        "after=print('new') wrong_sha=None"
    )


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

    stored_run_evidence = repository.get_run_evidence("run-risk5")
    assert stored_run_evidence is not None
    repository._run_evidence_by_run_id["run-risk5"] = replace(
        repository._run_evidence_by_run_id["run-risk5"],
        commit_sha=new_sha,
    )

    with pytest.raises(VersionConsistencyError, match=f"run commit_sha={new_sha}"):
        Phase9AuditEngine(repository).audit_run("run-risk5")

    print(f"risk5_observed: stale snapshot rejected old_sha={old_sha} new_sha={new_sha}")


def test_risk6_task_log_files_must_be_subset_of_diff_file_list() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    diff = _valid_diff(file_path="README.md", commit_sha="2" * 40)

    with pytest.raises(EvidenceInconsistencyError, match="task log files missing from diff snapshot"):
        repository.save_run_with_diff_snapshot(
            _run("run-risk6"),
            pr_url="https://github.com/acme/repo/pull/6",
            commit_sha="2" * 40,
            diff_body=diff,
            expected_size_bytes=len(diff.encode("utf-8")),
            file_count=1,
            task_log_files=("app/logic.py",),
        )

    print("risk6_observed: task_log_file=app/logic.py missing from diff_file_list=['README.md']")


def test_risk7_audit_uses_stored_evidence_only_without_git_directory(monkeypatch: pytest.MonkeyPatch) -> None:
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

    monkeypatch.setenv("GIT_DIR", "/tmp/definitely-missing-git-dir")
    report = Phase9AuditEngine(repository).audit_run("run-risk7")

    print(
        "risk7_observed: git_dir=/tmp/definitely-missing-git-dir "
        f"report_commit_sha={report['commit_sha']}"
    )
    assert report["run_id"] == "run-risk7"
    assert report["commit_sha"] == "3" * 40
    assert report["file_paths"] == ("app/logic.py",)


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

    with pytest.raises(LegacyDataUnsupportedError, match="unsupported schema_version=1, expected=2"):
        repository.get_snapshot_by_pr_and_sha(
            pr_url="https://github.com/acme/repo/pull/8",
            commit_sha="4" * 40,
        )

    print("risk8_observed: schema_version=1 rejected when supported_version=2")


def test_risk9_metadata_mismatch_is_rejected_for_conflicting_blob_content() -> None:
    repository = InMemoryPhase9DiffSnapshotRepository()
    diff = _valid_diff(file_path="file_a.py", commit_sha="5" * 40)

    with pytest.raises(MetadataBlobMismatchError, match="file_count does not match parsed diff file count"):
        repository.save_run_with_diff_snapshot(
            _run("run-risk9-count"),
            pr_url="https://github.com/acme/repo/pull/9",
            commit_sha="5" * 40,
            diff_body=diff,
            expected_size_bytes=len(diff.encode("utf-8")),
            file_count=2,
            task_log_files=("file_a.py",),
        )

    with pytest.raises(CorruptedDiffFormatError, match="diff_body has no valid diff file headers"):
        repository.save_run_with_diff_snapshot(
            _run("run-risk9-corrupt"),
            pr_url="https://github.com/acme/repo/pull/9",
            commit_sha="5" * 40,
            diff_body="not a unified diff",
            expected_size_bytes=len("not a unified diff".encode("utf-8")),
            file_count=1,
            task_log_files=("file_a.py",),
        )

    print("risk9_observed: file_count mismatch and malformed diff both rejected")


def test_risk10_execution_evidence_reuse_is_rejected() -> None:
    registry = IndependentEvidenceRegistry()
    registry.bind(risk_id="risk-1", evidence_id="exec-001")

    with pytest.raises(
        EvidenceReuseError,
        match="evidence_id 'exec-001' already bound to risk 'risk-1', cannot reuse for 'risk-2'",
    ):
        registry.bind(risk_id="risk-2", evidence_id="exec-001")

    print("risk10_observed: evidence_id exec-001 cannot bind to two risks")
