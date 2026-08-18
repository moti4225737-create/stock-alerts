from unittest.mock import Mock, patch

from application.autonomous_source_acquisition import (
    build_autonomous_source_acquisition,
)


def test_builder_wires_work_evidence_reporter_to_coordinator() -> None:
    providers = {"SEC": Mock()}
    policies = {"SEC": Mock()}
    runtime_factory = Mock()
    evidence_reporter = Mock()

    coordinator = Mock()

    with patch(
        "application.autonomous_source_acquisition."
        "AutonomousAcquisitionCoordinator",
        return_value=coordinator,
    ) as coordinator_factory:
        result = build_autonomous_source_acquisition(
            providers=providers,
            policies=policies,
            runtime_factory=runtime_factory,
            work_evidence_reporter=evidence_reporter,
        )

    assert result is coordinator

    kwargs = coordinator_factory.call_args.kwargs

    assert kwargs["policies"] is policies
    assert kwargs["work_evidence_reporter"] is evidence_reporter
    assert "SEC" in kwargs["sources"]
