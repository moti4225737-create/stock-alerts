from datetime import datetime, time, timezone
from unittest.mock import Mock

from engines.autonomous_acquisition_coordinator import (
    AutonomousAcquisitionCoordinator,
)
from engines.source_acquisition_policy import SourceAcquisitionPolicy


def test_coordinator_runs_due_source_and_skips_not_due_source() -> None:
    sec_runner = Mock()
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
                interval_seconds=3600,
            ),
        },
    )

    now = datetime(
        2026,
        8,
        7,
        12,
        0,
        tzinfo=timezone.utc,
    )

    coordinator.run_due(now)
    coordinator.run_due(
        datetime(
            2026,
            8,
            7,
            12,
            1,
            tzinfo=timezone.utc,
        )
    )

    assert sec_runner.call_count == 2
    assert fda_runner.call_count == 1


def test_coordinator_uses_faster_interval_inside_publication_window() -> None:
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
            ),
        },
    )

    coordinator.run_due(
        datetime(
            2026,
            8,
            7,
            8,
            50,
            tzinfo=timezone.utc,
        )
    )

    coordinator.run_due(
        datetime(
            2026,
            8,
            7,
            8,
            51,
            tzinfo=timezone.utc,
        )
    )

    assert clinical_trials_runner.call_count == 2


def test_coordinator_returns_to_normal_interval_after_publication_window() -> None:
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
            ),
        },
    )

    coordinator.run_due(
        datetime(
            2026,
            8,
            7,
            9,
            14,
            tzinfo=timezone.utc,
        )
    )

    coordinator.run_due(
        datetime(
            2026,
            8,
            7,
            9,
            15,
            tzinfo=timezone.utc,
        )
    )

    coordinator.run_due(
        datetime(
            2026,
            8,
            7,
            9,
            16,
            tzinfo=timezone.utc,
        )
    )

    assert clinical_trials_runner.call_count == 2
