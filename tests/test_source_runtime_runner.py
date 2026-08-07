from unittest.mock import Mock

from application.source_runtime_runner import SourceRuntimeRunner
from engines.intelligence_pipeline import IntelligencePipeline


def test_source_runtime_runner_uses_single_provider_pipeline() -> None:
    provider = Mock()
    runtime_factory = Mock()
    runtime = Mock()
    runtime_factory.return_value = runtime

    runner = SourceRuntimeRunner(
        provider=provider,
        runtime_factory=runtime_factory,
    )

    runner()

    runtime_factory.assert_called_once()

    pipeline = runtime_factory.call_args.args[0]

    assert isinstance(pipeline, IntelligencePipeline)
    assert pipeline.providers == [provider]

    runtime.run.assert_called_once_with()
