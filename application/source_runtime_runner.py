from collections.abc import Callable

from engines.intelligence_pipeline import IntelligencePipeline
from modules.data_provider import DataProvider


class SourceRuntimeRunner:
    def __init__(
        self,
        provider: DataProvider,
        runtime_factory: Callable[[IntelligencePipeline], object],
    ) -> None:
        self._provider = provider
        self._runtime_factory = runtime_factory

    def __call__(self) -> None:
        pipeline = IntelligencePipeline(
            providers=[self._provider],
        )

        runtime = self._runtime_factory(pipeline)
        runtime.run()
