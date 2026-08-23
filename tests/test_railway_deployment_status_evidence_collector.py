from unittest.mock import Mock

from modules.railway_deployment_status_evidence_collector import (
    RailwayDeploymentStatusEvidenceCollector,
)


def test_railway_deployment_status_collector_returns_pass_for_success() -> None:
    requester = Mock(
        return_value={
            "deployments": [
                {
                    "id": "deployment-123",
                    "status": "SUCCESS",
                    "commit_sha": "aaa111",
                }
            ]
        }
    )

    collector = RailwayDeploymentStatusEvidenceCollector(
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.deployment_passed is True
    assert evidence.deployment_id == "deployment-123"
    assert evidence.deployed_sha == "aaa111"
    assert evidence.error is None


def test_railway_deployment_status_collector_returns_failed_for_failed_deployment() -> None:
    requester = Mock(
        return_value={
            "deployments": [
                {
                    "id": "deployment-123",
                    "status": "FAILED",
                    "commit_sha": "aaa111",
                }
            ]
        }
    )

    collector = RailwayDeploymentStatusEvidenceCollector(
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.deployment_passed is False
    assert evidence.deployment_id == "deployment-123"
    assert evidence.deployed_sha == "aaa111"
    assert evidence.error is None


def test_railway_deployment_status_collector_returns_not_verified_when_matching_deployment_is_missing() -> None:
    requester = Mock(
        return_value={
            "deployments": [
                {
                    "id": "deployment-456",
                    "status": "SUCCESS",
                    "commit_sha": "bbb222",
                }
            ]
        }
    )

    collector = RailwayDeploymentStatusEvidenceCollector(
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.deployment_passed is None
    assert evidence.deployment_id is None
    assert evidence.deployed_sha is None
    assert evidence.error is None


def test_railway_deployment_status_collector_returns_not_verified_on_request_failure() -> None:
    requester = Mock(
        side_effect=RuntimeError("Railway unavailable")
    )

    collector = RailwayDeploymentStatusEvidenceCollector(
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.deployment_passed is None
    assert evidence.deployment_id is None
    assert evidence.deployed_sha is None
    assert evidence.error == "railway_deployment_status_error"


def test_railway_deployment_status_collector_returns_not_verified_for_in_progress_deployment() -> None:
    requester = Mock(
        return_value={
            "deployments": [
                {
                    "id": "deployment-123",
                    "status": "DEPLOYING",
                    "commit_sha": "aaa111",
                }
            ]
        }
    )

    collector = RailwayDeploymentStatusEvidenceCollector(
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.deployment_passed is None
    assert evidence.deployment_id == "deployment-123"
    assert evidence.deployed_sha == "aaa111"
    assert evidence.error is None


def test_railway_deployment_status_collector_preserves_deployment_timestamp() -> None:
    requester = Mock(
        return_value={
            "deployments": [
                {
                    "id": "deployment-123",
                    "status": "SUCCESS",
                    "commit_sha": "aaa111",
                    "created_at": "2026-08-23T05:00:00Z",
                }
            ]
        }
    )

    collector = RailwayDeploymentStatusEvidenceCollector(
        requester=requester,
    )

    evidence = collector.collect(
        authoritative_sha="aaa111",
    )

    assert evidence.deployment_passed is True
    assert evidence.deployed_at == "2026-08-23T05:00:00Z"
