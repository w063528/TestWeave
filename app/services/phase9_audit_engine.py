from app.storage.phase9_diff_snapshot_repository import (
    InMemoryPhase9DiffSnapshotRepository,
    VersionConsistencyError,
)


class Phase9AuditEngine:
    def __init__(self, evidence_provider: InMemoryPhase9DiffSnapshotRepository) -> None:
        self._evidence_provider = evidence_provider

    def audit_run(self, run_id: str) -> dict[str, object]:
        run = self._evidence_provider.get_run_by_id(run_id)
        if run is None:
            raise VersionConsistencyError(f"run not found: {run_id}")

        snapshot = self._evidence_provider.get_snapshot_for_run(run_id)
        if snapshot is None:
            raise VersionConsistencyError(f"snapshot not found for run: {run_id}")

        snapshot_sha = snapshot.get("commit_sha")
        if snapshot_sha != run.commit_sha:
            raise VersionConsistencyError(
                f"snapshot commit_sha={snapshot_sha} does not match run commit_sha={run.commit_sha}"
            )

        return {
            "run_id": run.run_id,
            "pr_url": run.pr_url,
            "commit_sha": run.commit_sha,
            "snapshot_id": snapshot["snapshot_id"],
            "file_count": snapshot["file_count"],
        }
