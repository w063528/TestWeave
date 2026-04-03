from app.storage.phase9_diff_snapshot_repository import EvidenceProvider, VersionConsistencyError


class Phase9AuditEngine:
    def __init__(self, evidence_provider: EvidenceProvider) -> None:
        self._evidence_provider = evidence_provider

    def audit_run(self, run_id: str) -> dict[str, object]:
        run_evidence = self._evidence_provider.get_run_evidence(run_id)
        if run_evidence is None:
            raise VersionConsistencyError(f"run not found: {run_id}")

        snapshot = self._evidence_provider.get_snapshot_for_run(run_id)
        if snapshot is None:
            raise VersionConsistencyError(f"snapshot not found for run: {run_id}")

        if snapshot.commit_sha != run_evidence.commit_sha:
            raise VersionConsistencyError(
                f"snapshot commit_sha={snapshot.commit_sha} "
                f"does not match run commit_sha={run_evidence.commit_sha}"
            )

        return {
            "run_id": run_evidence.run.run_id,
            "pr_url": run_evidence.pr_url,
            "commit_sha": run_evidence.commit_sha,
            "snapshot_id": snapshot.snapshot_id,
            "file_count": snapshot.file_count,
            "file_paths": snapshot.file_paths,
        }
