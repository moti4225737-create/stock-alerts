from datetime import datetime, timezone
from unittest.mock import Mock

from engines.autonomous_acquisition_coordinator import (
    AutonomousAcquisitionCoordinator,
)
from engines.source_acquisition_policy import SourceAcquisitionPolicy


def test_coordinator_reports_successful_source_execution(capsys) -> None:
    runner = Mock()

    coordinator = AutonomousAcquisitionCoordinator(
        sources={"SEC": runner},
        policies={
            "SEC": SourceAcquisitionPolicy(
                source_name="SEC",
                interval_seconds=60,
            ),
        },
    )

    coordinator.run_due(
        datetime(
            2026,
            8,
            7,
            12,
            0,
            tzinfo=timezone.utc,
        )
    )

    output = capsys.readouterr().out

    assert "[INFO] Autonomous source SEC completed." in output
