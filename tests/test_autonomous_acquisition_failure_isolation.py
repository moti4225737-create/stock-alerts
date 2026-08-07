from datetime import datetime, timezone
from unittest.mock import Mock

from engines.autonomous_acquisition_coordinator import (
    AutonomousAcquisitionCoordinator,
)
from engines.source_acquisition_policy import SourceAcquisitionPolicy


def test_coordinator_isolates_source_failure_and_continues() -> None:
    sec_runner = Mock(side_effect=RuntimeError("SEC failure"))
    fda_runner = Mock()

    coordinator = AutonomousAcquisitionCoordinator(
        sources={
            "SEC": sec_runner,
            "FDA": fda_runner,
        },
        policies={
            "SEC": SourceAcquisitionPolicy(
                source_name="SEC",
                interval_seconds=60,
            ),
            "FDA": SourceAcquisitionPolicy(
                source_name="FDA",
                interval_seconds=60,
            ),
        },
    )

    first_run = datetime(
        2026,
        8,
        7,
        12,
        0,
        tzinfo=timezone.utc,
    )

    coordinator.run_due(first_run)

    assert sec_runner.call_count == 1
    assert fda_runner.call_count == 1

    sec_runner.side_effect = None

    second_run = datetime(
        2026,
        8,
        7,
        12,
        1,
        tzinfo=timezone.utc,
    )

    coordinator.run_due(second_run)

    assert sec_runner.call_count == 2
    assert fda_runner.call_count == 2
