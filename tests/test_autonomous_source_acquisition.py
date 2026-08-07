from unittest.mock import Mock

from application.autonomous_source_acquisition import (
    build_autonomous_source_acquisition,
)
from engines.autonomous_acquisition_coordinator import (
    AutonomousAcquisitionCoordinator,
)
from engines.source_acquisition_policy import SourceAcquisitionPolicy


def test_build_autonomous_source_acquisition_wires_named_sources() -> None:
    providers = {
        "FDA": Mock(),
        "ClinicalTrials.gov": Mock(),
        "SEC": Mock(),
    }
    runtime_factory = Mock()

    policies = {
        "FDA": SourceAcquisitionPolicy(
            source_name="FDA",
            interval_seconds=3600,
        ),
        "ClinicalTrials.gov": SourceAcquisitionPolicy(
            source_name="ClinicalTrials.gov",
            interval_seconds=3600,
        ),
        "SEC": SourceAcquisitionPolicy(
            source_name="SEC",
            interval_seconds=60,
        ),
    }

    coordinator = build_autonomous_source_acquisition(
        providers=providers,
        policies=policies,
        runtime_factory=runtime_factory,
    )

    assert isinstance(
        coordinator,
        AutonomousAcquisitionCoordinator,
    )
    assert tuple(coordinator._sources) == (
        "FDA",
        "ClinicalTrials.gov",
        "SEC",
    )
    assert coordinator._policies is policies
