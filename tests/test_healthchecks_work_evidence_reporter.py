from datetime import datetime, timezone
from unittest.mock import Mock

from modules.healthchecks_work_evidence_reporter import (
    HealthchecksWorkEvidenceReporter,
)


def test_reporter_pings_configured_healthchecks_url() -> None:
    response = Mock()
    requester = Mock(return_value=response)

    reporter = HealthchecksWorkEvidenceReporter(
        ping_url="https://example.test/ping",
        requester=requester,
        timeout_seconds=2,
    )

    reporter(
        source_name="SEC",
        completed_at=datetime(
            2026,
            8,
            18,
            8,
            0,
            tzinfo=timezone.utc,
        ),
    )

    requester.assert_called_once_with(
        "https://example.test/ping",
        timeout=2,
    )
    response.raise_for_status.assert_called_once_with()
