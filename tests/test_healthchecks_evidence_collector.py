from unittest.mock import Mock

from modules.healthchecks_evidence_collector import (
    HealthchecksEvidenceCollector,
)


def test_healthchecks_collector_returns_pass_for_up_check() -> None:
    response = Mock()
    response.json.return_value = {
        "checks": [
            {
                "name": "Stock Sentinel - Production Life",
                "status": "up",
                "last_ping": "2026-08-22T18:30:00Z",
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = HealthchecksEvidenceCollector(
        check_name="Stock Sentinel - Production Life",
        requester=requester,
    )

    evidence = collector.collect()

    assert evidence.health_passed is True
    assert evidence.error is None


def test_healthchecks_collector_returns_failed_for_down_check() -> None:
    response = Mock()
    response.json.return_value = {
        "checks": [
            {
                "name": "Stock Sentinel - Production Life",
                "status": "down",
                "last_ping": "2026-08-22T18:30:00Z",
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = HealthchecksEvidenceCollector(
        check_name="Stock Sentinel - Production Life",
        requester=requester,
    )

    evidence = collector.collect()

    assert evidence.health_passed is False
    assert evidence.last_ping == "2026-08-22T18:30:00Z"
    assert evidence.error is None


def test_healthchecks_collector_returns_not_verified_when_check_is_missing() -> None:
    response = Mock()
    response.json.return_value = {
        "checks": [
            {
                "name": "Some Other Check",
                "status": "up",
                "last_ping": "2026-08-22T18:30:00Z",
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = HealthchecksEvidenceCollector(
        check_name="Stock Sentinel - Production Life",
        requester=requester,
    )

    evidence = collector.collect()

    assert evidence.health_passed is None
    assert evidence.last_ping is None
    assert evidence.error is None


def test_healthchecks_collector_rejects_stale_ping_before_deployment() -> None:
    response = Mock()
    response.json.return_value = {
        "checks": [
            {
                "name": "Stock Sentinel - Production Life",
                "status": "up",
                "last_ping": "2026-08-22T18:30:00Z",
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = HealthchecksEvidenceCollector(
        check_name="Stock Sentinel - Production Life",
        requester=requester,
    )

    evidence = collector.collect(
        deployed_at="2026-08-22T18:31:00Z",
    )

    assert evidence.health_passed is False
    assert evidence.last_ping == "2026-08-22T18:30:00Z"


def test_healthchecks_collector_accepts_fresh_ping_after_deployment() -> None:
    response = Mock()
    response.json.return_value = {
        "checks": [
            {
                "name": "Stock Sentinel - Production Life",
                "status": "up",
                "last_ping": "2026-08-22T18:32:00Z",
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = HealthchecksEvidenceCollector(
        check_name="Stock Sentinel - Production Life",
        requester=requester,
    )

    evidence = collector.collect(
        deployed_at="2026-08-22T18:31:00Z",
    )

    assert evidence.health_passed is True
    assert evidence.last_ping == "2026-08-22T18:32:00Z"
    assert evidence.error is None


def test_healthchecks_collector_returns_not_verified_on_api_failure() -> None:
    requester = Mock(
        side_effect=RuntimeError("Healthchecks unavailable")
    )

    collector = HealthchecksEvidenceCollector(
        check_name="Stock Sentinel - Production Life",
        requester=requester,
    )

    evidence = collector.collect(
        deployed_at="2026-08-22T18:31:00Z",
    )

    assert evidence.health_passed is None
    assert evidence.last_ping is None
    assert evidence.error == "healthchecks_api_error"


def test_healthchecks_collector_uses_read_only_api_key_header() -> None:
    response = Mock()
    response.json.return_value = {
        "checks": []
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = HealthchecksEvidenceCollector(
        check_name="Stock Sentinel - Production Life",
        requester=requester,
        api_key="test-read-only-key",
    )

    collector.collect()

    requester.assert_called_once_with(
        "https://healthchecks.io/api/v3/checks/",
        headers={
            "Accept": "application/json",
            "User-Agent": "Stock-Sentinel-Gate-Evidence",
            "X-Api-Key": "test-read-only-key",
        },
        timeout=10,
    )


def test_healthchecks_collector_returns_not_verified_when_up_check_has_no_last_ping() -> None:
    response = Mock()
    response.json.return_value = {
        "checks": [
            {
                "name": "Stock Sentinel - Production Life",
                "status": "up",
                "last_ping": None,
            }
        ]
    }
    response.raise_for_status = Mock()

    requester = Mock(return_value=response)

    collector = HealthchecksEvidenceCollector(
        check_name="Stock Sentinel - Production Life",
        requester=requester,
    )

    evidence = collector.collect(
        deployed_at="2026-08-23T05:00:00Z",
    )

    assert evidence.health_passed is None
    assert evidence.last_ping is None
    assert evidence.error is None
