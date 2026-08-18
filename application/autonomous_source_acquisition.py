from collections.abc import Callable

from application.source_runtime_runner import SourceRuntimeRunner
from engines.autonomous_acquisition_coordinator import (
    AutonomousAcquisitionCoordinator,
)
from engines.source_acquisition_policy import SourceAcquisitionPolicy
from modules.data_provider import DataProvider


def build_autonomous_source_acquisition(
    providers: dict[str, DataProvider],
    policies: dict[str, SourceAcquisitionPolicy],
    runtime_factory: object,
    work_evidence_reporter: Callable[..., None] | None = None,
) -> AutonomousAcquisitionCoordinator:
    sources = {
        source_name: SourceRuntimeRunner(
            provider=provider,
            runtime_factory=runtime_factory,
        )
        for source_name, provider in providers.items()
    }

    return AutonomousAcquisitionCoordinator(
        sources=sources,
        policies=policies,
        work_evidence_reporter=work_evidence_reporter,
    )
