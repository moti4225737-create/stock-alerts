from application.gate_evidence_verifier import (
    GateEvidenceVerifier,
)


def test_gate_evidence_verifier_rejects_mismatched_ci_and_deployed_sha() -> None:
    verifier = GateEvidenceVerifier()

    result = verifier.verify(
        authoritative_sha="aaa111",
        ci_sha="aaa111",
        ci_passed=True,
        deployed_sha="bbb222",
        deployment_passed=True,
        health_passed=True,
    )

    assert result.passed is False
    assert "deployed_sha" in result.failures


def test_gate_evidence_verifier_rejects_ci_for_different_sha() -> None:
    verifier = GateEvidenceVerifier()

    result = verifier.verify(
        authoritative_sha="aaa111",
        ci_sha="bbb222",
        ci_passed=True,
        deployed_sha="aaa111",
        deployment_passed=True,
        health_passed=True,
    )

    assert result.passed is False
    assert "ci_sha" in result.failures


def test_gate_evidence_verifier_rejects_failed_ci_for_authoritative_sha() -> None:
    verifier = GateEvidenceVerifier()

    result = verifier.verify(
        authoritative_sha="aaa111",
        ci_sha="aaa111",
        ci_passed=False,
        deployed_sha="aaa111",
        deployment_passed=True,
        health_passed=True,
    )

    assert result.passed is False
    assert "ci_passed" in result.failures


def test_gate_evidence_verifier_rejects_failed_deployment_for_authoritative_sha() -> None:
    verifier = GateEvidenceVerifier()

    result = verifier.verify(
        authoritative_sha="aaa111",
        ci_sha="aaa111",
        ci_passed=True,
        deployed_sha="aaa111",
        deployment_passed=False,
        health_passed=True,
    )

    assert result.passed is False
    assert "deployment_passed" in result.failures


def test_gate_evidence_verifier_rejects_missing_health_evidence() -> None:
    verifier = GateEvidenceVerifier()

    result = verifier.verify(
        authoritative_sha="aaa111",
        ci_sha="aaa111",
        ci_passed=True,
        deployed_sha="aaa111",
        deployment_passed=True,
        health_passed=False,
    )

    assert result.passed is False
    assert "health_passed" in result.failures


def test_gate_evidence_verifier_passes_when_all_required_evidence_matches() -> None:
    verifier = GateEvidenceVerifier()

    result = verifier.verify(
        authoritative_sha="aaa111",
        ci_sha="aaa111",
        ci_passed=True,
        deployed_sha="aaa111",
        deployment_passed=True,
        health_passed=True,
    )

    assert result.passed is True
    assert result.failures == ()


def test_gate_evidence_verifier_rejects_unverified_ci() -> None:
    verifier = GateEvidenceVerifier()

    result = verifier.verify(
        authoritative_sha="aaa111",
        ci_sha=None,
        ci_passed=None,
        deployed_sha="aaa111",
        deployment_passed=True,
        health_passed=True,
    )

    assert result.passed is False
    assert "ci_not_verified" in result.failures


def test_gate_evidence_verifier_rejects_unverified_deployment() -> None:
    verifier = GateEvidenceVerifier()

    result = verifier.verify(
        authoritative_sha="aaa111",
        ci_sha="aaa111",
        ci_passed=True,
        deployed_sha=None,
        deployment_passed=None,
        health_passed=True,
    )

    assert result.passed is False
    assert "deployment_not_verified" in result.failures


def test_gate_evidence_verifier_rejects_unverified_health() -> None:
    verifier = GateEvidenceVerifier()

    result = verifier.verify(
        authoritative_sha="aaa111",
        ci_sha="aaa111",
        ci_passed=True,
        deployed_sha="aaa111",
        deployment_passed=True,
        health_passed=None,
    )

    assert result.passed is False
    assert "health_not_verified" in result.failures


def test_gate_evidence_verifier_rejects_missing_authoritative_sha() -> None:
    verifier = GateEvidenceVerifier()

    result = verifier.verify(
        authoritative_sha="",
        ci_sha="",
        ci_passed=True,
        deployed_sha="",
        deployment_passed=True,
        health_passed=True,
    )

    assert result.passed is False
    assert "authoritative_sha_not_verified" in result.failures
