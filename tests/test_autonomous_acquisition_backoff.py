from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from engines.autonomous_acquisition_coordinator import (
    AutonomousAcquisitionCoordinator,
)
from engines.source_acquisition_policy import SourceAcquisitionPolicy


def test_failed_source_uses_exponential_backoff() -> None:
    sec_runner = Mock(
        side_effect=[
            RuntimeError("first failure"),
            RuntimeError("second failure"),
        ]
    )

    coordinator = AutonomousAcquisitionCoordinator(
        sources={
            "SEC": sec_runner,
        },
        policies={
            "SEC": SourceAcquisitionPolicy(
                source_name="SEC",
                interval_seconds=60,
            ),
        },
    )

    start = datetime(
        2026,
        8,
        7,
        12,
        0,
        tzinfo=timezone.utc,
    )

    coordinator.run_due(start)

    coordinator.run_due(
        start + timedelta(seconds=59)
    )
    assert sec_runner.call_count == 1

    coordinator.run_due(
        start + timedelta(seconds=60)
    )
    assert sec_runner.call_count == 2

    coordinator.run_due(
        start + timedelta(seconds=179)
    )
    assert sec_runner.call_count == 2

    coordinator.run_due(
        start + timedelta(seconds=180)
    )
    assert sec_runner.call_count == 3
