from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class RailwayDeploymentStatusEvidence:
    deployment_passed: bool | None
    deployment_id: str | None
    deployed_sha: str | None
    deployed_at: str | None = None
    error: str | None = None


class RailwayDeploymentStatusEvidenceCollector:
    _FAILED_STATUSES = {
        "FAILED",
        "CRASHED",
    }

    _IN_PROGRESS_STATUSES = {
        "BUILDING",
        "DEPLOYING",
        "INITIALIZING",
        "WAITING",
        "QUEUED",
    }

    def __init__(
        self,
        *,
        requester: Callable[..., Any],
    ) -> None:
        self._requester = requester

    def collect(
        self,
        *,
        authoritative_sha: str,
    ) -> RailwayDeploymentStatusEvidence:
        try:
            payload = self._requester(
                authoritative_sha=authoritative_sha,
            )
        except Exception:
            return RailwayDeploymentStatusEvidence(
                deployment_passed=None,
                deployment_id=None,
                deployed_sha=None,
                error="railway_deployment_status_error",
            )

        deployments = payload.get(
            "deployments",
            [],
        )

        matching_deployment = next(
            (
                deployment
                for deployment in deployments
                if deployment.get("commit_sha") == authoritative_sha
            ),
            None,
        )

        if matching_deployment is None:
            return RailwayDeploymentStatusEvidence(
                deployment_passed=None,
                deployment_id=None,
                deployed_sha=None,
            )

        status = matching_deployment.get("status")

        if status == "SUCCESS":
            deployment_passed = True
        elif status in self._FAILED_STATUSES:
            deployment_passed = False
        elif status in self._IN_PROGRESS_STATUSES:
            deployment_passed = None
        else:
            deployment_passed = None

        return RailwayDeploymentStatusEvidence(
            deployment_passed=deployment_passed,
            deployment_id=matching_deployment.get("id"),
            deployed_sha=matching_deployment.get("commit_sha"),
            deployed_at=matching_deployment.get("created_at"),
        )
