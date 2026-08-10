from collections.abc import Callable
from typing import Protocol

from models.ai_benchmark_case import AIBenchmarkCase
from models.ai_benchmark_result import AIBenchmarkResult
from models.analyzer_execution_result import AnalyzerExecutionResult
from models.source_document import SourceDocument


class BenchmarkAnalyzer(Protocol):
    def analyze(
        self,
        document: SourceDocument,
    ) -> AnalyzerExecutionResult:
        ...


class AIBenchmarkRunner:
    def __init__(
        self,
        provider: str,
        model: str,
        analyzer: BenchmarkAnalyzer,
        clock: Callable[[], float],
    ) -> None:
        if not provider.strip():
            raise ValueError("provider is required")

        if not model.strip():
            raise ValueError("model is required")

        self._provider = provider
        self._model = model
        self._analyzer = analyzer
        self._clock = clock

    def run(
        self,
        benchmark_case: AIBenchmarkCase,
    ) -> AIBenchmarkResult:
        started_at = self._clock()

        execution = self._analyzer.analyze(
            benchmark_case.document
        )

        finished_at = self._clock()

        return AIBenchmarkResult(
            provider=self._provider,
            model=self._model,
            proposals=execution.proposals,
            latency_seconds=finished_at - started_at,
            input_tokens=execution.input_tokens,
            output_tokens=execution.output_tokens,
        )
