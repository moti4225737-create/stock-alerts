from application.gate_evidence_collector import (
    GateEvidenceCollector,
)
from modules.github_ci_evidence_collector import GitHubCIEvidence
from modules.healthchecks_evidence_collector import HealthchecksEvidence
from modules.railway_deployment_evidence_collector import (
    RailwayDeploymentEvidence,
)


class StubGitHubCollector:
    def collect(self, *, authoritative_sha: str) -> GitHubCIEvidence:
        return GitHubCIEvidence(
            ci_sha=authoritative_sha,
            ci_passed=True,
        )


class StubRailwayCollector:
    def collect(self, *, environment: dict[str, str]) -> RailwayDeploymentEvidence:
        return RailwayDeploymentEvidence(
            deployed_sha=environment["RAILWAY_GIT_COMMIT_SHA"],
            branch="main",
            service_name="stock-alerts",
            environment_name="production",
        )


class StubHealthchecksCollector:
    def collect(self, *, deployed_at: str | None = None) -> HealthchecksEvidence:
        return HealthchecksEvidence(
            health_passed=True,
            last_ping="2026-08-23T05:05:22+00:00",
        )


def test_gate_evidence_collector_fails_closed_without_deployment_status_evidence() -> None:
    collector = GateEvidenceCollector(
        github_collector=StubGitHubCollector(),
        railway_collector=StubRailwayCollector(),
        healthchecks_collector=StubHealthchecksCollector(),
    )

    result = collector.collect_and_verify(
        authoritative_sha="aaa111",
        railway_environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "main",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        },
    )

    assert result.passed is False
    assert "deployment_not_verified" in result.failures


class MismatchedRailwayCollector:
    def collect(self, *, environment: dict[str, str]) -> RailwayDeploymentEvidence:
        return RailwayDeploymentEvidence(
            deployed_sha=environment["RAILWAY_GIT_COMMIT_SHA"],
            branch="v0.5",
            service_name="stock-alerts",
            environment_name="production",
            error="railway_deployment_identity_mismatch",
        )


def test_gate_evidence_collector_preserves_railway_source_diagnostic() -> None:
    collector = GateEvidenceCollector(
        github_collector=StubGitHubCollector(),
        railway_collector=MismatchedRailwayCollector(),
        healthchecks_collector=StubHealthchecksCollector(),
    )

    result = collector.collect_and_verify(
        authoritative_sha="aaa111",
        railway_environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "v0.5",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        },
    )

    assert result.passed is False
    assert "deployment_not_verified" in result.failures
    assert (
        "railway_deployment_identity_mismatch"
        in result.source_diagnostics
    )


class FailedGitHubCollector:
    def collect(self, *, authoritative_sha: str) -> GitHubCIEvidence:
        return GitHubCIEvidence(
            ci_sha=None,
            ci_passed=None,
            error="github_api_error",
        )


class FailedHealthchecksCollector:
    def collect(
        self,
        *,
        deployed_at: str | None = None,
    ) -> HealthchecksEvidence:
        return HealthchecksEvidence(
            health_passed=None,
            last_ping=None,
            error="healthchecks_api_error",
        )


def test_gate_evidence_collector_preserves_github_source_diagnostic() -> None:
    collector = GateEvidenceCollector(
        github_collector=FailedGitHubCollector(),
        railway_collector=StubRailwayCollector(),
        healthchecks_collector=StubHealthchecksCollector(),
    )

    result = collector.collect_and_verify(
        authoritative_sha="aaa111",
        railway_environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "main",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        },
    )

    assert result.passed is False
    assert "ci_not_verified" in result.failures
    assert "github_api_error" in result.source_diagnostics


def test_gate_evidence_collector_preserves_healthchecks_source_diagnostic() -> None:
    collector = GateEvidenceCollector(
        github_collector=StubGitHubCollector(),
        railway_collector=StubRailwayCollector(),
        healthchecks_collector=FailedHealthchecksCollector(),
    )

    result = collector.collect_and_verify(
        authoritative_sha="aaa111",
        railway_environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "main",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        },
    )

    assert result.passed is False
    assert "health_not_verified" in result.failures
    assert "healthchecks_api_error" in result.source_diagnostics


class SuccessfulDeploymentStatusCollector:
    def collect(self, *, authoritative_sha: str):
        from modules.railway_deployment_status_evidence_collector import (
            RailwayDeploymentStatusEvidence,
        )

        return RailwayDeploymentStatusEvidence(
            deployment_passed=True,
            deployment_id="deployment-123",
            deployed_sha=authoritative_sha,
            deployed_at="2026-08-23T05:00:00Z",
        )


def test_gate_evidence_collector_passes_when_all_required_evidence_is_verified() -> None:
    collector = GateEvidenceCollector(
        github_collector=StubGitHubCollector(),
        railway_collector=StubRailwayCollector(),
        healthchecks_collector=StubHealthchecksCollector(),
        deployment_status_collector=SuccessfulDeploymentStatusCollector(),
    )

    result = collector.collect_and_verify(
        authoritative_sha="aaa111",
        railway_environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "main",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        },
    )

    assert result.passed is True
    assert result.failures == ()
    assert result.source_diagnostics == ()


class FailedDeploymentStatusCollector:
    def collect(self, *, authoritative_sha: str):
        from modules.railway_deployment_status_evidence_collector import (
            RailwayDeploymentStatusEvidence,
        )

        return RailwayDeploymentStatusEvidence(
            deployment_passed=None,
            deployment_id=None,
            deployed_sha=None,
            error="railway_deployment_status_error",
        )


def test_gate_evidence_collector_preserves_deployment_status_source_diagnostic() -> None:
    collector = GateEvidenceCollector(
        github_collector=StubGitHubCollector(),
        railway_collector=StubRailwayCollector(),
        healthchecks_collector=StubHealthchecksCollector(),
        deployment_status_collector=FailedDeploymentStatusCollector(),
    )

    result = collector.collect_and_verify(
        authoritative_sha="aaa111",
        railway_environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "main",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        },
    )

    assert result.passed is False
    assert "deployment_not_verified" in result.failures
    assert (
        "railway_deployment_status_error"
        in result.source_diagnostics
    )


class TimestampedDeploymentStatusCollector:
    def collect(self, *, authoritative_sha: str):
        from modules.railway_deployment_status_evidence_collector import (
            RailwayDeploymentStatusEvidence,
        )

        return RailwayDeploymentStatusEvidence(
            deployment_passed=True,
            deployment_id="deployment-123",
            deployed_sha=authoritative_sha,
            deployed_at="2026-08-23T05:00:00Z",
        )


class CapturingHealthchecksCollector:
    def __init__(self) -> None:
        self.deployed_at = None

    def collect(
        self,
        *,
        deployed_at: str | None = None,
    ) -> HealthchecksEvidence:
        self.deployed_at = deployed_at

        return HealthchecksEvidence(
            health_passed=True,
            last_ping="2026-08-23T05:05:00Z",
        )


def test_gate_evidence_collector_passes_deployment_timestamp_to_healthchecks() -> None:
    healthchecks_collector = CapturingHealthchecksCollector()

    collector = GateEvidenceCollector(
        github_collector=StubGitHubCollector(),
        railway_collector=StubRailwayCollector(),
        healthchecks_collector=healthchecks_collector,
        deployment_status_collector=TimestampedDeploymentStatusCollector(),
    )

    result = collector.collect_and_verify(
        authoritative_sha="aaa111",
        railway_environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "main",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        },
    )

    assert result.passed is True
    assert healthchecks_collector.deployed_at == "2026-08-23T05:00:00Z"


class SuccessfulDeploymentWithoutTimestampCollector:
    def collect(self, *, authoritative_sha: str):
        from modules.railway_deployment_status_evidence_collector import (
            RailwayDeploymentStatusEvidence,
        )

        return RailwayDeploymentStatusEvidence(
            deployment_passed=True,
            deployment_id="deployment-123",
            deployed_sha=authoritative_sha,
            deployed_at=None,
        )


def test_gate_evidence_collector_fails_closed_when_deployment_timestamp_is_missing() -> None:
    collector = GateEvidenceCollector(
        github_collector=StubGitHubCollector(),
        railway_collector=StubRailwayCollector(),
        healthchecks_collector=StubHealthchecksCollector(),
        deployment_status_collector=SuccessfulDeploymentWithoutTimestampCollector(),
    )

    result = collector.collect_and_verify(
        authoritative_sha="aaa111",
        railway_environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "main",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        },
    )

    assert result.passed is False
    assert "health_not_verified" in result.failures


def test_gate_evidence_collector_fails_when_runtime_identity_mismatches_despite_other_green_evidence() -> None:
    collector = GateEvidenceCollector(
        github_collector=StubGitHubCollector(),
        railway_collector=MismatchedRailwayCollector(),
        healthchecks_collector=StubHealthchecksCollector(),
        deployment_status_collector=TimestampedDeploymentStatusCollector(),
    )

    result = collector.collect_and_verify(
        authoritative_sha="aaa111",
        railway_environment={
            "RAILWAY_GIT_COMMIT_SHA": "aaa111",
            "RAILWAY_GIT_BRANCH": "v0.5",
            "RAILWAY_SERVICE_NAME": "stock-alerts",
            "RAILWAY_ENVIRONMENT_NAME": "production",
        },
    )

    assert result.passed is False
    assert "deployment_not_verified" in result.failures
    assert (
        "railway_deployment_identity_mismatch"
        in result.source_diagnostics
    )
