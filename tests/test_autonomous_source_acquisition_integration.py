from datetime import datetime, timezone
from unittest.mock import Mock

from application.autonomous_source_acquisition import (
    build_autonomous_source_acquisition,
)
from engines.intelligence_pipeline import IntelligencePipeline
from engines.source_acquisition_policy import SourceAcquisitionPolicy


def test_autonomous_acquisition_runs_due_source_through_single_provider_pipeline() -> None:
    sec_provider = Mock()
    fda_provider = Mock()

    providers = {
        "SEC": sec_provider,
        "FDA": fda_provider,
    }

    policies = {
        "SEC": SourceAcquisitionPolicy(
            source_name="SEC",
            interval_seconds=60,
        ),
        "FDA": SourceAcquisitionPolicy(
            source_name="FDA",
            interval_seconds=3600,
        ),
    }

    created_runtimes: list[tuple[IntelligencePipeline, Mock]] = []

    def runtime_factory(
        pipeline: IntelligencePipeline,
    ) -> Mock:
        runtime = Mock()
        created_runtimes.append((pipeline, runtime))
        return runtime

    coordinator = build_autonomous_source_acquisition(
        providers=providers,
        policies=policies,
        runtime_factory=runtime_factory,
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

    assert len(created_runtimes) == 2

    first_pipeline, first_runtime = created_runtimes[0]
    second_pipeline, second_runtime = created_runtimes[1]

    assert first_pipeline.providers == [sec_provider]
    assert second_pipeline.providers == [fda_provider]

    first_runtime.run.assert_called_once_with()
    second_runtime.run.assert_called_once_with()

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

    assert len(created_runtimes) == 3

    third_pipeline, third_runtime = created_runtimes[2]

    assert third_pipeline.providers == [sec_provider]
    third_runtime.run.assert_called_once_with()
