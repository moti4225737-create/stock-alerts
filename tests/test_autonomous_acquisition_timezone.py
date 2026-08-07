from datetime import datetime, time, timezone
from unittest.mock import Mock

from engines.autonomous_acquisition_coordinator import (
    AutonomousAcquisitionCoordinator,
)
from engines.source_acquisition_policy import SourceAcquisitionPolicy


def test_coordinator_uses_source_timezone_for_publication_window() -> None:
    clinical_trials_runner = Mock()

    coordinator = AutonomousAcquisitionCoordinator(
        sources={
            "ClinicalTrials.gov": clinical_trials_runner,
        },
        policies={
            "ClinicalTrials.gov": SourceAcquisitionPolicy(
                source_name="ClinicalTrials.gov",
                interval_seconds=3600,
                publication_time=time(hour=9),
                publication_window_minutes=15,
                publication_interval_seconds=60,
                publication_timezone="America/New_York",
            ),
        },
    )

    coordinator.run_due(
        datetime(
            2026,
            8,
            7,
            12,
            50,
            tzinfo=timezone.utc,
        )
    )

    coordinator.run_due(
        datetime(
            2026,
            8,
            7,
            12,
            51,
            tzinfo=timezone.utc,
        )
    )

    assert clinical_trials_runner.call_count == 2
