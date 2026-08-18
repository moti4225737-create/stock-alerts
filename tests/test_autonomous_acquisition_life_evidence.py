from datetime import datetime, timezone
from unittest.mock import Mock

from engines.autonomous_acquisition_coordinator import (
    AutonomousAcquisitionCoordinator,
)
from engines.source_acquisition_policy import SourceAcquisitionPolicy


def make_coordinator(
    runner: Mock,
    evidence_reporter: Mock,
) -> AutonomousAcquisitionCoordinator:
    return AutonomousAcquisitionCoordinator(
        sources={"SEC": runner},
        policies={
            "SEC": SourceAcquisitionPolicy(
                source_name="SEC",
                interval_seconds=60,
            ),
        },
        work_evidence_reporter=evidence_reporter,
    )


def test_successful_source_execution_emits_work_evidence() -> None:
    runner = Mock()
    evidence_reporter = Mock()

    coordinator = make_coordinator(
        runner=runner,
        evidence_reporter=evidence_reporter,
    )

    now = datetime(
        2026,
        8,
        18,
        8,
        0,
        tzinfo=timezone.utc,
    )

    coordinator.run_due(now)

    evidence_reporter.assert_called_once_with(
        source_name="SEC",
        completed_at=now,
    )


def test_failed_source_execution_does_not_emit_success_evidence() -> None:
    runner = Mock(
        side_effect=RuntimeError("source unavailable"),
    )
    evidence_reporter = Mock()

    coordinator = make_coordinator(
        runner=runner,
        evidence_reporter=evidence_reporter,
    )

    coordinator.run_due(
        datetime(
            2026,
            8,
            18,
            8,
            0,
            tzinfo=timezone.utc,
        )
    )

    evidence_reporter.assert_not_called()


def test_evidence_reporting_failure_does_not_fail_source_execution() -> None:
    runner = Mock()
    evidence_reporter = Mock(
        side_effect=RuntimeError("lifeguard unavailable"),
    )

    coordinator = make_coordinator(
        runner=runner,
        evidence_reporter=evidence_reporter,
    )

    now = datetime(
        2026,
        8,
        18,
        8,
        0,
        tzinfo=timezone.utc,
    )

    coordinator.run_due(now)

    runner.assert_called_once_with()

    evidence_reporter.assert_called_once_with(
        source_name="SEC",
        completed_at=now,
    )
