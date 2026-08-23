from dataclasses import dataclass


@dataclass(frozen=True)
class GateEvidenceResult:
    passed: bool
    failures: tuple[str, ...]


class GateEvidenceVerifier:
    def verify(
        self,
        *,
        authoritative_sha: str,
        ci_sha: str | None,
        ci_passed: bool | None,
        deployed_sha: str | None,
        deployment_passed: bool | None,
        health_passed: bool | None,
    ) -> GateEvidenceResult:
        failures = []

        if not authoritative_sha:
            failures.append("authoritative_sha_not_verified")

        if ci_sha is None or ci_passed is None:
            failures.append("ci_not_verified")
        else:
            if ci_sha != authoritative_sha:
                failures.append("ci_sha")

            if not ci_passed:
                failures.append("ci_passed")

        if deployed_sha is None or deployment_passed is None:
            failures.append("deployment_not_verified")
        else:
            if deployed_sha != authoritative_sha:
                failures.append("deployed_sha")

            if not deployment_passed:
                failures.append("deployment_passed")

        if health_passed is None:
            failures.append("health_not_verified")
        elif not health_passed:
            failures.append("health_passed")

        return GateEvidenceResult(
            passed=not failures,
            failures=tuple(failures),
        )
