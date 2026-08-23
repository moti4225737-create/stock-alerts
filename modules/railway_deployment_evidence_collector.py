from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class RailwayDeploymentEvidence:
    deployed_sha: str | None
    branch: str | None
    service_name: str | None
    environment_name: str | None
    error: str | None = None


class RailwayDeploymentEvidenceCollector:
    def collect(
        self,
        *,
        environment: Mapping[str, str],
    ) -> RailwayDeploymentEvidence:
        deployed_sha = environment.get("RAILWAY_GIT_COMMIT_SHA")
        branch = environment.get("RAILWAY_GIT_BRANCH")
        service_name = environment.get("RAILWAY_SERVICE_NAME")
        environment_name = environment.get(
            "RAILWAY_ENVIRONMENT_NAME"
        )

        if not all(
            (
                deployed_sha,
                branch,
                service_name,
                environment_name,
            )
        ):
            return RailwayDeploymentEvidence(
                deployed_sha=deployed_sha,
                branch=branch,
                service_name=service_name,
                environment_name=environment_name,
                error="railway_deployment_identity_incomplete",
            )

        if (
            branch != "main"
            or service_name != "stock-alerts"
            or environment_name != "production"
        ):
            return RailwayDeploymentEvidence(
                deployed_sha=deployed_sha,
                branch=branch,
                service_name=service_name,
                environment_name=environment_name,
                error="railway_deployment_identity_mismatch",
            )

        return RailwayDeploymentEvidence(
            deployed_sha=deployed_sha,
            branch=branch,
            service_name=service_name,
            environment_name=environment_name,
        )
