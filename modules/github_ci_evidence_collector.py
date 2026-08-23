from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class GitHubCIEvidence:
    ci_sha: str | None
    ci_passed: bool | None
    error: str | None = None


class GitHubCIEvidenceCollector:
    def __init__(
        self,
        *,
        owner: str,
        repo: str,
        requester: Callable[..., Any],
    ) -> None:
        self._owner = owner
        self._repo = repo
        self._requester = requester

    @staticmethod
    def _run_sort_key(run: dict[str, Any]) -> tuple[str, int]:
        timestamp = (
            run.get("run_started_at")
            or run.get("created_at")
            or ""
        )

        run_id = run.get("id") or 0

        return timestamp, int(run_id)

    def collect(
        self,
        *,
        authoritative_sha: str,
    ) -> GitHubCIEvidence:
        url = (
            f"https://api.github.com/repos/"
            f"{self._owner}/{self._repo}/actions/runs"
        )

        try:
            response = self._requester(
                url,
                params={
                    "head_sha": authoritative_sha,
                    "branch": "main",
                },
                timeout=10,
            )
            response.raise_for_status()

            payload = response.json()
        except Exception:
            return GitHubCIEvidence(
                ci_sha=None,
                ci_passed=None,
                error="github_api_error",
            )

        workflow_runs = payload.get(
            "workflow_runs",
            [],
        )

        matching_runs = [
            run
            for run in workflow_runs
            if (
                run.get("head_sha") == authoritative_sha
                and run.get("head_branch") == "main"
            )
        ]

        if not matching_runs:
            return GitHubCIEvidence(
                ci_sha=None,
                ci_passed=None,
            )

        matching_run = max(
            matching_runs,
            key=self._run_sort_key,
        )

        status = matching_run.get("status")
        conclusion = matching_run.get("conclusion")

        if status != "completed":
            ci_passed = None
        else:
            ci_passed = conclusion == "success"

        return GitHubCIEvidence(
            ci_sha=matching_run.get("head_sha"),
            ci_passed=ci_passed,
        )
