from dataclasses import dataclass
from typing import Any, Mapping

from application.gate_evidence_verifier import (
    GateEvidenceResult,
    GateEvidenceVerifier,
)


@dataclass(frozen=True)
class GateEvidenceReport:
    verification: GateEvidenceResult
    source_diagnostics: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.verification.passed

    @property
    def failures(self) -> tuple[str, ...]:
        return self.verification.failures


class GateEvidenceCollector:
    def __init__(
        self,
        *,
        github_collector: Any,
        railway_collector: Any,
        healthchecks_collector: Any,
        deployment_status_collector: Any | None = None,
        verifier: GateEvidenceVerifier | None = None,
    ) -> None:
        self._github_collector = github_collector
        self._railway_collector = railway_collector
        self._healthchecks_collector = healthchecks_collector
        self._deployment_status_collector = deployment_status_collector
        self._verifier = verifier or GateEvidenceVerifier()

    def collect_and_verify(
        self,
        *,
        authoritative_sha: str,
        railway_environment: Mapping[str, str],
    ) -> GateEvidenceReport:
        github_evidence = self._github_collector.collect(
            authoritative_sha=authoritative_sha,
        )

        railway_evidence = self._railway_collector.collect(
            environment=railway_environment,
        )

        deployment_status_evidence = None
        if self._deployment_status_collector is not None:
            deployment_status_evidence = (
                self._deployment_status_collector.collect(
                    authoritative_sha=authoritative_sha,
                )
            )

        deployed_at = (
            deployment_status_evidence.deployed_at
            if deployment_status_evidence is not None
            else None
        )

        healthchecks_evidence = self._healthchecks_collector.collect(
            deployed_at=deployed_at,
        )

        deployment_passed = (
            deployment_status_evidence.deployment_passed
            if deployment_status_evidence is not None
            else None
        )

        health_passed = healthchecks_evidence.health_passed

        if (
            deployment_status_evidence is not None
            and deployed_at is None
        ):
            health_passed = None

        verified_deployed_sha = (
            railway_evidence.deployed_sha
            if getattr(railway_evidence, "error", None) is None
            else None
        )

        verification = self._verifier.verify(
            authoritative_sha=authoritative_sha,
            ci_sha=github_evidence.ci_sha,
            ci_passed=github_evidence.ci_passed,
            deployed_sha=verified_deployed_sha,
            deployment_passed=deployment_passed,
            health_passed=health_passed,
        )

        source_diagnostics = tuple(
            diagnostic
            for diagnostic in (
                getattr(github_evidence, "error", None),
                getattr(railway_evidence, "error", None),
                getattr(healthchecks_evidence, "error", None),
                getattr(
                    deployment_status_evidence,
                    "error",
                    None,
                ),
            )
            if diagnostic is not None
        )

        return GateEvidenceReport(
            verification=verification,
            source_diagnostics=source_diagnostics,
        )
